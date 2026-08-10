<?php

declare(strict_types=1);

namespace Azucar\Controllers;

use Azucar\Database;
use Azucar\Support\ApiError;
use Azucar\Support\Dt;
use Azucar\Support\Respond;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

final class AlarmController
{
    public function list(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $stmt = Database::pdo()->prepare(
            'SELECT * FROM alarms WHERE user_id = ? ORDER BY config_time ASC'
        );
        $stmt->execute([$user['id']]);
        return Respond::json($response, array_map([self::class, 'serialize'], $stmt->fetchAll()));
    }

    /** POST /alarms — upsert by (user, type); the frontend has no PUT/DELETE flow. */
    public function createOrUpdate(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $body = (array) $request->getParsedBody();

        $type = (string) ($body['type'] ?? '');
        $configTime = (string) ($body['config_time'] ?? '');
        $isActive = array_key_exists('is_active', $body) ? (bool) $body['is_active'] : true;

        if ($type === '') {
            throw new ApiError('El tipo de alarma es obligatorio.', 422);
        }
        if (!Dt::isValidHhmm($configTime)) {
            throw new ApiError('Hora inválida (formato HH:MM).', 422);
        }

        $pdo = Database::pdo();
        $stmt = $pdo->prepare('SELECT id FROM alarms WHERE user_id = ? AND type = ?');
        $stmt->execute([$user['id'], $type]);
        $existing = $stmt->fetch();

        if ($existing !== false) {
            $pdo->prepare('UPDATE alarms SET config_time = ?, is_active = ? WHERE id = ?')
                ->execute([$configTime, (int) $isActive, $existing['id']]);
            $id = (int) $existing['id'];
        } else {
            $pdo->prepare(
                'INSERT INTO alarms (user_id, type, config_time, is_active) VALUES (?, ?, ?, ?)'
            )->execute([$user['id'], $type, $configTime, (int) $isActive]);
            $id = (int) $pdo->lastInsertId();
        }

        $stmt = $pdo->prepare('SELECT * FROM alarms WHERE id = ?');
        $stmt->execute([$id]);
        return Respond::json($response, self::serialize($stmt->fetch()), 201);
    }

    public function update(Request $request, Response $response, array $args): Response
    {
        $user = $request->getAttribute('user');
        $body = (array) $request->getParsedBody();

        $pdo = Database::pdo();
        $stmt = $pdo->prepare('SELECT * FROM alarms WHERE id = ? AND user_id = ?');
        $stmt->execute([(int) $args['id'], $user['id']]);
        $alarm = $stmt->fetch();
        if ($alarm === false) {
            throw new ApiError('Alarma no encontrada.', 404);
        }

        $configTime = $alarm['config_time'];
        if (isset($body['config_time'])) {
            if (!Dt::isValidHhmm((string) $body['config_time'])) {
                throw new ApiError('Hora inválida (formato HH:MM).', 422);
            }
            $configTime = (string) $body['config_time'];
        }
        $isActive = isset($body['is_active']) ? (bool) $body['is_active'] : (bool) $alarm['is_active'];

        $pdo->prepare('UPDATE alarms SET config_time = ?, is_active = ? WHERE id = ?')
            ->execute([$configTime, (int) $isActive, $alarm['id']]);

        $stmt = $pdo->prepare('SELECT * FROM alarms WHERE id = ?');
        $stmt->execute([$alarm['id']]);
        return Respond::json($response, self::serialize($stmt->fetch()));
    }

    public function delete(Request $request, Response $response, array $args): Response
    {
        $user = $request->getAttribute('user');
        $stmt = Database::pdo()->prepare('DELETE FROM alarms WHERE id = ? AND user_id = ?');
        $stmt->execute([(int) $args['id'], $user['id']]);
        if ($stmt->rowCount() === 0) {
            throw new ApiError('Alarma no encontrada.', 404);
        }
        return Respond::noContent($response);
    }

    private static function serialize(array $row): array
    {
        return [
            'id' => (int) $row['id'],
            'user_id' => (int) $row['user_id'],
            'type' => $row['type'],
            'config_time' => $row['config_time'],
            'is_active' => (bool) $row['is_active'],
        ];
    }
}
