<?php

declare(strict_types=1);

namespace Azucar\Controllers;

use Azucar\Database;
use Azucar\Support\ApiError;
use Azucar\Support\Dt;
use Azucar\Support\Respond;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

final class GlucoseController
{
    public function list(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $stmt = Database::pdo()->prepare(
            'SELECT * FROM glucose_readings WHERE user_id = ? ORDER BY datetime DESC'
        );
        $stmt->execute([$user['id']]);
        return Respond::json($response, array_map([self::class, 'serialize'], $stmt->fetchAll()));
    }

    public function create(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $body = (array) $request->getParsedBody();

        $datetime = Dt::parseToUtcSql($body['datetime'] ?? null);
        $value = (int) ($body['value_mgdl'] ?? 0);
        $condition = (string) ($body['condition'] ?? '');

        if ($datetime === null) {
            throw new ApiError('Fecha y hora inválidas.', 422);
        }
        if ($value <= 0 || $value >= 1000) {
            throw new ApiError('Nivel de glucosa fuera de rango (1-999 mg/dL).', 422);
        }
        if ($condition === '') {
            throw new ApiError('La condición de la lectura es obligatoria.', 422);
        }

        $pdo = Database::pdo();
        $pdo->prepare(
            'INSERT INTO glucose_readings (user_id, datetime, value_mgdl, `condition`, notes)
             VALUES (?, ?, ?, ?, ?)'
        )->execute([$user['id'], $datetime, $value, $condition, $body['notes'] ?? null]);

        return Respond::json($response, self::fetch($pdo, (int) $pdo->lastInsertId()), 201);
    }

    public function delete(Request $request, Response $response, array $args): Response
    {
        $user = $request->getAttribute('user');
        $stmt = Database::pdo()->prepare(
            'DELETE FROM glucose_readings WHERE id = ? AND user_id = ?'
        );
        $stmt->execute([(int) $args['id'], $user['id']]);
        if ($stmt->rowCount() === 0) {
            throw new ApiError('Lectura de glucosa no encontrada.', 404);
        }
        return Respond::noContent($response);
    }

    public function stats(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $stmt = Database::pdo()->prepare(
            "SELECT
                AVG(value_mgdl) AS avg_all,
                AVG(CASE WHEN `condition` = 'ayunas' THEN value_mgdl END) AS avg_fasting,
                AVG(CASE WHEN `condition` = 'postprandial' THEN value_mgdl END) AS avg_postprandial,
                COUNT(id) AS readings_count
             FROM glucose_readings WHERE user_id = ?"
        );
        $stmt->execute([$user['id']]);
        $row = $stmt->fetch();

        return Respond::json($response, [
            'avg_all' => $row['avg_all'] !== null ? round((float) $row['avg_all'], 1) : 0,
            'avg_fasting' => $row['avg_fasting'] !== null ? round((float) $row['avg_fasting'], 1) : 0,
            'avg_postprandial' => $row['avg_postprandial'] !== null ? round((float) $row['avg_postprandial'], 1) : 0,
            'readings_count' => (int) $row['readings_count'],
        ]);
    }

    private static function fetch(\PDO $pdo, int $id): array
    {
        $stmt = $pdo->prepare('SELECT * FROM glucose_readings WHERE id = ?');
        $stmt->execute([$id]);
        return self::serialize($stmt->fetch());
    }

    private static function serialize(array $row): array
    {
        return [
            'id' => (int) $row['id'],
            'user_id' => (int) $row['user_id'],
            'datetime' => Dt::out($row['datetime']),
            'value_mgdl' => (int) $row['value_mgdl'],
            'condition' => $row['condition'],
            'notes' => $row['notes'],
        ];
    }
}
