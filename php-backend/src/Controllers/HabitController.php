<?php

declare(strict_types=1);

namespace Azucar\Controllers;

use Azucar\Database;
use Azucar\Support\ApiError;
use Azucar\Support\Dt;
use Azucar\Support\Respond;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

final class HabitController
{
    private const HABIT_KEYS = ['ejercicio', 'agua', 'ayuno', 'medicacion'];

    /** GET /habits/today — {habit_key: bool} map for the standard PWA keys. */
    public function today(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $stmt = Database::pdo()->prepare(
            'SELECT habit_key, completed FROM habit_logs WHERE user_id = ? AND date = ?'
        );
        $stmt->execute([$user['id'], Dt::todayLocal()]);

        $habits = array_fill_keys(self::HABIT_KEYS, false);
        foreach ($stmt->fetchAll() as $log) {
            if (array_key_exists($log['habit_key'], $habits)) {
                $habits[$log['habit_key']] = (bool) $log['completed'];
            }
        }
        return Respond::json($response, $habits);
    }

    /** POST /habits/toggle — {date, habit_key}; flips or creates completed=true. */
    public function toggle(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $body = (array) $request->getParsedBody();

        $date = (string) ($body['date'] ?? '');
        $habitKey = (string) ($body['habit_key'] ?? '');
        if (!Dt::isValidDate($date) || $habitKey === '') {
            throw new ApiError('Datos de hábito inválidos.', 422);
        }

        $pdo = Database::pdo();
        $stmt = $pdo->prepare(
            'SELECT * FROM habit_logs WHERE user_id = ? AND date = ? AND habit_key = ?'
        );
        $stmt->execute([$user['id'], $date, $habitKey]);
        $log = $stmt->fetch();

        if ($log !== false) {
            $pdo->prepare('UPDATE habit_logs SET completed = ? WHERE id = ?')
                ->execute([(int) !$log['completed'], $log['id']]);
            $id = (int) $log['id'];
        } else {
            $pdo->prepare(
                'INSERT INTO habit_logs (user_id, date, habit_key, completed) VALUES (?, ?, ?, 1)'
            )->execute([$user['id'], $date, $habitKey]);
            $id = (int) $pdo->lastInsertId();
        }

        $stmt = $pdo->prepare('SELECT * FROM habit_logs WHERE id = ?');
        $stmt->execute([$id]);
        $row = $stmt->fetch();
        return Respond::json($response, [
            'id' => (int) $row['id'],
            'user_id' => (int) $row['user_id'],
            'date' => $row['date'],
            'habit_key' => $row['habit_key'],
            'completed' => (bool) $row['completed'],
        ]);
    }

    /** GET /habits/progress — completion percentage over the last 30 days. */
    public function progress(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $endDate = Dt::todayLocal();
        $startDate = (new \DateTimeImmutable($endDate))->modify('-29 days')->format('Y-m-d');

        $stmt = Database::pdo()->prepare(
            'SELECT habit_key, COUNT(*) AS n FROM habit_logs
             WHERE user_id = ? AND date >= ? AND date <= ? AND completed = 1
             GROUP BY habit_key'
        );
        $stmt->execute([$user['id'], $startDate, $endDate]);
        $counts = array_fill_keys(self::HABIT_KEYS, 0);
        foreach ($stmt->fetchAll() as $row) {
            if (array_key_exists($row['habit_key'], $counts)) {
                $counts[$row['habit_key']] = (int) $row['n'];
            }
        }

        $progress = [];
        foreach ($counts as $key => $count) {
            $progress[] = [
                'habit_key' => $key,
                'completed_days' => $count,
                'total_days' => 30,
                'percentage' => round(($count / 30.0) * 100, 1),
            ];
        }
        return Respond::json($response, $progress);
    }
}
