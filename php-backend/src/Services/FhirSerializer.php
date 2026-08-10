<?php

declare(strict_types=1);

namespace Azucar\Services;

use Azucar\Support\Dt;

/**
 * Hand-built FHIR R5 JSON, ported field-for-field from fhir_serializer.py
 * (the fhir.resources dependency only added validation).
 */
final class FhirSerializer
{
    public static function urnUuid(): string
    {
        $data = random_bytes(16);
        $data[6] = chr((ord($data[6]) & 0x0f) | 0x40);
        $data[8] = chr((ord($data[8]) & 0x3f) | 0x80);
        return 'urn:uuid:' . vsprintf('%s%s-%s-%s-%s-%s%s%s', str_split(bin2hex($data), 4));
    }

    public static function userToPatient(array $user): array
    {
        return [
            'resourceType' => 'Patient',
            'id' => (string) $user['id'],
            'identifier' => [['system' => 'urn:ietf:rfc:3986', 'value' => 'mailto:' . $user['email']]],
            'name' => [['use' => 'usual', 'text' => $user['name']]],
        ];
    }

    public static function glucoseToObservation(array $reading, string $patientRef): array
    {
        $isFasting = $reading['condition'] === 'ayunas';
        return [
            'resourceType' => 'Observation',
            'status' => 'final',
            'category' => [[
                'coding' => [[
                    'system' => 'http://terminology.hl7.org/CodeSystem/observation-category',
                    'code' => 'laboratory',
                ]],
            ]],
            'code' => [
                'coding' => [[
                    'system' => 'http://loinc.org',
                    'code' => '15074-8',
                    'display' => 'Glucose [Moles/volume] in Blood',
                ]],
            ],
            'subject' => ['reference' => $patientRef],
            'effectiveDateTime' => Dt::out($reading['datetime']),
            'valueQuantity' => [
                'value' => (int) $reading['value_mgdl'],
                'unit' => 'mg/dL',
                'system' => 'http://unitsofmeasure.org',
                'code' => 'mg/dL',
            ],
            'component' => [[
                'code' => [
                    'coding' => [[
                        'system' => 'http://loinc.org',
                        'code' => $isFasting ? '1558-6' : '1521-4',
                        'display' => $isFasting ? 'Fasting glucose' : 'Postprandial glucose',
                    ]],
                ],
            ]],
        ];
    }

    public static function mealToNutritionIntake(array $meal, string $patientRef): array
    {
        $analysis = $meal['ai_analysis'] !== null ? (json_decode($meal['ai_analysis'], true) ?? []) : [];
        $items = $analysis['food_items'] ?? [];
        $calories = (int) ($analysis['calories_estimated'] ?? 0);

        $desc = $items !== [] ? implode(', ', $items) : ($meal['notes'] ?: 'Comida');

        $consumedItem = ['nutritionProduct' => ['concept' => ['text' => $desc]]];
        if ($calories > 0) {
            $consumedItem['amount'] = [
                'value' => $calories,
                'unit' => 'kcal',
                'system' => 'http://unitsofmeasure.org',
                'code' => 'kcal',
            ];
        }

        $intake = [
            'resourceType' => 'NutritionIntake',
            'status' => 'completed',
            'code' => [
                'coding' => [[
                    'system' => 'http://snomed.info/sct',
                    'code' => '226379006',
                    'display' => 'Food intake',
                ]],
            ],
            'subject' => ['reference' => $patientRef],
            'occurrenceDateTime' => Dt::out($meal['datetime']),
            'consumedItem' => [$consumedItem],
        ];

        $impact = $analysis['glycemic_impact'] ?? null;
        if ($impact) {
            $intake['extension'] = [[
                'url' => 'http://azucar.aeisoftware.com/fhir/StructureDefinition/glycemic-impact',
                'valueString' => $impact,
            ]];
        }
        return $intake;
    }

    public static function fastingToObservation(array $session, string $patientRef): array
    {
        $period = ['start' => Dt::out($session['start_time'])];
        if ($session['end_time'] !== null) {
            $period['end'] = Dt::out($session['end_time']);
        }
        return [
            'resourceType' => 'Observation',
            'status' => $session['completed'] ? 'final' : 'preliminary',
            'code' => [
                'coding' => [[
                    'system' => 'http://snomed.info/sct',
                    'code' => '61144006',
                    'display' => 'Fasting',
                ]],
            ],
            'subject' => ['reference' => $patientRef],
            'effectivePeriod' => $period,
            'note' => [['text' => 'Protocol: ' . $session['protocol']]],
        ];
    }

    /** $row must contain medication_logs columns + med_name + med_kind. */
    public static function medicationLogToStatement(array $row, string $patientRef): array
    {
        $effective = $row['marked_at'] !== null
            ? Dt::out($row['marked_at'])
            : $row['date'] . 'T00:00:00Z';

        return [
            'resourceType' => 'MedicationStatement',
            'status' => $row['status'] === 'taken' ? 'completed' : 'not-taken',
            'medication' => ['concept' => ['text' => $row['med_name']]],
            'subject' => ['reference' => $patientRef],
            'effectiveDateTime' => $effective,
            'extension' => [[
                'url' => 'http://azucar.aeisoftware.com/fhir/StructureDefinition/medication-kind',
                'valueString' => $row['med_kind'],
            ]],
        ];
    }

    public static function buildPatientBundle(array $user, array $readings, array $meals, array $fastings, array $medicationLogs): array
    {
        $entries = [];
        $patientUuid = self::urnUuid();
        $entries[] = ['fullUrl' => $patientUuid, 'resource' => self::userToPatient($user)];

        $entries[] = ['fullUrl' => self::urnUuid(), 'resource' => [
            'resourceType' => 'Condition',
            'clinicalStatus' => [
                'coding' => [[
                    'system' => 'http://terminology.hl7.org/CodeSystem/condition-clinical',
                    'code' => 'active',
                ]],
            ],
            'code' => [
                'coding' => [[
                    'system' => 'http://snomed.info/sct',
                    'code' => '44054006',
                    'display' => 'Diabetes mellitus type 2',
                ]],
            ],
            'subject' => ['reference' => $patientUuid],
        ]];

        foreach ($readings as $r) {
            $entries[] = ['fullUrl' => self::urnUuid(), 'resource' => self::glucoseToObservation($r, $patientUuid)];
        }
        foreach ($meals as $m) {
            $entries[] = ['fullUrl' => self::urnUuid(), 'resource' => self::mealToNutritionIntake($m, $patientUuid)];
        }
        foreach ($fastings as $f) {
            $entries[] = ['fullUrl' => self::urnUuid(), 'resource' => self::fastingToObservation($f, $patientUuid)];
        }
        foreach ($medicationLogs as $log) {
            $entries[] = ['fullUrl' => self::urnUuid(), 'resource' => self::medicationLogToStatement($log, $patientUuid)];
        }

        return ['resourceType' => 'Bundle', 'type' => 'collection', 'entry' => $entries];
    }
}
