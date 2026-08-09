<?php

declare(strict_types=1);

namespace Azucar\Controllers;

use Azucar\Database;
use Azucar\Support\ApiError;
use Azucar\Support\Dt;
use Azucar\Support\Respond;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

final class MedicationController
{
    public function list(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $kind = $request->getQueryParams()['kind'] ?? null;

        $sql = 'SELECT * FROM medications WHERE user_id = ?';
        $params = [$user['id']];
        if ($kind !== null && $kind !== '') {
            $sql .= ' AND kind = ?';
            $params[] = $kind;
        }
        $stmt = Database::pdo()->prepare($sql . ' ORDER BY name ASC');
        $stmt->execute($params);
        return Respond::json($response, array_map([self::class, 'serialize'], $stmt->fetchAll()));
    }

    public function create(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $data = $this->validated((array) $request->getParsedBody(), requireAll: true);

        $pdo = Database::pdo();
        $pdo->prepare(
            'INSERT INTO medications (user_id, name, kind, dosage, times, days_of_week, is_active, notes)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
        )->execute([
            $user['id'],
            $data['name'],
            $data['kind'],
            $data['dosage'],
            json_encode($data['times']),
            json_encode($data['days_of_week']),
            (int) $data['is_active'],
            $data['notes'],
        ]);

        return Respond::json($response, self::fetch($pdo, (int) $pdo->lastInsertId()), 201);
    }

    public function update(Request $request, Response $response, array $args): Response
    {
        $user = $request->getAttribute('user');
        $body = (array) $request->getParsedBody();

        $pdo = Database::pdo();
        $stmt = $pdo->prepare('SELECT * FROM medications WHERE id = ? AND user_id = ?');
        $stmt->execute([(int) $args['id'], $user['id']]);
        $med = $stmt->fetch();
        if ($med === false) {
            throw new ApiError('Medicamento no encontrado.', 404);
        }

        $data = $this->validated($body, requireAll: false);
        $updates = [];
        $params = [];
        foreach (['name', 'kind', 'dosage', 'notes'] as $field) {
            if (array_key_exists($field, $body)) {
                $updates[] = "$field = ?";
                $params[] = $data[$field];
            }
        }
        foreach (['times', 'days_of_week'] as $field) {
            if (array_key_exists($field, $body)) {
                $updates[] = "$field = ?";
                $params[] = json_encode($data[$field]);
            }
        }
        if (array_key_exists('is_active', $body)) {
            $updates[] = 'is_active = ?';
            $params[] = (int) $data['is_active'];
        }

        if ($updates !== []) {
            $params[] = $med['id'];
            $pdo->prepare('UPDATE medications SET ' . implode(', ', $updates) . ' WHERE id = ?')
                ->execute($params);
        }

        return Respond::json($response, self::fetch($pdo, (int) $med['id']));
    }

    public function delete(Request $request, Response $response, array $args): Response
    {
        $user = $request->getAttribute('user');
        $stmt = Database::pdo()->prepare('DELETE FROM medications WHERE id = ? AND user_id = ?');
        $stmt->execute([(int) $args['id'], $user['id']]);
        if ($stmt->rowCount() === 0) {
            throw new ApiError('Medicamento no encontrado.', 404);
        }
        return Respond::noContent($response);
    }

    /** GET /medications/today — computed dose slots with taken/skipped status. */
    public function today(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $today = Dt::todayLocal();
        $weekday = Dt::weekdayLocal();
        $pdo = Database::pdo();

        $stmt = $pdo->prepare('SELECT * FROM medications WHERE user_id = ? AND is_active = 1');
        $stmt->execute([$user['id']]);
        $medications = $stmt->fetchAll();

        $stmt = $pdo->prepare('SELECT * FROM medication_logs WHERE user_id = ? AND date = ?');
        $stmt->execute([$user['id'], $today]);
        $logsByKey = [];
        foreach ($stmt->fetchAll() as $log) {
            $logsByKey[$log['medication_id'] . '|' . $log['scheduled_time']] = $log;
        }

        $slots = [];
        foreach ($medications as $med) {
            $days = json_decode($med['days_of_week'], true) ?? [];
            if (!in_array($weekday, array_map('intval', $days), true)) {
                continue;
            }
            foreach ((json_decode($med['times'], true) ?? []) as $time) {
                $log = $logsByKey[$med['id'] . '|' . $time] ?? null;
                $slots[] = [
                    'medication_id' => (int) $med['id'],
                    'name' => $med['name'],
                    'kind' => $med['kind'],
                    'dosage' => $med['dosage'],
                    'scheduled_time' => $time,
                    'status' => $log['status'] ?? null,
                    'log_id' => $log !== null ? (int) $log['id'] : null,
                ];
            }
        }
        usort($slots, fn (array $a, array $b) => strcmp($a['scheduled_time'], $b['scheduled_time']));
        return Respond::json($response, $slots);
    }

    /** POST /medications/log — upsert by (medication, date, time). */
    public function markDose(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $body = (array) $request->getParsedBody();

        $medicationId = (int) ($body['medication_id'] ?? 0);
        $date = (string) ($body['date'] ?? '');
        $scheduledTime = (string) ($body['scheduled_time'] ?? '');
        $status = (string) ($body['status'] ?? '');

        if (!Dt::isValidDate($date) || !Dt::isValidHhmm($scheduledTime)
            || !in_array($status, ['taken', 'skipped'], true)) {
            throw new ApiError('Datos de registro inválidos.', 422);
        }

        $pdo = Database::pdo();
        $stmt = $pdo->prepare('SELECT id FROM medications WHERE id = ? AND user_id = ?');
        $stmt->execute([$medicationId, $user['id']]);
        if ($stmt->fetch() === false) {
            throw new ApiError('Medicamento no encontrado.', 404);
        }

        $stmt = $pdo->prepare(
            'SELECT id FROM medication_logs WHERE medication_id = ? AND date = ? AND scheduled_time = ?'
        );
        $stmt->execute([$medicationId, $date, $scheduledTime]);
        $existing = $stmt->fetch();

        if ($existing !== false) {
            $pdo->prepare('UPDATE medication_logs SET status = ?, marked_at = ? WHERE id = ?')
                ->execute([$status, Dt::nowUtcSql(), $existing['id']]);
            $id = (int) $existing['id'];
        } else {
            $pdo->prepare(
                'INSERT INTO medication_logs (medication_id, user_id, date, scheduled_time, status)
                 VALUES (?, ?, ?, ?, ?)'
            )->execute([$medicationId, $user['id'], $date, $scheduledTime, $status]);
            $id = (int) $pdo->lastInsertId();
        }

        $stmt = $pdo->prepare('SELECT * FROM medication_logs WHERE id = ?');
        $stmt->execute([$id]);
        $row = $stmt->fetch();
        return Respond::json($response, [
            'id' => (int) $row['id'],
            'medication_id' => (int) $row['medication_id'],
            'user_id' => (int) $row['user_id'],
            'date' => $row['date'],
            'scheduled_time' => $row['scheduled_time'],
            'status' => $row['status'],
        ]);
    }

    /** Validate/normalize a medication payload; with requireAll, missing fields are errors. */
    private function validated(array $body, bool $requireAll): array
    {
        $data = [
            'name' => isset($body['name']) ? trim((string) $body['name']) : null,
            'kind' => $body['kind'] ?? null,
            'dosage' => isset($body['dosage']) ? (string) $body['dosage'] : null,
            'times' => $body['times'] ?? null,
            'days_of_week' => $body['days_of_week'] ?? null,
            'is_active' => array_key_exists('is_active', $body) ? (bool) $body['is_active'] : true,
            'notes' => isset($body['notes']) ? (string) $body['notes'] : null,
        ];

        if ($requireAll || array_key_exists('name', $body)) {
            if ($data['name'] === null || $data['name'] === '' || strlen($data['name']) > 100) {
                throw new ApiError('Nombre de medicamento inválido.', 422);
            }
        }
        if ($requireAll || array_key_exists('kind', $body)) {
            if (!in_array($data['kind'], ['medication', 'supplement'], true)) {
                throw new ApiError("Tipo inválido ('medication' o 'supplement').", 422);
            }
        }
        if ($requireAll || array_key_exists('times', $body)) {
            if (!is_array($data['times']) || $data['times'] === []) {
                throw new ApiError('Debe indicar al menos una hora.', 422);
            }
            foreach ($data['times'] as $time) {
                if (!is_string($time) || !Dt::isValidHhmm($time)) {
                    throw new ApiError('Hora inválida (formato HH:MM).', 422);
                }
            }
        }
        if ($requireAll || array_key_exists('days_of_week', $body)) {
            if (!is_array($data['days_of_week']) || $data['days_of_week'] === []) {
                throw new ApiError('Debe indicar al menos un día.', 422);
            }
            foreach ($data['days_of_week'] as $day) {
                if (!is_int($day) || $day < 0 || $day > 6) {
                    throw new ApiError('Día inválido (0=lunes .. 6=domingo).', 422);
                }
            }
        }
        return $data;
    }

    private static function fetch(\PDO $pdo, int $id): array
    {
        $stmt = $pdo->prepare('SELECT * FROM medications WHERE id = ?');
        $stmt->execute([$id]);
        return self::serialize($stmt->fetch());
    }

    private static function serialize(array $row): array
    {
        return [
            'id' => (int) $row['id'],
            'user_id' => (int) $row['user_id'],
            'name' => $row['name'],
            'kind' => $row['kind'],
            'dosage' => $row['dosage'],
            'times' => json_decode($row['times'], true) ?? [],
            'days_of_week' => array_map('intval', json_decode($row['days_of_week'], true) ?? []),
            'is_active' => (bool) $row['is_active'],
            'notes' => $row['notes'],
        ];
    }
}
