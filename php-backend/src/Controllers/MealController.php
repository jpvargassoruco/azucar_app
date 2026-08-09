<?php

declare(strict_types=1);

namespace Azucar\Controllers;

use Azucar\Database;
use Azucar\Services\AiService;
use Azucar\Services\ImageService;
use Azucar\Services\MealAnalyzer;
use Azucar\Support\ApiError;
use Azucar\Support\Dt;
use Azucar\Support\Respond;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

final class MealController
{
    private const ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp'];

    public function list(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $stmt = Database::pdo()->prepare(
            'SELECT * FROM meal_entries WHERE user_id = ? ORDER BY datetime DESC'
        );
        $stmt->execute([$user['id']]);
        return Respond::json($response, array_map([self::class, 'serialize'], $stmt->fetchAll()));
    }

    /** POST /meals/upload — multipart {photo, notes?, meal_datetime?} with inline AI analysis. */
    public function upload(Request $request, Response $response): Response
    {
        set_time_limit(120); // inline vision call may take up to ~45s
        ignore_user_abort(true);

        $user = $request->getAttribute('user');
        $body = (array) $request->getParsedBody();
        $files = $request->getUploadedFiles();

        $photo = $files['photo'] ?? null;
        if ($photo === null || $photo->getError() !== UPLOAD_ERR_OK) {
            throw new ApiError('No se recibió la foto de comida.', 400);
        }

        $mealDatetime = Dt::nowUtcSql();
        if (!empty($body['meal_datetime'])) {
            $parsed = Dt::parseToUtcSql((string) $body['meal_datetime']);
            if ($parsed === null) {
                throw new ApiError('Formato de fecha inválido. Usa formato ISO 8601 (YYYY-MM-DDTHH:MM).', 400);
            }
            $mealDatetime = $parsed;
        }

        $ext = strtolower('.' . pathinfo($photo->getClientFilename() ?? '', PATHINFO_EXTENSION));
        if (!in_array($ext, self::ALLOWED_EXTENSIONS, true)) {
            throw new ApiError('Formato de imagen no soportado. Por favor sube archivos JPG, PNG o WebP.', 400);
        }

        $uploadsDir = ImageService::uploadsDir();
        if (!is_dir($uploadsDir)) {
            mkdir($uploadsDir, 0775, true);
        }
        $uniqueId = bin2hex(random_bytes(16));
        $tempPath = "$uploadsDir/temp_{$uniqueId}{$ext}";

        $pdo = Database::pdo();
        try {
            $photo->moveTo($tempPath);
            if (getimagesize($tempPath) === false) {
                throw new ApiError('El archivo no es una imagen válida.', 400);
            }

            $healthContext = AiService::getUserHealthContext($pdo, $user);
            $analysis = MealAnalyzer::analyzeMealImage($tempPath, $user, $healthContext);
            $thumbnailPath = ImageService::compressToThumbnail($tempPath, $uploadsDir, "{$uniqueId}{$ext}");
        } catch (ApiError $ex) {
            throw $ex;
        } catch (\Throwable $ex) {
            throw new ApiError('Error al procesar la foto de comida: ' . $ex->getMessage(), 500);
        } finally {
            if (is_file($tempPath)) {
                unlink($tempPath);
            }
        }

        $webThumbPath = '/uploads/' . basename($thumbnailPath);
        $pdo->prepare(
            'INSERT INTO meal_entries (user_id, datetime, photo_path, thumbnail_path, notes, ai_analysis)
             VALUES (?, ?, NULL, ?, ?, ?)'
        )->execute([
            $user['id'],
            $mealDatetime,
            $webThumbPath,
            $body['notes'] ?? null,
            json_encode($analysis, JSON_UNESCAPED_UNICODE),
        ]);

        return Respond::json($response, self::fetch($pdo, (int) $pdo->lastInsertId()), 201);
    }

    public function update(Request $request, Response $response, array $args): Response
    {
        $user = $request->getAttribute('user');
        $body = (array) $request->getParsedBody();
        $pdo = Database::pdo();

        $meal = self::findOwned($pdo, (int) $args['id'], (int) $user['id'], 'Meal not found');

        if (array_key_exists('notes', $body) && $body['notes'] !== null) {
            $pdo->prepare('UPDATE meal_entries SET notes = ? WHERE id = ?')
                ->execute([(string) $body['notes'], $meal['id']]);
        }
        if (array_key_exists('ai_analysis', $body) && is_array($body['ai_analysis'])) {
            $pdo->prepare('UPDATE meal_entries SET ai_analysis = ? WHERE id = ?')
                ->execute([json_encode($body['ai_analysis'], JSON_UNESCAPED_UNICODE), $meal['id']]);
        }

        return Respond::json($response, self::fetch($pdo, (int) $meal['id']));
    }

    /** POST /meals/{id}/correct — AI re-analysis from a user comment. */
    public function correct(Request $request, Response $response, array $args): Response
    {
        set_time_limit(120);
        $user = $request->getAttribute('user');
        $body = (array) $request->getParsedBody();
        $pdo = Database::pdo();

        $meal = self::findOwned($pdo, (int) $args['id'], (int) $user['id'], 'Meal not found');
        if ($meal['ai_analysis'] === null) {
            throw new ApiError('Meal has no existing analysis to correct', 400);
        }
        $comment = trim((string) ($body['correction_comment'] ?? ''));
        if ($comment === '') {
            throw new ApiError('El comentario de corrección es obligatorio.', 422);
        }

        $healthContext = AiService::getUserHealthContext($pdo, $user);
        $corrected = MealAnalyzer::correctMealAnalysis(
            json_decode($meal['ai_analysis'], true) ?? [],
            $comment,
            $user,
            $healthContext
        );

        $pdo->prepare('UPDATE meal_entries SET ai_analysis = ? WHERE id = ?')
            ->execute([json_encode($corrected, JSON_UNESCAPED_UNICODE), $meal['id']]);

        return Respond::json($response, self::fetch($pdo, (int) $meal['id']));
    }

    public function delete(Request $request, Response $response, array $args): Response
    {
        $user = $request->getAttribute('user');
        $pdo = Database::pdo();

        $meal = self::findOwned(
            $pdo,
            (int) $args['id'],
            (int) $user['id'],
            'Comida no encontrada o no tienes permisos para eliminarla.'
        );

        if ($meal['thumbnail_path'] !== null) {
            $diskPath = ImageService::uploadsDir() . '/' . basename($meal['thumbnail_path']);
            if (is_file($diskPath) && !unlink($diskPath)) {
                error_log("[azucar] No se pudo eliminar el archivo $diskPath");
            }
        }

        $pdo->prepare('DELETE FROM meal_entries WHERE id = ?')->execute([$meal['id']]);
        return Respond::noContent($response);
    }

    private static function findOwned(\PDO $pdo, int $id, int $userId, string $notFoundDetail): array
    {
        $stmt = $pdo->prepare('SELECT * FROM meal_entries WHERE id = ? AND user_id = ?');
        $stmt->execute([$id, $userId]);
        $meal = $stmt->fetch();
        if ($meal === false) {
            throw new ApiError($notFoundDetail, 404);
        }
        return $meal;
    }

    private static function fetch(\PDO $pdo, int $id): array
    {
        $stmt = $pdo->prepare('SELECT * FROM meal_entries WHERE id = ?');
        $stmt->execute([$id]);
        return self::serialize($stmt->fetch());
    }

    private static function serialize(array $row): array
    {
        return [
            'id' => (int) $row['id'],
            'user_id' => (int) $row['user_id'],
            'datetime' => Dt::out($row['datetime']),
            'photo_path' => $row['photo_path'],
            'thumbnail_path' => $row['thumbnail_path'],
            'notes' => $row['notes'],
            'ai_analysis' => $row['ai_analysis'] !== null ? json_decode($row['ai_analysis'], true) : null,
        ];
    }
}
