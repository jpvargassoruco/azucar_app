<?php

/**
 * Phase-0 host recon for CloudLogin shared hosting.
 * Upload this single file to the docroot (e.g. as /recon.php), open it in a
 * browser, save the output, then DELETE THE FILE.
 *
 * Checks: PHP version/extensions, execution-time ceiling, Authorization
 * header survival, and outbound HTTPS to the push + AI endpoints.
 */

header('Content-Type: text/plain; charset=utf-8');

echo "=== azucar host recon ===\n\n";
echo 'PHP version: ' . PHP_VERSION . "\n";
echo 'SAPI: ' . php_sapi_name() . "\n\n";

echo "--- Required extensions ---\n";
foreach (['pdo_mysql', 'curl', 'openssl', 'mbstring', 'gd', 'sodium', 'gmp', 'bcmath', 'exif', 'json'] as $ext) {
    printf("%-10s %s\n", $ext, extension_loaded($ext) ? 'OK' : 'MISSING');
}
echo "(web-push needs gmp OR bcmath; gmp is much faster)\n\n";

echo "--- Limits ---\n";
foreach (['max_execution_time', 'memory_limit', 'upload_max_filesize', 'post_max_size'] as $ini) {
    printf("%-20s %s\n", $ini, (string) ini_get($ini));
}
echo "\n";

echo "--- Authorization header ---\n";
$auth = $_SERVER['HTTP_AUTHORIZATION']
    ?? $_SERVER['REDIRECT_HTTP_AUTHORIZATION']
    ?? (function_exists('getallheaders') ? (getallheaders()['Authorization'] ?? null) : null);
echo $auth !== null
    ? "RECEIVED: $auth\n"
    : "NOT RECEIVED — retry with: curl -H 'Authorization: Bearer test123' <this url>\n";
echo "\n";

echo "--- Outbound HTTPS ---\n";
foreach ([
    'https://fcm.googleapis.com' => 'push (Chrome/FCM)',
    'https://updates.push.services.mozilla.com' => 'push (Firefox)',
    'https://api.deepseek.com' => 'AI (DeepSeek)',
    'https://api.anthropic.com' => 'AI (Anthropic)',
    'https://api.moonshot.ai' => 'AI (Kimi)',
] as $url => $label) {
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_NOBODY => true,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 8,
        CURLOPT_FOLLOWLOCATION => false,
    ]);
    curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
    $err = curl_error($ch);
    curl_close($ch);
    printf("%-45s %s\n", "$label ($url):", $err !== '' ? "FAIL: $err" : "OK (HTTP $code)");
}
echo "\n";

echo "--- Execution ceiling test (sleeps 65s; a timeout below means a hard FastCGI cap) ---\n";
if (($_GET['sleep'] ?? '') === '1') {
    set_time_limit(120);
    $start = time();
    sleep(65);
    echo 'Survived ' . (time() - $start) . "s — inline AI calls are safe.\n";
} else {
    echo "Run with ?sleep=1 to test (page should take ~65s and then print a result).\n";
}

echo "\n--- Filesystem ---\n";
echo 'Docroot: ' . ($_SERVER['DOCUMENT_ROOT'] ?? getcwd()) . "\n";
echo 'Writable outside docroot (' . dirname($_SERVER['DOCUMENT_ROOT'] ?? getcwd()) . '): '
    . (is_writable(dirname($_SERVER['DOCUMENT_ROOT'] ?? getcwd())) ? 'YES' : 'NO') . "\n";
echo "\nDone. DELETE THIS FILE NOW.\n";
