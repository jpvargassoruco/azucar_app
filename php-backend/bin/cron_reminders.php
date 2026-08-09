<?php

declare(strict_types=1);

/**
 * Every-minute reminder job (panel cron: * * * * * php .../bin/cron_reminders.php).
 *
 * Replaces the Docker scheduler (check_reminders.py) + Redis queue + worker:
 * checks alarms and medication doses, then sends the pushes inline.
 *
 * Improvements over the original, per the migration plan:
 * - Time-window catch-up: every minute in (last_run, now] is checked (capped
 *   at 10), so a skipped/late cron minute no longer silently drops reminders.
 * - Dedup via the sent_notifications table (replaces Redis SETEX) makes
 *   delivery at-least-once-with-dedup even across overlapping runs.
 * - Timezone comes from APP_TZ instead of a hardcoded UTC-4.
 */

use Azucar\Database;
use Azucar\Services\PushService;
use Azucar\Support\Dt;

require dirname(__DIR__) . '/vendor/autoload.php';
Dotenv\Dotenv::createImmutable(dirname(__DIR__))->safeLoad();
date_default_timezone_set('UTC');

const WINDOW_CAP_MINUTES = 10;

$logDir = dirname(__DIR__) . '/logs';
if (!is_dir($logDir)) {
    mkdir($logDir, 0775, true);
}
$lock = fopen($logDir . '/cron_reminders.lock', 'c');
if ($lock === false || !flock($lock, LOCK_EX | LOCK_NB)) {
    logLine('Previous run still active; exiting.');
    exit(0);
}

$pdo = Database::pdo();
$push = new PushService();

// ---- Compute the minute window (UTC) ----
$now = new DateTimeImmutable('now', Dt::utc());
$nowMinute = $now->setTime((int) $now->format('H'), (int) $now->format('i'));

$lastRun = $pdo->query('SELECT last_run_utc FROM cron_state WHERE id = 1')->fetchColumn();
if ($lastRun !== false) {
    $lastRunDt = new DateTimeImmutable((string) $lastRun, Dt::utc());
    $lastRunMinute = $lastRunDt->setTime((int) $lastRunDt->format('H'), (int) $lastRunDt->format('i'));
} else {
    $lastRunMinute = $nowMinute->modify('-1 minute');
}

$minutes = [];
for ($m = $lastRunMinute->modify('+1 minute'); $m <= $nowMinute; $m = $m->modify('+1 minute')) {
    $minutes[] = $m;
}
if ($minutes === []) {
    $minutes = [$nowMinute]; // same-minute rerun: still check the current minute
}
if (count($minutes) > WINDOW_CAP_MINUTES) {
    $minutes = array_slice($minutes, -WINDOW_CAP_MINUTES);
}

$appTz = Dt::appTz();
logLine(sprintf('Checking %d minute(s), local now %s', count($minutes), $now->setTimezone($appTz)->format('Y-m-d H:i')));

foreach ($minutes as $minuteUtc) {
    $local = $minuteUtc->setTimezone($appTz);
    $hhmm = $local->format('H:i');
    $localDate = $local->format('Y-m-d');
    $weekday = ((int) $local->format('N')) - 1; // Monday = 0

    checkAlarms($pdo, $push, $hhmm, $localDate);
    checkMedications($pdo, $push, $hhmm, $localDate, $weekday);
}

checkOverdueDoses($pdo, $push, $now->setTimezone($appTz));

// ---- Watermark + dedup-table hygiene ----
$pdo->prepare('UPDATE cron_state SET last_run_utc = ? WHERE id = 1')
    ->execute([$nowMinute->format('Y-m-d H:i:s')]);
$pdo->prepare('DELETE FROM sent_notifications WHERE sent_at < ?')
    ->execute([$now->modify('-2 days')->format('Y-m-d H:i:s')]);

flock($lock, LOCK_UN);
exit(0);

// ---------------------------------------------------------------------------

function checkAlarms(PDO $pdo, PushService $push, string $hhmm, string $localDate): void
{
    $stmt = $pdo->prepare(
        'SELECT a.id, a.user_id, a.type, u.name
         FROM alarms a JOIN users u ON a.user_id = u.id
         WHERE a.is_active = 1 AND a.config_time = ?'
    );
    $stmt->execute([$hhmm]);

    foreach ($stmt->fetchAll() as $alarm) {
        if (!claimDedup($pdo, "alarm:{$alarm['id']}:$localDate:$hhmm")) {
            continue;
        }

        $title = 'Azúcar Control';
        $body = 'Recordatorio de salud';
        $url = '/';

        if ($alarm['type'] === 'metformina') {
            $title = '💊 Tomar Metformina';
            $body = "Hola {$alarm['name']}, es momento de tomar tu dosis de Metformina. Recuerda acompañarla con comida.";
            $url = '/#alarms';
        } elseif ($alarm['type'] === 'postprandial') {
            $title = '🩸 Medir Glucosa Postprandial';
            $body = "Hola {$alarm['name']}, han pasado 2 horas desde tu comida. Es momento de medir tu nivel de glucosa.";
            $url = '/#registry';
            // One-shot alarm: deactivate after firing
            $pdo->prepare('UPDATE alarms SET is_active = 0 WHERE id = ?')->execute([$alarm['id']]);
        } else {
            $body = "Recordatorio de tu alarma de {$alarm['type']}.";
        }

        $result = $push->sendToUser($pdo, (int) $alarm['user_id'], PushService::basePayload($title, $body, $url));
        logLine("Alarm {$alarm['type']} @$hhmm user {$alarm['user_id']}: sent {$result['sent']}, pruned {$result['deleted']}");
    }
}

function checkMedications(PDO $pdo, PushService $push, string $hhmm, string $localDate, int $weekday): void
{
    foreach (activeMedications($pdo) as $med) {
        if (!in_array($weekday, $med['days'], true) || !in_array($hhmm, $med['times'], true)) {
            continue;
        }
        if (!claimDedup($pdo, "med:{$med['id']}:$localDate:$hhmm")) {
            continue;
        }

        [$emoji, $label] = $med['kind'] === 'medication' ? ['💊', 'medicamento'] : ['🌿', 'suplemento'];
        $result = $push->sendToUser($pdo, (int) $med['user_id'], PushService::basePayload(
            "$emoji Tomar {$med['name']}",
            "Hola {$med['user_name']}, es momento de tomar tu $label {$med['name']}.",
            '/#medications'
        ));
        logLine("Med dose {$med['name']} @$hhmm user {$med['user_id']}: sent {$result['sent']}, pruned {$result['deleted']}");
    }
}

function checkOverdueDoses(PDO $pdo, PushService $push, DateTimeImmutable $nowLocal): void
{
    $localDate = $nowLocal->format('Y-m-d');
    $weekday = ((int) $nowLocal->format('N')) - 1;
    $currMinutes = (int) $nowLocal->format('H') * 60 + (int) $nowLocal->format('i');

    foreach (activeMedications($pdo) as $med) {
        if (!in_array($weekday, $med['days'], true)) {
            continue;
        }
        foreach ($med['times'] as $timeStr) {
            [$h, $m] = array_map('intval', explode(':', $timeStr) + [0, 0]);
            $diff = $currMinutes - ($h * 60 + $m);
            if ($diff < 15 || $diff > 120) {
                continue;
            }

            $stmt = $pdo->prepare(
                'SELECT 1 FROM medication_logs
                 WHERE medication_id = ? AND date = ? AND scheduled_time = ? LIMIT 1'
            );
            $stmt->execute([$med['id'], $localDate, $timeStr]);
            if ($stmt->fetch() !== false) {
                continue; // already taken/skipped
            }

            if (!claimDedup($pdo, "overdue_med:{$med['id']}:$localDate:$timeStr")) {
                continue; // reminded within the last 24h window already
            }

            $label = $med['kind'] === 'medication' ? 'medicamento' : 'suplemento';
            $result = $push->sendToUser($pdo, (int) $med['user_id'], PushService::basePayload(
                "⚠️ Dosis vencida: {$med['name']}",
                "Hola {$med['user_name']}, la dosis de $label {$med['name']} estaba programada para las $timeStr (hace $diff min). No olvides tomarla.",
                '/#medications'
            ));
            logLine("Overdue {$med['name']} @$timeStr user {$med['user_id']}: sent {$result['sent']}, pruned {$result['deleted']}");
        }
    }
}

/** @return array<int, array{id:int, user_id:int, name:string, kind:string, user_name:string, times:array, days:array}> */
function activeMedications(PDO $pdo): array
{
    static $cache = null;
    if ($cache !== null) {
        return $cache;
    }
    $rows = $pdo->query(
        'SELECT m.id, m.user_id, m.name, m.kind, m.times, m.days_of_week, u.name AS user_name
         FROM medications m JOIN users u ON m.user_id = u.id
         WHERE m.is_active = 1'
    )->fetchAll();

    $cache = array_map(static fn (array $r): array => [
        'id' => (int) $r['id'],
        'user_id' => (int) $r['user_id'],
        'name' => $r['name'],
        'kind' => $r['kind'],
        'user_name' => $r['user_name'],
        'times' => json_decode($r['times'], true) ?? [],
        'days' => array_map('intval', json_decode($r['days_of_week'], true) ?? []),
    ], $rows);
    return $cache;
}

/** INSERT IGNORE on the unique dedup key; true when this run claimed the send. */
function claimDedup(PDO $pdo, string $key): bool
{
    $stmt = $pdo->prepare('INSERT IGNORE INTO sent_notifications (dedup_key) VALUES (?)');
    $stmt->execute([$key]);
    return $stmt->rowCount() === 1;
}

function logLine(string $message): void
{
    echo '[' . gmdate('Y-m-d H:i:s') . ' UTC] ' . $message . PHP_EOL;
}
