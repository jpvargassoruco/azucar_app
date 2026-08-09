<?php

declare(strict_types=1);

// Front controller. On the hosting, app code lives outside the docroot at
// ~/app (adjust the path below if the layout differs).
$bootstrap = null;
foreach ([
    __DIR__ . '/../../src/bootstrap.php',   // repo layout (local dev)
    dirname(__DIR__) . '/app/src/bootstrap.php', // shared hosting: docroot/app (web chroot sees only the docroot)
    dirname(__DIR__, 3) . '/app/src/bootstrap.php', // generic: ~/app next to docroot
] as $candidate) {
    if (is_file($candidate)) {
        $bootstrap = $candidate;
        break;
    }
}
if ($bootstrap === null) {
    http_response_code(500);
    header('Content-Type: application/json');
    echo '{"detail": "Backend bootstrap not found"}';
    exit;
}

$app = require $bootstrap;
$app->run();
