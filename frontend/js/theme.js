// ===== THEME SYSTEM =====
// Order of precedence:
// 1. User explicit choice (localStorage)
// 2. System preference (prefers-color-scheme)
// 3. Default: dark

function getSystemTheme() {
  return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('azucar_theme', theme);

  // Update manifest theme-color meta tag
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) {
    meta.content = theme === 'dark' ? '#0a0e1a' : '#f0fdfa';
  }

  // Update apple status bar style
  const appleBar = document.querySelector('meta[name="apple-mobile-web-app-status-bar-style"]');
  if (appleBar) {
    appleBar.content = theme === 'dark' ? 'black-translucent' : 'default';
  }

  // Update toggle button text
  const toggleBtn = document.getElementById('themeToggleBtn');
  if (toggleBtn) {
    toggleBtn.textContent = theme === 'dark' ? '☀️ Modo Claro' : '🌙 Modo Oscuro';
  }
}

function initTheme() {
  const saved = localStorage.getItem('azucar_theme');
  applyTheme(saved || getSystemTheme());

  // Listen for system theme changes
  window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', (e) => {
    // Only auto-switch if user hasn't explicitly chosen
    if (!localStorage.getItem('azucar_theme')) {
      applyTheme(e.matches ? 'light' : 'dark');
    }
  });
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  applyTheme(current === 'dark' ? 'light' : 'dark');
}

// Initialize on load
initTheme();
