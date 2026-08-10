<?php

declare(strict_types=1);

namespace Azucar\Controllers;

use Azucar\Database;
use Azucar\Services\AiService;
use Azucar\Services\MealPlanner;
use Azucar\Support\ApiError;
use Azucar\Support\Dt;
use Azucar\Support\Respond;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

final class MealPlanController
{
    /** POST /meal-plan/generate — {preferences?, num_meals?} */
    public function generate(Request $request, Response $response): Response
    {
        set_time_limit(120); // inline AI call
        $user = $request->getAttribute('user');
        $body = (array) $request->getParsedBody();

        $preferences = isset($body['preferences']) ? (string) $body['preferences'] : null;
        $numMeals = (int) ($body['num_meals'] ?? 3);

        $pdo = Database::pdo();
        $healthContext = AiService::getUserHealthContext($pdo, $user);
        $planData = MealPlanner::generateMealPlan($healthContext, $preferences, $numMeals, $user);

        $pdo->prepare(
            'INSERT INTO meal_plans (user_id, preferences, plan_data) VALUES (?, ?, ?)'
        )->execute([$user['id'], $preferences, json_encode($planData, JSON_UNESCAPED_UNICODE)]);

        return Respond::json($response, self::fetch($pdo, (int) $pdo->lastInsertId()));
    }

    /** GET /meal-plan/latest */
    public function latest(Request $request, Response $response): Response
    {
        $user = $request->getAttribute('user');
        $stmt = Database::pdo()->prepare(
            'SELECT * FROM meal_plans WHERE user_id = ? ORDER BY created_at DESC, id DESC LIMIT 1'
        );
        $stmt->execute([$user['id']]);
        $plan = $stmt->fetch();
        if ($plan === false) {
            throw new ApiError('No meal plans found', 404);
        }
        return Respond::json($response, self::serialize($plan));
    }

    private static function fetch(\PDO $pdo, int $id): array
    {
        $stmt = $pdo->prepare('SELECT * FROM meal_plans WHERE id = ?');
        $stmt->execute([$id]);
        return self::serialize($stmt->fetch());
    }

    private static function serialize(array $row): array
    {
        return [
            'id' => (int) $row['id'],
            'user_id' => (int) $row['user_id'],
            'created_at' => Dt::out($row['created_at']),
            'preferences' => $row['preferences'],
            'plan_data' => json_decode($row['plan_data'], true),
        ];
    }
}
