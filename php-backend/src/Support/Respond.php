<?php

declare(strict_types=1);

namespace Azucar\Support;

use Psr\Http\Message\ResponseInterface as Response;

final class Respond
{
    public static function json(Response $response, mixed $data, int $status = 200): Response
    {
        $response->getBody()->write(
            json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)
        );
        return $response
            ->withHeader('Content-Type', 'application/json')
            ->withStatus($status);
    }

    public static function error(Response $response, string $detail, int $status): Response
    {
        return self::json($response, ['detail' => $detail], $status);
    }

    public static function noContent(Response $response): Response
    {
        return $response->withStatus(204);
    }

    /** MySQL DATETIME (UTC) -> "Y-m-d\TH:i:sZ" (matches pydantic's tz-aware output). */
    public static function iso(?string $mysqlDatetime): ?string
    {
        return Dt::out($mysqlDatetime);
    }
}
