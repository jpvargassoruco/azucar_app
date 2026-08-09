<?php

declare(strict_types=1);

namespace Azucar\Controllers;

use Azucar\Support\ApiError;

final class Hba1cController extends VitalsController
{
    protected function table(): string
    {
        return 'hba1c_readings';
    }

    protected function notFoundDetail(): string
    {
        return 'HbA1c reading not found';
    }

    protected function valueColumns(array $body): array
    {
        $percent = (float) ($body['value_percent'] ?? 0);
        if ($percent < 3 || $percent > 15) {
            throw new ApiError('Valor de HbA1c fuera de rango (3-15%).', 422);
        }
        return ['value_percent' => $percent];
    }

    protected function serializeValues(array $row): array
    {
        return ['value_percent' => (float) $row['value_percent']];
    }
}
