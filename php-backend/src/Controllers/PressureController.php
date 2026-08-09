<?php

declare(strict_types=1);

namespace Azucar\Controllers;

use Azucar\Support\ApiError;

final class PressureController extends VitalsController
{
    protected function table(): string
    {
        return 'blood_pressures';
    }

    protected function notFoundDetail(): string
    {
        return 'Pressure reading not found';
    }

    protected function valueColumns(array $body): array
    {
        $sys = (int) ($body['systolic_mmhg'] ?? 0);
        $dia = (int) ($body['diastolic_mmhg'] ?? 0);
        if ($sys < 40 || $sys > 250 || $dia < 40 || $dia > 250) {
            throw new ApiError('Presión arterial fuera de rango (40-250 mmHg).', 422);
        }
        return ['systolic_mmhg' => $sys, 'diastolic_mmhg' => $dia];
    }

    protected function serializeValues(array $row): array
    {
        return [
            'systolic_mmhg' => (int) $row['systolic_mmhg'],
            'diastolic_mmhg' => (int) $row['diastolic_mmhg'],
        ];
    }
}
