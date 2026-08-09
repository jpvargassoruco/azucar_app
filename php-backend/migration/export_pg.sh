#!/usr/bin/env bash
# Run ON THE VPS (10.40.2.156), from the azucar_app directory.
# Exports every table as CSV, tars the meal thumbnails, and prints the
# .env values that must carry over to the new hosting.
set -euo pipefail

OUT=/tmp/azucar_export
mkdir -p "$OUT"

TABLES=(users glucose_readings fasting_sessions habit_logs alarms meal_entries \
        meal_plans push_subscriptions medications medication_logs weights \
        blood_pressures hba1c_readings)

echo ">> Freezing writes (stopping backend containers)..."
docker compose stop backend worker scheduler || true

echo ">> Exporting tables to CSV..."
for table in "${TABLES[@]}"; do
    docker compose exec -T db psql -U "${POSTGRES_USER:-azucar}" -d "${POSTGRES_DB:-azucar}" \
        -c "\\copy ${table} TO STDOUT WITH CSV HEADER" > "$OUT/${table}.csv"
    echo "   ${table}: $(($(wc -l < "$OUT/${table}.csv") - 1)) rows"
done

echo ">> Archiving meal thumbnails..."
docker run --rm -v azucar_meal_uploads:/uploads -v "$OUT":/out alpine \
    tar czf /out/uploads.tar.gz -C /uploads .

echo ">> Values to carry into the hosting .env:"
grep -E '^(JWT_SECRET_KEY|VAPID_PUBLIC_KEY|VAPID_PRIVATE_KEY|VAPID_MAILTO|OPENROUTER_API_KEY|API_KEY_ENCRYPTION_KEY)=' .env || true

echo ">> Done. Copy $OUT/ back with:"
echo "   scp -i .ssh/vps_key -r <user>@10.40.2.156:$OUT ./migration_data"
echo ">> Rollback note: containers left stopped. Restart with: docker compose start backend worker scheduler"
