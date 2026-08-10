<?php

declare(strict_types=1);

namespace Azucar\Services\Providers;

use GuzzleHttp\Client;

/** OpenRouter, DeepSeek, NVIDIA, Kimi (Moonshot) — POST {base}/chat/completions. */
final class OpenAiCompatProvider
{
    public function chat(array $config, array $messages, bool $jsonMode, ?float $temperature, int $timeout): string
    {
        $payload = [
            'model' => $config['model'],
            'messages' => $messages,
        ];
        if ($temperature !== null) {
            $payload['temperature'] = $temperature;
        }
        if ($jsonMode) {
            $payload['response_format'] = ['type' => 'json_object'];
        }

        $client = new Client(['timeout' => $timeout, 'connect_timeout' => 10]);
        $response = $client->post(rtrim($config['base_url'], '/') . '/chat/completions', [
            'headers' => [
                'Authorization' => 'Bearer ' . $config['api_key'],
                'Content-Type' => 'application/json',
                'HTTP-Referer' => 'https://azucar.redesk.us',
                'X-Title' => 'Azucar Control',
            ],
            'json' => $payload,
        ]);

        $data = json_decode((string) $response->getBody(), true);
        $content = $data['choices'][0]['message']['content'] ?? null;
        if (!is_string($content)) {
            throw new \RuntimeException('Unexpected AI response shape');
        }
        return $content;
    }
}
