<?php

declare(strict_types=1);

namespace Azucar\Controllers;

use Azucar\Database;
use Azucar\Support\ApiError;
use Azucar\Support\Dt;
use Azucar\Support\Respond;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

final class FastingController
{
    public function list(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $stmt = Database::pdo()->prepare(
            'SELECT * FROM fasting_sessions WHERE user_id = ? ORDER BY start_time DESC'
        );
        $stmt->execute([$user['id']]);
        return Respond::json($response, array_map([self::class, 'serialize'], $stmt->fetchAll()));
    }

    /** GET /fasting/active — the not-yet-completed session, or null. */
    public function active(Request $request, Response $response): Response
    {
        $session = $this->findActive($request->getAttribute('user'));
        return Respond::json($response, $session === null ? null : self::serialize($session));
    }

    public function start(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $body = (array) $request->getParsedBody();

        if ($this->findActive($user) !== null) {
            throw new ApiError('Ya tienes un ayuno activo. Detenlo antes de comenzar uno nuevo.', 400);
        }

        $startTime = Dt::parseToUtcSql($body['start_time'] ?? null);
        $protocol = (string) ($body['protocol'] ?? '');
        if ($startTime === null || $protocol === '') {
            throw new ApiError('Datos de ayuno inválidos.', 422);
        }

        $pdo = Database::pdo();
        $pdo->prepare(
            'INSERT INTO fasting_sessions (user_id, start_time, protocol, completed) VALUES (?, ?, ?, 0)'
        )->execute([$user['id'], $startTime, $protocol]);

        $stmt = $pdo->prepare('SELECT * FROM fasting_sessions WHERE id = ?');
        $stmt->execute([(int) $pdo->lastInsertId()]);
        return Respond::json($response, self::serialize($stmt->fetch()));
    }

    public function stop(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $body = (array) $request->getParsedBody();

        $session = $this->findActive($user);
        if ($session === null) {
            throw new ApiError('No hay ningún ayuno activo para finalizar.', 404);
        }

        $endTime = Dt::parseToUtcSql($body['end_time'] ?? null);
        if ($endTime === null) {
            throw new ApiError('Fecha de finalización inválida.', 422);
        }
        $completed = array_key_exists('completed', $body) ? (bool) $body['completed'] : true;

        $pdo = Database::pdo();
        $pdo->prepare('UPDATE fasting_sessions SET end_time = ?, completed = ? WHERE id = ?')
            ->execute([$endTime, (int) $completed, $session['id']]);

        $stmt = $pdo->prepare('SELECT * FROM fasting_sessions WHERE id = ?');
        $stmt->execute([$session['id']]);
        return Respond::json($response, self::serialize($stmt->fetch()));
    }

    private function findActive(array $user): ?array
    {
        $stmt = Database::pdo()->prepare(
            'SELECT * FROM fasting_sessions WHERE user_id = ? AND completed = 0 LIMIT 1'
        );
        $stmt->execute([$user['id']]);
        $row = $stmt->fetch();
        return $row === false ? null : $row;
    }

    private static function serialize(array $row): array
    {
        return [
            'id' => (int) $row['id'],
            'user_id' => (int) $row['user_id'],
            'start_time' => Dt::out($row['start_time']),
            'end_time' => Dt::out($row['end_time']),
            'protocol' => $row['protocol'],
            'completed' => (bool) $row['completed'],
        ];
    }
}
