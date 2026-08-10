<?php

declare(strict_types=1);

namespace Azucar\Controllers;

use Azucar\Database;
use Azucar\Services\AiClient;
use Azucar\Services\AiService;
use Azucar\Support\Respond;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

final class AiController
{
    /** POST /ai/chat — {message, history?} -> {response} */
    public function chat(Request $request, Response $response): Response
    {
        set_time_limit(120); // AI call up to 45s
        $user = $request->getAttribute('user');
        $body = (array) $request->getParsedBody();

        $message = (string) ($body['message'] ?? '');
        $history = is_array($body['history'] ?? null) ? $body['history'] : [];

        $healthContext = AiService::getUserHealthContext(Database::pdo(), $user);
        $responseText = AiService::queryAssistant($message, $history, $healthContext, $user);

        return Respond::json($response, ['response' => $responseText]);
    }

    /** POST /auth/test-ai — probe a provider config before saving (15s timeout). */
    public function testAi(Request $request, Response $response): Response
    {
        $body = (array) $request->getParsedBody();

        $provider = (string) ($body['ai_provider'] ?? '');
        $apiKey = (string) ($body['ai_api_key'] ?? '');
        $model = (string) ($body['ai_model'] ?? '');
        $baseUrl = (string) ($body['ai_base_url'] ?? '');

        $defaults = AiClient::PROVIDER_DEFAULTS[$provider] ?? null;
        $config = [
            'provider' => $provider,
            'api_key' => $apiKey,
            'model' => $model !== '' ? $model : ($defaults['model'] ?? ''),
            'base_url' => $baseUrl !== '' ? $baseUrl : ($defaults['url'] ?? 'https://openrouter.ai/api/v1'),
        ];

        try {
            $content = AiClient::dispatch(
                $config,
                [['role' => 'user', 'content' => 'Hola']],
                jsonMode: false,
                temperature: 0.7,
                timeout: 15
            );
            return Respond::json($response, [
                'success' => true,
                'message' => 'Conexion exitosa',
                'response' => $content,
            ]);
        } catch (\GuzzleHttp\Exception\BadResponseException $ex) {
            return Respond::json($response, [
                'success' => false,
                'message' => 'Error HTTP ' . $ex->getResponse()->getStatusCode(),
                'details' => substr((string) $ex->getResponse()->getBody(), 0, 300),
            ]);
        } catch (\Throwable $ex) {
            return Respond::json($response, [
                'success' => false,
                'message' => 'Error de conexion: ' . $ex->getMessage(),
            ]);
        }
    }
}
