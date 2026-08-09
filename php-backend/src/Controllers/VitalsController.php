<?php

declare(strict_types=1);

namespace Azucar\Controllers;

use Azucar\Database;
use Azucar\Support\ApiError;
use Azucar\Support\Dt;
use Azucar\Support\Respond;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

/**
 * Shared implementation for the three simple vitals resources
 * (weights, blood_pressures, hba1c_readings): list DESC / create / delete.
 * Mirrors routers/weight.py, pressure.py, hba1c.py.
 */
abstract class VitalsController
{
    abstract protected function table(): string;

    abstract protected function notFoundDetail(): string;

    /** Validate the body and return [column => value] for the INSERT (without user_id/datetime). */
    abstract protected function valueColumns(array $body): array;

    /** Serialize the value columns for a response row. */
    abstract protected function serializeValues(array $row): array;

    public function list(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $stmt = Database::pdo()->prepare(
            "SELECT * FROM {$this->table()} WHERE user_id = ? ORDER BY datetime DESC"
        );
        $stmt->execute([$user['id']]);
        return Respond::json($response, array_map([$this, 'serialize'], $stmt->fetchAll()));
    }

    public function create(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $body = (array) $request->getParsedBody();

        $datetime = Dt::parseToUtcSql($body['datetime'] ?? null);
        if ($datetime === null) {
            throw new ApiError('Fecha y hora inválidas.', 422);
        }
        $values = $this->valueColumns($body);

        $columns = array_merge(['user_id', 'datetime'], array_keys($values), ['notes']);
        $params = array_merge([$user['id'], $datetime], array_values($values), [$body['notes'] ?? null]);
        $placeholders = implode(', ', array_fill(0, count($params), '?'));

        $pdo = Database::pdo();
        $pdo->prepare(
            "INSERT INTO {$this->table()} (" . implode(', ', $columns) . ") VALUES ($placeholders)"
        )->execute($params);

        $stmt = $pdo->prepare("SELECT * FROM {$this->table()} WHERE id = ?");
        $stmt->execute([(int) $pdo->lastInsertId()]);
        return Respond::json($response, $this->serialize($stmt->fetch()), 201);
    }

    public function delete(Request $request, Response $response, array $args): Response
    {
        $user = $request->getAttribute('user');
        $stmt = Database::pdo()->prepare(
            "DELETE FROM {$this->table()} WHERE id = ? AND user_id = ?"
        );
        $stmt->execute([(int) $args['id'], $user['id']]);
        if ($stmt->rowCount() === 0) {
            throw new ApiError($this->notFoundDetail(), 404);
        }
        return Respond::noContent($response);
    }

    public function serialize(array $row): array
    {
        return array_merge(
            [
                'id' => (int) $row['id'],
                'user_id' => (int) $row['user_id'],
                'datetime' => Dt::out($row['datetime']),
            ],
            $this->serializeValues($row),
            ['notes' => $row['notes']]
        );
    }
}
