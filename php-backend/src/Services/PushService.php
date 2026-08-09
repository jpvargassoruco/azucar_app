<?php

declare(strict_types=1);

namespace Azucar\Services;

use Minishlink\WebPush\Subscription;
use Minishlink\WebPush\WebPush;
use PDO;

/**
 * Web Push via VAPID (replaces pywebpush). Dead subscriptions (404/410) are
 * deleted by sendToUser, mirroring the worker/notifications-test behavior.
 */
final class PushService
{
    private ?WebPush $webPush = null;

    private function client(): WebPush
    {
        if ($this->webPush === null) {
            $this->webPush = new WebPush([
                'VAPID' => [
                    'subject' => $_ENV['VAPID_MAILTO'] ?? 'mailto:admin@example.com',
                    'publicKey' => $_ENV['VAPID_PUBLIC_KEY'] ?? '',
                    'privateKey' => $_ENV['VAPID_PRIVATE_KEY'] ?? '',
                ],
            ]);
            $this->webPush->setAutomaticPadding(false);
        }
        return $this->webPush;
    }

    /** @return bool true when delivered; false when the subscription is dead/failed */
    public function sendToSubscription(array $sub, array $payload): bool
    {
        try {
            $report = $this->client()->sendOneNotification(
                Subscription::create([
                    'endpoint' => $sub['endpoint'],
                    'publicKey' => $sub['p256dh'],
                    'authToken' => $sub['auth'],
                ]),
                json_encode($payload, JSON_UNESCAPED_UNICODE)
            );
            return $report->isSuccess();
        } catch (\Throwable $e) {
            error_log('[azucar-push] ' . $e->getMessage());
            return false;
        }
    }

    /**
     * Send to every subscription of a user; failed subscriptions are removed.
     *
     * @return array{sent: int, deleted: int}
     */
    public function sendToUser(PDO $pdo, int $userId, array $payload): array
    {
        $stmt = $pdo->prepare('SELECT * FROM push_subscriptions WHERE user_id = ?');
        $stmt->execute([$userId]);
        $subscriptions = $stmt->fetchAll();

        $sent = 0;
        $deleted = 0;
        foreach ($subscriptions as $sub) {
            if ($this->sendToSubscription($sub, $payload)) {
                $sent++;
            } else {
                $pdo->prepare('DELETE FROM push_subscriptions WHERE id = ?')->execute([$sub['id']]);
                $deleted++;
            }
        }
        return ['sent' => $sent, 'deleted' => $deleted];
    }

    public static function basePayload(string $title, string $body, string $url): array
    {
        return [
            'title' => $title,
            'body' => $body,
            'icon' => '/icons/icon-192x192.png',
            'badge' => '/icons/icon-192x192.png',
            'url' => $url,
        ];
    }
}
