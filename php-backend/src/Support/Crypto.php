<?php

declare(strict_types=1);

namespace Azucar\Support;

/**
 * AI API-key encryption at rest using libsodium secretbox.
 * Ciphertexts are stored as "sbx1:" . base64(nonce . box) so legacy plaintext
 * values (the FastAPI deployment never enabled Fernet) remain readable.
 */
final class Crypto
{
    private const PREFIX = 'sbx1:';

    private static function key(): ?string
    {
        $appKey = $_ENV['APP_KEY'] ?? '';
        if ($appKey === '') {
            return null;
        }
        return hash('sha256', $appKey, true); // 32 bytes = SODIUM_CRYPTO_SECRETBOX_KEYBYTES
    }

    public static function encrypt(?string $plain): ?string
    {
        if ($plain === null || $plain === '') {
            return null;
        }
        $key = self::key();
        if ($key === null) {
            return $plain; // no encryption configured; store as-is (mirrors FastAPI behavior)
        }
        $nonce = random_bytes(SODIUM_CRYPTO_SECRETBOX_NONCEBYTES);
        $box = sodium_crypto_secretbox($plain, $nonce, $key);
        return self::PREFIX . base64_encode($nonce . $box);
    }

    public static function decrypt(?string $stored): ?string
    {
        if ($stored === null || $stored === '') {
            return null;
        }
        if (!str_starts_with($stored, self::PREFIX)) {
            return $stored; // legacy plaintext
        }
        $key = self::key();
        if ($key === null) {
            return null; // encrypted but no key configured: unreadable
        }
        $raw = base64_decode(substr($stored, strlen(self::PREFIX)), true);
        if ($raw === false || strlen($raw) <= SODIUM_CRYPTO_SECRETBOX_NONCEBYTES) {
            return null;
        }
        $nonce = substr($raw, 0, SODIUM_CRYPTO_SECRETBOX_NONCEBYTES);
        $box = substr($raw, SODIUM_CRYPTO_SECRETBOX_NONCEBYTES);
        $plain = sodium_crypto_secretbox_open($box, $nonce, $key);
        return $plain === false ? null : $plain;
    }
}
