<?php

declare(strict_types=1);

namespace Azucar\Controllers;

use Azucar\Support\ApiError;

final class WeightController extends VitalsController
{
    protected function table(): string
    {
        return 'weights';
    }

    protected function notFoundDetail(): string
    {
        return 'Weight reading not found';
    }

    protected function valueColumns(array $body): array
    {
        $kg = (float) ($body['weight_kg'] ?? 0);
        if ($kg <= 0 || $kg > 300) {
            throw new ApiError('Peso fuera de rango (0-300 kg).', 422);
        }
        return ['weight_kg' => $kg];
    }

    protected function serializeValues(array $row): array
    {
        return ['weight_kg' => (float) $row['weight_kg']];
    }
}
