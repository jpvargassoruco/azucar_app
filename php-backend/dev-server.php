<?php

declare(strict_types=1);

// Local dev router for `php -S 127.0.0.1:8080 dev-server.php`.
// Serves the unchanged frontend/ statically and routes /api/* into Slim,
// mimicking the shared-hosting Apache layout.

$uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH) ?? '/';

if (str_starts_with($uri, '/api')) {
    require __DIR__ . '/public/api/index.php';
    return;
}

$frontendRoot = dirname(__DIR__) . '/frontend';
$uploadsDir = $_ENV['UPLOADS_DIR'] ?? getenv('UPLOADS_DIR') ?: __DIR__ . '/public/uploads';

if (str_starts_with($uri, '/uploads/')) {
    $file = $uploadsDir . '/' . basename($uri);
} else {
    $file = realpath($frontendRoot . $uri);
    if ($file === false || is_dir($file)) {
        $file = $frontendRoot . '/index.html'; // SPA fallback
    } elseif (!str_starts_with($file, realpath($frontendRoot))) {
        http_response_code(403);
        return;
    }
}

if (!is_file($file)) {
    http_response_code(404);
    return;
}

$types = [
    'html' => 'text/html; charset=utf-8',
    'js' => 'application/javascript',
    'css' => 'text/css',
    'json' => 'application/json',
    'png' => 'image/png',
    'jpg' => 'image/jpeg',
    'jpeg' => 'image/jpeg',
    'webp' => 'image/webp',
    'svg' => 'image/svg+xml',
    'ico' => 'image/x-icon',
    'woff2' => 'font/woff2',
];
$ext = strtolower(pathinfo($file, PATHINFO_EXTENSION));
header('Content-Type: ' . ($types[$ext] ?? 'application/octet-stream'));
readfile($file);
