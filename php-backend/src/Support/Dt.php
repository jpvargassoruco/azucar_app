<?php

declare(strict_types=1);

namespace Azucar\Support;

use DateTimeImmutable;
use DateTimeZone;

/**
 * Datetime conventions, mirroring the FastAPI backend:
 * - The frontend sends ISO-8601 (usually toISOString(): UTC with "Z").
 * - Storage is UTC DATETIME ("Y-m-d H:i:s").
 * - Output is "Y-m-d\TH:i:sZ" so new Date() in the browser converts to local,
 *   exactly like pydantic's tz-aware serialization did.
 * - "Today" for habits/medications is computed in APP_TZ (the users' timezone).
 */
final class Dt
{
    public static function utc(): DateTimeZone
    {
        return new DateTimeZone('UTC');
    }

    public static function appTz(): DateTimeZone
    {
        return new DateTimeZone($_ENV['APP_TZ'] ?? 'America/La_Paz');
    }

    /** ISO-8601 input (with or without offset; naive treated as UTC) -> "Y-m-d H:i:s" UTC, or null. */
    public static function parseToUtcSql(?string $iso): ?string
    {
        if ($iso === null || trim($iso) === '') {
            return null;
        }
        try {
            $dt = new DateTimeImmutable(trim($iso), self::utc());
        } catch (\Exception) {
            return null;
        }
        return $dt->setTimezone(self::utc())->format('Y-m-d H:i:s');
    }

    /** MySQL DATETIME (UTC) -> "Y-m-d\TH:i:sZ". Null-safe. */
    public static function out(?string $mysqlDatetime): ?string
    {
        if ($mysqlDatetime === null) {
            return null;
        }
        return str_replace(' ', 'T', $mysqlDatetime) . 'Z';
    }

    public static function nowUtcSql(): string
    {
        return (new DateTimeImmutable('now', self::utc()))->format('Y-m-d H:i:s');
    }

    /** Current date in APP_TZ ("Y-m-d"). */
    public static function todayLocal(): string
    {
        return (new DateTimeImmutable('now', self::appTz()))->format('Y-m-d');
    }

    /** Weekday in APP_TZ, Monday = 0 (Python date.weekday() convention). */
    public static function weekdayLocal(): int
    {
        return ((int) (new DateTimeImmutable('now', self::appTz()))->format('N')) - 1;
    }

    public static function isValidDate(string $value): bool
    {
        return (bool) preg_match('/^\d{4}-\d{2}-\d{2}$/', $value)
            && DateTimeImmutable::createFromFormat('Y-m-d', $value) !== false;
    }

    public static function isValidHhmm(string $value): bool
    {
        return (bool) preg_match('/^(?:[01]\d|2[0-3]):[0-5]\d$/', $value);
    }
}
