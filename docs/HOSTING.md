# Production hosting — azucar.redesk.us (CloudLogin shared hosting)

As of 2026-08-10 the app runs on CloudLogin shared hosting as a **PHP 8.4 + MySQL 8.4**
port of the original FastAPI/Postgres/Docker stack (see `php-backend/`). The old VPS
stack (azucar.aeisoftware.com) is deprecated and kept only as rollback.

## Architecture

| Piece | Where |
|---|---|
| Frontend (unchanged PWA) | `~/www/azucar.redesk.us/` (docroot) |
| API front controller | `docroot/api/index.php` (+ `.htaccess` rewrite of `/api/*`) |
| Backend app (Slim 4 + PDO) | `docroot/app/{src,vendor,bin,sql}` — protected by `app/.htaccess` (`Require all denied`) |
| Secrets | `docroot/app/.env` (chmod 600; DB, JWT, APP_KEY, VAPID, AI keys) |
| Database | MySQL `redeskus_azucar` (localhost, utf8mb4) |
| Reminders | Panel cron, every minute: `/usr/local/php8.4/bin/php .../app/bin/cron_reminders.php` (replaces Redis+worker+scheduler; dedup in `sent_notifications`, catch-up window in `cron_state`) |
| Uploads | `docroot/uploads/` (thumbnails only, 30-day cache, PHP execution disabled) |
| AI | Kimi (`kimi-k3`, vision-capable) via per-user key and system default; adapters also support DeepSeek/OpenRouter/NVIDIA/Google/Anthropic |

Access (SSH port 2222, FTP, MySQL, panel) — credentials live in the CloudLogin panel
and in the maintainer's password manager; **never commit them to this repo**.

## Deploy flow

There is no local runtime anymore — changes go straight to production:

1. Edit locally → commit → push (`feature/php-backend` until merged to `main`).
2. Copy changed files over SSH (port 2222):
   - Frontend files → `~/www/azucar.redesk.us/<same relative path>`
   - Backend files (`php-backend/src/...`) → `~/www/azucar.redesk.us/app/src/...`
3. Frontend changes: bump the `?v=N` on the script tags in `index.html` **and**
   `CACHE_NAME` in `sw.js` together (currently v9) so PWA clients refresh.
4. Dependency changes: run `composer install` somewhere with PHP 8.4 and rsync the
   resulting `vendor/` to `app/vendor/` (the host's default `composer` wrapper is
   broken for 8.4; alternatively run composer.phar on the host with the 8.4 binary).

Full deploy/migration runbook: `php-backend/deploy/DEPLOY.md`.

## Hosting quirks (hard-won knowledge)

- **Web chroot** exposes only the vhost docroot — app code cannot live outside it;
  that is why the backend sits at `docroot/app` behind a deny-all `.htaccess`.
- **Default CLI `php` is 5.3.** Always use `/usr/local/php8.4/bin/php` (cron included).
- **ModSecurity** rejects empty-body POSTs (HTTP 412) — the frontend sends `'{}'`
  where needed. It also rate-limits request bursts per IP (~60 rapid requests →
  temporary block). For API test batches, run server-side:
  `curl -H "Host: azucar.redesk.us" http://127.0.0.1/...` over SSH.
- **No hairpin**: the server cannot reach its own public domain; use the localhost
  + Host-header trick above.
- `crontab` over SSH is blocked — cron jobs are managed in the panel UI only.
- `kimi-k3` rejects any `temperature` parameter (the Kimi adapter omits it) and
  `kimi-latest` is not available to standard keys.

## Operations

- Cron log: `app/logs/cron.log`; scheduler watermark: `cron_state.last_run_utc`
  (should never be more than ~90 s old).
- DB check: `mysql -u redeskus_azucar -p redeskus_azucar` from SSH.
- Push subscriptions are origin-bound: any domain change invalidates logins and
  push subscriptions (users must log in and re-enable notifications).
- Timezone: reminders are computed in `APP_TZ` (America/La_Paz); DB stores UTC.
