# Deployment Guide - Azúcar Control

VPS: `10.40.2.156` | Conectar: `ssh -i ~/.ssh/vps_key ubuntu@10.40.2.156` | Root dir: `/home/ubuntu/azucar_app`

---

## Frontend (HTML/CSS/JS)

Cambios aplican **sin restart** — nginx sirve volumen en tiempo real.

```bash
# Local development
git add frontend/
git commit -m "feat: description"
git push

# VPS
ssh -i ~/.ssh/vps_key ubuntu@10.40.2.156
cd /home/ubuntu/azucar_app
git pull
```

**En cliente:** `Ctrl+Shift+R` (hard refresh) garantiza cargar versión nueva.

**Verificar en VPS:**
```bash
git log --oneline -5 frontend/
```

---

## Backend (Python/FastAPI)

Cambios requieren **restart del container**.

```bash
# Local
git add backend/app/
git commit -m "feat: description"
git push

# VPS
ssh -i ~/.ssh/vps_key ubuntu@10.40.2.156
cd /home/ubuntu/azucar_app
git pull
docker-compose restart backend

# Verificar health
docker ps | grep azucar-backend
docker logs azucar-backend | tail -20
```

Backend reinicia con código nuevo. Tarda ~5s.

---

## Database Migrations

Alembic es el migration tool. Cambios de schema **siempre** requieren migration file.

### Crear nueva migration (local)

```bash
cd backend
alembic revision --autogenerate -m "add new table"
```

Crea archivo en `backend/alembic/versions/`. **Revisar y editar si es necesario.**

```bash
git add backend/alembic/versions/
git commit -m "migration: add new table"
git push
```

### Aplicar migration (VPS)

```bash
ssh -i ~/.ssh/vps_key ubuntu@10.40.2.156
cd /home/ubuntu/azucar_app
git pull

# Copiar archivo a container
MIGRATION_FILE=$(ls -t backend/alembic/versions/*.py | head -1)
docker cp "$MIGRATION_FILE" azucar-backend:/app/alembic/versions/

# Ejecutar
docker exec azucar-backend alembic upgrade head

# Restart backend
docker-compose restart backend

# Verificar estado
docker exec azucar-backend alembic current
```

**Si migration falla:**
```bash
# Ver error completo
docker exec azucar-backend alembic upgrade head --verbose

# Rollback si es necesario
docker exec azucar-backend alembic downgrade -1
```

---

## Routers nuevos (Backend)

1. Crear archivo `backend/app/routers/myrouter.py`
2. Importar en `backend/app/main.py`: `from app.routers import myrouter`
3. Registrar: `app.include_router(myrouter.router, prefix="/api/v1/mypath", tags=["mytag"])`
4. Commit, push, restart backend en VPS

**Verificar que router está cargado:**
```bash
# En VPS
docker logs azucar-backend | grep "GET\|POST" | head -5

# O test en navegador
curl http://10.40.2.156/api/docs  # Swagger
```

---

## Schemas/Models nuevos

Si crease modelo nuevo (e.g. `backend/app/models/newmodel.py`):

1. **Crear schema** correspondiente en `backend/app/schemas/newmodel.py`
2. **Crear migration** con Alembic (ver sección de migrations)
3. **Crear router** que use modelo + schema
4. **Importar modelo** en `backend/app/models/__init__.py` si es necesario para relaciones
5. Commit, push, apply migration, restart backend

---

## Problemas Comunes

### Error: "Not found" en frontend

**Causas:**
1. Cambios no fueron pushed/pulled
2. Migration no aplicada (tabla no existe)
3. Router no registrado en main.py
4. Caché del navegador

**Soluciones:**
```bash
# VPS: verificar cambios están
git log --oneline -3
git status

# Verificar migration status
docker exec azucar-backend alembic current

# Verificar router está cargado
docker logs azucar-backend | tail -50

# Cliente: hard refresh
Ctrl+Shift+R
```

### Error: Service Worker corrupted

Service Worker es `frontend/sw.js`. Nginx sirve con `no-cache` headers, así que siempre verifica versión nueva. Si aún hay problema:

```bash
# Cliente
1. Abrir DevTools (F12)
2. Application → Service Workers → Unregister
3. Ctrl+Shift+R
```

### Backend no reinicia correctamente

```bash
# VPS
docker-compose logs backend  # Ver error
docker-compose restart backend  # Forzar restart
docker ps | grep azucar-backend  # Verificar status
```

---

## Testing después de deploy

```bash
# Frontend: abrir app
https://azucar.aeisoftware.com/

# Backend API: verificar endpoints
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://azucar.aeisoftware.com/api/v1/glucose/

# Ver logs en tiempo real
docker logs -f azucar-backend
docker logs -f azucar-nginx
```

---

## Rollback

Si algo se rompe:

```bash
# VPS
cd /home/ubuntu/azucar_app

# Ver commits recientes
git log --oneline -5

# Revertir último commit
git revert HEAD --no-edit
git push

# O volver a commit específico
git checkout COMMIT_HASH
git push -f  # Force push (cuidado en prod)

# Luego restart lo que corresponda
docker-compose restart backend  # o pull frontend
```

---

## Checklist de Deploy

- [ ] Cambios commiteados localmente
- [ ] Tests pasando (si existen)
- [ ] `git push` ejecutado
- [ ] VPS: `git pull`
- [ ] Si backend: `docker-compose restart backend`
- [ ] Si migration: `docker exec azucar-backend alembic upgrade head`
- [ ] Cliente: `Ctrl+Shift+R` (si es frontend)
- [ ] Verificar en Swagger (`/api/docs`) que endpoints están
- [ ] Test manual de feature
- [ ] Ver logs si hay error: `docker logs CONTAINER`
