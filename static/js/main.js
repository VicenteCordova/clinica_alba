/* ================================================================
   static/js/main.js  |  Clínica El Alba — JS v2
   ================================================================ */

// ── Toast notifications ─────────────────────────────────────────
const TOAST_ICONS = {
  success: '<i class="bi bi-check-circle-fill"></i>',
  error:   '<i class="bi bi-exclamation-circle-fill"></i>',
  warning: '<i class="bi bi-exclamation-triangle-fill"></i>',
  info:    '<i class="bi bi-info-circle-fill"></i>',
};

function showToast(message, type = 'info', duration = 5000) {
  let container = document.querySelector('.toast-container-alba');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container-alba';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast-alba toast-${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${TOAST_ICONS[type] || TOAST_ICONS.info}</span>
    <span class="toast-message">${message}</span>
    <button class="toast-close" aria-label="Cerrar notificación"><i class="bi bi-x"></i></button>
  `;
  container.appendChild(toast);
  toast.querySelector('.toast-close').addEventListener('click', () => dismissToast(toast));
  if (duration > 0) setTimeout(() => dismissToast(toast), duration);
  return toast;
}

function dismissToast(toast) {
  toast.classList.add('hiding');
  toast.addEventListener('animationend', () => toast.remove(), { once: true });
}

// ── Sidebar toggle (móvil) ──────────────────────────────────────
function initSidebar() {
  const sidebar  = document.getElementById('sidebar');
  const overlay  = document.getElementById('sidebar-overlay');
  const toggleBtn = document.getElementById('menu-toggle');
  if (!sidebar) return;

  function openSidebar() {
    sidebar.classList.add('open');
    if (overlay) { overlay.classList.add('active'); }
    document.body.style.overflow = 'hidden';
  }
  function closeSidebar() {
    sidebar.classList.remove('open');
    if (overlay) { overlay.classList.remove('active'); }
    document.body.style.overflow = '';
  }

  if (toggleBtn) toggleBtn.addEventListener('click', () => {
    sidebar.classList.contains('open') ? closeSidebar() : openSidebar();
  });
  if (overlay) overlay.addEventListener('click', closeSidebar);
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeSidebar(); });
}

// ── Sidebar active state automático ─────────────────────────────
function initSidebarActiveState() {
  const links = document.querySelectorAll('.sidebar-link');
  const current = window.location.pathname;
  links.forEach(link => {
    const href = link.getAttribute('href');
    if (href && href !== '/' && current.startsWith(href)) {
      link.classList.add('active');
    } else if (href === '/' && current === '/') {
      link.classList.add('active');
    }
  });
}

// ── Drawer lateral ──────────────────────────────────────────────
function initDrawers() {
  document.querySelectorAll('[data-drawer]').forEach(trigger => {
    trigger.addEventListener('click', e => {
      e.preventDefault();
      const drawerId = trigger.dataset.drawer;
      openDrawer(drawerId);
    });
  });
  document.querySelectorAll('.drawer-close').forEach(btn => {
    btn.addEventListener('click', () => {
      const drawer = btn.closest('.drawer');
      if (drawer) closeDrawer(drawer.id);
    });
  });
  document.querySelectorAll('.drawer-overlay').forEach(overlay => {
    overlay.addEventListener('click', () => {
      const drawerId = overlay.dataset.for;
      if (drawerId) closeDrawer(drawerId);
    });
  });
}

function openDrawer(drawerId) {
  const drawer = document.getElementById(drawerId);
  const overlay = document.querySelector(`.drawer-overlay[data-for="${drawerId}"]`);
  if (drawer) { drawer.classList.add('open'); }
  if (overlay) { overlay.classList.add('active'); }
  document.body.style.overflow = 'hidden';
  const firstFocusable = drawer?.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
  if (firstFocusable) firstFocusable.focus();
}

function closeDrawer(drawerId) {
  const drawer = document.getElementById(drawerId);
  const overlay = document.querySelector(`.drawer-overlay[data-for="${drawerId}"]`);
  if (drawer) { drawer.classList.remove('open'); }
  if (overlay) { overlay.classList.remove('active'); }
  document.body.style.overflow = '';
}

// ── Confirm dialog (reemplaza confirm() nativo) ──────────────────
function confirmAction(message, onConfirm, options = {}) {
  const { title = '¿Confirmar acción?', btnLabel = 'Confirmar', btnClass = 'btn-danger' } = options;
  const existing = document.getElementById('alba-confirm-modal');
  if (existing) existing.remove();

  const modal = document.createElement('div');
  modal.id = 'alba-confirm-modal';
  modal.innerHTML = `
    <div style="position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:600;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(2px);">
      <div style="background:white;border-radius:16px;padding:28px;max-width:400px;width:90%;box-shadow:0 20px 60px rgba(0,0,0,.2);">
        <h5 style="font-size:16px;font-weight:700;margin:0 0 8px;">${title}</h5>
        <p style="font-size:13.5px;color:#607D8B;margin:0 0 20px;">${message}</p>
        <div style="display:flex;gap:10px;justify-content:flex-end;">
          <button id="alba-confirm-cancel" class="btn btn-outline">Cancelar</button>
          <button id="alba-confirm-ok" class="btn ${btnClass}">${btnLabel}</button>
        </div>
      </div>
    </div>`;
  document.body.appendChild(modal);

  modal.querySelector('#alba-confirm-ok').addEventListener('click', () => { modal.remove(); onConfirm(); });
  modal.querySelector('#alba-confirm-cancel').addEventListener('click', () => modal.remove());
  modal.addEventListener('click', e => { if (e.target === modal.firstElementChild) modal.remove(); });
  document.addEventListener('keydown', function esc(e) { if (e.key === 'Escape') { modal.remove(); document.removeEventListener('keydown', esc); } });
}

// ── Buscador universal — cerrar al clic fuera ────────────────────
function initSearchDropdown() {
  const input = document.getElementById('busqueda-global');
  const results = document.getElementById('resultados-busqueda-global');
  if (!input || !results) return;
  document.addEventListener('click', e => {
    if (!input.contains(e.target) && !results.contains(e.target)) {
      results.innerHTML = '';
    }
  });
  input.addEventListener('keydown', e => {
    if (e.key === 'Escape') { results.innerHTML = ''; input.blur(); }
  });
}

// ── Auto-guardar indicador ───────────────────────────────────────
let autoSaveTimer = null;
function initAutoSaveIndicator() {
  const forms = document.querySelectorAll('[data-autosave]');
  forms.forEach(form => {
    const indicator = form.querySelector('[data-save-indicator]');
    form.addEventListener('input', () => {
      if (indicator) { indicator.textContent = 'Sin guardar'; indicator.className = 'text-warning small'; }
      clearTimeout(autoSaveTimer);
    });
  });
}

// ── HTMX: mostrar toast en respuesta ────────────────────────────
document.addEventListener('htmx:afterRequest', function(e) {
  const headers = e.detail.xhr.getAllResponseHeaders();
  if (headers.includes('X-Toast')) {
    const msg = e.detail.xhr.getResponseHeader('X-Toast');
    const type = e.detail.xhr.getResponseHeader('X-Toast-Type') || 'success';
    if (msg) showToast(msg, type);
  }
});

// ── Mensajes Django → Toast ──────────────────────────────────────
function convertDjangoMessages() {
  document.querySelectorAll('[data-django-message]').forEach(el => {
    const type = el.dataset.djangoMessage;
    const msg = el.textContent.trim();
    const typeMap = { success:'success', error:'error', warning:'warning', info:'info', debug:'info' };
    showToast(msg, typeMap[type] || 'info');
    el.remove();
  });
}

// ── Init ──────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initSidebar();
  initSidebarActiveState();
  initDrawers();
  initSearchDropdown();
  initAutoSaveIndicator();
  convertDjangoMessages();
});

// ── Exportar globales ─────────────────────────────────────────────
window.Alba = { showToast, confirmAction, openDrawer, closeDrawer };
