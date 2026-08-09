<?php

declare(strict_types=1);

use Azucar\Middleware\ErrorHandler;
use Azucar\Middleware\TrailingSlash;
use Slim\Factory\AppFactory;

require __DIR__ . '/../vendor/autoload.php';

$dotenv = Dotenv\Dotenv::createImmutable(dirname(__DIR__));
$dotenv->safeLoad();

date_default_timezone_set('UTC');

$app = AppFactory::create();
$app->setBasePath('/api');

$app->addBodyParsingMiddleware();
$app->add(new TrailingSlash());
$app->addRoutingMiddleware();

$errorMiddleware = $app->addErrorMiddleware(false, true, false);
$errorMiddleware->setDefaultErrorHandler(new ErrorHandler());

(require __DIR__ . '/routes.php')($app);

return $app;
