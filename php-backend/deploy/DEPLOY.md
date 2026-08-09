# Deploy runbook — azucar.redesk.us (CloudLogin shared hosting)

## Phase 0 — Host recon (do this first)

1. In the CloudLogin panel, create the site for `azucar.redesk.us` and issue the Let's Encrypt certificate.
2. Upload `deploy/recon.php` to the docroot (File Manager or FTP), open
   `https://azucar.redesk.us/recon.php`, save the output, then run
   `https://azucar.redesk.us/recon.php?sleep=1` (should take ~65 s).
   Also run: `curl -H 'Authorization: Bearer test123' https://azucar.redesk.us/recon.php`
3. **Delete recon.php.** All extensions must be OK, outbound HTTPS must reach the
   push/AI endpoints, the Authorization header must be RECEIVED, and the sleep
   test must survive. If the sleep test dies early, ask support to raise the
   FastCGI timeout, or we enable the async-analysis fallback before cutover.

## 1 — Database

1. Panel → Databases: create MySQL database + user (e.g. `azucar` / strong password).
2. Import schema: `mysql -u <user> -p <db> < sql/schema.sql` (via SSH), or through phpMyAdmin.

## 2 — Application code

Layout on the host (app code outside the docroot when possible):

```
~/app/                      <- php-backend/ contents (src, bin, vendor, .env, logs)
~/public_html/azucar/       <- docroot: frontend files + api/ + uploads/ + .htaccess
```

1. SSH in. Upload `php-backend/` to `~/app/` (rsync/scp/git).
2. `cd ~/app && composer install --no-dev --optimize-autoloader`
   (if composer is missing: `php -r "copy('https://getcomposer.org/installer','c.php');" && php c.php`)
3. Copy `frontend/` files into the docroot — **exclude** `nginx.conf` and `Dockerfile`.
4. Copy from `php-backend/public/` into the docroot: `.htaccess`, `api/` (both files),
   `uploads/.htaccess`.
5. If `~/app` is not possible, use `docroot/app/` and add an `.htaccess` there with
   `Require all denied` (api/index.php auto-detects both layouts).

## 3 — Configuration

Create `~/app/.env` from `.env.example` (`chmod 600 .env`):

- `DB_*` — the panel database credentials
- `JWT_SECRET_KEY` — copy from the VPS `.env`
- `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` / `VAPID_MAILTO` — copy from the VPS `.env`
- `APP_KEY` — NEW random string: `php -r "echo bin2hex(random_bytes(32));"`
- `APP_TZ=America/La_Paz`
- `DEFAULT_AI_API_KEY` — DeepSeek key; `DEFAULT_VISION_*` — Kimi or Anthropic key
- `UPLOADS_DIR` — absolute docroot path, e.g. `/home/<user>/public_html/azucar/uploads`

## 4 — Data migration (VPS → hosting)

1. On the VPS: `bash export_pg.sh` (freezes writes, exports CSVs + thumbnails tar).
2. Locally: `scp -i .ssh/vps_key -r <user>@10.40.2.156:/tmp/azucar_export ./migration_data`
3. `python3 migration/transform.py ./migration_data --app-key <APP_KEY> > data.sql`
4. On hosting: `mysql -u <user> -p <db> < data.sql`
5. Extract `uploads.tar.gz` into the docroot `uploads/` directory.
6. Verify row counts per table against the export output; log in with an existing account.

## 5 — Cron

Panel → Advanced → Cron Jobs, every minute:

```
* * * * * php /home/<user>/app/bin/cron_reminders.php >> /home/<user>/app/logs/cron.log 2>&1
```

## 6 — Smoke test

```
curl https://azucar.redesk.us/api/health                          # {"status":"ok"}
curl -H "Authorization: Bearer <token>" https://azucar.redesk.us/api/v1/auth/me
curl -I https://azucar.redesk.us/sw.js                            # Cache-Control: no-cache
curl -I https://azucar.redesk.us/uploads/<any-thumb>.jpg          # Cache-Control: max-age=2592000
```

Then in the PWA: log in (pre-migration account), add a glucose reading, enable
notifications + send test, set an alarm 2 min ahead and wait for the push,
upload a meal photo, generate a meal plan, download the FHIR export.

## 7 — Users & rollback

- Announce: everyone must log in again and re-enable notifications on the new
  domain (origin change invalidates tokens and push subscriptions).
- Keep the VPS stack stopped-but-intact for at least a week as rollback
  (`docker compose start` brings the old site back on the old domain).
