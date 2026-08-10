<?php

declare(strict_types=1);

namespace Azucar\Services\Providers;

use GuzzleHttp\Client;

/** Google Gemini — POST {base}/models/{model}:generateContent (port of _call_google). */
final class GoogleProvider
{
    public function chat(array $config, array $messages, bool $jsonMode, int $timeout): string
    {
        $payload = self::buildPayload($config['model'], $messages, $jsonMode);
        $url = sprintf(
            '%s/models/%s:generateContent?key=%s',
            rtrim($config['base_url'], '/'),
            $config['model'],
            $config['api_key']
        );

        $client = new Client(['timeout' => $timeout, 'connect_timeout' => 10]);
        $response = $client->post($url, [
            'headers' => [
                'Content-Type' => 'application/json',
                'X-goog-api-key' => $config['api_key'],
            ],
            'json' => $payload,
        ]);

        return self::parseResponse(json_decode((string) $response->getBody(), true));
    }

    /** Translate OpenAI-format messages (incl. image data-URLs) into Gemini payload. */
    public static function buildPayload(string $model, array $messages, bool $jsonMode): array
    {
        $contents = [];
        $systemInstruction = null;

        foreach ($messages as $msg) {
            $role = $msg['role'] ?? 'user';
            $content = $msg['content'] ?? '';

            if ($role === 'system') {
                $systemInstruction = is_string($content) ? $content : json_encode($content);
                continue;
            }

            $parts = [];
            if (is_string($content)) {
                $parts[] = ['text' => $content];
            } elseif (is_array($content)) {
                foreach ($content as $item) {
                    if (($item['type'] ?? '') === 'text') {
                        $parts[] = ['text' => $item['text']];
                    } elseif (($item['type'] ?? '') === 'image_url') {
                        $imageUrl = $item['image_url']['url'] ?? '';
                        if (str_starts_with($imageUrl, 'data:image')) {
                            [$header, $b64data] = explode(',', $imageUrl, 2);
                            $mimeType = explode(';', explode(':', $header)[1] ?? 'image/jpeg')[0];
                            $parts[] = ['inline_data' => ['mime_type' => $mimeType, 'data' => $b64data]];
                        }
                    }
                }
            }

            if ($parts !== []) {
                $contents[] = [
                    'role' => $role === 'assistant' ? 'model' : 'user',
                    'parts' => $parts,
                ];
            }
        }

        $payload = ['contents' => $contents];
        if ($systemInstruction !== null) {
            $payload['systemInstruction'] = ['parts' => [['text' => $systemInstruction]]];
        }
        if ($jsonMode) {
            $payload['generationConfig'] = ['responseMimeType' => 'application/json'];
        }
        return $payload;
    }

    public static function parseResponse(?array $json): string
    {
        $parts = $json['candidates'][0]['content']['parts'] ?? [];
        $text = '';
        foreach ($parts as $part) {
            $text .= $part['text'] ?? '';
        }
        return $text;
    }
}
