<?php

declare(strict_types=1);

namespace Azucar\Services;

use Azucar\Support\JsonExtractor;

/** Port of meal_analyzer.py — vision analysis + AI-assisted correction. */
final class MealAnalyzer
{
    private const SCHEMA_PROMPT =
        "{\n"
        . "  \"food_items\": [\"lista de alimentos identificados\"],\n"
        . "  \"calories_estimated\": número,\n"
        . "  \"carbs_g\": número,\n"
        . "  \"protein_g\": número,\n"
        . "  \"fat_g\": número,\n"
        . "  \"fiber_g\": número,\n"
        . "  \"glycemic_impact\": \"bajo|moderado|alto\",\n"
        . "  \"recommendation\": \"consejo breve de nutrición para un paciente con diabetes tipo 2\"\n"
        . "}\n";

    public static function analyzeMealImage(string $imagePath, ?array $user, string $healthContext): array
    {
        if (!AiClient::hasKey($user, vision: true)) {
            error_log('[azucar-ai] No API key configured for meal analysis. Returning fallback.');
            return self::fallbackAnalysis();
        }

        try {
            $base64Image = base64_encode((string) file_get_contents($imagePath));
            $imageDataUrl = 'data:image/jpeg;base64,' . $base64Image;

            $prompt = 'Eres un nutricionista experto en diabetes tipo 2. Analiza esta foto de comida y responde EXCLUSIVAMENTE '
                . "con un objeto JSON estructurado que siga exactamente este esquema, sin bloques de código markdown, sin texto adicional:\n"
                . self::SCHEMA_PROMPT;
            if ($healthContext !== '') {
                $prompt .= "\nCONTEXTO DE SALUD DEL PACIENTE:\n{$healthContext}\n";
            }

            $messages = [[
                'role' => 'user',
                'content' => [
                    ['type' => 'text', 'text' => $prompt],
                    ['type' => 'image_url', 'image_url' => ['url' => $imageDataUrl]],
                ],
            ]];

            $content = AiClient::chat($messages, $user, jsonMode: true, vision: true);
            $analysis = JsonExtractor::extract($content);
            if ($analysis === null) {
                throw new \RuntimeException('AI response is not valid JSON');
            }
            return $analysis;
        } catch (\Throwable $ex) {
            error_log('[azucar-ai] Error in Vision analysis: ' . $ex->getMessage());
            return self::fallbackAnalysis();
        }
    }

    public static function correctMealAnalysis(array $currentAnalysis, string $correctionComment, ?array $user, string $healthContext): array
    {
        if (!AiClient::hasKey($user)) {
            return $currentAnalysis;
        }

        try {
            $prompt = "Eres un nutricionista experto en diabetes tipo 2. El usuario ha proveído una corrección para el análisis nutricional de una comida reciente.\n"
                . 'El análisis anterior era:' . "\n"
                . json_encode($currentAnalysis, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE) . "\n\n"
                . "El usuario comenta lo siguiente sobre la comida: \"{$correctionComment}\"\n\n"
                . 'Por favor corrige el análisis considerando el comentario del usuario y devuelve EXCLUSIVAMENTE el objeto JSON estructurado actualizado. '
                . "No incluyas bloques de código markdown, solo el JSON:\n"
                . self::SCHEMA_PROMPT;
            if ($healthContext !== '') {
                $prompt .= "\n\nCONTEXTO DE SALUD DEL PACIENTE:\n{$healthContext}";
            }

            $content = AiClient::chat([['role' => 'user', 'content' => $prompt]], $user, jsonMode: true);
            $analysis = JsonExtractor::extract($content);
            return $analysis ?? $currentAnalysis;
        } catch (\Throwable $ex) {
            error_log('[azucar-ai] Error in meal correction: ' . $ex->getMessage());
            return $currentAnalysis;
        }
    }

    /**
     * IMPORTANT: the frontend string-matches "Fallback" in food_items and
     * "No se pudo conectar" in recommendation to auto-delete failed analyses
     * (js/app.js). These exact strings must not change.
     */
    public static function fallbackAnalysis(): array
    {
        return [
            'food_items' => ['Alimento no identificado (Fallback)'],
            'calories_estimated' => 350,
            'carbs_g' => 30,
            'protein_g' => 15,
            'fat_g' => 10,
            'fiber_g' => 3,
            'glycemic_impact' => 'moderado',
            'recommendation' => 'No se pudo conectar con el servicio de análisis de IA. Por favor, verifica tu OpenRouter API Key.',
        ];
    }
}
