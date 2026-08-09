<?php

declare(strict_types=1);

use Azucar\Controllers\AlarmController;
use Azucar\Controllers\AuthController;
use Azucar\Controllers\FastingController;
use Azucar\Controllers\GlucoseController;
use Azucar\Controllers\HabitController;
use Azucar\Controllers\Hba1cController;
use Azucar\Controllers\MedicationController;
use Azucar\Controllers\PressureController;
use Azucar\Controllers\WeightController;
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

        $v1->group('/glucose', function (RouteCollectorProxy $g): void {
            $g->get('', [GlucoseController::class, 'list']);
            $g->post('', [GlucoseController::class, 'create']);
            $g->get('/stats', [GlucoseController::class, 'stats']);
            $g->delete('/{id:[0-9]+}', [GlucoseController::class, 'delete']);
        })->add($auth);

        $v1->group('/weights', function (RouteCollectorProxy $g): void {
            $g->get('', [WeightController::class, 'list']);
            $g->post('', [WeightController::class, 'create']);
            $g->delete('/{id:[0-9]+}', [WeightController::class, 'delete']);
        })->add($auth);

        $v1->group('/pressures', function (RouteCollectorProxy $g): void {
            $g->get('', [PressureController::class, 'list']);
            $g->post('', [PressureController::class, 'create']);
            $g->delete('/{id:[0-9]+}', [PressureController::class, 'delete']);
        })->add($auth);

        $v1->group('/hba1c', function (RouteCollectorProxy $g): void {
            $g->get('', [Hba1cController::class, 'list']);
            $g->post('', [Hba1cController::class, 'create']);
            $g->delete('/{id:[0-9]+}', [Hba1cController::class, 'delete']);
        })->add($auth);

        $v1->group('/fasting', function (RouteCollectorProxy $g): void {
            $g->get('', [FastingController::class, 'list']);
            $g->get('/active', [FastingController::class, 'active']);
            $g->post('/start', [FastingController::class, 'start']);
            $g->post('/stop', [FastingController::class, 'stop']);
        })->add($auth);

        $v1->group('/habits', function (RouteCollectorProxy $g): void {
            $g->get('/today', [HabitController::class, 'today']);
            $g->post('/toggle', [HabitController::class, 'toggle']);
            $g->get('/progress', [HabitController::class, 'progress']);
        })->add($auth);

        $v1->group('/alarms', function (RouteCollectorProxy $g): void {
            $g->get('', [AlarmController::class, 'list']);
            $g->post('', [AlarmController::class, 'createOrUpdate']);
            $g->put('/{id:[0-9]+}', [AlarmController::class, 'update']);
            $g->delete('/{id:[0-9]+}', [AlarmController::class, 'delete']);
        })->add($auth);

        $v1->group('/medications', function (RouteCollectorProxy $g): void {
            $g->get('', [MedicationController::class, 'list']);
            $g->post('', [MedicationController::class, 'create']);
            $g->get('/today', [MedicationController::class, 'today']);
            $g->post('/log', [MedicationController::class, 'markDose']);
            $g->put('/{id:[0-9]+}', [MedicationController::class, 'update']);
            $g->delete('/{id:[0-9]+}', [MedicationController::class, 'delete']);
        })->add($auth);
    });
};
