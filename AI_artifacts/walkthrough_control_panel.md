# Walkthrough — Despliegue Azúcar Control (Actualizado)

¡El despliegue de la plataforma Azúcar Control se ha completado con éxito! Todos los servicios están corriendo de forma estable y saludable en tu VPS (`ubuntu@10.40.2.156`).

---

## 🚀 Nuevas Funcionalidades Implementadas

### 1. Panel de Configuración de IA (Multi-tenant)
- **Frontend**: Añadida una nueva pestaña llamada **Configuración** (icono ⚙️) que permite personalizar la clave de API, modelo, y URL base de forma dinámica para cada usuario.
  - Soporta **OpenRouter** y **Kimi / Moonshot API** nativamente.
  - Implementa un botón **"Probar Conexión"** que permite al usuario verificar si su clave y modelo funcionan antes de guardar.
  - Oculta por defecto la clave y permite alternar la visibilidad (ojo visor).
- **Backend**:
  - Actualizado el modelo de base de datos `User` para incluir campos personalizados.
  - Creados los endpoints `PUT /api/v1/auth/me/ai-settings` para guardar la configuración, y `POST /api/v1/auth/test-ai` para probar las credenciales mediante un chat completion ultraligero de 10 tokens.
  - Resolución dinámica: `analyze_meal_image` (Visión) y `query_hermes_agent` (Chat) ahora utilizan las llaves e integraciones guardadas del usuario actual, cayendo en el fallback del sistema únicamente si no están configuradas.

### 2. Eliminación de Comidas del Historial
- **Frontend**: Añadido un botón de eliminación flotante (🗑️) con fondo translúcido sobre la imagen de cada tarjeta del feed de nutrición.
- **Backend**: Implementado el endpoint `DELETE /api/v1/meals/{meal_id}` en el backend.
  - **Seguridad**: Asegura que el usuario autenticado solo pueda eliminar sus propias comidas (aislamiento multi-tenant).
  - **Eficiencia**: Al eliminar un registro de comida, el backend localiza y **elimina físicamente el archivo de imagen de previsualización (thumbnail)** guardado en el disco (`uploads/`), liberando espacio en el disco del servidor.

---

## 🛠️ Problemas de Despliegue Resueltos Anteriormente

### 1. Tiempo de espera (Timeout) al compilar Supercronic
- **Problema**: La descarga de la herramienta `supercronic` mediante `curl` en la compilación de la imagen del `scheduler` fallaba por timeout desde el VPS.
- **Solución**: Descargamos el binario `supercronic-linux-amd64` localmente y actualizamos el `scheduler/Dockerfile` para hacerle un `COPY` en lugar de una descarga de red durante la compilación.

### 2. Error de montaje de carpeta en Nginx (Read-Only rootfs)
- **Problema**: Nginx fallaba al iniciar porque intentaba montar el volumen de uploads sobre la ruta `/usr/share/nginx/html/uploads`. Al estar `/usr/share/nginx/html` montada como sólo lectura (`:ro`) desde el host, Docker no podía crear el punto de montaje.
- **Solución**: Creamos la carpeta física `frontend/uploads/` con un archivo `.gitkeep` en el host. Al existir previamente la carpeta en la fuente de sólo lectura, Docker la monta de inmediato sin intentar escribir en el contenedor.

### 3. Timeout en la conexión Redis del Worker
- **Problema**: El worker de notificaciones reportaba errores continuos de timeout al leer de Redis (`Timeout reading from redis:6379`). Esto ocurría porque el socket read timeout del cliente de Python era inferior al tiempo de espera de bloqueo del comando `blpop`.
- **Solución**: Configuramos explícitamente `socket_timeout=10.0` al instanciar el cliente de Redis y reducimos el timeout del comando `blpop` de 5 a 2 segundos en `backend/app/workers/notification_worker.py`. El worker ahora escucha de forma limpia y permanente sin generar errores de timeout.

---

## 📊 Estado Actual de los Servicios en el VPS

Al ejecutar `docker compose ps` en la carpeta `~/azucar_app`, todos los contenedores reportan un estado saludable:

| Contenedor | Imagen / Servicio | Estado | Puertos / Detalles |
| :--- | :--- | :--- | :--- |
| **azucar-nginx** | `nginx:1.25-alpine` | **Up / Running** | Expone puerto 80 (Proxy principal frontend/api) |
| **azucar-backend** | `azucar_app-backend` | **Up (healthy)** | API FastAPI corriendo en puerto 8000 |
| **azucar-worker** | `azucar_app-worker` | **Up / Running** | Escuchando la cola `notifications_queue` |
| **azucar-scheduler**| `azucar_app-scheduler` | **Up / Running** | Supercronic ejecutando tareas programadas |
| **azucar-db** | `postgres:16-alpine` | **Up (healthy)** | Base de datos PostgreSQL en puerto 5432 |
| **azucar-redis** | `redis:7-alpine` | **Up (healthy)** | Caché y colas en puerto 6379 |
| **azucar-hermes** | `nousresearch/hermes-agent` | **Up / Running** | Asistente de IA clínico interactivo |
| **azucar-tunnel** | `cloudflare/cloudflared` | **Up / Running** | Túnel de Cloudflare exponiendo `azucar.aeisoftware.com` |
| **azucar-db-backup**| `postgres-backup-local` | **Up (healthy)** | Respaldos automáticos diarios de base de datos |

---

## 🔒 Base de Datos y Migraciones

La base de datos cuenta con dos migraciones aplicadas correctamente en el contenedor de PostgreSQL:
1. `2026_06_07_0000_initial`: Esquema multi-tenant básico.
2. `2026_06_07_2127-00a34ea76c45_add_user_ai_settings`: Columnas de configuración de IA añadidas a la tabla `users`.
