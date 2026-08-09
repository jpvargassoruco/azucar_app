<?php

declare(strict_types=1);

namespace Azucar\Middleware;

use Azucar\Database;
use Azucar\Support\ApiError;
use Firebase\JWT\JWT;
use Firebase\JWT\Key;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

/**
 * Bearer-JWT auth. On success the users row is attached as the "user" request
 * attribute. Mirrors app/auth/dependencies.py: 401 on any token problem,
 * 400 when the account is inactive.
 */
final class AuthMiddleware implements MiddlewareInterface
{
    public function process(ServerRequestInterface $request, RequestHandlerInterface $handler): ResponseInterface
    {
        $token = $this->extractBearerToken($request);
        if ($token === null) {
            throw $this->credentialsError();
        }

        try {
            $payload = JWT::decode(
                $token,
                new Key($_ENV['JWT_SECRET_KEY'], $_ENV['JWT_ALGORITHM'] ?? 'HS256')
            );
            $userId = (int) ($payload->sub ?? 0);
        } catch (\Throwable) {
            throw $this->credentialsError();
        }
        if ($userId <= 0) {
            throw $this->credentialsError();
        }

        $stmt = Database::pdo()->prepare('SELECT * FROM users WHERE id = ?');
        $stmt->execute([$userId]);
        $user = $stmt->fetch();
        if ($user === false) {
            throw $this->credentialsError();
        }
        if (!(bool) $user['is_active']) {
            throw new ApiError('La cuenta de usuario está desactivada.', 400);
        }

        return $handler->handle($request->withAttribute('user', $user));
    }

    private function credentialsError(): ApiError
    {
        return new ApiError(
            'Credenciales de acceso inválidas o expiradas.',
            401,
            ['WWW-Authenticate' => 'Bearer']
        );
    }

    private function extractBearerToken(ServerRequestInterface $request): ?string
    {
        // Shared-hosting fallback chain: PSR-7 header (populated from
        // HTTP_AUTHORIZATION) -> REDIRECT_HTTP_AUTHORIZATION -> getallheaders().
        $header = $request->getHeaderLine('Authorization');
        if ($header === '') {
            $server = $request->getServerParams();
            $header = $server['HTTP_AUTHORIZATION']
                ?? $server['REDIRECT_HTTP_AUTHORIZATION']
                ?? '';
        }
        if ($header === '' && function_exists('getallheaders')) {
            foreach (getallheaders() as $name => $value) {
                if (strcasecmp($name, 'Authorization') === 0) {
                    $header = $value;
                    break;
                }
            }
        }
        if (preg_match('/^Bearer\s+(\S+)$/i', $header, $m)) {
            return $m[1];
        }
        return null;
    }
}
