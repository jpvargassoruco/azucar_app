<?php

declare(strict_types=1);

namespace Azucar\Services\Providers;

use GuzzleHttp\Client;

/**
 * Anthropic Messages API adapter (new provider, not in the FastAPI original).
 * Translates OpenAI-format messages into /v1/messages: system content becomes
 * the top-level `system` param, image_url data-URLs become base64 image blocks.
 * No `temperature` is sent (removed on current Claude models) and thinking is
 * left at its default. Responses with stop_reason "refusal" raise so callers
 * fall back gracefully.
 */
final class AnthropicProvider
{
    private const API_VERSION = '2023-06-01';

    public function chat(array $config, array $messages, bool $jsonMode, int $timeout): string
    {
        [$system, $anthropicMessages] = self::convertMessages($messages);

        $payload = [
            'model' => $config['model'],
            // Deliberately short JSON/chat outputs; also bounds latency for
            // the inline shared-hosting request path.
            'max_tokens' => 4096,
            'messages' => $anthropicMessages,
        ];
        if ($system !== null) {
            $payload['system'] = $system;
        }
        if ($jsonMode) {
            // No response_format equivalent needed: the prompts already demand
            // JSON-only output and callers extract fenced-or-bare JSON.
            $payload['system'] = trim(($system ?? '') . "\nResponde únicamente con el objeto JSON solicitado, sin texto adicional.");
        }

        $client = new Client(['timeout' => $timeout, 'connect_timeout' => 10]);
        $response = $client->post(rtrim($config['base_url'], '/') . '/v1/messages', [
            'headers' => [
                'x-api-key' => $config['api_key'],
                'anthropic-version' => self::API_VERSION,
                'Content-Type' => 'application/json',
            ],
            'json' => $payload,
        ]);

        $data = json_decode((string) $response->getBody(), true);
        if (($data['stop_reason'] ?? '') === 'refusal') {
            throw new \RuntimeException('El proveedor de IA rechazó la solicitud.');
        }

        $text = '';
        foreach ($data['content'] ?? [] as $block) {
            if (($block['type'] ?? '') === 'text') {
                $text .= $block['text'];
            }
        }
        if ($text === '') {
            throw new \RuntimeException('Unexpected AI response shape');
        }
        return $text;
    }

    /** @return array{0: ?string, 1: array} [system, messages] */
    public static function convertMessages(array $messages): array
    {
        $system = null;
        $converted = [];

        foreach ($messages as $msg) {
            $role = $msg['role'] ?? 'user';
            $content = $msg['content'] ?? '';

            if ($role === 'system') {
                $system = is_string($content) ? $content : json_encode($content);
                continue;
            }

            if (is_string($content)) {
                $converted[] = ['role' => $role, 'content' => $content];
                continue;
            }

            $blocks = [];
            foreach ($content as $item) {
                if (($item['type'] ?? '') === 'text') {
                    $blocks[] = ['type' => 'text', 'text' => $item['text']];
                } elseif (($item['type'] ?? '') === 'image_url') {
                    $imageUrl = $item['image_url']['url'] ?? '';
                    if (str_starts_with($imageUrl, 'data:image')) {
                        [$header, $b64data] = explode(',', $imageUrl, 2);
                        $mimeType = explode(';', explode(':', $header)[1] ?? 'image/jpeg')[0];
                        $blocks[] = [
                            'type' => 'image',
                            'source' => ['type' => 'base64', 'media_type' => $mimeType, 'data' => $b64data],
                        ];
                    }
                }
            }
            if ($blocks !== []) {
                $converted[] = ['role' => $role, 'content' => $blocks];
            }
        }

        return [$system, $converted];
    }
}
