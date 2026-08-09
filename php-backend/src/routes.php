<?php

declare(strict_types=1);

use Azucar\Controllers\AuthController;
use Azucar\Middleware\AuthMiddleware;
use Azucar\Support\Respond;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;
use Slim\App;
use Slim\Routing\RouteCollectorProxy;

return static function (App $app): void {
    $auth = new AuthMiddleware();

    $app->get('/health', function (Request $request, Response $response): Response {
        return Respond::json($response, ['status' => 'ok']);
    });

    $app->group('/v1', function (RouteCollectorProxy $v1) use ($auth): void {

        $v1->group('/auth', function (RouteCollectorProxy $g) use ($auth): void {
            $g->post('/register', [AuthController::class, 'register']);
            $g->post('/login', [AuthController::class, 'login']);
            $g->get('/me', [AuthController::class, 'me'])->add($auth);
            $g->put('/me/ai-settings', [AuthController::class, 'updateAiSettings'])->add($auth);
            // POST /auth/test-ai registered in Phase 4 (AI providers)
        });
    });
};
