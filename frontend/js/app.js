    // ===================================================================
    //  AZÚCAR CONTROL — PWA Cloud Application Logic
    // ===================================================================

    let currentUser = null;

    // ===== UTILITY FUNCTIONS =====
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    function getTodayStr() {
      const d = new Date();
      return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0');
    }

    function formatDate(dateStr) {
      // Handle date formatting without timezone offsets
      const parts = dateStr.split('T')[0].split('-');
      const d = new Date(parts[0], parts[1] - 1, parts[2]);
      return d.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });
    }

    function formatTime(dateTimeStr) {
      const d = new Date(dateTimeStr);
      let h = d.getHours();
      const m = String(d.getMinutes()).padStart(2, '0');
      const ampm = h >= 12 ? 'PM' : 'AM';
      h = h % 12 || 12;
      return `${h}:${m} ${ampm}`;
    }

    function padZero(n) { return String(n).padStart(2, '0'); }

    function showToast(msg, type = 'info') {
      const container = $('#toastContainer');
      const icons = { info: 'ℹ️', warning: '⚠️', danger: '🚨', success: '✅' };
      const toast = document.createElement('div');
      toast.className = `toast ${type}`;
      toast.innerHTML = `<span class="toast-icon">${icons[type]}</span><span class="toast-msg">${msg}</span>`;
      container.appendChild(toast);
      toast.onclick = () => toast.remove();
      setTimeout(() => {
        toast.style.transition = '0.3s';
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
      }, 5000);
    }

    // Play Beep Alert
    function playAlarmSound() {
      try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const notes = [880, 1046.5, 880, 1046.5];
        notes.forEach((freq, i) => {
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          osc.connect(gain);
          gain.connect(ctx.destination);
          osc.type = 'sine';
          osc.frequency.value = freq;
          gain.gain.value = 0.15;
          osc.start(ctx.currentTime + i * 0.25);
          osc.stop(ctx.currentTime + i * 0.25 + 0.2);
          gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i * 0.25 + 0.2);
        });
      } catch (e) { /* silent fallback */ }
    }

    // ===== DATE HEADER =====
    function updateDateHeader() {
      const now = new Date();
      const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
      $('#currentDate').textContent = now.toLocaleDateString('es-ES', options);
    }
    updateDateHeader();

    // ===== AUTHENTICATION JWT UTILITIES =====
    let isRegisterMode = false;

    function toggleAuthMode(e) {
      e.preventDefault();
      isRegisterMode = !isRegisterMode;
      if (isRegisterMode) {
        $('#authSubtitle').textContent = 'Crear cuenta en la plataforma';
        $('#nameGroup').style.display = 'block';
        $('#authSubmitBtn').textContent = 'Crear Cuenta';
        $('#authToggleText').textContent = '¿Ya tienes una cuenta?';
        $('#authToggleLink').textContent = 'Inicia Sesión';
      } else {
        $('#authSubtitle').textContent = 'Plataforma Privada de Gestión de Diabetes';
        $('#nameGroup').style.display = 'none';
        $('#authSubmitBtn').textContent = 'Iniciar Sesión';
        $('#authToggleText').textContent = '¿No tienes una cuenta?';
        $('#authToggleLink').textContent = 'Regístrate';
      }
    }

    async function handleAuthSubmit(e) {
      e.preventDefault();
      const email = $('#authEmail').value;
      const password = $('#authPassword').value;
      const name = $('#authName').value;
      
      const btn = $('#authSubmitBtn');
      btn.disabled = true;
      btn.textContent = 'Procesando...';
      
      try {
        if (isRegisterMode) {
          // Register flow
          const res = await fetch('/api/v1/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, name })
          });
          if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || 'Fallo en registro');
          }
          showToast('Cuenta creada con éxito. Iniciando sesión...', 'success');
        }
        
        // Login flow
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);
        
        const res = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: formData
        });
        
        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.detail || 'Fallo en login');
        }
        
        const data = await res.json();
        localStorage.setItem('azucar_token', data.access_token);
        $('#authOverlay').classList.add('hidden');
        showToast('Acceso autorizado', 'success');
        initializeSession();
      } catch (err) {
        showToast(err.message, 'danger');
      } finally {
        btn.disabled = false;
        btn.textContent = isRegisterMode ? 'Crear Cuenta' : 'Iniciar Sesión';
      }
    }

    function handleLogout() {
      localStorage.removeItem('azucar_token');
      // Reset UI states
      $('#authOverlay').classList.remove('hidden');
      $('#userBanner').style.display = 'none';
      showToast('Sesión cerrada correctamente', 'info');
    }

    // Generic Fetch Wrapper
    async function apiFetch(path, options = {}) {
      const token = localStorage.getItem('azucar_token');
      if (!token) {
        handleLogout();
        throw new Error('No token found');
      }
      
      const headers = options.headers || {};
      if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
      }
      headers['Authorization'] = `Bearer ${token}`;
      
      const response = await fetch(path, { ...options, headers });
      
      if (response.status === 401) {
        handleLogout();
        throw new Error('Sesión expirada');
      }
      
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'API error');
      }
      
      if (response.status === 204) return null;
      return await response.json();
    }

    // ===== MAIN INIT SESSION =====
    async function initializeSession() {
      try {
        const user = await apiFetch('/api/v1/auth/me');
        currentUser = user;
        $('#userNameDisplay').textContent = user.name;
        $('#userBanner').style.display = 'flex';
        
        // Set date defaults in metrics and fasting forms
        const now = new Date();
        $('#metricDate').value = getTodayStr();
        $('#metricTime').value = `${padZero(now.getHours())}:${padZero(now.getMinutes())}`;
        
        $('#fastingStartDate').value = getTodayStr();
        $('#fastingStartTime').value = `${padZero(now.getHours())}:${padZero(now.getMinutes())}`;
        
        // Populate config panel
        populateConfigPanel(user);
        
        // Trigger loads
        await loadGlucoseData();
        await loadMealsData();
        await loadLatestMealPlan();
        await loadFastingState();
        await loadHabits();
        await loadAlarms();
        await loadMedications();
        await loadTodayDoses();
        await loadAllVitals();
      } catch (err) {
        console.error("Initialization failed", err);
      }
    }

    // ===== NAVIGATION TABS =====
    function capitalize(str) {
      return str.charAt(0).toUpperCase() + str.slice(1);
    }

    // Map bottom nav tabs to section IDs
    const TAB_MAP = {
      registry: 'sectionRegistry',
      nutrition: 'sectionMeals',  // default to Comidas sub-tab
      meals: 'sectionMeals',
      mealPlan: 'sectionMealPlan',
      fasting: 'sectionFasting',
      alarms: 'sectionAlarms',
      habits: 'sectionHabits',
      medications: 'sectionMedications',
      ai: 'sectionAi',
      config: 'sectionConfig'
    };

    function navigateToTab(tabName) {
      const sectionId = TAB_MAP[tabName];
      if (!sectionId) return;

      // Deactivate all sections
      $$('.tab-section').forEach(s => s.classList.remove('active'));

      // Deactivate all nav items (top + bottom)
      $$('.nav-tab').forEach(t => t.classList.remove('active'));
      $$('.bottom-nav-item').forEach(t => t.classList.remove('active'));

      // Activate target section
      const section = $(`#${sectionId}`);
      if (section) section.classList.add('active');

      // Activate matching top nav tab
      const topTab = document.querySelector(`.nav-tab[data-tab="${tabName}"]`);
      if (topTab) topTab.classList.add('active');

      // Activate matching bottom nav item
      const bottomItem = document.querySelector(`.bottom-nav-item[data-tab="${tabName}"]`);
      if (bottomItem) {
        bottomItem.classList.add('active');
        bottomItem.setAttribute('aria-selected', 'true');
      }

      // Update aria-selected on all bottom nav items
      $$('.bottom-nav-item').forEach(item => {
        if (item !== bottomItem) item.setAttribute('aria-selected', 'false');
      });

      // Show/hide sub-nav for nutrition sections
      const subNav = $('#mealsSubNav');
      if (subNav) {
        subNav.style.display = (tabName === 'nutrition' || tabName === 'meals' || tabName === 'mealPlan') ? 'flex' : 'none';
      }
    }

    // Top nav click handlers
    $$('.nav-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        navigateToTab(tab.dataset.tab);
      });
    });

    // Bottom nav click handlers
    $$('.bottom-nav-item').forEach(item => {
      item.addEventListener('click', () => {
        const tabName = item.dataset.tab;
        if (tabName === 'more') {
          openMoreSheet();
        } else {
          navigateToTab(tabName);
        }
      });
    });

    // Bottom sheet
    function openMoreSheet() {
      const sheet = $('#moreSheet');
      sheet.classList.add('open');
      sheet.setAttribute('aria-hidden', 'false');
      // Focus first item
      const firstItem = sheet.querySelector('.sheet-item');
      if (firstItem) firstItem.focus();
    }

    function closeMoreSheet() {
      const sheet = $('#moreSheet');
      sheet.classList.remove('open');
      sheet.setAttribute('aria-hidden', 'true');
    }

    // Bottom sheet backdrop click
    const moreSheet = $('#moreSheet');
    if (moreSheet) {
      moreSheet.querySelector('.bottom-sheet-backdrop').addEventListener('click', closeMoreSheet);

      // Bottom sheet item clicks
      moreSheet.querySelectorAll('.sheet-item').forEach(item => {
        item.addEventListener('click', () => {
          navigateToTab(item.dataset.tab);
          closeMoreSheet();
        });
      });

      // ESC to close
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && moreSheet.classList.contains('open')) {
          closeMoreSheet();
        }
      });
    }

    // Sub-navigation pills for Nutricion (created dynamically in meal sections)
    function createSubNav() {
      const mealsSection = $('#sectionMeals');
      const mealPlanSection = $('#sectionMealPlan');
      if (!mealsSection || !mealPlanSection) return;

      // Check if sub-nav already exists
      if ($('#mealsSubNav')) return;

      const subNav = document.createElement('div');
      subNav.id = 'mealsSubNav';
      subNav.className = 'sub-nav';
      subNav.style.display = 'none';
      subNav.innerHTML = `
        <button class="sub-nav-pill active" data-sub="meals">📸 Comidas</button>
        <button class="sub-nav-pill" data-sub="mealPlan">🥗 Menú IA</button>
      `;

      // Insert before meals section
      mealsSection.parentNode.insertBefore(subNav, mealsSection);

      // Sub-nav pill clicks
      subNav.querySelectorAll('.sub-nav-pill').forEach(pill => {
        pill.addEventListener('click', () => {
          subNav.querySelectorAll('.sub-nav-pill').forEach(p => p.classList.remove('active'));
          pill.classList.add('active');
          $$('.tab-section').forEach(s => s.classList.remove('active'));
          if (pill.dataset.sub === 'meals') {
            $('#sectionMeals').classList.add('active');
          } else if (pill.dataset.sub === 'mealPlan') {
            $('#sectionMealPlan').classList.add('active');
          }
        });
      });
    }

    // Call after DOM ready
    createSubNav();

    // ===== AI CONFIGURATION PANEL =====
    function populateConfigPanel(user) {
      $('#configProvider').value = user.ai_provider || 'openrouter';
      $('#configApiKey').value = user.ai_api_key_masked || '';
      $('#configModel').value = user.ai_model || '';
      $('#configBaseUrl').value = user.ai_base_url || '';
      handleProviderChange();
    }

    // Provider defaults: model + base URL
    const PROVIDER_DEFAULTS = {
      google:    { model: 'gemini-flash-latest',     url: 'https://generativelanguage.googleapis.com/v1beta' },
      openrouter:{ model: 'openrouter/auto',      url: 'https://openrouter.ai/api/v1' },
      deepseek:  { model: 'deepseek-chat',        url: 'https://api.deepseek.com/v1' },
      nvidia:    { model: 'nvidia/nemotron-3-super-120b-a12b', url: 'https://integrate.api.nvidia.com/v1' }
    };

    function handleProviderChange() {
      const provider = $('#configProvider').value;
      const modelInput = $('#configModel');
      const urlInput = $('#configBaseUrl');
      const defaults = PROVIDER_DEFAULTS[provider];

      if (defaults) {
        // Always set model and URL to provider defaults when switching
        modelInput.value = defaults.model;
        urlInput.value = defaults.url;
        urlInput.placeholder = defaults.url;
      }
    }
    window.handleProviderChange = handleProviderChange;

    function togglePasswordVisibility(inputId) {
      const input = $(`#${inputId}`);
      if (input.type === 'password') {
        input.type = 'text';
      } else {
        input.type = 'password';
      }
    }

    async function testAIConnection() {
      const provider = $('#configProvider').value;
      let apiKey = $('#configApiKey').value.trim();
      const model = $('#configModel').value.trim();
      const baseUrl = $('#configBaseUrl').value.trim();
      
      if (!apiKey) {
        showToast('Ingresa una API Key para probar.', 'warning');
        return;
      }
      
      // If they submitted the masked version, they can't test unless they write a new one
      if (apiKey.startsWith('***') || apiKey === (currentUser && currentUser.ai_api_key_masked)) {
        showToast('No se puede probar la conexión con una clave enmascarada. Escribe una nueva clave para verificarla.', 'warning');
        return;
      }
      
      const btn = $('#btnTestConfig');
      const originalText = btn.textContent;
      btn.textContent = '⏳ Probando...';
      btn.disabled = true;
      
      try {
        const res = await apiFetch('/api/v1/auth/test-ai', {
          method: 'POST',
          body: JSON.stringify({
            ai_provider: provider,
            ai_api_key: apiKey,
            ai_model: model,
            ai_base_url: baseUrl || null
          })
        });
        
        if (res.success) {
          showToast(`Conexión exitosa: "${res.response}"`, 'success');
        } else {
          showToast(`Error de conexión: ${res.message}`, 'danger');
          console.error(res.details);
        }
      } catch (err) {
        showToast('Error de red al probar conexión: ' + err.message, 'danger');
      } finally {
        btn.textContent = originalText;
        btn.disabled = false;
      }
    }

    async function handleConfigSave(e) {
      e.preventDefault();
      const provider = $('#configProvider').value;
      let apiKey = $('#configApiKey').value.trim();
      const model = $('#configModel').value.trim();
      const baseUrl = $('#configBaseUrl').value.trim();
      
      const btn = $('#btnSaveConfig');
      const originalText = btn.textContent;
      btn.textContent = '⏳ Guardando...';
      btn.disabled = true;
      
      try {
        const user = await apiFetch('/api/v1/auth/me/ai-settings', {
          method: 'PUT',
          body: JSON.stringify({
            ai_provider: provider,
            ai_api_key: apiKey,
            ai_model: model,
            ai_base_url: baseUrl || null
          })
        });
        currentUser = user;
        populateConfigPanel(user);
        showToast('Configuración guardada exitosamente.', 'success');
      } catch (err) {
        showToast('Error al guardar la configuración: ' + err.message, 'danger');
      } finally {
        btn.textContent = originalText;
        btn.disabled = false;
      }
    }

    async function exportFHIRBundle() {
      try {
        const token = localStorage.getItem('azucar_token');
        if (!token) throw new Error('No estás autenticado');
        
        // Use standard fetch because we want to download a file, not parse JSON directly
        const res = await fetch('/api/v1/fhir/Bundle/export', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (!res.ok) {
          throw new Error('No se pudo generar el Bundle FHIR');
        }
        
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        // Parse content-disposition if possible, or just default name
        const cd = res.headers.get('Content-Disposition');
        let filename = 'fhir_bundle.json';
        if (cd && cd.includes('filename=')) {
          filename = cd.split('filename=')[1].replace(/["']/g, '');
        }
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        showToast('Bundle FHIR exportado con éxito.', 'success');
      } catch (err) {
        showToast('Error al exportar: ' + err.message, 'danger');
      }
    }


    // ===== 1. GLUCOSE ALERT PANEL =====
    function getGlucoseZone(val) {
      if (val >= 250) return 'crisis';
      if (val >= 180) return 'warning';
      if (val >= 130) return 'safe';
      return 'optimal';
    }

    function getZoneLabel(zone) {
      const labels = {
        crisis: '🔴 ZONA DE CRISIS — Actuar Ahora',
        warning: '🟡 Glucosa Elevada — Precaución',
        safe: '🟢 Zona Segura — Estable',
        optimal: '🔵 Zona Óptima — Excelente'
      };
      return labels[zone];
    }

    function updateGlucoseAlert() {
      const val = parseInt($('#glucoseInput').value);
      if (!val || val < 30 || val > 600) {
        showToast('Ingresa un valor de glucosa válido (30-600 mg/dL)', 'warning');
        return;
      }

      const zone = getGlucoseZone(val);
      const display = $('#glucoseDisplay');
      const valueEl = $('#glucoseValueDisplay');
      const statusBadge = $('#glucoseStatusBadge');
      const statusDot = statusBadge.querySelector('.status-dot');
      const statusText = $('#glucoseStatusText');
      const alertRecs = $('#alertRecs');

      // Update display
      display.className = `glucose-display ${zone}`;
      valueEl.className = `glucose-value ${zone}`;
      valueEl.textContent = val;
      statusBadge.className = `glucose-status ${zone}`;
      statusDot.className = `status-dot ${zone}`;
      statusText.textContent = getZoneLabel(zone);

      // Gauge
      const maxVal = 400;
      const pct = Math.min(val / maxVal, 1);
      const circumference = 2 * Math.PI * 68;
      const offset = circumference * (1 - pct);
      const gaugeFill = $('#gaugeFill');
      gaugeFill.style.strokeDashoffset = offset;

      const colors = { crisis: '#ef4444', warning: '#fbbf24', safe: '#34d399', optimal: '#22d3ee' };
      gaugeFill.style.stroke = colors[zone];

      // Recommendations
      if (zone === 'crisis') {
        alertRecs.classList.add('show');
        playAlarmSound();
        showToast(`⚠️ Glucosa en ${val} mg/dL — Sigue las recomendaciones de emergencia`, 'danger');
      } else if (zone === 'warning') {
        alertRecs.classList.remove('show');
        showToast(`Glucosa en ${val} mg/dL — Evita carbohidratos simples`, 'warning');
      } else {
        alertRecs.classList.remove('show');
        showToast(`Glucosa en ${val} mg/dL — Nivel estable`, 'success');
      }
    }

    // ===== 2. METRICS REGISTRY =====
    async function loadGlucoseData() {
      try {
        const readings = await apiFetch('/api/v1/glucose/');
        const stats = await apiFetch('/api/v1/glucose/stats');
        
        // Counter statistics
        $('#avgToday').textContent = stats.avg_all > 0 ? stats.avg_all : '--';
        
        const lastEl = $('#lastReading');
        if (readings.length > 0) {
          lastEl.textContent = readings[0].value_mgdl;
          const lzone = getGlucoseZone(readings[0].value_mgdl);
          const zoneColors = { crisis: '#ef4444', warning: '#fbbf24', safe: '#34d399', optimal: '#22d3ee' };
          lastEl.style.color = zoneColors[lzone];
        } else {
          lastEl.textContent = '--';
          lastEl.style.color = 'var(--text-muted)';
        }
        $('#countToday').textContent = stats.readings_count;

        renderMetricsTable(readings);
        renderDashboardChart(readings);
      } catch (err) {
        console.error("Failed to load glucose data", err);
      }
    }

    async function addMetricEntry(e) {
      e.preventDefault();
      const dateVal = $('#metricDate').value;
      const timeVal = $('#metricTime').value;
      const glucose = parseInt($('#metricGlucose').value);
      const condition = document.querySelector('input[name="metricCondition"]:checked').value;

      if (!dateVal || !timeVal || !glucose) {
        showToast('Completa todos los campos', 'warning');
        return;
      }

      // Combine local date and time into ISO
      const dt = new Date(`${dateVal}T${timeVal}:00`);

      try {
        await apiFetch('/api/v1/glucose/', {
          method: 'POST',
          body: JSON.stringify({
            datetime: dt.toISOString(),
            value_mgdl: glucose,
            condition: condition,
            notes: ''
          })
        });
        showToast(`Lectura de ${glucose} mg/dL registrada`, 'success');
        $('#metricGlucose').value = '';
        await loadGlucoseData();
      } catch (err) {
        showToast('Error al guardar la lectura', 'danger');
      }
    }

    async function deleteMetric(id) {
      if (!await showConfirm('¿Seguro de eliminar este registro?')) return;
      try {
        await apiFetch(`/api/v1/glucose/${id}`, { method: 'DELETE' });
        showToast('Registro eliminado', 'info');
        await loadGlucoseData();
      } catch (err) {
        showToast('Error al eliminar', 'danger');
      }
    }

    function renderMetricsTable(readings) {
      const container = $('#metricsTableContainer');
      const emptyEl = $('#metricsEmpty');

      const existingTable = container.querySelector('.metrics-table-wrap');
      if (existingTable) existingTable.remove();

      if (readings.length === 0) {
        emptyEl.style.display = '';
        return;
      }

      emptyEl.style.display = 'none';

      let html = `<div class="metrics-table-wrap"><table class="metrics-table">
        <thead><tr>
          <th>Fecha</th><th>Hora</th><th>Glucosa</th><th>Condición</th><th></th>
        </tr></thead><tbody>`;

      readings.forEach(m => {
        const zone = getGlucoseZone(m.value_mgdl);
        const condLabel = m.condition === 'ayunas' ? '🌙 Ayunas' : '🍽️ Postprandial';
        html += `<tr>
          <td>${formatDate(m.datetime)}</td>
          <td>${formatTime(m.datetime)}</td>
          <td><span class="glucose-badge ${zone}">${m.value_mgdl}</span></td>
          <td>${condLabel}</td>
          <td><button class="delete-btn" onclick="deleteMetric(${m.id})" title="Eliminar">🗑️</button></td>
        </tr>`;
      });

      html += '</tbody></table></div>';
      container.insertAdjacentHTML('beforeend', html);
    }

    function renderDashboardChart(readings) {
      const chart = $('#dashboardChart');
      if (readings.length === 0) {
        chart.innerHTML = `<div style="text-align:center; width:100%; color:var(--text-muted)">Añade lecturas para ver gráfico</div>`;
        return;
      }

      const last7 = readings.slice(0, 7).reverse();
      const maxVal = Math.max(...last7.map(m => m.value_mgdl), 200);

      let html = '';
      last7.forEach(m => {
        const zone = getGlucoseZone(m.value_mgdl);
        const height = Math.max((m.value_mgdl / maxVal) * 80, 4);
        const colors = { crisis: 'var(--accent-rose)', warning: 'var(--accent-amber)', safe: 'var(--accent-emerald)', optimal: 'var(--accent-cyan)' };
        html += `<div class="chart-bar-wrap">
          <div class="chart-bar-value">${m.value_mgdl}</div>
          <div class="chart-bar" style="height:${height}px; background:${colors[zone]};"></div>
          <div class="chart-bar-label">${formatTime(m.datetime)}</div>
        </div>`;
      });

      chart.innerHTML = html;
    }

    // ===== 3. MEALS IA SECTION =====
    window.mealsMap = {};

    async function loadMealsData() {
      window.loadMealsData = loadMealsData;
      try {
        const meals = await apiFetch('/api/v1/meals/');
        window.mealsMap = {};
        const gallery = $('#mealsGallery');
        gallery.innerHTML = '';
        
        if (meals.length === 0) {
          gallery.innerHTML = `<p style="grid-column:1/-1; color:var(--text-muted); text-align:center;">No hay fotos de comida registradas aún.</p>`;
          return;
        }
        
        meals.forEach(meal => {
          window.mealsMap[meal.id] = meal;
          const analysis = meal.ai_analysis || {};
          const items = analysis.food_items ? analysis.food_items.join(', ') : 'Comida';
          const impact = analysis.glycemic_impact || 'bajo';
          
          const card = document.createElement('div');
          card.className = 'meal-card';
          card.innerHTML = `
            <button class="delete-btn" onclick="deleteMeal(${meal.id})" style="position: absolute; top: 12px; right: 12px; background: rgba(10, 14, 26, 0.6); backdrop-filter: blur(4px); border-radius: 50%; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; z-index: 5;" title="Eliminar Comida">🗑️</button>
            <button class="edit-btn" onclick="openMealEditModal(${meal.id})" style="position: absolute; top: 12px; right: 50px; background: rgba(10, 14, 26, 0.6); backdrop-filter: blur(4px); border-radius: 50%; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; z-index: 5; color: white; border: none; cursor: pointer;" title="Editar Análisis">✏️</button>
            <img src="${meal.thumbnail_path}" alt="Plato" class="meal-img">
            <div class="meal-info">
              <span class="meal-date">${formatDate(meal.datetime)} a las ${formatTime(meal.datetime)}</span>
              <div class="meal-title">${meal.notes || items}</div>
              
              <div class="meal-macros">
                <div>
                  <div class="macro-val">${analysis.calories_estimated || '--'}</div>
                  <div class="macro-label">kcal</div>
                </div>
                <div>
                  <div class="macro-val">${analysis.carbs_g || '--'}g</div>
                  <div class="macro-label">Carbs</div>
                </div>
                <div>
                  <div class="macro-val">${analysis.protein_g || '--'}g</div>
                  <div class="macro-label">Prot</div>
                </div>
                <div>
                  <div class="macro-val">${analysis.fat_g || '--'}g</div>
                  <div class="macro-label">Grasa</div>
                </div>
              </div>
              
              <span class="meal-impact ${impact}">Carga Glucémica: ${impact.toUpperCase()}</span>
              <p class="meal-rec">${analysis.recommendation || 'Sin recomendaciones disponibles.'}</p>
            </div>
          `;
          gallery.appendChild(card);
        });
      } catch (err) {
        console.error("Failed to load meals data", err);
      }
    }

    function openMealEditModal(id) {
      const meal = window.mealsMap[id];
      if (!meal) return;
      
      $('#editMealId').value = meal.id;
      
      const analysis = meal.ai_analysis || {};
      $('#editMealItems').value = meal.notes || (analysis.food_items ? analysis.food_items.join(', ') : '');
      $('#editMealCalories').value = analysis.calories_estimated || 0;
      $('#editMealCarbs').value = analysis.carbs_g || 0;
      $('#editMealProtein').value = analysis.protein_g || 0;
      $('#editMealFat').value = analysis.fat_g || 0;
      $('#editMealImpact').value = analysis.glycemic_impact || 'moderado';
      $('#editMealRec').value = analysis.recommendation || '';
      $('#editMealCorrection').value = '';
      
      $('#mealEditModal').classList.remove('hidden');
    }

    function closeMealEditModal() {
      $('#mealEditModal').classList.add('hidden');
    }

    async function saveMealEdit() {
      const id = $('#editMealId').value;
      const notes = $('#editMealItems').value;
      const analysis = {
        food_items: notes.split(',').map(s => s.trim()).filter(Boolean),
        calories_estimated: parseInt($('#editMealCalories').value) || 0,
        carbs_g: parseInt($('#editMealCarbs').value) || 0,
        protein_g: parseInt($('#editMealProtein').value) || 0,
        fat_g: parseInt($('#editMealFat').value) || 0,
        fiber_g: window.mealsMap[id]?.ai_analysis?.fiber_g || 0,
        glycemic_impact: $('#editMealImpact').value,
        recommendation: $('#editMealRec').value
      };
      
      try {
        await apiFetch(`/api/v1/meals/${id}`, {
          method: 'PUT',
          body: JSON.stringify({
            notes: notes,
            ai_analysis: analysis
          })
        });
        showToast('Comida actualizada', 'success');
        closeMealEditModal();
        await loadMealsData();
      } catch (err) {
        showToast('Error al actualizar: ' + err.message, 'danger');
      }
    }

    async function correctMealWithAI() {
      const id = $('#editMealId').value;
      const comment = $('#editMealCorrection').value.trim();
      
      if (!comment) {
        showToast('Escribe un comentario para que Hermes sepa qué corregir.', 'warning');
        return;
      }
      
      const btn = $('#btnCorrectMeal');
      const originalText = btn.textContent;
      btn.textContent = '⏳...';
      btn.disabled = true;
      
      try {
        await apiFetch(`/api/v1/meals/${id}/correct`, {
          method: 'POST',
          body: JSON.stringify({
            correction_comment: comment
          })
        });
        showToast('Hermes ha corregido el análisis exitosamente.', 'success');
        closeMealEditModal();
        await loadMealsData();
      } catch (err) {
        showToast('Error al corregir con IA: ' + err.message, 'danger');
      } finally {
        btn.textContent = originalText;
        btn.disabled = false;
      }
    }

    async function deleteMeal(id) {
      window.deleteMeal = deleteMeal;
      if (!await showConfirm('¿Seguro que deseas eliminar esta comida de tu historial?')) return;
      try {
        await apiFetch(`/api/v1/meals/${id}`, { method: 'DELETE' });
        showToast('Comida eliminada con éxito', 'success');
        await loadMealsData();
      } catch (err) {
        showToast('Error al eliminar la comida: ' + err.message, 'danger');
      }
    }

    // ===== 3.1 MEAL PLANNER SECTION =====
    async function generateMealPlan(e) {
      e.preventDefault();
      const btn = $('#btnGeneratePlan');
      const originalText = btn.textContent;
      btn.textContent = '⏳ Generando plan...';
      btn.disabled = true;

      const prefs = $('#planPreferences').value;
      const numMeals = parseInt($('#planNumMeals').value) || 3;

      try {
        const plan = await apiFetch('/api/v1/meal-plan/generate', {
          method: 'POST',
          body: JSON.stringify({ preferences: prefs, num_meals: numMeals })
        });
        showToast('Plan de comidas generado con éxito.', 'success');
        renderMealPlan(plan.plan_data);
      } catch (err) {
        showToast('Error al generar el plan: ' + err.message, 'danger');
      } finally {
        btn.textContent = originalText;
        btn.disabled = false;
      }
    }

    // ===== 3.5. VITALS (WEIGHT, PRESSURE, HbA1c) =====
    async function loadWeights() {
      try {
        const res = await apiFetch('/api/v1/weights/');
        const weights = res || [];
        const historyEl = $('#weightHistory');
        historyEl.innerHTML = weights.length > 0
          ? '<table>' + weights.map(w => `
            <tr>
              <td>${new Date(w.datetime).toLocaleString()}</td>
              <td>${w.weight_kg} kg</td>
              <td>${w.notes || '—'}</td>
              <td><button onclick="deleteWeight(${w.id})" class="delete-btn">Borrar</button></td>
            </tr>`).join('') + '</table>'
          : '<p>Sin registros.</p>';
      } catch (err) {
        showToast('Error al cargar pesos: ' + err.message, 'danger');
      }
    }

    async function addWeight() {
      const weight_kg = parseFloat($('#weightInput').value);
      const notes = $('#weightNotes').value;
      if (!weight_kg || weight_kg <= 0 || weight_kg > 300) {
        showToast('Peso inválido (0–300 kg)', 'warning');
        return;
      }
      try {
        await apiFetch('/api/v1/weights/', {
          method: 'POST',
          body: JSON.stringify({
            datetime: new Date().toISOString(),
            weight_kg: weight_kg,
            notes: notes || null
          })
        });
        $('#weightInput').value = '';
        $('#weightNotes').value = '';
        showToast('Peso guardado', 'success');
        loadWeights();
      } catch (err) {
        showToast('Error al guardar peso: ' + err.message, 'danger');
      }
    }

    async function deleteWeight(id) {
      if (!await showConfirm('¿Borrar este peso?')) return;
      try {
        await apiFetch(`/api/v1/weights/${id}`, { method: 'DELETE' });
        showToast('Peso borrado', 'success');
        loadWeights();
      } catch (err) {
        showToast('Error al borrar: ' + err.message, 'danger');
      }
    }

    async function loadPressures() {
      try {
        const res = await apiFetch('/api/v1/pressures/');
        const pressures = res || [];
        const historyEl = $('#pressureHistory');
        historyEl.innerHTML = pressures.length > 0
          ? '<table>' + pressures.map(p => `
            <tr>
              <td>${new Date(p.datetime).toLocaleString()}</td>
              <td>${p.systolic_mmhg}/${p.diastolic_mmhg} mmHg</td>
              <td>${p.notes || '—'}</td>
              <td><button onclick="deletePressure(${p.id})" class="delete-btn">Borrar</button></td>
            </tr>`).join('') + '</table>'
          : '<p>Sin registros.</p>';
      } catch (err) {
        showToast('Error al cargar presión: ' + err.message, 'danger');
      }
    }

    async function addPressure() {
      const systolic = parseInt($('#systolicInput').value);
      const diastolic = parseInt($('#diastolicInput').value);
      const notes = $('#pressureNotes').value;
      if (!systolic || !diastolic || systolic < 40 || systolic > 250 || diastolic < 40 || diastolic > 250) {
        showToast('Presión inválida (40–250 mmHg)', 'warning');
        return;
      }
      try {
        await apiFetch('/api/v1/pressures/', {
          method: 'POST',
          body: JSON.stringify({
            datetime: new Date().toISOString(),
            systolic_mmhg: systolic,
            diastolic_mmhg: diastolic,
            notes: notes || null
          })
        });
        $('#systolicInput').value = '';
        $('#diastolicInput').value = '';
        $('#pressureNotes').value = '';
        showToast('Presión guardada', 'success');
        loadPressures();
      } catch (err) {
        showToast('Error al guardar presión: ' + err.message, 'danger');
      }
    }

    async function deletePressure(id) {
      if (!await showConfirm('¿Borrar esta presión?')) return;
      try {
        await apiFetch(`/api/v1/pressures/${id}`, { method: 'DELETE' });
        showToast('Presión borrada', 'success');
        loadPressures();
      } catch (err) {
        showToast('Error al borrar: ' + err.message, 'danger');
      }
    }

    async function loadHbA1c() {
      try {
        const res = await apiFetch('/api/v1/hba1c/');
        const readings = res || [];
        const historyEl = $('#hba1cHistory');
        historyEl.innerHTML = readings.length > 0
          ? '<table>' + readings.map(r => `
            <tr>
              <td>${new Date(r.datetime).toLocaleString()}</td>
              <td>${r.value_percent}%</td>
              <td>${r.notes || '—'}</td>
              <td><button onclick="deleteHbA1c(${r.id})" class="delete-btn">Borrar</button></td>
            </tr>`).join('') + '</table>'
          : '<p>Sin registros.</p>';
      } catch (err) {
        showToast('Error al cargar HbA1c: ' + err.message, 'danger');
      }
    }

    async function addHbA1c() {
      const value_percent = parseFloat($('#hba1cInput').value);
      const notes = $('#hba1cNotes').value;
      if (!value_percent || value_percent < 3 || value_percent > 15) {
        showToast('HbA1c inválido (3–15%)', 'warning');
        return;
      }
      try {
        await apiFetch('/api/v1/hba1c/', {
          method: 'POST',
          body: JSON.stringify({
            datetime: new Date().toISOString(),
            value_percent: value_percent,
            notes: notes || null
          })
        });
        $('#hba1cInput').value = '';
        $('#hba1cNotes').value = '';
        showToast('HbA1c guardado', 'success');
        loadHbA1c();
      } catch (err) {
        showToast('Error al guardar HbA1c: ' + err.message, 'danger');
      }
    }

    async function deleteHbA1c(id) {
      if (!await showConfirm('¿Borrar este HbA1c?')) return;
      try {
        await apiFetch(`/api/v1/hba1c/${id}`, { method: 'DELETE' });
        showToast('HbA1c borrado', 'success');
        loadHbA1c();
      } catch (err) {
        showToast('Error al borrar: ' + err.message, 'danger');
      }
    }

    // Call on app init
    async function loadAllVitals() {
      loadWeights();
      loadPressures();
      loadHbA1c();
    }

    async function loadLatestMealPlan() {
      try {
        const plan = await apiFetch('/api/v1/meal-plan/latest');
        if (plan && plan.plan_data) {
          renderMealPlan(plan.plan_data);
        }
      } catch (err) {
        // Not found is fine
        if (!err.message.includes('404')) {
          console.error("Failed to load meal plan", err);
        }
      }
    }

    function renderMealPlan(planData) {
      const container = $('#mealPlanResult');
      container.style.display = 'block';
      
      let html = `<div style="background: rgba(167, 139, 250, 0.1); border: 1px solid var(--border-glass); padding: 15px; border-radius: var(--radius-lg); margin-bottom: 20px;">
        <h3 style="color: var(--accent-violet); margin-top: 0;">Resumen del Día (${planData.plan_date})</h3>
        <p style="margin: 5px 0;">Calorías Totales: <strong>${planData.daily_summary.total_calories} kcal</strong></p>
        <p style="margin: 5px 0;">Carbohidratos: <strong>${planData.daily_summary.total_carbs_g}g</strong></p>
      </div>`;

      planData.meals.forEach(meal => {
        const impactColors = { 'bajo': '#34d399', 'moderado': '#fbbf24', 'alto': '#fb7185' };
        html += `<div class="card" style="margin-bottom: 15px;">
          <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-glass); padding-bottom: 10px; margin-bottom: 10px;">
            <h4 style="margin: 0; text-transform: capitalize; color: var(--accent-indigo);">${meal.meal_type} <span style="color: var(--text-muted); font-size: 0.8rem;">(${meal.time_suggestion})</span></h4>
            <span style="font-size: 0.75rem; background: rgba(255,255,255,0.05); padding: 2px 8px; border-radius: 10px; color: ${impactColors[meal.glycemic_impact] || 'var(--text-primary)'}; border: 1px solid currentColor;">Impacto: ${meal.glycemic_impact}</span>
          </div>
          <p style="margin: 10px 0; font-weight: 500;">${meal.description}</p>
          <div style="display: flex; gap: 15px; font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 10px;">
            <span>🔥 ${meal.estimated_calories} kcal</span>
            <span>🌾 ${meal.estimated_carbs_g}g carbs</span>
          </div>
          <p style="font-size: 0.8rem; color: var(--text-muted); border-left: 2px solid var(--accent-cyan); padding-left: 8px;">${meal.reasoning}</p>
        </div>`;
      });

      if (planData.tips && planData.tips.length > 0) {
        html += `<div style="background: rgba(34, 211, 238, 0.05); padding: 15px; border-radius: var(--radius-lg); margin-top: 20px;">
          <h4 style="color: var(--accent-cyan); margin-top: 0; margin-bottom: 10px;">💡 Consejos de Hermes</h4>
          <ul style="margin: 0; padding-left: 20px; color: var(--text-secondary); font-size: 0.85rem;">
            ${planData.tips.map(tip => `<li style="margin-bottom: 5px;">${tip}</li>`).join('')}
          </ul>
        </div>`;
      }

      container.innerHTML = html;
    }

    // ===== PENDING PHOTO QUEUE =====
    let pendingPhotos = [];

    window.addToPendingQueue = function() {
      const cameraInput = $('#mealPhotoCamera');
      const galleryInput = $('#mealPhotoGallery');
      const notesInput = $('#mealNotes');

      // Get file from whichever input has one
      const photoInput = (cameraInput && cameraInput.files.length > 0) ? cameraInput :
                         (galleryInput && galleryInput.files.length > 0) ? galleryInput : null;

      if (!photoInput || photoInput.files.length === 0) {
        showToast('Selecciona una foto primero.', 'warning');
        return;
      }

      const file = photoInput.files[0];
      const now = new Date();
      const timeStr = now.getFullYear() + '-' +
        String(now.getMonth()+1).padStart(2,'0') + '-' +
        String(now.getDate()).padStart(2,'0') + 'T' +
        String(now.getHours()).padStart(2,'0') + ':' +
        String(now.getMinutes()).padStart(2,'0');

      const reader = new FileReader();
      reader.onload = function(e) {
        pendingPhotos.push({
          dataUrl: e.target.result,
          filename: file.name,
          datetime: timeStr,
          notes: notesInput ? notesInput.value : ''
        });
        renderPendingQueue();
        // Clear inputs
        if (cameraInput) cameraInput.value = '';
        if (galleryInput) galleryInput.value = '';
        const nameEl = $('#mealPhotoName');
        if (nameEl) nameEl.style.display = 'none';
        if (notesInput) notesInput.value = '';
        showToast('📋 ' + pendingPhotos.length + ' foto(s) en cola. Desliza hacia abajo para verlas.', 'success');
        // Auto-scroll to queue
        setTimeout(() => {
          const card = $('#pendingQueueCard');
          if (card) card.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 200);
      };
      reader.onerror = function() {
        showToast('Error al leer la imagen. Intenta de nuevo.', 'danger');
      };
      reader.readAsDataURL(file);
    };

    function renderPendingQueue() {
      const card = $('#pendingQueueCard');
      const grid = $('#pendingPhotosGrid');
      const countEl = $('#pendingCount');
      const toProcess = $('#pendingToProcess');
      const btnProcess = $('#btnProcessQueue');

      if (!card || !grid) return;

      if (pendingPhotos.length === 0) {
        card.style.display = 'none';
        if (countEl) { countEl.style.display = 'none'; countEl.textContent = '0'; }
        return;
      }

      card.style.display = 'block';
      if (countEl) { countEl.style.display = 'inline'; countEl.textContent = pendingPhotos.length; }
      if (toProcess) toProcess.textContent = pendingPhotos.length;

      grid.innerHTML = pendingPhotos.map((p, i) => `
        <div class="pending-photo-card" style="display:flex;gap:12px;align-items:center;background:var(--bg-glass);border:1px solid var(--border-glass);border-radius:12px;padding:10px;">
          <img src="${p.dataUrl}" style="width:60px;height:60px;object-fit:cover;border-radius:8px;">
          <div style="flex:1;min-width:0;">
            <input type="datetime-local" value="${p.datetime}" onchange="pendingPhotos[${i}].datetime=this.value"
                   style="width:100%;padding:8px;background:rgba(255,255,255,0.05);border:1px solid var(--border-glass);border-radius:8px;color:var(--text-primary);font-size:0.82rem;">
            <div style="font-size:0.72rem;color:var(--text-muted);margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${p.filename}</div>
          </div>
          <button onclick="pendingPhotos.splice(${i},1); renderPendingQueue();"
                  style="background:none;border:none;color:var(--accent-rose);font-size:1.2rem;cursor:pointer;padding:8px;min-width:44px;">✕</button>
        </div>
      `).join('');
    }

    window.processPendingQueue = async function() {
      if (pendingPhotos.length === 0) {
        showToast('No hay fotos pendientes.', 'warning');
        return;
      }

      const btn = $('#btnProcessQueue');
      const origText = btn.textContent;
      btn.disabled = true;
      const failed = [];
      let success = 0;

      for (let i = 0; i < pendingPhotos.length; i++) {
        const photo = pendingPhotos[i];
        btn.textContent = '⏳ Analizando ' + (i+1) + '/' + pendingPhotos.length + '...';

        try {
          const resp = await fetch(photo.dataUrl);
          const blob = await resp.blob();

          const formData = new FormData();
          formData.append('photo', blob, photo.filename);
          formData.append('meal_datetime', photo.datetime);
          if (photo.notes) formData.append('notes', photo.notes);

          const token = localStorage.getItem('azucar_token');
          const res = await fetch('/api/v1/meals/upload', {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + token },
            body: formData
          });

          if (res.ok) {
            const data = await res.json();
            // Check if AI returned fallback data (not real analysis)
            const foods = data.ai_analysis?.food_items || [];
            const isFallback = foods.some(f => f.includes('Fallback')) ||
                               (data.ai_analysis?.recommendation || '').includes('No se pudo conectar');
            if (isFallback) {
              failed.push(photo);
              // AI failed - discard the fake fallback entry the backend already saved
              try { await apiFetch(`/api/v1/meals/${data.id}`, { method: 'DELETE' }); } catch (e) {}
              showToast('⚠️ Foto ' + (i+1) + ' no reconocida. La IA no pudo identificar el alimento. Queda en cola.', 'warning');
            } else {
              success++;
            }
          } else {
            failed.push(photo);
            const errData = await res.json().catch(() => ({}));
            showToast('Error en foto ' + (i+1) + ': ' + (errData.detail || 'falló'), 'danger');
          }
        } catch (err) {
          failed.push(photo);
          showToast('Error: ' + err.message, 'danger');
        }
      }

      const total = pendingPhotos.length;
      // Keep failed photos in queue so user can retry
      pendingPhotos = failed;
      renderPendingQueue();
      if (success > 0) {
        await loadMealsData();
        showToast('✅ ' + success + '/' + total + ' fotos analizadas con éxito', 'success');
      }
      if (failed.length > 0) {
        showToast('⚠️ ' + failed.length + ' foto(s) no reconocidas permanecen en cola. Podés reintentarlas.', 'warning');
      }
      btn.textContent = origText;
      btn.disabled = false;
    };

    window.renderPendingQueue = renderPendingQueue;

    // Update filename display when photo selected
    function updateMealPhotoName(input) {
      const nameEl = $('#mealPhotoName');
      if (input.files.length > 0) {
        nameEl.textContent = '📎 ' + input.files[0].name;
        nameEl.style.display = 'block';
        // Clear the other input so we know which one was used
        const otherId = input.id === 'mealPhotoCamera' ? 'mealPhotoGallery' : 'mealPhotoCamera';
        const otherInput = $(`#${otherId}`);
        if (otherInput) otherInput.value = '';
        // Enable submit button
        $('#btnUploadMeal').disabled = false;
      }
    }

    // Attach change handlers to both inputs
    const cameraInput = $('#mealPhotoCamera');
    const galleryInput = $('#mealPhotoGallery');
    if (cameraInput) cameraInput.addEventListener('change', () => updateMealPhotoName(cameraInput));
    if (galleryInput) galleryInput.addEventListener('change', () => updateMealPhotoName(galleryInput));

    async function handleMealUpload(e) {
      e.preventDefault();
      const cameraInput = $('#mealPhotoCamera');
      const galleryInput = $('#mealPhotoGallery');
      const notesInput = $('#mealNotes');
      const btn = $('#btnUploadMeal');
      const nameEl = $('#mealPhotoName');

      // Get file from whichever input has one
      const photoInput = (cameraInput && cameraInput.files.length > 0) ? cameraInput :
                         (galleryInput && galleryInput.files.length > 0) ? galleryInput : null;

      if (!photoInput || photoInput.files.length === 0) {
        showToast('Por favor, selecciona una foto de comida.', 'warning');
        return;
      }

      const formData = new FormData();
      formData.append('photo', photoInput.files[0]);
      if (notesInput.value) {
        formData.append('notes', notesInput.value);
      }

      const originalText = btn.textContent;
      btn.textContent = '⏳ Analizando con Vision IA...';
      btn.disabled = true;

      try {
        const token = localStorage.getItem('azucar_token');
        const res = await fetch('/api/v1/meals/upload', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || 'Vision API failed');
        }

        const data = await res.json();
        const foods = data.ai_analysis?.food_items || [];
        const isFallback = foods.some(f => f.includes('Fallback')) ||
                           (data.ai_analysis?.recommendation || '').includes('No se pudo conectar');
        if (isFallback) {
          // AI failed - discard the fake fallback entry the backend already saved
          try { await apiFetch(`/api/v1/meals/${data.id}`, { method: 'DELETE' }); } catch (e) {}
          showToast('⚠️ La IA no pudo reconocer el alimento. Intentá con otra foto o usa la cola para reintentar.', 'warning');
        } else {
          showToast('Plato analizado con éxito', 'success');
        }
        if (cameraInput) cameraInput.value = '';
        if (galleryInput) galleryInput.value = '';
        if (nameEl) nameEl.style.display = 'none';
        notesInput.value = '';
        await loadMealsData();
      } catch (err) {
        showToast('Error al enviar la imagen: ' + err.message, 'danger');
      } finally {
        btn.textContent = originalText;
        btn.disabled = false;
      }
    }

    // ===== 4. FASTING TIMER =====
    let fastingState = {
      active: false,
      startTime: null,
      protocol: { fasting: 16, eating: 8 },
      intervalId: null
    };

    async function loadFastingState() {
      try {
        const active = await apiFetch('/api/v1/fasting/active');
        if (active) {
          const [fastHours, eatHours] = active.protocol.split(':').map(Number);
          fastingState = {
            active: true,
            startTime: new Date(active.start_time),
            protocol: { fasting: fastHours, eating: eatHours },
            intervalId: null
          };
          resumeFasting();
        } else {
          resetFastingUI();
        }
      } catch (err) {
        console.error("Failed to load fasting status", err);
      }
    }

    function selectProtocol(btn) {
      $$('.protocol-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      fastingState.protocol = {
        fasting: parseInt(btn.dataset.fasting),
        eating: parseInt(btn.dataset.eating)
      };
      if (!fastingState.active) {
        $('#fastEatWindow').textContent = `${fastingState.protocol.eating}h`;
      }
    }

    async function startFasting() {
      const dateVal = $('#fastingStartDate').value;
      const timeVal = $('#fastingStartTime').value;
      
      if (!dateVal || !timeVal) {
        showToast('Por favor, selecciona una fecha y hora de inicio válida', 'warning');
        return;
      }
      
      const startTime = new Date(`${dateVal}T${timeVal}:00`);
      const protocolStr = `${fastingState.protocol.fasting}:${fastingState.protocol.eating}`;
      
      try {
        const session = await apiFetch('/api/v1/fasting/start', {
          method: 'POST',
          body: JSON.stringify({
            start_time: startTime.toISOString(),
            protocol: protocolStr
          })
        });
        
        fastingState.active = true;
        fastingState.startTime = new Date(session.start_time);
        
        $('#btnStartFast').classList.add('hidden');
        $('#btnStopFast').classList.remove('hidden');
        $('#fastingTimeGroup').classList.add('hidden');
        
        const end = new Date(fastingState.startTime.getTime() + fastingState.protocol.fasting * 3600000);
        $('#fastStartTime').textContent = `${padZero(fastingState.startTime.getHours())}:${padZero(fastingState.startTime.getMinutes())}`;
        $('#fastEndTime').textContent = `${padZero(end.getHours())}:${padZero(end.getMinutes())}`;
        $('#fastEatWindow').textContent = `${fastingState.protocol.eating}h`;
        
        updateFastingTimer();
        fastingState.intervalId = setInterval(updateFastingTimer, 1000);
        showToast(`Ayuno iniciado (${protocolStr})`, 'success');
      } catch (err) {
        showToast('Error al iniciar ayuno: ' + err.message, 'danger');
      }
    }

    function resumeFasting() {
      $('#btnStartFast').classList.add('hidden');
      $('#btnStopFast').classList.remove('hidden');
      $('#fastingTimeGroup').classList.add('hidden');

      const start = fastingState.startTime;
      const end = new Date(start.getTime() + fastingState.protocol.fasting * 3600000);
      $('#fastStartTime').textContent = `${padZero(start.getHours())}:${padZero(start.getMinutes())}`;
      $('#fastEndTime').textContent = `${padZero(end.getHours())}:${padZero(end.getMinutes())}`;
      $('#fastEatWindow').textContent = `${fastingState.protocol.eating}h`;

      $$('.protocol-btn').forEach(b => {
        b.classList.remove('active');
        if (parseInt(b.dataset.fasting) === fastingState.protocol.fasting) {
          b.classList.add('active');
        }
      });

      if (fastingState.intervalId) clearInterval(fastingState.intervalId);
      updateFastingTimer();
      fastingState.intervalId = setInterval(updateFastingTimer, 1000);
    }

    async function stopFasting() {
      const endTime = new Date();
      try {
        await apiFetch('/api/v1/fasting/stop', {
          method: 'POST',
          body: JSON.stringify({
            end_time: endTime.toISOString(),
            completed: true
          })
        });
        
        fastingState.active = false;
        if (fastingState.intervalId) clearInterval(fastingState.intervalId);
        fastingState.intervalId = null;
        
        $('#btnStartFast').classList.remove('hidden');
        $('#btnStopFast').classList.add('hidden');
        showToast('Ayuno completado. ¡Buen trabajo!', 'success');
        resetFastingUI();
      } catch (err) {
        showToast('Error al finalizar el ayuno: ' + err.message, 'danger');
      }
    }

    function resetFastingUI() {
      fastingState.active = false;
      fastingState.startTime = null;
      if (fastingState.intervalId) clearInterval(fastingState.intervalId);
      fastingState.intervalId = null;
      
      $('#btnStartFast').classList.remove('hidden');
      $('#btnStopFast').classList.add('hidden');
      $('#fastingTimeGroup').classList.remove('hidden');
      
      const now = new Date();
      $('#fastingStartDate').value = getTodayStr();
      $('#fastingStartTime').value = `${padZero(now.getHours())}:${padZero(now.getMinutes())}`;
      
      $('#fastingTimerValue').textContent = '00:00:00';
      $('#fastingTimerLabel').textContent = 'Sin iniciar';
      $('#fastStartTime').textContent = '--:--';
      $('#fastEndTime').textContent = '--:--';
      $('#fastEatWindow').textContent = `${fastingState.protocol.eating}h`;
      
      const gauge = $('#fastingGaugeFill');
      gauge.style.strokeDashoffset = 534.07;
      gauge.style.stroke = 'var(--accent-indigo)';
    }

    function resetFasting() {
      resetFastingUI();
    }

    function updateFastingTimer() {
      if (!fastingState.active || !fastingState.startTime) return;

      const now = new Date();
      const elapsed = now - fastingState.startTime;
      const totalMs = fastingState.protocol.fasting * 3600000;
      const remaining = totalMs - elapsed;

      if (remaining <= 0) {
        $('#fastingTimerValue').textContent = '✅';
        $('#fastingTimerLabel').textContent = 'Ayuno Completado';
        if (fastingState.intervalId) clearInterval(fastingState.intervalId);
        playAlarmSound();
        showToast('🎉 Ventana de ayuno finalizada. Puedes ingerir alimentos.', 'success');

        const gauge = $('#fastingGaugeFill');
        gauge.style.strokeDashoffset = 0;
        gauge.style.stroke = 'var(--accent-emerald)';
        return;
      }

      const hrs = Math.floor(remaining / 3600000);
      const mins = Math.floor((remaining % 3600000) / 60000);
      const secs = Math.floor((remaining % 60000) / 1000);

      $('#fastingTimerValue').textContent = `${padZero(hrs)}:${padZero(mins)}:${padZero(secs)}`;

      const pct = elapsed / totalMs;
      if (pct < 0.5) {
        $('#fastingTimerLabel').textContent = '🔥 Quemando glucógeno...';
      } else if (pct < 0.75) {
        $('#fastingTimerLabel').textContent = '⚡ Entrando en cetosis leve';
      } else {
        $('#fastingTimerLabel').textContent = '🏆 Ayuno profundo — ¡Casi lo logras!';
      }

      const circumference = 2 * Math.PI * 85;
      const offset = circumference * (1 - pct);
      const gauge = $('#fastingGaugeFill');
      gauge.style.strokeDashoffset = offset;

      if (pct < 0.5) gauge.style.stroke = 'var(--accent-indigo)';
      else if (pct < 0.75) gauge.style.stroke = 'var(--accent-violet)';
      else gauge.style.stroke = 'var(--accent-emerald)';
    }

    // ===== 5. ALARMS SYSTEM (HYBRID LOCAL/PUSH) =====
    let alarmIntervals = { postprandial: null, hydration: null, metformin: null };
    let alarmEndTimes = { postprandial: null, hydration: null, metformin: null };

    async function loadAlarms() {
      try {
        const dbAlarms = await apiFetch('/api/v1/alarms/');
        // Sync local clocks with database configs
        let dbHydrationActive = false;
        dbAlarms.forEach(alarm => {
          if (alarm.type === 'metformina' && alarm.is_active) {
            $('#metforminTime').value = alarm.config_time;
            restoreLocalMetformin(alarm.config_time);
          }
          if (alarm.type === 'hidratacion' && alarm.is_active) {
            dbHydrationActive = true;
          }
        });
        
        // Restore local counter alarms
        const ppEnd = localStorage.getItem('azucar_alarm_pp');
        if (ppEnd && parseInt(ppEnd) > Date.now()) {
          alarmEndTimes.postprandial = parseInt(ppEnd);
          $('#btnAteNow').classList.add('hidden');
          $('#btnCancelPP').classList.remove('hidden');
          $('#alarmPostprandial').classList.add('active-alarm');
          if (alarmIntervals.postprandial) clearInterval(alarmIntervals.postprandial);
          alarmIntervals.postprandial = setInterval(updatePostprandialTimer, 1000);
          updatePostprandialTimer();
        }
        
        const hydEnd = localStorage.getItem('azucar_alarm_hydration');
        if ((hydEnd && parseInt(hydEnd) > Date.now()) || dbHydrationActive) {
          if (hydEnd && parseInt(hydEnd) > Date.now()) {
            alarmEndTimes.hydration = parseInt(hydEnd);
          } else if (dbHydrationActive) {
            // Restore timer even if localStorage expired
            alarmEndTimes.hydration = Date.now() + (2 * 60 * 60 * 1000);
            localStorage.setItem('azucar_alarm_hydration', alarmEndTimes.hydration);
          }
          $('#btnStartHydration').classList.add('hidden');
          $('#btnCancelHydration').classList.remove('hidden');
          $('#alarmHydration').classList.add('active-alarm');
          if (alarmIntervals.hydration) clearInterval(alarmIntervals.hydration);
          alarmIntervals.hydration = setInterval(updateHydrationTimer, 1000);
          updateHydrationTimer();
        }
      } catch (err) {
        console.error("Failed to load alarms", err);
      }
    }

    async function startPostprandialAlarm() {
      const twoHoursMs = 2 * 60 * 60 * 1000;
      alarmEndTimes.postprandial = Date.now() + twoHoursMs;
      localStorage.setItem('azucar_alarm_pp', alarmEndTimes.postprandial);

      $('#btnAteNow').classList.add('hidden');
      $('#btnCancelPP').classList.remove('hidden');
      $('#alarmPostprandial').classList.add('active-alarm');

      showToast('⏱️ Temporizador de 2 horas activado para medición Postprandial.', 'info');
      
      // Register with the database for Server-Side Push fallback
      const alertTime = new Date(alarmEndTimes.postprandial);
      try {
        await apiFetch('/api/v1/alarms/', {
          method: 'POST',
          body: JSON.stringify({
            type: 'postprandial',
            config_time: `${padZero(alertTime.getHours())}:${padZero(alertTime.getMinutes())}`,
            is_active: true
          })
        });
      } catch {}

      if (alarmIntervals.postprandial) clearInterval(alarmIntervals.postprandial);
      alarmIntervals.postprandial = setInterval(updatePostprandialTimer, 1000);
      updatePostprandialTimer();
    }

    function updatePostprandialTimer() {
      const end = alarmEndTimes.postprandial;
      if (!end) return;

      const remaining = end - Date.now();
      if (remaining <= 0) {
        clearInterval(alarmIntervals.postprandial);
        alarmIntervals.postprandial = null;
        alarmEndTimes.postprandial = null;
        localStorage.removeItem('azucar_alarm_pp');

        $('#postprandialTimerDisplay').textContent = '¡AHORA!';
        $('#postprandialTimerDisplay').style.color = 'var(--accent-rose)';
        $('#alarmPostprandial').classList.remove('active-alarm');
        $('#alarmPostprandial').classList.add('ringing');

        playAlarmSound();
        showToast('🩸 ¡Pasaron 2 horas! Mide tu nivel de glucosa postprandial.', 'danger');

        setTimeout(() => {
          $('#alarmPostprandial').classList.remove('ringing');
          $('#postprandialTimerDisplay').style.color = 'var(--text-muted)';
          $('#postprandialTimerDisplay').textContent = '--:--';
          $('#btnAteNow').classList.remove('hidden');
          $('#btnCancelPP').classList.add('hidden');
        }, 15000);
        return;
      }

      const mins = Math.floor(remaining / 60000);
      const secs = Math.floor((remaining % 60000) / 1000);
      $('#postprandialTimerDisplay').textContent = `${padZero(mins)}:${padZero(secs)}`;
      $('#postprandialTimerDisplay').style.color = 'var(--accent-amber)';
    }

    async function cancelPostprandialAlarm() {
      if (alarmIntervals.postprandial) clearInterval(alarmIntervals.postprandial);
      alarmIntervals.postprandial = null;
      alarmEndTimes.postprandial = null;
      localStorage.removeItem('azucar_alarm_pp');

      $('#postprandialTimerDisplay').textContent = '--:--';
      $('#postprandialTimerDisplay').style.color = 'var(--text-muted)';
      $('#btnAteNow').classList.remove('hidden');
      $('#btnCancelPP').classList.add('hidden');
      $('#alarmPostprandial').classList.remove('active-alarm');
      
      // Deactivate on DB
      try {
        await apiFetch('/api/v1/alarms/', {
          method: 'POST',
          body: JSON.stringify({
            type: 'postprandial',
            config_time: '00:00',
            is_active: false
          })
        });
      } catch {}
      
      showToast('Alarma postprandial desactivada', 'info');
    }

    // Hydration Timer
    async function startHydrationAlarm() {
      const twoHoursMs = 2 * 60 * 60 * 1000;
      alarmEndTimes.hydration = Date.now() + twoHoursMs;
      localStorage.setItem('azucar_alarm_hydration', alarmEndTimes.hydration);

      $('#btnStartHydration').classList.add('hidden');
      $('#btnCancelHydration').classList.remove('hidden');
      $('#alarmHydration').classList.add('active-alarm');

      showToast('💧 Recordatorio de hidratación activado (2 horas).', 'success');

      if (alarmIntervals.hydration) clearInterval(alarmIntervals.hydration);
      alarmIntervals.hydration = setInterval(updateHydrationTimer, 1000);
      updateHydrationTimer();

      // Register hydration alarm in DB for server-side push notification
      try {
        const triggerTime = new Date(Date.now() + twoHoursMs);
        const hh = String(triggerTime.getHours()).padStart(2, '0');
        const mm = String(triggerTime.getMinutes()).padStart(2, '0');
        await apiFetch('/api/v1/alarms/', {
          method: 'POST',
          body: JSON.stringify({ type: 'hidratacion', config_time: `${hh}:${mm}`, is_active: true })
        });
      } catch (err) {
        console.error('Failed to register hydration alarm in DB:', err);
      }
    }

    function updateHydrationTimer() {
      const end = alarmEndTimes.hydration;
      if (!end) return;

      const remaining = end - Date.now();
      if (remaining <= 0) {
        playAlarmSound();
        showToast('💧 ¡Hora de hidratarte! Bebe un vaso de agua pura.', 'warning');
        $('#alarmHydration').classList.add('ringing');

        setTimeout(() => {
          $('#alarmHydration').classList.remove('ringing');
        }, 5000);

        // Auto restart local cycle + re-register in DB
        const twoHoursMs = 2 * 60 * 60 * 1000;
        alarmEndTimes.hydration = Date.now() + twoHoursMs;
        localStorage.setItem('azucar_alarm_hydration', alarmEndTimes.hydration);
        // Re-register in DB for next push notification
        (async () => {
          try {
            const triggerTime = new Date(Date.now() + twoHoursMs);
            const hh = String(triggerTime.getHours()).padStart(2, '0');
            const mm = String(triggerTime.getMinutes()).padStart(2, '0');
            await apiFetch('/api/v1/alarms/', {
              method: 'POST',
              body: JSON.stringify({ type: 'hidratacion', config_time: `${hh}:${mm}`, is_active: true })
            });
          } catch (err) {
            console.error('Failed to re-register hydration alarm:', err);
          }
        })();
        return;
      }

      const hrs = Math.floor(remaining / 3600000);
      const mins = Math.floor((remaining % 3600000) / 60000);
      const secs = Math.floor((remaining % 60000) / 1000);

      $('#hydrationTimerDisplay').textContent = hrs > 0 
        ? `${hrs}:${padZero(mins)}:${padZero(secs)}`
        : `${padZero(mins)}:${padZero(secs)}`;
      $('#hydrationTimerDisplay').style.color = 'var(--accent-cyan)';
    }

    async function cancelHydrationAlarm() {
      if (alarmIntervals.hydration) clearInterval(alarmIntervals.hydration);
      alarmIntervals.hydration = null;
      alarmEndTimes.hydration = null;
      localStorage.removeItem('azucar_alarm_hydration');

      // Deactivate in DB
      try {
        await apiFetch('/api/v1/alarms/', {
          method: 'POST',
          body: JSON.stringify({ type: 'hidratacion', config_time: '00:00', is_active: false })
        });
      } catch (err) {
        console.error('Failed to deactivate hydration alarm in DB:', err);
      }

      $('#hydrationTimerDisplay').textContent = '--:--';
      $('#hydrationTimerDisplay').style.color = 'var(--text-muted)';
      $('#btnStartHydration').classList.remove('hidden');
      $('#btnCancelHydration').classList.add('hidden');
      $('#alarmHydration').classList.remove('active-alarm');
      showToast('Alarma de hidratación desactivada', 'info');
    }

    // Metformin Daily Alarms
    async function setMetforminAlarm() {
      const timeVal = $('#metforminTime').value;
      if (!timeVal) {
        showToast('Configura una hora válida', 'warning');
        return;
      }

      try {
        await apiFetch('/api/v1/alarms/', {
          method: 'POST',
          body: JSON.stringify({
            type: 'metformina',
            config_time: timeVal,
            is_active: true
          })
        });
        showToast(`💊 Alarma de Metformina programada a las ${timeVal}`, 'success');
        restoreLocalMetformin(timeVal);
      } catch (err) {
        showToast('Error al programar recordatorio en DB', 'danger');
      }
    }

    function restoreLocalMetformin(timeVal) {
      const [h, m] = timeVal.split(':').map(Number);
      const now = new Date();
      let target = new Date();
      target.setHours(h, m, 0, 0);
      if (target <= now) target.setDate(target.getDate() + 1);

      alarmEndTimes.metformin = target.getTime();

      $('#btnSetMetformin').classList.add('hidden');
      $('#btnCancelMetformin').classList.remove('hidden');
      $('#alarmMetformin').classList.add('active-alarm');

      if (alarmIntervals.metformin) clearInterval(alarmIntervals.metformin);
      alarmIntervals.metformin = setInterval(updateMetforminTimer, 1000);
      updateMetforminTimer();
    }

    function updateMetforminTimer() {
      const end = alarmEndTimes.metformin;
      if (!end) return;

      const remaining = end - Date.now();
      if (remaining <= 0) {
        playAlarmSound();
        showToast('💊 ¡Hora de la Metformina! Recuérdala acompañar con comida.', 'danger');
        $('#alarmMetformin').classList.add('ringing');

        setTimeout(() => {
          $('#alarmMetformin').classList.remove('ringing');
          // Re-schedule for next day
          const timeVal = $('#metforminTime').value;
          restoreLocalMetformin(timeVal);
        }, 10000);
        return;
      }

      const hrs = Math.floor(remaining / 3600000);
      const mins = Math.floor((remaining % 3600000) / 60000);
      const secs = Math.floor((remaining % 60000) / 1000);

      $('#metforminTimerDisplay').textContent = `${hrs}:${padZero(mins)}:${padZero(secs)}`;
      $('#metforminTimerDisplay').style.color = 'var(--accent-violet)';
    }

    async function cancelMetforminAlarm() {
      try {
        await apiFetch('/api/v1/alarms/', {
          method: 'POST',
          body: JSON.stringify({
            type: 'metformina',
            config_time: '00:00',
            is_active: false
          })
        });
        
        if (alarmIntervals.metformin) clearInterval(alarmIntervals.metformin);
        alarmIntervals.metformin = null;
        alarmEndTimes.metformin = null;

        $('#metforminTimerDisplay').textContent = '--:--';
        $('#metforminTimerDisplay').style.color = 'var(--text-muted)';
        $('#btnSetMetformin').classList.remove('hidden');
        $('#btnCancelMetformin').classList.add('hidden');
        $('#alarmMetformin').classList.remove('active-alarm');
        showToast('Alarma de Metformina desactivada', 'info');
      } catch (err) {
        showToast('Error al desactivar la alarma', 'danger');
      }
    }

    // ===== 6. HABITS CHECKLIST =====
    async function loadHabits() {
      try {
        const habits = await apiFetch('/api/v1/habits/today');
        renderHabitsUI(habits);
      } catch (err) {
        console.error("Failed to load habits", err);
      }
    }

    async function toggleHabit(el) {
      const habitId = el.dataset.habit;
      try {
        await apiFetch('/api/v1/habits/toggle', {
          method: 'POST',
          body: JSON.stringify({
            date: getTodayStr(),
            habit_key: habitId
          })
        });
        await loadHabits();
      } catch (err) {
        showToast('Error al registrar hábito', 'danger');
      }
    }

    function renderHabitsUI(habits) {
      const items = $$('.habit-item');
      let completed = 0;

      items.forEach(item => {
        const id = item.dataset.habit;
        if (habits[id]) {
          item.classList.add('completed');
          item.querySelector('.habit-checkbox').innerHTML = '✓';
          completed++;
        } else {
          item.classList.remove('completed');
          item.querySelector('.habit-checkbox').innerHTML = '';
        }
      });

      const total = items.length;
      const pct = total > 0 ? Math.round((completed / total) * 100) : 0;
      $('#habitsProgressPct').textContent = `${pct}%`;
      $('#habitsProgressFill').style.width = `${pct}%`;

      if (pct === 100 && completed > 0) {
        showToast('🏆 ¡Felicidades! Completaste todos tus hábitos diarios.', 'success');
      }
    }

    // ===== 6.5. MEDICATIONS / SUPPLEMENTS =====
    let allMedications = [];
    let medicationsFilter = 'all';
    const DAY_LABELS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];

    async function loadMedications() {
      try {
        allMedications = await apiFetch('/api/v1/medications/');
        renderMedicationsList();
      } catch (err) {
        console.error("Failed to load medications", err);
      }
    }

    function filterMedicationsByKind(kind) {
      medicationsFilter = kind;
      $('#medFilterAll').classList.toggle('btn-primary', kind === 'all');
      $('#medFilterMedication').classList.toggle('btn-primary', kind === 'medication');
      $('#medFilterSupplement').classList.toggle('btn-primary', kind === 'supplement');
      renderMedicationsList();
    }

    function renderMedicationsList() {
      const container = $('#medicationsList');
      const items = medicationsFilter === 'all'
        ? allMedications
        : allMedications.filter(m => m.kind === medicationsFilter);

      if (items.length === 0) {
        container.innerHTML = `<p style="color:var(--text-muted); text-align:center;">No hay medicamentos configurados aún.</p>`;
        return;
      }

      container.innerHTML = '';
      items.forEach(med => {
        const days = med.days_of_week.slice().sort().map(d => DAY_LABELS[d]).join(', ');
        const card = document.createElement('div');
        card.className = 'habit-item';
        card.style.cursor = 'default';
        card.innerHTML = `
          <div class="habit-content-side">
            <span class="tab-icon">${med.kind === 'medication' ? '💊' : '🌿'}</span>
            <div>
              <div class="habit-text">${med.name}${med.dosage ? ' — ' + med.dosage : ''}</div>
              <div style="font-size:0.75rem; color:var(--text-muted);">${med.times.join(', ')} · ${days}</div>
            </div>
          </div>
          <div style="display:flex;gap:4px;">
            <button class="delete-btn" onclick="editMedication(${med.id})" title="Editar" style="font-size:0.9rem;">✏️</button>
            <button class="delete-btn" onclick="deleteMedication(${med.id})" title="Eliminar">🗑️</button>
          </div>
        `;
        container.appendChild(card);
      });
    }

    let editingMedicationId = null;

    window.editMedication = function(id) {
      const med = allMedications.find(m => m.id === id);
      if (!med) return;
      editingMedicationId = id;
      $('#medName').value = med.name;
      $('#medKind').value = med.kind;
      $('#medDosage').value = med.dosage || '';
      $('#medTimesContainer').innerHTML = med.times.map(t =>
        `<input type="time" class="form-input med-time-input" style="width:120px;" value="${t}">`
      ).join('');
      // Set day checkboxes
      $$('.med-day-checkbox').forEach(cb => { cb.checked = med.days_of_week.includes(parseInt(cb.value)); });
      $('#btnSaveMed').textContent = '💾 Guardar Cambios';
      window.scrollTo(0, $('#sectionMedications').offsetTop);
    };

    function addMedTimeInput() {
      const container = $('#medTimesContainer');
      const input = document.createElement('input');
      input.type = 'time';
      input.className = 'form-input med-time-input';
      input.style.width = '120px';
      input.value = '08:00';
      container.appendChild(input);
    }

    async function createMedication(event) {
      event.preventDefault();

      const times = Array.from($$('.med-time-input')).map(el => el.value).filter(Boolean);
      const daysOfWeek = Array.from($$('.med-day-checkbox')).filter(el => el.checked).map(el => parseInt(el.value));

      if (times.length === 0 || daysOfWeek.length === 0) {
        showToast('Agrega al menos un horario y un día activo.', 'warning');
        return;
      }

      const isEdit = !!editingMedicationId;
      const method = isEdit ? 'PUT' : 'POST';
      const url = isEdit ? `/api/v1/medications/${editingMedicationId}` : '/api/v1/medications/';

      try {
        await apiFetch(url, {
          method,
          body: JSON.stringify({
            name: $('#medName').value,
            kind: $('#medKind').value,
            dosage: $('#medDosage').value || null,
            times,
            days_of_week: daysOfWeek,
            is_active: true
          })
        });
        showToast(isEdit ? 'Medicamento actualizado' : 'Medicamento agregado', 'success');
        // Reset form
        editingMedicationId = null;
        $('#medicationForm').reset();
        $('#btnSaveMed').textContent = '➕ Agregar Medicamento';
        $('#medTimesContainer').innerHTML = '<input type="time" class="form-input med-time-input" style="width:120px;" value="08:00">';
        $$('.med-day-checkbox').forEach(el => el.checked = true);
        await loadMedications();
        await loadTodayDoses();
      } catch (err) {
        showToast('Error: ' + err.message, 'danger');
      }
    }

    async function deleteMedication(id) {
      if (!await showConfirm('¿Seguro que deseas eliminar este medicamento/suplemento?')) return;
      try {
        await apiFetch(`/api/v1/medications/${id}`, { method: 'DELETE' });
        showToast('Eliminado con éxito', 'success');
        await loadMedications();
        await loadTodayDoses();
      } catch (err) {
        showToast('Error al eliminar: ' + err.message, 'danger');
      }
    }

    async function loadTodayDoses() {
      try {
        const slots = await apiFetch('/api/v1/medications/today');
        renderTodayDoses(slots);
      } catch (err) {
        console.error("Failed to load today's doses", err);
      }
    }

    function renderTodayDoses(slots) {
      const container = $('#todayDosesList');
      if (slots.length === 0) {
        container.innerHTML = `<p style="color:var(--text-muted); text-align:center;">No hay dosis programadas para hoy.</p>`;
        return;
      }

      container.innerHTML = '';
      slots.forEach(slot => {
        const card = document.createElement('div');
        card.className = 'habit-item';
        card.style.cursor = 'default';
        if (slot.status === 'taken') card.classList.add('completed');

        const statusLabel = slot.status === 'taken' ? ' (Tomado)' : slot.status === 'skipped' ? ' (Omitido)' : '';
        card.innerHTML = `
          <div class="habit-content-side">
            <span class="tab-icon">${slot.kind === 'medication' ? '💊' : '🌿'}</span>
            <span class="habit-text">${slot.scheduled_time} — ${slot.name}${slot.dosage ? ' (' + slot.dosage + ')' : ''}${statusLabel}</span>
          </div>
          <div style="display:flex; gap:6px;">
            <button class="btn btn-sm btn-success" onclick="markDose(${slot.medication_id}, '${slot.scheduled_time}', 'taken')">✓</button>
            <button class="btn btn-sm btn-danger" onclick="markDose(${slot.medication_id}, '${slot.scheduled_time}', 'skipped')">✗</button>
          </div>
        `;
        container.appendChild(card);
      });
    }

    async function markDose(medicationId, time, status) {
      try {
        await apiFetch('/api/v1/medications/log', {
          method: 'POST',
          body: JSON.stringify({
            medication_id: medicationId,
            date: getTodayStr(),
            scheduled_time: time,
            status
          })
        });
        await loadTodayDoses();
      } catch (err) {
        showToast('Error al registrar dosis: ' + err.message, 'danger');
      }
    }

    // ===== 7. AI HERMES ASSISTANT =====
    let chatHistory = [];

    function appendChatMessage(text, sender) {
      const container = $('#chatMessages');
      const msg = document.createElement('div');
      msg.className = `chat-msg ${sender}`;
      msg.textContent = text;
      container.appendChild(msg);
      container.scrollTop = container.scrollHeight;
    }

    async function handleChatSubmit(e) {
      e.preventDefault();
      const input = $('#chatInput');
      const message = input.value.trim();
      if (!message) return;
      
      appendChatMessage(message, 'user');
      input.value = '';
      
      const btn = $('#btnSendChat');
      btn.disabled = true;
      
      try {
        const res = await apiFetch('/api/v1/ai/chat', {
          method: 'POST',
          body: JSON.stringify({
            message: message,
            history: chatHistory
          })
        });
        
        appendChatMessage(res.response, 'bot');
        chatHistory.push({ role: 'user', content: message });
        chatHistory.push({ role: 'assistant', content: res.response });
        
        if (chatHistory.length > 20) chatHistory = chatHistory.slice(-20);
      } catch (err) {
        appendChatMessage('Error al conectar con Hermes. Por favor intenta más tarde.', 'bot');
      } finally {
        btn.disabled = false;
      }
    }

    // ===== PUSH NOTIFICATIONS REGISTRATION =====
    async function requestPushNotifications() {
      if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        showToast('Las notificaciones Push no son soportadas en este navegador.', 'warning');
        return;
      }
      
      const btn = $('#btnEnablePush');
      btn.disabled = true;
      
      try {
        const permission = await Notification.requestPermission();
        if (permission !== 'granted') {
          showToast('Permiso de notificación denegado.', 'warning');
          btn.disabled = false;
          return;
        }
        
        const registration = await navigator.serviceWorker.ready;
        
        // Fetch VAPID key from backend
        const keyRes = await apiFetch('/api/v1/notifications/key');
        if (!keyRes.public_key) {
          throw new Error('VAPID public key empty');
        }
        
        // Convert base64 url-safe VAPID key to UInt8Array
        const convertedKey = urlBase64ToUint8Array(keyRes.public_key);
        
        const subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: convertedKey
        });
        
        // Send subscription object to backend
        await apiFetch('/api/v1/notifications/subscribe', {
          method: 'POST',
          body: JSON.stringify(subscription)
        });
        
        showToast('🔔 Alertas en tiempo real activadas.', 'success');
        btn.textContent = '✅ Alertas Activas';
        btn.style.color = 'var(--text-muted)';
        
        // Trigger a test notification
        await apiFetch('/api/v1/notifications/test', { method: 'POST' }).catch(() => {});
      } catch (err) {
        console.error(err);
        showToast('Error al activar notificaciones Push.', 'danger');
        btn.disabled = false;
      }
    }

    function urlBase64ToUint8Array(base64String) {
      const padding = '='.repeat((4 - base64String.length % 4) % 4);
      const base64 = (base64String + padding)
        .replace(/\-/g, '+')
        .replace(/_/g, '/');
      const rawData = window.atob(base64);
      const outputArray = new Uint8Array(rawData.length);
      for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
      }
      return outputArray;
    }

    // ===== SWIPE GESTURES FOR TAB NAVIGATION =====
    let touchStartX = 0, touchStartY = 0;
    const SWIPE_THRESHOLD = 60;

    document.addEventListener('touchstart', (e) => {
      touchStartX = e.changedTouches[0].screenX;
      touchStartY = e.changedTouches[0].screenY;
    }, { passive: true });

    document.addEventListener('touchend', (e) => {
      if (window._sheetOpen) return; // Don't swipe when sheet is open
      const diffX = e.changedTouches[0].screenX - touchStartX;
      const diffY = e.changedTouches[0].screenY - touchStartY;
      if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > SWIPE_THRESHOLD) {
        const TAB_ORDER = ['registry', 'nutrition', 'fasting'];
        const activeTab = document.querySelector('.bottom-nav-item.active');
        if (activeTab) {
          const currentIdx = TAB_ORDER.indexOf(activeTab.dataset.tab);
          if (currentIdx >= 0) {
            if (diffX < 0 && currentIdx < TAB_ORDER.length - 1) {
              navigateToTab(TAB_ORDER[currentIdx + 1]);
            } else if (diffX > 0 && currentIdx > 0) {
              navigateToTab(TAB_ORDER[currentIdx - 1]);
            }
          }
        }
      }
    }, { passive: true });

    // Track bottom sheet state for swipe guard
    const _sheetEl = $('#moreSheet');
    if (_sheetEl) {
      window._sheetOpen = false;
      const observer = new MutationObserver(() => {
        window._sheetOpen = _sheetEl.classList.contains('open');
      });
      observer.observe(_sheetEl, { attributes: true, attributeFilter: ['class'] });
    }

    // ===== KEYBOARD-AWARE LAYOUT (Chat) =====
    if ('visualViewport' in window) {
      window.visualViewport.addEventListener('resize', () => {
        const diff = window.innerHeight - window.visualViewport.height;
        const bottomNav = document.querySelector('.bottom-nav');
        const chatMessages = $('#chatMessages');

        if (diff > 100) {
          // Keyboard likely visible
          if (bottomNav) bottomNav.style.display = 'none';
          if (chatMessages) {
            chatMessages.style.maxHeight = `${window.visualViewport.height - 200}px`;
          }
        } else {
          if (bottomNav) bottomNav.style.display = '';
          if (chatMessages) {
            chatMessages.style.maxHeight = '';
          }
        }
      });
    }

    // ===== HAPTIC FEEDBACK =====
    // Light haptic on button taps
    document.addEventListener('click', (e) => {
      const target = e.target.closest('.btn, .bottom-nav-item, .sheet-item, .nav-tab, .protocol-btn, .habit-item');
      if (target && navigator.vibrate) {
        navigator.vibrate(10);
      }
    }, { passive: true });

    // Stronger haptic on delete actions
    const origShowConfirm = window.showConfirm;
    // haptic is handled by the global showConfirm defined in init

    // Listen for SW reload messages
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('message', (e) => {
        if (e.data && e.data.type === 'RELOAD_APP') {
          window.location.reload();
        }
      });
    }

    // ===== FORCE UPDATE =====
    window.forceUpdateApp = async function() {
      const btn = $('#btnUpdateApp');
      if (!btn) return;
      const origText = btn.textContent;
      btn.textContent = '⏳ Actualizando...';
      btn.disabled = true;

      try {
        // Tell service worker to update and clear caches
        if ('serviceWorker' in navigator) {
          const reg = await navigator.serviceWorker.ready;
          if (reg.waiting) {
            reg.waiting.postMessage({ type: 'FORCE_UPDATE' });
          } else if (reg.active) {
            reg.active.postMessage({ type: 'FORCE_UPDATE' });
          }
          // Also unregister to be safe
          const registrations = await navigator.serviceWorker.getRegistrations();
          for (const r of registrations) {
            await r.unregister();
          }
        }

        // Clear all caches directly
        if ('caches' in window) {
          const keys = await caches.keys();
          await Promise.all(keys.map(k => caches.delete(k)));
        }

        // Hard reload after short delay
        setTimeout(() => {
          window.location.href = '/';
        }, 300);
      } catch (err) {
        btn.textContent = origText;
        btn.disabled = false;
        // Fallback: just reload
        window.location.reload(true);
      }
    };

    // ===== ZOOM CONTROLS =====
    let currentZoom = 100;
    const ZOOM_STEP = 10;
    const ZOOM_MIN = 70;
    const ZOOM_MAX = 200;

    window.zoomIn = function() {
      currentZoom = Math.min(currentZoom + ZOOM_STEP, ZOOM_MAX);
      applyZoom();
    };

    window.zoomOut = function() {
      currentZoom = Math.max(currentZoom - ZOOM_STEP, ZOOM_MIN);
      applyZoom();
    };

    window.zoomReset = function() {
      currentZoom = 100;
      applyZoom();
    };

    function applyZoom() {
      document.documentElement.style.fontSize = currentZoom + '%';
      const zoomEl = $('#zoomLevel');
      if (zoomEl) zoomEl.textContent = currentZoom + '%';
      localStorage.setItem('azucar_zoom', currentZoom);
    }

    // Restore saved zoom
    const savedZoom = localStorage.getItem('azucar_zoom');
    if (savedZoom) {
      currentZoom = parseInt(savedZoom);
      setTimeout(applyZoom, 100);
    }

    // ===== MAIN INITIALIZER =====
    function init() {
      const token = localStorage.getItem('azucar_token');
      if (token) {
        $('#authOverlay').classList.add('hidden');
        initializeSession();
      } else {
        $('#authOverlay').classList.remove('hidden');
      }

      // Confirm modal setup
      window.showConfirm = function(message) {
        return new Promise((resolve) => {
          const modal = $('#confirmModal');
          if (!modal) { resolve(confirm(message)); return; }
          $('#confirmMessage').textContent = message;
          modal.classList.remove('hidden');
          $('#confirmCancel').focus();

          const cleanup = (result) => {
            modal.classList.add('hidden');
            document.removeEventListener('keydown', onKeydown);
            resolve(result);
          };

          const onKeydown = (e) => {
            if (e.key === 'Escape') cleanup(false);
          };

          $('#confirmOk').onclick = () => cleanup(true);
          $('#confirmCancel').onclick = () => cleanup(false);
          document.addEventListener('keydown', onKeydown);

          // Backdrop click to cancel
          modal.addEventListener('click', (e) => {
            if (e.target === modal) cleanup(false);
          });
        });
      };

      // Network status indicator
      const networkStatus = $('#networkStatus');
      if (networkStatus) {
        window.addEventListener('online', () => {
          networkStatus.classList.add('hidden');
          networkStatus.classList.remove('show');
        });
        window.addEventListener('offline', () => {
          networkStatus.classList.remove('hidden');
          networkStatus.classList.add('show');
          showToast('📡 Sin conexión a internet', 'warning');
        });
      }

      // Register Service Worker
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js')
          .then(reg => {
            console.log('Service Worker Registered successfully', reg.scope);
            // If already subscribed, update push button state
            reg.pushManager.getSubscription().then(sub => {
              if (sub) {
                const btn = $('#btnEnablePush');
                btn.textContent = '✅ Alertas Activas';
                btn.style.color = 'var(--text-muted)';
                btn.disabled = true;
              }
            });
          })
          .catch(err => console.error('Service Worker registration failed:', err));
      }
    }

    // Window aliases for inline onclick handlers
    window.handleLogout = handleLogout;
    window.toggleAuthMode = toggleAuthMode;
    window.togglePasswordVisibility = togglePasswordVisibility;
    window.testAIConnection = testAIConnection;
    window.exportFHIRBundle = exportFHIRBundle;
    window.selectProtocol = selectProtocol;
    window.startFasting = startFasting;
    window.stopFasting = stopFasting;
    window.resetFasting = resetFasting;
    window.startPostprandialAlarm = startPostprandialAlarm;
    window.cancelPostprandialAlarm = cancelPostprandialAlarm;
    window.startHydrationAlarm = startHydrationAlarm;
    window.cancelHydrationAlarm = cancelHydrationAlarm;
    window.setMetforminAlarm = setMetforminAlarm;
    window.cancelMetforminAlarm = cancelMetforminAlarm;
    window.addMedTimeInput = addMedTimeInput;
    window.filterMedicationsByKind = filterMedicationsByKind;
    window.openMealEditModal = openMealEditModal;
    window.closeMealEditModal = closeMealEditModal;
    window.saveMealEdit = saveMealEdit;
    window.correctMealWithAI = correctMealWithAI;
    window.toggleHabit = toggleHabit;
    window.requestPushNotifications = requestPushNotifications;
    window.handleProviderChange = handleProviderChange;
    window.handleConfigSave = handleConfigSave;
    window.handleChatSubmit = handleChatSubmit;
    window.handleMealUpload = handleMealUpload;
    window.generateMealPlan = generateMealPlan;
    window.handleAuthSubmit = handleAuthSubmit;
    window.navigateToTab = navigateToTab;
    window.selectProtocol = selectProtocol;

    init();
