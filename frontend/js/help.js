// ===== USER HELP GUIDE =====

const HELP_SECTIONS = [
  {
    title: 'Registro de Glucosa',
    icon: '📊',
    content: `
      <p>Registra tus niveles de glucosa manualmente ingresando el valor en mg/dL.</p>
      <p><strong>Condiciones:</strong></p>
      <ul>
        <li><strong>Ayunas:</strong> medición antes de comer (ideal: 70-130 mg/dL)</li>
        <li><strong>Postprandial:</strong> 2 horas después de comer (ideal: &lt;180 mg/dL)</li>
        <li><strong>Otro:</strong> cualquier otro momento</li>
      </ul>
      <p>El <strong>gráfico de tendencia</strong> muestra tus últimas 7 lecturas. Desliza horizontalmente para verlas todas.</p>
      <p>Usa el botón 🗑️ para eliminar registros individuales.</p>
    `
  },
  {
    title: 'Análisis de Comidas con IA',
    icon: '🍽️',
    content: `
      <p>Toma una foto de tu plato y la Inteligencia Artificial estimará:</p>
      <ul>
        <li>Calorías, carbohidratos, proteínas, grasas y fibra</li>
        <li>Impacto glucémico (bajo, moderado, alto)</li>
        <li>Recomendaciones personalizadas para diabetes tipo 2</li>
      </ul>
      <p><strong>Consejos para mejores resultados:</strong></p>
      <ul>
        <li>Buena iluminación sobre el plato</li>
        <li>Enfocar desde arriba para capturar todas las porciones</li>
        <li>Las fotos originales se borran después del análisis (solo se guarda miniatura)</li>
      </ul>
      <p>Puedes <strong>editar</strong> cualquier análisis tocando el ícono ✏️ en la tarjeta de la comida. También puedes <strong>corregir con IA</strong> si el análisis no es preciso.</p>
    `
  },
  {
    title: 'Cola de Fotos Pendientes',
    icon: '📋',
    content: `
      <p>¿Comiste varias veces y quieres registrar todo junto?</p>
      <ol>
        <li>Toma fotos de cada comida con 📷 <strong>Cámara</strong> o 🖼️ <strong>Galería</strong></li>
        <li>Toca <strong>Agregar a Cola</strong> para cada foto</li>
        <li>Ajusta la <strong>fecha y hora</strong> exacta en que consumiste cada alimento</li>
        <li>Toca <strong>Analizar Todo</strong> para procesarlas juntas</li>
      </ol>
      <p>Las fotos se envían al servidor con la hora que especificaste, no con la hora actual.</p>
    `
  },
  {
    title: 'Ayuno Intermitente',
    icon: '⏳',
    content: `
      <p>Activa un temporizador de ayuno con el protocolo que prefieras:</p>
      <ul>
        <li><strong>16:8</strong> — 16 horas de ayuno, 8 de alimentación</li>
        <li><strong>12:12</strong> — 12 horas de ayuno</li>
        <li><strong>18:6</strong> — 18 horas de ayuno</li>
        <li><strong>20:4</strong> — 20 horas de ayuno</li>
      </ul>
      <p>Puedes ajustar la <strong>fecha y hora de inicio</strong>. El temporizador corre en segundo plano mientras la app está abierta.</p>
      <p>El historial de sesiones de ayuno se guarda y se incluye en la exportación FHIR.</p>
    `
  },
  {
    title: 'Alarmas y Recordatorios',
    icon: '⏰',
    content: `
      <p>Tres tipos de recordatorios:</p>
      <ul>
        <li><strong>Postprandial:</strong> te avisa 2 horas después de comer para medir tu glucosa</li>
        <li><strong>Hidratación:</strong> recuerda beber agua cada 2 horas</li>
        <li><strong>Metformina:</strong> alarma diaria a la hora configurada</li>
      </ul>
      <p>Los recordatorios funcionan con notificaciones push. Asegúrate de <strong>activar las notificaciones</strong> cuando la app lo solicite. En Android, instala la app como PWA (Agregar a pantalla de inicio) para recibir notificaciones incluso con la app cerrada.</p>
    `
  },
  {
    title: 'Hábitos Diarios',
    icon: '✓',
    content: `
      <p>Marca los hábitos que completes cada día:</p>
      <ul>
        <li>Ejercicio físico</li>
        <li>Consumo de agua</li>
        <li>Cumplimiento del ayuno</li>
        <li>Toma de medicación</li>
      </ul>
      <p>La barra de progreso muestra tu avance diario. ¡Llegar al 100% celebra tu consistencia!</p>
    `
  },
  {
    title: 'Medicamentos y Suplementos',
    icon: '💊',
    content: `
      <p>Configura tus medicamentos y suplementos:</p>
      <ul>
        <li>Nombre, tipo (medicamento o suplemento), dosis</li>
        <li>Múltiples horarios por día</li>
        <li>Días de la semana específicos</li>
      </ul>
      <p>En la sección <strong>Dosis de Hoy</strong> puedes marcar cada dosis como Tomada o Saltada.</p>
      <p>Filtra por tipo (todos, medicamentos, suplementos) para ver solo lo que necesitas.</p>
    `
  },
  {
    title: 'Asistente Hermes IA',
    icon: '🤖',
    content: `
      <p>Chatea con un asistente virtual experto en nutrición y diabetes tipo 2.</p>
      <p>Preguntas frecuentes que puedes hacer:</p>
      <ul>
        <li>"¿Qué alimentos debo evitar antes de dormir?"</li>
        <li>"¿Es mejor hacer ejercicio antes o después de comer?"</li>
        <li>"¿Cómo afecta el estrés a mi glucosa?"</li>
        <li>"¿Qué meriendas son buenas para la diabetes?"</li>
      </ul>
      <p>El asistente usa el proveedor de IA que configures (Google AI Studio, OpenRouter, Deepseek o Nvidia). Tu contexto de salud se comparte para respuestas personalizadas.</p>
    `
  },
  {
    title: 'Planificador de Menú IA',
    icon: '🥗',
    content: `
      <p>Genera un plan de comidas de 1 día personalizado:</p>
      <ol>
        <li>Escribe tus preferencias o restricciones (ej. "sin lácteos, me gusta el pollo")</li>
        <li>Selecciona cuántas comidas (2 a 5)</li>
        <li>Toca <strong>Generar Plan</strong></li>
      </ol>
      <p>El plan incluye estimaciones de calorías, carbohidratos, impacto glucémico y recomendaciones para cada comida.</p>
    `
  },
  {
    title: 'Configuración de IA',
    icon: '⚙️',
    content: `
      <p>Elige tu proveedor de Inteligencia Artificial:</p>
      <ul>
        <li><strong>Google AI Studio:</strong> Gemini Flash, gratuito</li>
        <li><strong>OpenRouter:</strong> acceso a múltiples modelos</li>
        <li><strong>Deepseek:</strong> modelo económico</li>
        <li><strong>Nvidia NIM:</strong> 5,000 créditos gratis</li>
      </ul>
      <p>Solo necesitas tu <strong>API Key</strong> del proveedor. El modelo y URL se llenan automáticamente.</p>
      <p>Usa <strong>Probar Conexión</strong> para verificar que tu clave funciona antes de guardar.</p>
      <p>Si tu proveedor falla, la app automáticamente intenta con Nvidia como respaldo.</p>
    `
  },
  {
    title: 'Exportar Datos (FHIR)',
    icon: '🏥',
    content: `
      <p>Descarga tu historial completo en formato <strong>HL7 FHIR R4</strong>, el estándar internacional para datos de salud.</p>
      <p>El archivo incluye:</p>
      <ul>
        <li>Perfil del paciente</li>
        <li>Condición (Diabetes tipo 2)</li>
        <li>Todas las lecturas de glucosa</li>
        <li>Comidas analizadas</li>
        <li>Sesiones de ayuno</li>
      </ul>
      <p>Compatible con sistemas como Epic, Cerner y HAPI FHIR. Puedes compartirlo con tu médico.</p>
    `
  },
  {
    title: 'Temas y Zoom',
    icon: '🎨',
    content: `
      <p><strong>Tema claro/oscuro:</strong> La app detecta automáticamente tu preferencia del sistema. Puedes cambiarlo manualmente en Configuración.</p>
      <p><strong>Zoom:</strong> Usa los botones 🔍+ y 🔍− en Configuración para ajustar el tamaño de la interfaz. El nivel se guarda automáticamente.</p>
    `
  },
  {
    title: 'Signos Vitales: Peso',
    icon: '📏',
    content: `
      <p>Registra tu peso corporal en kilogramos para monitorear cambios a lo largo del tiempo.</p>
      <p><strong>Información registrada:</strong></p>
      <ul>
        <li>Peso en kg (rango: 0–300 kg)</li>
        <li>Fecha y hora de medición</li>
        <li>Notas opcionales (ej. "antes del desayuno", "después del ejercicio")</li>
      </ul>
      <p>El historial de peso se usa para calcular tu Índice de Masa Corporal (IMC) cuando combinas con tu altura. Elimina registros individuales con el botón 🗑️.</p>
    `
  },
  {
    title: 'Signos Vitales: Presión Arterial',
    icon: '💧',
    content: `
      <p>Registra tu presión arterial (sistólica y diastólica) en mmHg (milímetros de mercurio).</p>
      <p><strong>Rangos clínicos:</strong></p>
      <ul>
        <li><strong>Normal:</strong> &lt; 120 / &lt; 80 mmHg</li>
        <li><strong>Elevada:</strong> 120–129 / &lt; 80 mmHg</li>
        <li><strong>Hipertensión:</strong> ≥ 130 / ≥ 80 mmHg</li>
      </ul>
      <p>La presión arterial es especialmente importante en diabetes tipo 2. Registra en reposo, 5 minutos después de sentarte. Incluye notas sobre medicamentos tomados o condiciones especiales.</p>
    `
  },
  {
    title: 'Signos Vitales: HbA1c Lab',
    icon: '🩸',
    content: `
      <p>Registra los resultados de tu <strong>análisis de laboratorio de HbA1c</strong> (hemoglobina glicosilada).</p>
      <p><strong>¿Qué es?</strong> HbA1c mide tu glucosa promedio de los últimos 3 meses. No es una medición diaria como tu glucómetro.</p>
      <p><strong>Objetivos según tu médico:</strong></p>
      <ul>
        <li>Diabetes tipo 2: generalmente &lt; 7% (algunos pacientes 6.5%)</li>
        <li>Rango normal: 4–6%</li>
      </ul>
      <p>Ingresa el valor en porcentaje que tu laboratorio reportó. La app lo almacena con la fecha del análisis para seguimiento a largo plazo.</p>
    `
  },
  {
    title: 'Actualizar la App',
    icon: '🔄',
    content: `
      <p>Si la app no muestra los cambios más recientes:</p>
      <ol>
        <li>Ve a <strong>Configuración → Actualizar App</strong></li>
        <li>Toca <strong>Buscar e instalar actualización</strong></li>
        <li>La app se recargará con la última versión</li>
      </ol>
      <p><strong>Nota:</strong> El navegador guarda la app en caché. Si no ves cambios después de actualizar:</p>
      <ul>
        <li>Abre Configuración → Actualizar App y repite el proceso</li>
        <li>O, en el menú del navegador, busca "Borrar datos del sitio" o "Clear storage" y recarga</li>
      </ul>
      <p>También puedes instalar la app en tu pantalla de inicio desde el menú del navegador (⋮ → Agregar a pantalla de inicio) para usarla como una app nativa.</p>
    `
  }
];

function openHelpGuide() {
  const existing = document.getElementById('helpSheet');
  if (existing) {
    existing.classList.add('open');
    existing.setAttribute('aria-hidden', 'false');
    return;
  }

  const sheet = document.createElement('div');
  sheet.id = 'helpSheet';
  sheet.className = 'bottom-sheet open';
  sheet.setAttribute('role', 'dialog');
  sheet.setAttribute('aria-label', 'Guía de ayuda');
  sheet.setAttribute('aria-hidden', 'false');
  sheet.innerHTML = `
    <div class="bottom-sheet-backdrop"></div>
    <div class="bottom-sheet-panel" style="max-height:85vh;">
      <div class="bottom-sheet-handle"></div>
      <div class="bottom-sheet-header" style="font-size:1.2rem;">📖 Guía de Azúcar Control</div>
      <div style="max-height:70vh;overflow-y:auto;-webkit-overflow-scrolling:touch;">
        ${HELP_SECTIONS.map(s => `
          <details class="card" style="cursor:pointer;margin-bottom:8px;padding:16px;">
            <summary style="list-style:none;display:flex;align-items:center;gap:10px;font-weight:700;font-size:0.95rem;color:var(--text-primary);">
              <span style="font-size:1.3rem;">${s.icon}</span> ${s.title}
            </summary>
            <div style="margin-top:12px;font-size:0.82rem;color:var(--text-secondary);line-height:1.6;">
              ${s.content}
            </div>
          </details>
        `).join('')}
      </div>
    </div>
  `;

  document.body.appendChild(sheet);

  sheet.querySelector('.bottom-sheet-backdrop').addEventListener('click', closeHelpGuide);
  document.addEventListener('keydown', function onEsc(e) {
    if (e.key === 'Escape') { closeHelpGuide(); document.removeEventListener('keydown', onEsc); }
  });
}

function closeHelpGuide() {
  const sheet = document.getElementById('helpSheet');
  if (sheet) {
    sheet.classList.remove('open');
    sheet.setAttribute('aria-hidden', 'true');
    setTimeout(() => sheet.remove(), 300);
  }
}

window.openHelpGuide = openHelpGuide;
window.closeHelpGuide = closeHelpGuide;
