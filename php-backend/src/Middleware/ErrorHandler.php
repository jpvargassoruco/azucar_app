<?php

declare(strict_types=1);

namespace Azucar\Middleware;

use Azucar\Support\ApiError;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Slim\Exception\HttpMethodNotAllowedException;
use Slim\Exception\HttpNotFoundException;
use Slim\Psr7\Response;
use Throwable;

/**
 * Every error leaves the API as {"detail": "..."} — the frontend parses that
 * exact shape (js/app.js apiFetch).
 */
final class ErrorHandler
{
    public function __invoke(
        ServerRequestInterface $request,
        Throwable $exception,
        bool $displayErrorDetails,
        bool $logErrors,
        bool $logErrorDetails
    ): ResponseInterface {
        $response = new Response();

        if ($exception instanceof ApiError) {
            $status = $exception->status;
            $detail = $exception->getMessage();
            foreach ($exception->headers as $name => $value) {
                $response = $response->withHeader($name, $value);
            }
        } elseif ($exception instanceof HttpNotFoundException) {
            $status = 404;
            $detail = 'Not Found';
        } elseif ($exception instanceof HttpMethodNotAllowedException) {
            $status = 405;
            $detail = 'Method Not Allowed';
        } else {
            $status = 500;
            $detail = 'Internal server error';
            error_log(sprintf(
                '[azucar] %s: %s in %s:%d',
                get_class($exception),
                $exception->getMessage(),
                $exception->getFile(),
                $exception->getLine()
            ));
        }

        $response->getBody()->write(
            json_encode(['detail' => $detail], JSON_UNESCAPED_UNICODE)
        );
        return $response
            ->withHeader('Content-Type', 'application/json')
            ->withStatus($status);
    }
}
