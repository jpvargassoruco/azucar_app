<?php

declare(strict_types=1);

namespace Azucar\Controllers;

use Azucar\Database;
use Azucar\Services\FhirSerializer;
use Azucar\Support\Respond;
use PDO;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

final class FhirController
{
    public function patient(Request $request, Response $response): Response
    {
        return Respond::json($response, FhirSerializer::userToPatient($request->getAttribute('user')));
    }

    public function observations(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $category = $request->getQueryParams()['category'] ?? null;
        if ($category !== null && $category !== '' && $category !== 'laboratory') {
            return Respond::json($response, []);
        }

        $stmt = Database::pdo()->prepare(
            'SELECT * FROM glucose_readings WHERE user_id = ? ORDER BY datetime DESC LIMIT 100'
        );
        $stmt->execute([$user['id']]);

        $patientRef = 'Patient/' . $user['id'];
        return Respond::json($response, array_map(
            fn (array $r) => FhirSerializer::glucoseToObservation($r, $patientRef),
            $stmt->fetchAll()
        ));
    }

    public function nutritionIntakes(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $stmt = Database::pdo()->prepare(
            'SELECT * FROM meal_entries WHERE user_id = ? ORDER BY datetime DESC LIMIT 100'
        );
        $stmt->execute([$user['id']]);

        $patientRef = 'Patient/' . $user['id'];
        return Respond::json($response, array_map(
            fn (array $m) => FhirSerializer::mealToNutritionIntake($m, $patientRef),
            $stmt->fetchAll()
        ));
    }

    public function medicationStatements(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $rows = $this->medicationLogRows(Database::pdo(), (int) $user['id'], 100);

        $patientRef = 'Patient/' . $user['id'];
        return Respond::json($response, array_map(
            fn (array $row) => FhirSerializer::medicationLogToStatement($row, $patientRef),
            $rows
        ));
    }

    public function bundle(Request $request, Response $response): Response
    {
        return Respond::json($response, $this->buildBundle($request));
    }

    public function export(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $bundle = $this->buildBundle($request);

        $response->getBody()->write(
            json_encode($bundle, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)
        );
        return $response
            ->withHeader('Content-Type', 'application/fhir+json')
            ->withHeader('Content-Disposition', 'attachment; filename=fhir_bundle_patient_' . $user['id'] . '.json');
    }

    private function buildBundle(Request $request): array
    {
        $user = $request->getAttribute('user');
        $pdo = Database::pdo();
        $userId = (int) $user['id'];

        $stmt = $pdo->prepare('SELECT * FROM glucose_readings WHERE user_id = ?');
        $stmt->execute([$userId]);
        $readings = $stmt->fetchAll();

        $stmt = $pdo->prepare('SELECT * FROM meal_entries WHERE user_id = ?');
        $stmt->execute([$userId]);
        $meals = $stmt->fetchAll();

        $stmt = $pdo->prepare('SELECT * FROM fasting_sessions WHERE user_id = ?');
        $stmt->execute([$userId]);
        $fastings = $stmt->fetchAll();

        return FhirSerializer::buildPatientBundle(
            $user,
            $readings,
            $meals,
            $fastings,
            $this->medicationLogRows($pdo, $userId, null)
        );
    }

    private function medicationLogRows(PDO $pdo, int $userId, ?int $limit): array
    {
        $sql = 'SELECT ml.*, m.name AS med_name, m.kind AS med_kind
                FROM medication_logs ml
                JOIN medications m ON ml.medication_id = m.id
                WHERE ml.user_id = ? ORDER BY ml.date DESC';
        if ($limit !== null) {
            $sql .= ' LIMIT ' . $limit;
        }
        $stmt = $pdo->prepare($sql);
        $stmt->execute([$userId]);
        return $stmt->fetchAll();
    }
}
