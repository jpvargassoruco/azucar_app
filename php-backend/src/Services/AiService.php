<?php

declare(strict_types=1);

namespace Azucar\Services;

use Azucar\Support\Dt;
use PDO;

/** Port of ai_service.py: health-context compilation + chat dispatch (Hermes dropped). */
final class AiService
{
    public static function getUserHealthContext(PDO $pdo, array $user): string
    {
        $userId = (int) $user['id'];

        $stmt = $pdo->prepare(
            'SELECT datetime, value_mgdl, `condition` FROM glucose_readings
             WHERE user_id = ? ORDER BY datetime DESC LIMIT 5'
        );
        $stmt->execute([$userId]);
        $readings = $stmt->fetchAll();
        $readingsStr = '';
        foreach ($readings as $r) {
            $readingsStr .= sprintf(
                "- %s: %d mg/dL (%s)\n",
                substr($r['datetime'], 0, 16),
                $r['value_mgdl'],
                $r['condition']
            );
        }
        if ($readingsStr === '') {
            $readingsStr = "No hay lecturas de glucosa registradas aún.\n";
        }

        $stmt = $pdo->prepare('SELECT habit_key, completed FROM habit_logs WHERE user_id = ? AND date = ?');
        $stmt->execute([$userId, Dt::todayLocal()]);
        $logs = $stmt->fetchAll();
        $habitsStr = '';
        foreach ($logs as $log) {
            $habitsStr .= sprintf("- %s: %s\n", $log['habit_key'], $log['completed'] ? 'Completado' : 'Pendiente');
        }
        if ($habitsStr === '') {
            $habitsStr = "Ninguno completado aún hoy.\n";
        }

        $stmt = $pdo->prepare(
            'SELECT start_time, protocol FROM fasting_sessions WHERE user_id = ? AND completed = 0 LIMIT 1'
        );
        $stmt->execute([$userId]);
        $activeFast = $stmt->fetch();
        $fastStr = "No hay ayuno activo en curso.\n";
        if ($activeFast !== false) {
            $fastStr = sprintf(
                "Ayuno activo iniciado a las %s bajo el protocolo %s.\n",
                substr($activeFast['start_time'], 0, 16),
                $activeFast['protocol']
            );
        }

        $stmt = $pdo->prepare(
            'SELECT datetime, notes, ai_analysis FROM meal_entries
             WHERE user_id = ? ORDER BY datetime DESC LIMIT 3'
        );
        $stmt->execute([$userId]);
        $meals = $stmt->fetchAll();
        $mealsStr = '';
        foreach ($meals as $m) {
            $analysis = $m['ai_analysis'] !== null ? json_decode($m['ai_analysis'], true) : null;
            $items = $analysis['food_items'] ?? [];
            $itemsStr = $items !== [] ? implode(', ', $items) : 'Comida';
            $mealsStr .= sprintf("- %s: %s\n", substr($m['datetime'], 0, 16), $m['notes'] ?: $itemsStr);
        }
        if ($mealsStr === '') {
            $mealsStr = "No hay comidas registradas recientemente.\n";
        }

        return "INFORMACIÓN DEL PACIENTE:\n"
            . "- Nombre: {$user['name']}\n"
            . "- Condición: Diabetes Tipo 2\n"
            . '- Fecha actual: ' . Dt::todayLocal() . "\n\n"
            . "ÚLTIMAS LECTURAS DE GLUCOSA:\n{$readingsStr}\n"
            . "ESTADO DE HÁBITOS DIARIOS DE HOY:\n{$habitsStr}\n"
            . "ESTADO DE AYUNO INTERMITENTE:\n{$fastStr}\n"
            . "ÚLTIMAS COMIDAS:\n{$mealsStr}\n"
            . 'Instrucciones: Utiliza este contexto para dar recomendaciones de salud personalizadas, '
            . 'científicas y alentadoras en Español. Si los niveles de glucosa superan 250 mg/dL, '
            . 'recomienda fuertemente la hidratación con agua, evitar ejercicio pesado de inmediato '
            . 'y vigilar síntomas de crisis.';
    }

    /** Chat with the assistant: personal provider first, else system default. */
    public static function queryAssistant(string $message, array $history, string $healthContext, ?array $user): string
    {
        $messages = [
            [
                'role' => 'system',
                'content' => 'Eres Hermes-Health, un asistente virtual experto en nutrición y entrenamiento para '
                    . "pacientes con Diabetes Tipo 2. Responde en Español de manera clara y motivadora.\n\n"
                    . "CONTEXTO DE SALUD DEL PACIENTE:\n" . $healthContext,
            ],
        ];
        foreach ($history as $msg) {
            if (isset($msg['role'], $msg['content'])) {
                $messages[] = ['role' => (string) $msg['role'], 'content' => (string) $msg['content']];
            }
        }
        $messages[] = ['role' => 'user', 'content' => $message];

        $hasPersonalKey = $user !== null && !empty($user['ai_api_key']);

        if ($hasPersonalKey) {
            try {
                return AiClient::chat($messages, $user);
            } catch (\Throwable $err) {
                error_log('[azucar-ai] user provider failed: ' . $err->getMessage());
                return 'Lo siento, hubo un error al conectar con tu proveedor de IA configurado: '
                    . $err->getMessage() . '. Por favor verifica tus credenciales.';
            }
        }

        if (!AiClient::hasKey(null)) {
            return 'El Asistente de IA no está configurado. Falta la variable DEFAULT_AI_API_KEY '
                . 'en el archivo de configuración (.env) del servidor.';
        }

        try {
            return AiClient::chat($messages, null);
        } catch (\Throwable $err) {
            error_log('[azucar-ai] system provider failed: ' . $err->getMessage());
            return 'Lo siento, en este momento no puedo conectarme con los servidores de '
                . 'Inteligencia Artificial. Por favor intenta más tarde.';
        }
    }
}
