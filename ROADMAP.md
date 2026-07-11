# 🗺️ Roadmap de Azúcar Control

Roadmap derivado del análisis comparativo entre **[Diaguard](https://github.com/Faltenreich/Diaguard)** (app Android nativa de diabetes, madura, local-only, orientada a T1/T2) y **Azúcar Control** (PWA Tipo 2, cloud, con IA).

Azúcar Control es fuerte en IA (análisis de comidas por foto, planificador, chat Hermes), ayuno intermitente, hábitos, medicamentos, push y exportación FHIR. Diaguard aporta capacidades clínicas estándar que aún no tenemos. Este roadmap **prioriza las features relevantes para diabetes Tipo 2**, dejando lo puramente insulino-dependiente (T1) para una fase final opcional.

> **Nota:** este documento es una guía de planificación. Las "notas de arquitectura" por fase indican dónde encajaría cada feature siguiendo los patrones actuales del proyecto; no son implementaciones.

---

## 📊 Tabla de gap (Diaguard → Azúcar Control)

| Feature de Diaguard | Estado en Azúcar | Relevancia T2 | Fase |
|---|---|---|---|
| Glucosa | ✅ Tiene | — | — |
| Comidas / carbohidratos | ✅ (foto IA; sin carb manual) | — | 4 |
| Recordatorios | ✅ (push, superior) | — | — |
| Dark mode | ✅ | — | — |
| Peso + IMC | ❌ | Alta | 1 |
| Presión arterial (sistólica/diastólica) | ❌ | Alta | 1 |
| HbA1c (lab) + eA1c/GMI estimado | ❌ | Alta | 1–2 |
| Tiempo-en-rango (TIR) / distribución | ❌ | Alta | 2 |
| Gráfico con banda de rango objetivo | ⚠️ básico (barras 7 días) | Alta | 2 |
| Rango objetivo personalizado + alerta hipo/hiper | ❌ | Alta | 2 |
| Export PDF (diario para el médico) | ❌ | Alta | 3 |
| Export CSV | ❌ | Alta | 3 |
| Backup / restore (export + import) | ❌ | Alta | 3 |
| Actividad / ejercicio (duración) | ❌ (solo toggle de hábito) | Media | 4 |
| Pulso + SpO2 | ❌ | Media/Baja | 4 |
| Tags en registros + búsqueda | ❌ | Media (UX) | 4 |
| Base de datos de alimentos (Open Food Facts) | ❌ | Media | 4 |
| Unidades configurables (mmol/L) | ❌ (mg/dL fijo) | Media | 5 |
| Multi-idioma | ❌ (solo español) | Baja | 5 |
| Insulina + calculadora de bolo | ❌ | Solo insulino-dep. | 6 (opcional) |

---

## 🚦 Fases

### Fase 1 — Signos vitales y tracking clínico T2
Ampliar el modelo de datos más allá de la glucosa con las mediciones clínicas clave para Tipo 2:
- **Peso + IMC** (requiere añadir `height` al perfil de usuario).
- **Presión arterial** (sistólica/diastólica, con clasificación de rango).
- **HbA1c de laboratorio** (registro manual del valor reportado).

**Notas de arquitectura:** nuevas entidades siguiendo el patrón de `backend/app/models/glucose.py`; routers siguiendo `backend/app/routers/glucose.py`; schemas en `backend/app/schemas/`; registrar cada router en `backend/app/main.py` (`include_router` con prefijo `/api/v1/...`); migración Alembic en `backend/alembic/versions/`.

### Fase 2 — Analítica e insights de glucosa
Convertir datos crudos en información accionable:
- **Tiempo-en-rango (TIR)** y distribución hipo / en-rango / hiper.
- **eA1c y GMI estimados** desde la glucosa:
  - `eA1c(%) = (media_mgdl + 46.7) / 28.7`
  - `GMI(%) = 3.31 + 0.02392 × media_mgdl`
- **Rango objetivo personalizado** + umbrales hipo/hiper por usuario, con alerta al guardar una lectura fuera de rango.
- **Gráfico mejorado** con banda de rango objetivo + líneas de umbral.

**Notas de arquitectura:** extender `get_glucose_stats` en `backend/app/routers/glucose.py:66` (hoy solo promedios/conteo) o crear un router `analytics`. Rango objetivo y umbrales en `backend/app/models/user.py`. Para el gráfico, evaluar Chart.js (skill `dataviz`); hoy es una barra CSS custom en `frontend/js/app.js`.

### Fase 3 — Exportación y portabilidad
Datos que el paciente puede llevar a su médico y respaldar:
- **Export PDF** (diario/logbook tipo Diaguard, formateado para consulta médica).
- **Export CSV**.
- **Backup / restore** completo (export JSON + import).

**Notas de arquitectura:** nueva service para PDF (`reportlab` o `fpdf2`) + endpoint; reutilizar `backend/app/services/fhir_serializer.py` como referencia de serialización por entidad.

### Fase 4 — Logging enriquecido (UX)
- **Actividad/ejercicio** con duración (más allá del toggle de hábito).
- **Pulso + SpO2**.
- **Tags** en registros + búsqueda full-text.
- **Carbohidratos manuales** + búsqueda opcional en **Open Food Facts** (complementa el análisis por foto de `backend/app/services/meal_analyzer.py`).

### Fase 5 — Unidades e i18n (opcional)
- Soporte **mmol/L** + preferencia de unidad por usuario (conversión mg/dL ↔ mmol/L).
- **Multi-idioma** (inglés primero).

### Fase 6 — Terapia con insulina (diferido, solo insulino-dependientes)
- Registro de dosis (bolo / corrección / basal).
- **Calculadora de bolo** (ratio de carbohidratos + factor de corrección + objetivo).
- Horarios de factores por hora del día (basal/corrección/comida), como en Diaguard.

---

**Referencia:** [Diaguard en GitHub](https://github.com/Faltenreich/Diaguard) · [Volver al README](README.md)
