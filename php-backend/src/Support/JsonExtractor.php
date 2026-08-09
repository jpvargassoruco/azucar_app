<?php

declare(strict_types=1);

namespace Azucar\Support;

/**
 * Extract a JSON object from an LLM response that may or may not be wrapped in
 * markdown fences. Fixes the FastAPI meal_planner bug where fence-less
 * responses silently returned None.
 */
final class JsonExtractor
{
    public static function extract(string $content): ?array
    {
        $cleaned = trim($content);

        if (str_starts_with($cleaned, '```')) {
            $lines = explode("\n", $cleaned);
            if (str_starts_with($lines[0], '```')) {
                array_shift($lines);
            }
            if ($lines !== [] && str_starts_with(trim(end($lines)), '```')) {
                array_pop($lines);
            }
            $cleaned = trim(implode("\n", $lines));
        }

        $decoded = json_decode($cleaned, true);
        if (is_array($decoded)) {
            return $decoded;
        }

        // Last resort: take the outermost {...} span
        $start = strpos($cleaned, '{');
        $end = strrpos($cleaned, '}');
        if ($start !== false && $end !== false && $end > $start) {
            $decoded = json_decode(substr($cleaned, $start, $end - $start + 1), true);
            if (is_array($decoded)) {
                return $decoded;
            }
        }
        return null;
    }
}
