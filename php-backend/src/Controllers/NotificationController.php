<?php

declare(strict_types=1);

namespace Azucar\Controllers;

use Azucar\Database;
use Azucar\Services\PushService;
use Azucar\Support\ApiError;
use Azucar\Support\Respond;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

final class NotificationController
{
    /** GET /notifications/key — VAPID public key for pushManager.subscribe(). */
    public function key(Request $request, Response $response): Response
    {
        return Respond::json($response, ['public_key' => $_ENV['VAPID_PUBLIC_KEY'] ?? '']);
    }

    /** POST /notifications/subscribe — body is the raw browser PushSubscription JSON. */
    public function subscribe(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $body = (array) $request->getParsedBody();

        $endpoint = (string) ($body['endpoint'] ?? '');
        $p256dh = (string) ($body['keys']['p256dh'] ?? '');
        $auth = (string) ($body['keys']['auth'] ?? '');
        if ($endpoint === '' || $p256dh === '' || $auth === '') {
            throw new ApiError('Suscripción push inválida.', 422);
        }

        $pdo = Database::pdo();
        $stmt = $pdo->prepare('SELECT id FROM push_subscriptions WHERE endpoint = ?');
        $stmt->execute([$endpoint]);
        $existing = $stmt->fetch();

        if ($existing !== false) {
            $pdo->prepare(
                'UPDATE push_subscriptions SET user_id = ?, p256dh = ?, auth = ? WHERE id = ?'
            )->execute([$user['id'], $p256dh, $auth, $existing['id']]);
            $id = (int) $existing['id'];
        } else {
            $pdo->prepare(
                'INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth) VALUES (?, ?, ?, ?)'
            )->execute([$user['id'], $endpoint, $p256dh, $auth]);
            $id = (int) $pdo->lastInsertId();
        }

        return Respond::json($response, ['status' => 'subscribed', 'id' => $id], 201);
    }

    /** POST /notifications/test — synchronous fan-out to the user's devices. */
    public function test(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $pdo = Database::pdo();

        $stmt = $pdo->prepare('SELECT COUNT(*) AS n FROM push_subscriptions WHERE user_id = ?');
        $stmt->execute([$user['id']]);
        if ((int) $stmt->fetch()['n'] === 0) {
            throw new ApiError('No tienes ningún dispositivo registrado para recibir notificaciones.', 404);
        }

        $result = (new PushService())->sendToUser($pdo, (int) $user['id'], PushService::basePayload(
            'Prueba de Azúcar Control',
            '¡Hola! Las notificaciones Push están configuradas correctamente.',
            '/#stats'
        ));

        return Respond::json($response, [
            'status' => 'enviado',
            'sent_count' => $result['sent'],
            'deleted_count' => $result['deleted'],
        ]);
    }
}
