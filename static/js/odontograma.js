/**
 * static/js/odontograma_avanzado.js
 * Odontograma Anatómico Clínico Profesional V3
 */

const COLORES_ESTADO = {
  sano: { fill: '#ffffff', stroke: '#94a3b8' },
  existente: { fill: '#ede9ff', stroke: '#7c3aed' },
  condicion: { fill: '#fee2e2', stroke: '#dc2626' },
  planificado: { fill: '#dbeafe', stroke: '#2563eb' },
  en_tratamiento: { fill: '#ffedd5', stroke: '#ea580c' },
  completado: { fill: '#dcfce7', stroke: '#16a34a' },
  ausente: { fill: '#f1f5f9', stroke: '#475569' },
  extraccion_indicada: { fill: '#fff1f2', stroke: '#be123c' },
  urgencia: { fill: '#fef3c7', stroke: '#d97706' },
  anulado: { fill: '#f8fafc', stroke: '#cbd5e1' }
};

const CUADRANTES = {
  1: [18, 17, 16, 15, 14, 13, 12, 11],
  2: [21, 22, 23, 24, 25, 26, 27, 28],
  3: [31, 32, 33, 34, 35, 36, 37, 38],
  4: [48, 47, 46, 45, 44, 43, 42, 41],
};

// Paths base en 60x100
const PATHS_ANATOMIA = {
  incisivo: {
    corona: { v: "M10,10 Q30,-5 50,10 L45,30 Q30,40 15,30 Z", p: "M15,50 Q30,65 45,50 L50,30 Q30,40 10,30 Z", m: "M10,10 L15,30 L15,50 Q-5,30 10,10 Z", d: "M50,10 L45,30 L45,50 Q65,30 50,10 Z", c: "M15,30 Q30,40 45,30 L45,50 Q30,40 15,50 Z" },
    raices: { unica: "M20,10 Q30,-40 40,10 Z" }
  },
  canino: {
    corona: { v: "M15,15 Q30,-10 45,15 L40,30 Q30,45 20,30 Z", p: "M20,45 Q30,60 40,45 L45,30 Q30,15 15,30 Z", m: "M15,15 L20,30 L20,45 Q0,30 15,15 Z", d: "M45,15 L40,30 L40,45 Q60,30 45,15 Z", c: "M20,30 Q30,45 40,30 L40,45 Q30,30 20,45 Z" },
    raices: { unica: "M22,15 Q30,-50 38,15 Z" }
  },
  premolar: {
    corona: { v: "M10,15 Q30,0 50,15 L40,30 Q30,35 20,30 Z", p: "M20,45 Q30,60 40,45 L50,30 Q30,15 10,30 Z", m: "M10,15 L20,30 L20,45 Q-5,30 10,15 Z", d: "M50,15 L40,30 L40,45 Q65,30 50,15 Z", c: "M20,30 Q30,35 40,30 L40,45 Q30,35 20,45 Z" },
    raices: { unica: "M20,15 Q30,-40 40,15 Z", vestibular: "M15,15 Q25,-40 30,15 Z", palatina: "M30,15 Q35,-40 45,15 Z" }
  },
  molar_superior: {
    corona: { v: "M5,15 Q30,-5 55,15 L45,30 Q30,40 15,30 Z", p: "M15,45 Q30,65 45,45 L55,30 Q30,20 5,30 Z", m: "M5,15 L15,30 L15,45 Q-10,30 5,15 Z", d: "M55,15 L45,30 L45,45 Q70,30 55,15 Z", c: "M15,30 Q30,40 45,30 L45,45 Q30,30 15,45 Z" },
    raices: { mesiovestibular: "M10,15 Q15,-40 25,15 Z", distovestibular: "M35,15 Q45,-40 50,15 Z", palatina: "M22,15 Q30,-50 38,15 Z" }
  },
  molar_inferior: {
    corona: { v: "M5,15 Q30,-5 55,15 L45,30 Q30,40 15,30 Z", p: "M15,45 Q30,65 45,45 L55,30 Q30,20 5,30 Z", m: "M5,15 L15,30 L15,45 Q-10,30 5,15 Z", d: "M55,15 L45,30 L45,45 Q70,30 55,15 Z", c: "M15,30 Q30,40 45,30 L45,45 Q30,30 15,45 Z" },
    raices: { mesial: "M15,15 Q20,-45 28,15 Z", distal: "M32,15 Q40,-45 45,15 Z" }
  }
};

let estadoOdontograma = ODONTOGRAMA_CONFIG.estadoInicial || {};
let historialGlobal = ODONTOGRAMA_CONFIG.historialJson || [];
let piezaSeleccionada = null;
let tieneCambiosSinGuardar = false;

// Estado del formulario actual
let formState = {
  cara: '',
  raiz: '',
  estado_clinico: 'condicion',
  condicion_id: '',
  observacion: ''
};

function obtenerColor(estado) { return COLORES_ESTADO[estado] || COLORES_ESTADO.sano; }
function normalizarKey(v) { return String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim().toLowerCase().replace(/[\/\-\s]+/g, '_'); }

function obtenerAnatomia(numero) {
  const num = Number(numero);
  const cuadrante = Math.floor(num / 10);
  const diente = num % 10;
  const esSuperior = [1, 2, 5, 6].includes(cuadrante);
  const esAnterior = [1, 2, 3].includes(diente);
  const interna = esSuperior ? 'palatina' : 'lingual';
  const centro = esAnterior ? 'incisal' : 'oclusal';
  
  let tipoPath = 'incisivo';
  if (diente === 3) tipoPath = 'canino';
  else if (diente === 4 || diente === 5) tipoPath = 'premolar';
  else if (diente >= 6) tipoPath = esSuperior ? 'molar_superior' : 'molar_inferior';

  return { 
    esSuperior, tipoPath, 
    caras: { 'vestibular':'v', [interna]:'p', 'mesial':'m', 'distal':'d', [centro]:'c' },
    raicesDisp: Object.keys(PATHS_ANATOMIA[tipoPath].raices)
  };
}

// ─────────────────────────────────────────────────────────────────
// RENDERIZADO GRID PRINCIPAL
// ─────────────────────────────────────────────────────────────────

function renderizarGrid() {
  const container = document.getElementById('odontograma-container');
  if(!container) return;
  container.innerHTML = '';
  container.className = 'odontograma-grid';

  const crearFila = (cuads) => {
    const fila = document.createElement('div'); fila.className = 'odontograma-fila';
    cuads.forEach(cuad => {
      const grupo = document.createElement('div'); grupo.className = 'odontograma-cuadrante';
      CUADRANTES[cuad].forEach(num => grupo.appendChild(crearDiente(num, false)));
      fila.appendChild(grupo);
    });
    return fila;
  };

  container.appendChild(crearFila([1, 2]));
  const sep = document.createElement('div'); sep.className = 'odontograma-arch-sep';
  sep.innerHTML = '<span>Superior</span><span>Inferior</span>';
  container.appendChild(sep);
  container.appendChild(crearFila([4, 3]));
}

function crearDiente(numero, isZoom = false) {
  const anat = obtenerAnatomia(numero);
  const wrapper = document.createElement(isZoom ? 'div' : 'button');
  if(!isZoom) {
    wrapper.type = 'button';
    wrapper.className = `diente-anatomico-wrapper ${piezaSeleccionada === numero ? 'selected' : ''}`;
    wrapper.dataset.diente = numero;
  }
  
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 60 100');
  svg.setAttribute('class', isZoom ? 'pieza-zoom-svg' : 'diente-svg-anatomico');
  
  const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  if (!anat.esSuperior) g.setAttribute('transform', 'rotate(180 30 50)');
  
  const paths = PATHS_ANATOMIA[anat.tipoPath];
  const data = estadoOdontograma[numero] || {};
  const estadoGen = data._estado || 'presente';

  // Raíces
  Object.keys(paths.raices).forEach(rKey => {
    const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    p.setAttribute('d', paths.raices[rKey]);
    p.setAttribute('transform', 'translate(0, 45)');
    p.setAttribute('fill', '#ffffff');
    p.setAttribute('stroke', '#cbd5e1');
    p.setAttribute('class', 'raiz-path');
    p.dataset.raiz = rKey;
    if(isZoom && formState.raiz === rKey) p.classList.add('selected-zone');
    g.appendChild(p);
  });

  // Coronas
  const gCor = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  gCor.setAttribute('transform', 'translate(0, 40)');
  Object.entries(anat.caras).forEach(([nombre, pKey]) => {
    const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    p.setAttribute('d', paths.corona[pKey]);
    const color = obtenerColor(data[nombre]?.estado_clinico || 'sano');
    p.setAttribute('fill', color.fill);
    p.setAttribute('stroke', color.stroke);
    p.setAttribute('class', 'cara-path');
    p.dataset.cara = nombre;
    if(isZoom && formState.cara === nombre) p.classList.add('selected-zone');
    gCor.appendChild(p);
  });
  g.appendChild(gCor);

  // Overlays
  if(['ausente', 'extraccion_indicada'].includes(estadoGen)) {
    const color = estadoGen==='extraccion_indicada' ? '#be123c' : '#475569';
    const l1 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    l1.setAttribute('x1','5'); l1.setAttribute('y1','25'); l1.setAttribute('x2','55'); l1.setAttribute('y2','75');
    l1.setAttribute('stroke', color); l1.setAttribute('stroke-width','4');
    g.appendChild(l1);
  }

  svg.appendChild(g);

  if(!isZoom) {
    const numEl = document.createElement('div'); numEl.className = 'diente-numero'; numEl.textContent = numero;
    wrapper.appendChild(numEl);
    wrapper.appendChild(svg);
    wrapper.addEventListener('click', () => { seleccionarPieza(numero); });
  } else {
    // Zoom interaction
    svg.addEventListener('click', (e) => {
      if(e.target.tagName === 'path') {
        const c = e.target.dataset.cara;
        const r = e.target.dataset.raiz;
        if(c) { document.getElementById('cara-select').value = c; document.getElementById('raiz-select').value = ''; }
        if(r) { document.getElementById('raiz-select').value = r; document.getElementById('cara-select').value = ''; }
        actualizarFormState();
      }
    });
    wrapper.appendChild(svg);
  }
  return wrapper;
}

// ─────────────────────────────────────────────────────────────────
// PANEL LATERAL Y FORMULARIO
// ─────────────────────────────────────────────────────────────────

function initPanel() {
  // Render condiciones agrupadas
  const list = document.getElementById('lista-condiciones');
  if(!list) return;
  const conds = ODONTOGRAMA_CONFIG.condicionesJson || [];
  
  // Agrupar
  const grupos = {};
  conds.forEach(c => {
    if(!grupos[c.categoria_display]) grupos[c.categoria_display] = [];
    grupos[c.categoria_display].push(c);
  });

  list.innerHTML = '';
  Object.keys(grupos).forEach(cat => {
    const title = document.createElement('div');
    title.className = 'condition-category-title';
    title.textContent = cat;
    list.appendChild(title);
    
    grupos[cat].forEach(c => {
      const div = document.createElement('div');
      div.className = 'condition-item';
      div.dataset.id = c.id;
      div.dataset.name = c.nombre;
      div.textContent = c.nombre;
      div.addEventListener('click', () => {
        document.querySelectorAll('.condition-item').forEach(i=>i.classList.remove('selected'));
        div.classList.add('selected');
        actualizarFormState();
      });
      list.appendChild(div);
    });
  });

  // State buttons
  document.querySelectorAll('.state-btn').forEach(b => {
    b.addEventListener('click', () => {
      document.querySelectorAll('.state-btn').forEach(btn=>{ btn.classList.remove('selected'); btn.className = btn.className.replace(/\b(sano|existente|condicion|planificado|en_tratamiento|completado|ausente|extraccion_indicada|urgencia)\b/g, '').trim(); });
      b.classList.add('selected');
      b.classList.add(b.dataset.state); // Add color class dynamic
      actualizarFormState();
    });
  });

  // Inputs
  document.getElementById('cara-select')?.addEventListener('change', actualizarFormState);
  document.getElementById('raiz-select')?.addEventListener('change', actualizarFormState);
  document.getElementById('observacion-field')?.addEventListener('input', actualizarFormState);
  
  document.getElementById('btn-guardar-registro')?.addEventListener('click', guardarCambios);
  document.getElementById('btn-enviar-plan')?.addEventListener('click', enviarPlan);
}

function seleccionarPieza(num) {
  piezaSeleccionada = num;
  marcarCambio(false);
  
  // Actualizar UI Grid
  document.querySelectorAll('.diente-anatomico-wrapper').forEach(w => w.classList.remove('selected'));
  const w = document.querySelector(`.diente-anatomico-wrapper[data-diente="${num}"]`);
  if(w) w.classList.add('selected');

  document.getElementById('panel-no-selection').style.display = 'none';
  document.getElementById('panel-selection').style.display = 'block';
  document.getElementById('pieza-selected-label').textContent = `Pieza ${num}`;

  // Llenar selects según anatomía
  const anat = obtenerAnatomia(num);
  const sCara = document.getElementById('cara-select');
  sCara.innerHTML = '<option value="">— General / Pieza completa —</option>';
  Object.keys(anat.caras).forEach(c => {
    sCara.appendChild(new Option(c.toUpperCase(), c));
  });

  const sRaiz = document.getElementById('raiz-select');
  sRaiz.innerHTML = '<option value="">— Ninguna —</option>';
  anat.raicesDisp.forEach(r => {
    sRaiz.appendChild(new Option(r.toUpperCase(), r));
  });

  // Reset form visual
  document.getElementById('observacion-field').value = '';
  document.querySelectorAll('.condition-item').forEach(i=>i.classList.remove('selected'));
  document.querySelector('.state-btn[data-state="condicion"]').click();

  renderizarZoomPieza();
}

function renderizarZoomPieza() {
  if(!piezaSeleccionada) return;
  const cont = document.getElementById('pieza-zoom-container');
  cont.innerHTML = '';
  cont.appendChild(crearDiente(piezaSeleccionada, true));
}

function actualizarFormState() {
  formState = {
    cara: document.getElementById('cara-select').value,
    raiz: document.getElementById('raiz-select').value,
    estado_clinico: document.querySelector('.state-btn.selected')?.dataset.state || 'condicion',
    condicion_id: document.querySelector('.condition-item.selected')?.dataset.id || '',
    observacion: document.getElementById('observacion-field').value
  };

  const isPlan = ['planificado', 'en_tratamiento'].includes(formState.estado_clinico);
  document.getElementById('btn-enviar-plan').style.display = isPlan ? 'block' : 'none';

  renderizarZoomPieza();
  marcarCambio(true);
}

function marcarCambio(activo) {
  if(!ODONTOGRAMA_CONFIG.puedeEditar) return;
  tieneCambiosSinGuardar = activo;
  document.getElementById('unsaved-warning').style.display = activo ? 'flex' : 'none';
  const btn = document.getElementById('btn-guardar-registro');
  if(btn) btn.disabled = !activo;
}

// ─────────────────────────────────────────────────────────────────
// GUARDADO ASÍNCRONO
// ─────────────────────────────────────────────────────────────────

async function guardarCambios() {
  if(!piezaSeleccionada || !tieneCambiosSinGuardar) return;
  const btn = document.getElementById('btn-guardar-registro');
  const txtOrg = btn.innerHTML;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Guardando...';
  btn.disabled = true;

  try {
    const base = `${ODONTOGRAMA_CONFIG.apiBase}${ODONTOGRAMA_CONFIG.id}/pieza/${piezaSeleccionada}`;
    let endpoint = '';
    let payload = { observacion: formState.observacion, estado_clinico: formState.estado_clinico };

    if(formState.cara) {
      endpoint = '/superficie/';
      payload.cara = formState.cara;
      payload.condicion = formState.condicion_id;
    } else if(formState.raiz) {
      endpoint = '/raiz/';
      payload.raiz = formState.raiz;
      payload.condicion = formState.condicion_id;
    } else {
      endpoint = '/estado/';
      payload.estado_general = formState.condicion_id ? 'condicion' : 'presente'; // simplified
    }

    const res = await fetch(base + endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': ODONTOGRAMA_CONFIG.csrfToken },
      body: JSON.stringify(payload)
    });
    
    const data = await res.json();
    if(!data.success) throw new Error(data.error || 'Error desconocido al guardar');

    // Actualizar estado local
    if(!estadoOdontograma[piezaSeleccionada]) estadoOdontograma[piezaSeleccionada] = {};
    if(formState.cara) {
      estadoOdontograma[piezaSeleccionada][formState.cara] = { estado_clinico: formState.estado_clinico };
    } else if(!formState.raiz) {
      estadoOdontograma[piezaSeleccionada]._estado = payload.estado_general;
    }

    // Append historial nuevo si viene
    if(data.historial_item) {
      historialGlobal.unshift(data.historial_item);
      renderizarHistorial();
    }

    marcarCambio(false);
    renderizarGrid(); // Refrescar grid con nuevos colores
    renderizarZoomPieza(); // Refrescar zoom
    
    // Feedback visual toast/alert sutil
    const w = document.getElementById('unsaved-warning');
    w.innerHTML = '<i class="bi bi-check2-all text-success"></i> <span class="text-success">Guardado</span>';
    w.style.display = 'flex';
    setTimeout(() => { if(!tieneCambiosSinGuardar) w.style.display='none'; w.innerHTML = '<i class="bi bi-exclamation-circle-fill"></i> Sin guardar'; }, 3000);

  } catch(err) {
    alert(err.message);
  } finally {
    btn.innerHTML = txtOrg;
    btn.disabled = false;
  }
}

async function enviarPlan() {
  if(!piezaSeleccionada || !formState.condicion_id) {
    alert("Selecciona una condición/tratamiento primero."); return;
  }
  const btn = document.getElementById('btn-enviar-plan');
  btn.disabled = true;
  try {
    const res = await fetch(`${ODONTOGRAMA_CONFIG.apiBase}${ODONTOGRAMA_CONFIG.id}/enviar-plan/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': ODONTOGRAMA_CONFIG.csrfToken },
      body: JSON.stringify({
        codigo_pieza: piezaSeleccionada,
        condicion_id: formState.condicion_id,
        observacion: formState.observacion
      })
    });
    const data = await res.json();
    if(!data.success) throw new Error(data.error);
    alert(data.message);
    if(data.historial_item) {
      historialGlobal.unshift(data.historial_item);
      renderizarHistorial();
    }
  } catch(err) {
    alert(err.message);
  } finally {
    btn.disabled = false;
  }
}

// ─────────────────────────────────────────────────────────────────
// HISTORIAL DINÁMICO
// ─────────────────────────────────────────────────────────────────

function renderizarHistorial() {
  const tbody = document.getElementById('historial-tbody');
  if(!tbody) return;
  
  const search = document.getElementById('historial-search')?.value.toLowerCase() || '';
  
  const hFiltered = historialGlobal.filter(h => {
    return !search || 
           h.pieza.includes(search) || 
           h.detalle.toLowerCase().includes(search) || 
           h.usuario.toLowerCase().includes(search);
  });

  tbody.innerHTML = hFiltered.map(h => `
    <tr>
      <td>${h.fecha_display}</td>
      <td><strong>${h.pieza}</strong></td>
      <td><span class="badge bg-secondary">${h.tipo}</span></td>
      <td>${h.detalle}</td>
      <td class="text-muted">${h.estado_anterior}</td>
      <td class="fw-bold">${h.estado_nuevo}</td>
      <td>${h.usuario}</td>
    </tr>
  `).join('');
  
  if(hFiltered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted py-3">No hay registros que coincidan.</td></tr>`;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  renderizarGrid();
  initPanel();
  renderizarHistorial();
  document.getElementById('historial-search')?.addEventListener('input', renderizarHistorial);
});
