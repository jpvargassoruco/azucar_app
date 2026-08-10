<?php

declare(strict_types=1);

namespace Azucar\Controllers;

use Azucar\Database;
use Azucar\Support\ApiError;
use Azucar\Support\Crypto;
use Azucar\Support\Respond;
use Firebase\JWT\JWT;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

final class AuthController
{
    /** POST /auth/register — JSON {email, name, password} */
    public function register(Request $request, Response $response): Response
    {
        $body = (array) $request->getParsedBody();
        $email = trim((string) ($body['email'] ?? ''));
        $name = trim((string) ($body['name'] ?? ''));
        $password = (string) ($body['password'] ?? '');

        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            throw new ApiError('El correo electrónico no es válido.', 422);
        }
        if ($name === '') {
            throw new ApiError('El nombre es obligatorio.', 422);
        }
        $this->validatePasswordComplexity($password);

        $pdo = Database::pdo();
        $stmt = $pdo->prepare('SELECT id FROM users WHERE email = ?');
        $stmt->execute([$email]);
        if ($stmt->fetch() !== false) {
            throw new ApiError('El correo electrónico ya está registrado.', 400);
        }

        $stmt = $pdo->prepare(
            'INSERT INTO users (email, name, hashed_password, is_active) VALUES (?, ?, ?, 1)'
        );
        $stmt->execute([$email, $name, password_hash($password, PASSWORD_BCRYPT)]);

        $user = $this->fetchUser($pdo, (int) $pdo->lastInsertId());
        return Respond::json($response, self::userResponse($user), 201);
    }

    /** POST /auth/login — form-urlencoded {username, password} (OAuth2 password flow) */
    public function login(Request $request, Response $response): Response
    {
        $body = (array) $request->getParsedBody();
        $email = trim((string) ($body['username'] ?? ''));
        $password = (string) ($body['password'] ?? '');

        $stmt = Database::pdo()->prepare('SELECT * FROM users WHERE email = ?');
        $stmt->execute([$email]);
        $user = $stmt->fetch();

        if ($user === false || !password_verify($password, $user['hashed_password'])) {
            throw new ApiError(
                'Correo electrónico o contraseña incorrectos.',
                401,
                ['WWW-Authenticate' => 'Bearer']
            );
        }
        if (!(bool) $user['is_active']) {
            throw new ApiError('La cuenta de usuario está desactivada.', 403);
        }

        $now = time();
        $token = JWT::encode(
            [
                'exp' => $now + 60 * (int) ($_ENV['JWT_EXPIRE_MINUTES'] ?? 60),
                'sub' => (string) $user['id'],
                'iat' => $now,
            ],
            $_ENV['JWT_SECRET_KEY'],
            $_ENV['JWT_ALGORITHM'] ?? 'HS256'
        );

        return Respond::json($response, ['access_token' => $token, 'token_type' => 'bearer']);
    }

    /** GET /auth/me */
    public function me(Request $request, Response $response): Response
    {
        return Respond::json($response, self::userResponse($request->getAttribute('user')));
    }

    /** PUT /auth/me/ai-settings */
    public function updateAiSettings(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $body = (array) $request->getParsedBody();
        $pdo = Database::pdo();

        $updates = [];
        $params = [];
        foreach (['ai_provider', 'ai_model', 'ai_base_url'] as $field) {
            if (array_key_exists($field, $body) && $body[$field] !== null) {
                $updates[] = "$field = ?";
                $params[] = (string) $body[$field];
            }
        }
        // Bug fix vs FastAPI: height was accepted by the schema but never applied
        if (array_key_exists('height', $body) && $body['height'] !== null) {
            $updates[] = 'height = ?';
            $params[] = (int) $body['height'];
        }

        if (array_key_exists('ai_api_key', $body) && $body['ai_api_key'] !== null) {
            $keyValue = trim((string) $body['ai_api_key']);
            if ($keyValue === '') {
                $updates[] = 'ai_api_key = NULL';
            } elseif (str_starts_with($keyValue, '***') || $keyValue === self::maskedKey($user)) {
                // Masked representation submitted back: keep the stored key
            } else {
                $updates[] = 'ai_api_key = ?';
                $params[] = Crypto::encrypt($keyValue);
            }
        }

        if ($updates !== []) {
            $params[] = $user['id'];
            $pdo->prepare('UPDATE users SET ' . implode(', ', $updates) . ' WHERE id = ?')
                ->execute($params);
        }

        return Respond::json($response, self::userResponse($this->fetchUser($pdo, (int) $user['id'])));
    }

    private function fetchUser(\PDO $pdo, int $id): array
    {
        $stmt = $pdo->prepare('SELECT * FROM users WHERE id = ?');
        $stmt->execute([$id]);
        return $stmt->fetch();
    }

    private function validatePasswordComplexity(string $password): void
    {
        if (strlen($password) < 8) {
            throw new ApiError('La contraseña debe tener al menos 8 caracteres.', 422);
        }
        if (!preg_match('/[A-Z]/', $password)) {
            throw new ApiError('La contraseña debe incluir al menos una letra mayúscula.', 422);
        }
        if (!preg_match('/[a-z]/', $password)) {
            throw new ApiError('La contraseña debe incluir al menos una letra minúscula.', 422);
        }
        if (!preg_match('/\d/', $password)) {
            throw new ApiError('La contraseña debe incluir al menos un dígito.', 422);
        }
        if (!preg_match('/[!@#$%^&*(),.?":{}|<>_\-+=;:\[\]]/', $password)) {
            throw new ApiError(
                'La contraseña debe incluir al menos un carácter especial (!@#$%^&*...).',
                422
            );
        }
    }

    /** Mirrors UserResponse (schemas/user.py) including the masked-key computed fields. */
    public static function userResponse(array $user): array
    {
        return [
            'id' => (int) $user['id'],
            'email' => $user['email'],
            'name' => $user['name'],
            'is_active' => (bool) $user['is_active'],
            'created_at' => Respond::iso($user['created_at']),
            'ai_provider' => $user['ai_provider'],
            'ai_model' => $user['ai_model'],
            'ai_base_url' => $user['ai_base_url'],
            'has_ai_key' => !empty($user['ai_api_key']),
            'ai_api_key_masked' => self::maskedKey($user),
            'height' => $user['height'] !== null ? (int) $user['height'] : null,
        ];
    }

    public static function maskedKey(array $user): ?string
    {
        if (empty($user['ai_api_key'])) {
            return null;
        }
        $key = trim(Crypto::decrypt($user['ai_api_key']) ?? $user['ai_api_key']);
        if (strlen($key) <= 8) {
            return '****';
        }
        return substr($key, 0, 4) . '...' . substr($key, -4);
    }
}
