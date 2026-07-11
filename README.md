# 🩺 Azúcar Control — Plataforma de Gestión de Diabetes Tipo 2

PWA full-stack para el control diario de diabetes tipo 2: monitoreo de glucosa, análisis de comidas con IA, ayuno intermitente, recordatorios, hábitos, medicamentos y exportación FHIR.

**URL:** https://azucar.aeisoftware.com

---

## 🚀 Arquitectura

9 contenedores Docker en VPS con túnel Cloudflare:

```
Internet → Cloudflare Tunnel → Nginx (port 80)
                                ├── Frontend PWA (estáticos)
                                ├── Backend FastAPI (port 8000)
                                └── Hermes Agent (port 8642)
                                
Backend → PostgreSQL 16 + Redis 7
Cron → Supercronic scheduler
Push → Notification Worker (Redis → pywebpush)
```

## 📁 Estructura del Proyecto

```
azucar_app/
├── frontend/                 # PWA (vanilla HTML/CSS/JS)
│   ├── index.html            # Shell HTML ~850 líneas
│   ├── css/app.css           # Estilos mobile-first + dual theme
│   ├── js/
│   │   ├── app.js            # Lógica principal (~2100 líneas)
│   │   ├── theme.js          # Sistema claro/oscuro
│   │   ├── offline.js        # Caché IndexedDB + periodic sync
│   │   └── help.js           # Guía de usuario en la app
│   ├── sw.js                 # Service Worker (network-first)
│   ├── manifest.json         # PWA manifest
│   └── nginx.conf            # Reverse proxy + static files
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI entry point
│   │   ├── config.py         # Settings (.env)
│   │   ├── routers/          # API endpoints
│   │   ├── services/         # AI providers, meal analyzer, FHIR
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── auth/             # JWT + encryption
│   │   └── workers/          # Notification worker
│   └── Dockerfile
├── scheduler/                # Cron jobs (Supercronic)
├── docker-compose.yml        # 9 servicios
└── .ssh/vps_key             # SSH key (gitignored)
```

## ✨ Features

| Módulo | Descripción |
|--------|-------------|
| 📊 **Registro de Glucosa** | Entrada manual, gráfico de tendencia (7 días), tabla histórica |
| 📸 **Análisis de Comidas** | Foto → IA estima macros, calorías, impacto glucémico |
| 📋 **Cola de Fotos** | Acumula fotos del día, asigna hora de ingesta, analiza en batch |
| ⏳ **Ayuno Intermitente** | Timer con protocolos 16:8, 12:12, 18:6, 20:4 |
| ⏰ **Recordatorios** | Postprandial, hidratación, metformina — push notifications |
| ✓ **Hábitos** | Checklist diario con barra de progreso |
| 💊 **Medicamentos** | CRUD, dosis diarias con horarios, días de semana |
| 🤖 **Hermes IA** | Chat con asistente experto en diabetes |
| 🥗 **Planificador IA** | Genera plan de comidas personalizado |
| 🏥 **Export FHIR** | Bundle HL7 FHIR R4 (glucosa, comidas, ayunos) |
| 🎨 **Temas** | Claro/oscuro automático + toggle manual |
| 🔍 **Zoom** | Ajuste de tamaño de interfaz |
| 🔄 **Actualizar** | Botón para forzar actualización (limpia SW + caché) |

## 🗺️ Roadmap

Roadmap clínico enfocado en diabetes Tipo 2, derivado del análisis comparativo con [Diaguard](https://github.com/Faltenreich/Diaguard). Detalle completo (tabla de gap + notas de arquitectura) en **[ROADMAP.md](ROADMAP.md)**.

| Fase | Foco |
|------|------|
| **1** | Signos vitales T2: peso/IMC, presión arterial, HbA1c de laboratorio |
| **2** | Analítica de glucosa: tiempo-en-rango, eA1c/GMI, rango objetivo + alertas hipo/hiper |
| **3** | Exportación y portabilidad: PDF (diario médico), CSV, backup/restore |
| **4** | Logging enriquecido: actividad, pulso/SpO2, tags + búsqueda, carbohidratos manuales |
| **5** | Unidades e i18n (opcional): mmol/L, multi-idioma |
| **6** | Terapia con insulina (diferido): dosis y calculadora de bolo |

## 🤖 Proveedores de IA

| Proveedor | Modelo | Costo |
|-----------|--------|-------|
| Google AI Studio | Gemini Flash | Gratuito |
| OpenRouter | openrouter/auto | Pago por uso |
| Deepseek | deepseek-chat | Pago por uso |
| Nvidia NIM | Nemotron Super 120B | 5,000 créditos gratis |

El proveedor se configura en **Configuración → IA**. Cada proveedor funciona de forma independiente: se usa el que el usuario configure, sin fallback cruzado automático a otro proveedor.

## 🔒 Seguridad

- **JWT**: tokens de acceso con expiración de 1 hora
- **API Keys**: encriptadas en reposo con Fernet (AES-128)
- **CORS**: restringido al dominio de producción
- **Contraseñas**: complejidad mínima (8+ chars, mayúscula, minúscula, dígito, especial)
- **Headers**: X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
- **SW**: network-first para HTML/CSS/JS (siempre última versión)

## 🚢 Deploy

```bash
# En el VPS (ubuntu@10.40.2.156)
cd ~/azucar_app
git pull
docker compose up -d --build

# Variables de entorno requeridas (.env)
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/azucar
JWT_SECRET_KEY=<random>
OPENROUTER_API_KEY=<key>
API_KEY_ENCRYPTION_KEY=<random_64_hex>
```

## 📱 PWA

La app es instalable en Android/iOS como PWA (Agregar a pantalla de inicio). El Service Worker usa estrategia **network-first** para archivos principales y cache-first para fuentes/iconos.

Para forzar actualización manual: **Configuración → Actualizar App → Buscar e instalar actualización**.

## 📖 Documentación para el usuario

Toca el botón **?** en la esquina superior derecha de la app para acceder a la guía de uso completa con todas las funcionalidades.

---

**Repo:** https://github.com/jpvargassoruco/azucar_app  
**Autor:** jpvargassoruco  
**Última actualización:** Julio 2026
