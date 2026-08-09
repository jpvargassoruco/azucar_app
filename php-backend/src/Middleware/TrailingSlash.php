<?php

declare(strict_types=1);

namespace Azucar\Middleware;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

/**
 * The frontend calls both "/api/v1/glucose/" and "/api/v1/glucose". Normalize
 * by trimming trailing slashes before routing — no redirects, which would
 * drop the Authorization header on some clients.
 */
final class TrailingSlash implements MiddlewareInterface
{
    public function process(ServerRequestInterface $request, RequestHandlerInterface $handler): ResponseInterface
    {
        $uri = $request->getUri();
        $path = $uri->getPath();
        if ($path !== '/' && str_ends_with($path, '/')) {
            $request = $request->withUri($uri->withPath(rtrim($path, '/')));
        }
        return $handler->handle($request);
    }
}
