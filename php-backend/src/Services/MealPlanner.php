<?php

declare(strict_types=1);

namespace Azucar\Services;

use Azucar\Support\ApiError;
use Azucar\Support\JsonExtractor;

/** Port of meal_planner.py, with the fence-less-response bug fixed. */
final class MealPlanner
{
    public static function generateMealPlan(string $healthContext, ?string $preferences, int $numMeals, ?array $user): array
    {
        if (!AiClient::hasKey($user)) {
            throw new ApiError('No API Key configured for meal planner.', 500);
        }

        $prefStr = $preferences !== null && $preferences !== ''
            ? "Preferencias o restricciones: {$preferences}"
            : 'Sin restricciones particulares.';

        $prompt = "Eres un nutricionista experto en diabetes tipo 2. Diseña un plan de comidas de 1 día para este paciente.\n\n"
            . "CONTEXTO DE SALUD DEL PACIENTE:\n{$healthContext}\n\n"
            . "PREFERENCIAS:\n{$prefStr}\n"
            . "CANTIDAD DE COMIDAS SOLICITADAS: {$numMeals}\n\n"
            . "Responde EXCLUSIVAMENTE con un objeto JSON estructurado que siga exactamente este esquema, sin bloques de código markdown, sin texto adicional:\n"
            . "{\n"
            . "  \"plan_date\": \"YYYY-MM-DD\",\n"
            . "  \"meals\": [\n"
            . "    {\n"
            . "      \"meal_type\": \"desayuno|almuerzo|cena|merienda\",\n"
            . "      \"time_suggestion\": \"HH:MM\",\n"
            . "      \"description\": \"descripción del plato\",\n"
            . "      \"estimated_calories\": número,\n"
            . "      \"estimated_carbs_g\": número,\n"
            . "      \"glycemic_impact\": \"bajo|moderado|alto\",\n"
            . "      \"reasoning\": \"por qué es bueno para el paciente\"\n"
            . "    }\n"
            . "  ],\n"
            . "  \"daily_summary\": {\n"
            . "    \"total_calories\": número,\n"
            . "    \"total_carbs_g\": número\n"
            . "  },\n"
            . "  \"tips\": [\"consejo 1\", \"consejo 2\"]\n"
            . '}';

        try {
            $content = AiClient::chat([['role' => 'user', 'content' => $prompt]], $user, jsonMode: true);
        } catch (\Throwable $ex) {
            error_log('[azucar-ai] Error generating meal plan: ' . $ex->getMessage());
            throw new ApiError('Error generando plan: ' . $ex->getMessage(), 500);
        }

        $plan = JsonExtractor::extract($content);
        if ($plan === null) {
            // FastAPI stored null into a NOT NULL column here; fail loudly instead
            throw new ApiError('Error generando plan: la respuesta de la IA no es un JSON válido.', 500);
        }
        return $plan;
    }
}
