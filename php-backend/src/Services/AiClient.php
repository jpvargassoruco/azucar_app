<?php

declare(strict_types=1);

namespace Azucar\Services;

use Azucar\Services\Providers\AnthropicProvider;
use Azucar\Services\Providers\GoogleProvider;
use Azucar\Services\Providers\OpenAiCompatProvider;
use Azucar\Support\Crypto;

/**
 * Unified AI dispatcher (port of ai_providers.py, Hermes agent dropped).
 * Resolution order: user's personal provider/key -> system default from env.
 * DeepSeek (the system default) has no vision, so vision calls resolve to
 * DEFAULT_VISION_* when the user has no personal key.
 */
final class AiClient
{
    public const PROVIDER_DEFAULTS = [
        'google' => ['url' => 'https://generativelanguage.googleapis.com/v1beta', 'model' => 'gemini-flash-latest'],
        'openrouter' => ['url' => 'https://openrouter.ai/api/v1', 'model' => 'openrouter/auto'],
        'deepseek' => ['url' => 'https://api.deepseek.com/v1', 'model' => 'deepseek-chat'],
        'nvidia' => ['url' => 'https://integrate.api.nvidia.com/v1', 'model' => 'nvidia/nemotron-3-super-120b-a12b'],
        'kimi' => ['url' => 'https://api.moonshot.ai/v1', 'model' => 'kimi-latest'],
        'anthropic' => ['url' => 'https://api.anthropic.com', 'model' => 'claude-opus-5'],
    ];

    /** @return array{provider: string, api_key: string, model: string, base_url: string}|null */
    public static function resolveConfig(?array $user, bool $vision = false): ?array
    {
        if ($user !== null && !empty($user['ai_api_key'])) {
            $apiKey = Crypto::decrypt($user['ai_api_key']);
            if ($apiKey !== null && $apiKey !== '') {
                $provider = $user['ai_provider'] ?: 'openrouter';
                $defaults = self::PROVIDER_DEFAULTS[$provider] ?? self::PROVIDER_DEFAULTS['openrouter'];
                return [
                    'provider' => $provider,
                    'api_key' => $apiKey,
                    'model' => $user['ai_model'] ?: $defaults['model'],
                    'base_url' => $user['ai_base_url'] ?: $defaults['url'],
                ];
            }
        }

        $prefix = 'DEFAULT_AI';
        if ($vision && !empty($_ENV['DEFAULT_VISION_API_KEY'])) {
            $prefix = 'DEFAULT_VISION';
        }
        $apiKey = $_ENV[$prefix . '_API_KEY'] ?? '';
        if ($apiKey === '') {
            return null;
        }
        $provider = $_ENV[$prefix . '_PROVIDER'] ?? 'deepseek';
        $defaults = self::PROVIDER_DEFAULTS[$provider] ?? self::PROVIDER_DEFAULTS['deepseek'];
        return [
            'provider' => $provider,
            'api_key' => $apiKey,
            'model' => ($_ENV[$prefix . '_MODEL'] ?? '') ?: $defaults['model'],
            'base_url' => ($_ENV[$prefix . '_BASE_URL'] ?? '') ?: $defaults['url'],
        ];
    }

    public static function hasKey(?array $user, bool $vision = false): bool
    {
        return self::resolveConfig($user, $vision) !== null;
    }

    /**
     * Unified chat call. $messages use the OpenAI format (content may be a
     * string or a list of {type:text|image_url} parts). Throws on failure.
     */
    public static function chat(
        array $messages,
        ?array $user = null,
        bool $jsonMode = false,
        float $temperature = 0.7,
        int $timeout = 45,
        bool $vision = false
    ): string {
        $config = self::resolveConfig($user, $vision);
        if ($config === null) {
            throw new \RuntimeException('No API key configured');
        }
        return self::dispatch($config, $messages, $jsonMode, $temperature, $timeout);
    }

    /** @param array{provider: string, api_key: string, model: string, base_url: string} $config */
    public static function dispatch(array $config, array $messages, bool $jsonMode, float $temperature, int $timeout): string
    {
        return match ($config['provider']) {
            'google' => (new GoogleProvider())->chat($config, $messages, $jsonMode, $timeout),
            'anthropic' => (new AnthropicProvider())->chat($config, $messages, $jsonMode, $timeout),
            default => (new OpenAiCompatProvider())->chat($config, $messages, $jsonMode, $temperature, $timeout),
        };
    }
}
