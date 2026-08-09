<?php

declare(strict_types=1);

namespace Azucar\Support;

/** Exception carrying an HTTP status; rendered as {"detail": message} by the error handler. */
final class ApiError extends \RuntimeException
{
    public function __construct(
        string $detail,
        public readonly int $status = 400,
        public readonly array $headers = []
    ) {
        parent::__construct($detail);
    }
}
