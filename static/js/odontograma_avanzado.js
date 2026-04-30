/**
 * static/js/odontograma_avanzado.js
 * Odontograma FDI interactivo para Clinica El Alba.
 */

const COLORES_CONDICION = {
  sano: { fill: '#dcfce7', stroke: '#16a34a', label: 'Sano' },
  caries: { fill: '#fee2e2', stroke: '#dc2626', label: 'Caries' },
  restauracion: { fill: '#dbeafe', stroke: '#2563eb', label: 'Restauracion' },
  obturacion: { fill: '#dbeafe', stroke: '#2563eb', label: 'Obturacion' },
  ausente: { fill: '#f1f5f9', stroke: '#64748b', label: 'Ausente' },
  extraccion_indicada: { fill: '#fff1f2', stroke: '#be123c', label: 'Extraccion indicada' },
  extraccion: { fill: '#fff1f2', stroke: '#be123c', label: 'Extraccion' },
  endodoncia: { fill: '#fae8ff', stroke: '#c026d3', label: 'Endodoncia' },
  corona: { fill: '#fef3c7', stroke: '#d97706', label: 'Corona' },
  implante: { fill: '#ccfbf1', stroke: '#0f766e', label: 'Implante' },
  fractura: { fill: '#ffedd5', stroke: '#ea580c', label: 'Fractura' },
  movilidad: { fill: '#ede9fe', stroke: '#7c3aed', label: 'Movilidad' },
  observacion: { fill: '#e0f2fe', stroke: '#0284c7', label: 'Observacion' },
  sin_dato: { fill: '#f8fafc', stroke: '#cbd5e1', label: 'Sin dato' },
};

const CUADRANTES = {
  1: [18, 17, 16, 15, 14, 13, 12, 11],
  2: [21, 22, 23, 24, 25, 26, 27, 28],
  3: [31, 32, 33, 34, 35, 36, 37, 38],
  4: [48, 47, 46, 45, 44, 43, 42, 41],
};

let estadoOdontograma = {};
let piezaActualModal = null;
let modoEdicionOdontograma = true;

function normalizarKey(valor) {
  return String(valor || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase()
    .replace(/[\/\-\s]+/g, '_');
}

function condicionKey(valor) {
  const key = normalizarKey(valor);
  const aliases = {
    restauracion_defectuosa: 'restauracion',
    obturacion: 'restauracion',
    extraccion: 'extraccion_indicada',
    extraccion_indicada: 'extraccion_indicada',
  };
  return aliases[key] || key || 'sin_dato';
}

function colorCondicion(valor) {
  return COLORES_CONDICION[condicionKey(valor)] || COLORES_CONDICION.sin_dato;
}

function obtenerAnatomiaCliente(numero) {
  const num = Number(numero);
  const cuadrante = Math.floor(num / 10);
  const diente = num % 10;
  const esSuperior = [1, 2, 5, 6].includes(cuadrante);
  const esAnterior = [1, 2, 3].includes(diente);
  const caras = esAnterior
    ? ['vestibular', esSuperior ? 'palatina' : 'lingual', 'mesial', 'distal', 'incisal']
    : ['vestibular', esSuperior ? 'palatina' : 'lingual', 'mesial', 'distal', 'oclusal'];
  return { esSuperior, esAnterior, caras };
}

function escaparHTML(valor) {
  return String(valor || '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;',
  }[char]));
}

function inicializarOdontograma(estadoInicial = {}, modoEdicion = true) {
  estadoOdontograma = estadoInicial || {};
  modoEdicionOdontograma = Boolean(modoEdicion);
  const container = document.getElementById('odontograma-container');
  if (!container) return;

  container.innerHTML = '';
  container.className = `odontograma-wrapper${modoEdicionOdontograma ? '' : ' modo-solo-lectura'}`;

  container.appendChild(crearFila([1, 2], 'superior'));

  const sep = document.createElement('div');
  sep.className = 'odontograma-sep';
  sep.innerHTML = '<span>Superior</span><span>Inferior</span>';
  container.appendChild(sep);

  container.appendChild(crearFila([4, 3], 'inferior'));
}

function crearFila(cuadrantes, lado) {
  const fila = document.createElement('div');
  fila.className = 'odontograma-fila';
  cuadrantes.forEach((nroCuad) => {
    const grupo = document.createElement('div');
    grupo.className = 'odontograma-cuadrante';
    CUADRANTES[nroCuad].forEach((nro) => grupo.appendChild(crearDiente(nro, lado)));
    fila.appendChild(grupo);
  });
  return fila;
}

function crearDiente(numero, lado) {
  const wrapper = document.createElement('button');
  wrapper.type = 'button';
  wrapper.className = 'diente-wrapper';
  wrapper.dataset.diente = numero;
  wrapper.setAttribute('aria-label', `Pieza ${numero}`);

  const num = document.createElement('div');
  num.className = 'diente-numero';
  num.textContent = numero;

  const svg = crearDienteSVG(numero, lado);
  wrapper.appendChild(num);
  wrapper.appendChild(svg);
  wrapper.addEventListener('click', () => abrirModalDetalle(numero));
  return wrapper;
}

function crearDienteSVG(numero) {
  const SIZE = 52;
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', `0 0 ${SIZE} ${SIZE}`);
  svg.setAttribute('width', SIZE);
  svg.setAttribute('height', SIZE);
  svg.classList.add('diente-svg');

  const anatomia = obtenerAnatomiaCliente(numero);
  const centro = anatomia.esAnterior ? 'incisal' : 'oclusal';
  const interna = anatomia.esSuperior ? 'palatina' : 'lingual';
  const caras = {
    [centro]: { points: `${SIZE / 2},${SIZE / 4} ${SIZE * 3 / 4},${SIZE / 2} ${SIZE / 2},${SIZE * 3 / 4} ${SIZE / 4},${SIZE / 2}` },
    vestibular: { points: `${SIZE / 2},2 ${SIZE - 2},${SIZE / 4} 2,${SIZE / 4}` },
    [interna]: { points: `${SIZE / 2},${SIZE - 2} ${SIZE - 2},${SIZE * 3 / 4} 2,${SIZE * 3 / 4}` },
    mesial: { points: `2,${SIZE / 2} ${SIZE / 4},${SIZE / 4} ${SIZE / 4},${SIZE * 3 / 4}` },
    distal: { points: `${SIZE - 2},${SIZE / 2} ${SIZE * 3 / 4},${SIZE / 4} ${SIZE * 3 / 4},${SIZE * 3 / 4}` },
  };

  Object.entries(caras).forEach(([cara, config]) => {
    const el = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
    el.setAttribute('points', config.points);
    const condicion = estadoOdontograma[numero]?.[cara] || 'sin_dato';
    const col = colorCondicion(condicion);
    el.setAttribute('fill', col.fill);
    el.setAttribute('stroke', col.stroke);
    el.setAttribute('stroke-width', '1.7');
    el.dataset.cara = cara;
    const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
    title.textContent = `Pieza ${numero} - ${cara}: ${col.label}`;
    el.appendChild(title);
    svg.appendChild(el);
  });

  actualizarOverlaysDiente(numero, svg);
  return svg;
}

function actualizarOverlaysDiente(numero, svg) {
  svg.querySelectorAll('.overlay-cruz, .overlay-implante').forEach((el) => el.remove());
  const estado = estadoOdontograma[numero] || {};
  const condiciones = Object.values(estado).map(condicionKey);
  const estadoGeneral = estado._estado || 'presente';
  const tieneAusente = estadoGeneral === 'ausente' || condiciones.includes('ausente');
  const tieneExtraccion = ['extraccion_indicada', 'extraido'].includes(estadoGeneral) || condiciones.includes('extraccion_indicada');
  const tieneImplante = estadoGeneral === 'implante' || condiciones.includes('implante');

  if (tieneAusente || tieneExtraccion) {
    const color = tieneExtraccion ? '#be123c' : '#334155';
    const lineas = [
      ['5', '5', '47', '47'],
      ['47', '5', '5', '47'],
    ];
    lineas.forEach(([x1, y1, x2, y2]) => {
      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', x1);
      line.setAttribute('y1', y1);
      line.setAttribute('x2', x2);
      line.setAttribute('y2', y2);
      line.setAttribute('stroke', color);
      line.setAttribute('stroke-width', '4');
      line.setAttribute('stroke-linecap', 'round');
      line.setAttribute('class', 'overlay-cruz');
      svg.appendChild(line);
    });
  }

  if (tieneImplante) {
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', '26');
    circle.setAttribute('cy', '26');
    circle.setAttribute('r', '8');
    circle.setAttribute('fill', 'none');
    circle.setAttribute('stroke', '#0f766e');
    circle.setAttribute('stroke-width', '4');
    circle.setAttribute('class', 'overlay-implante');
    svg.appendChild(circle);
  }
}

function abrirModalDetalle(numeroPieza) {
  if (typeof ODONTOGRAMA_ID === 'undefined') return;
  piezaActualModal = numeroPieza;
  document.getElementById('modal-pieza-numero').textContent = numeroPieza;
  setModalLoading();

  fetch(`/odontograma/api/${ODONTOGRAMA_ID}/pieza/${numeroPieza}/`)
    .then((res) => res.json())
    .then((data) => {
      if (!data.success) throw new Error(data.error || 'No se pudo cargar la pieza.');
      llenarModal(data);
      const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('modal-detalle-pieza'));
      modal.show();
    })
    .catch((err) => mostrarEstado(err.message, 'danger'));
}

function setModalLoading() {
  ['svg-corona-container', 'svg-raiz-container'].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = '<span class="text-muted small">Cargando...</span>';
  });
  ['lista-superficies', 'lista-raices', 'lista-historial'].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = '';
  });
}

function llenarModal(data) {
  document.getElementById('select-estado-general').value = data.estado_general || 'presente';
  const obsPieza = document.getElementById('observacion-pieza');
  if (obsPieza) obsPieza.value = data.observacion_pieza || '';

  const selCara = document.getElementById('select-cara');
  selCara.innerHTML = '';
  data.anatomia.caras_coronarias.forEach((cara) => {
    const opt = document.createElement('option');
    opt.value = cara;
    opt.textContent = cara.toUpperCase();
    selCara.appendChild(opt);
  });

  const selRaiz = document.getElementById('select-raiz');
  selRaiz.innerHTML = '';
  data.anatomia.raices.forEach((raiz) => {
    const opt = document.createElement('option');
    opt.value = raiz;
    opt.textContent = raiz.toUpperCase();
    selRaiz.appendChild(opt);
  });

  renderSuperficies(data.superficies || []);
  renderRaices(data.raices || []);
  renderPeriodonto(data.periodonto || {});
  renderHistorial(data.historial || []);
  dibujarSVGDetalleCorona(data);
  dibujarSVGDetalleRaiz(data);
}

function renderSuperficies(superficies) {
  const ul = document.getElementById('lista-superficies');
  if (!superficies.length) {
    ul.innerHTML = '<li class="list-group-item text-muted px-0">Sin superficies registradas.</li>';
    return;
  }
  ul.innerHTML = superficies.map((s) => {
    const col = colorCondicion(s.condicion_key || s.condicion);
    return `<li class="list-group-item d-flex justify-content-between align-items-start px-0">
      <span><span class="badge me-2" style="background:${col.fill};color:#0f172a;border:1px solid ${col.stroke};">${escaparHTML(s.cara)}</span> ${escaparHTML(s.condicion)}</span>
      ${s.observacion ? `<small class="text-muted ms-2">${escaparHTML(s.observacion)}</small>` : ''}
    </li>`;
  }).join('');
}

function renderRaices(raices) {
  const ul = document.getElementById('lista-raices');
  if (!raices.length) {
    ul.innerHTML = '<li class="list-group-item text-muted px-0">Sin condiciones radiculares.</li>';
    return;
  }
  ul.innerHTML = raices.map((r) => {
    const col = colorCondicion(r.condicion_key || r.condicion);
    return `<li class="list-group-item d-flex justify-content-between align-items-start px-0">
      <span><span class="badge me-2" style="background:${col.fill};color:#0f172a;border:1px solid ${col.stroke};">${escaparHTML(r.raiz)} (${escaparHTML(r.tercio)})</span> ${escaparHTML(r.condicion || 'Sin dato')}</span>
      ${r.observacion ? `<small class="text-muted ms-2">${escaparHTML(r.observacion)}</small>` : ''}
    </li>`;
  }).join('');
}

function renderPeriodonto(p) {
  document.getElementById('perio-movilidad').value = p.movilidad || '';
  document.getElementById('perio-furca').value = p.furca || '';
  document.getElementById('perio-sondaje').value = p.profundidad_sondaje || '';
  document.getElementById('perio-recesion').value = p.recesion || '';
  document.getElementById('perio-sangrado').checked = Boolean(p.sangrado);
  document.getElementById('perio-placa').checked = Boolean(p.placa);
  document.getElementById('perio-supuracion').checked = Boolean(p.supuracion);
  const obs = document.getElementById('perio-observacion');
  if (obs) obs.value = p.observacion || '';
}

function renderHistorial(historial) {
  const ul = document.getElementById('lista-historial');
  if (!historial.length) {
    ul.innerHTML = '<li class="list-group-item text-muted">Sin cambios registrados.</li>';
    return;
  }
  ul.innerHTML = historial.map((h) => `<li class="list-group-item px-0">
    <div class="d-flex justify-content-between gap-2">
      <small class="fw-bold">${escaparHTML(h.usuario)}</small>
      <small class="text-muted">${escaparHTML(h.fecha)}</small>
    </div>
    <div class="small">[${escaparHTML(h.tipo_cambio)}] ${escaparHTML(h.detalle_cambio)}</div>
  </li>`).join('');
}

function dibujarSVGDetalleCorona(data) {
  const container = document.getElementById('svg-corona-container');
  const dummyState = {};
  (data.superficies || []).forEach((s) => { dummyState[s.cara] = s.condicion_key || s.condicion; });
  dummyState._estado = data.estado_general || 'presente';
  const previo = estadoOdontograma;
  estadoOdontograma = { [piezaActualModal]: dummyState };
  const svg = crearDienteSVG(piezaActualModal);
  estadoOdontograma = previo;
  svg.style.width = '128px';
  svg.style.height = '128px';
  container.innerHTML = '';
  container.appendChild(svg);
}

function dibujarSVGDetalleRaiz(data) {
  const container = document.getElementById('svg-raiz-container');
  container.innerHTML = '';
  const SIZE = 126;
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', `0 0 ${SIZE} ${SIZE}`);
  svg.setAttribute('width', SIZE);
  svg.setAttribute('height', SIZE);

  const raices = data.anatomia.raices || ['unica'];
  const paths = raices.map((raiz, idx) => {
    if (raices.length === 1) return { raiz, d: `M45,4 Q35,76 63,122 Q91,76 81,4 Z` };
    if (raices.length === 2) return idx === 0
      ? { raiz, d: `M58,4 Q42,68 18,122 Q50,82 64,4 Z` }
      : { raiz, d: `M68,4 Q84,68 108,122 Q76,82 62,4 Z` };
    if (idx === 0) return { raiz, d: `M56,4 Q42,58 20,122 Q52,76 66,4 Z` };
    if (idx === 1) return { raiz, d: `M70,4 Q84,58 106,122 Q74,76 60,4 Z` };
    return { raiz, d: `M58,4 Q58,76 63,112 Q68,76 68,4 Z` };
  });

  paths.forEach((item) => {
    const condicion = (data.raices || []).find((r) => r.raiz === item.raiz);
    const col = colorCondicion(condicion ? (condicion.condicion_key || condicion.condicion) : 'sin_dato');
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', item.d);
    path.setAttribute('fill', col.fill);
    path.setAttribute('stroke', col.stroke);
    path.setAttribute('stroke-width', '2');
    const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
    title.textContent = `${item.raiz}: ${col.label}`;
    path.appendChild(title);
    svg.appendChild(path);
  });
  container.appendChild(svg);
}

function fetchGuardar(url, payload) {
  if (!modoEdicionOdontograma) {
    mostrarEstado('Este odontograma esta en modo solo lectura.', 'warning');
    return Promise.resolve();
  }
  mostrarEstado('Guardando...', 'info');
  return fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify(payload),
  })
    .then((res) => res.json().then((data) => ({ ok: res.ok, data })))
    .then(({ ok, data }) => {
      if (!ok || !data.success) throw new Error(data.error || 'No se pudo guardar.');
      return refrescarPiezaActual(data.message || 'Cambio guardado.');
    })
    .catch((err) => mostrarEstado(err.message || 'Error de red', 'danger'));
}

function refrescarPiezaActual(mensaje) {
  return fetch(`/odontograma/api/${ODONTOGRAMA_ID}/pieza/${piezaActualModal}/`)
    .then((res) => res.json())
    .then((data) => {
      if (!data.success) throw new Error(data.error || 'No se pudo refrescar la pieza.');
      llenarModal(data);
      actualizarTableroConPieza(data);
      mostrarEstado(mensaje, 'success');
    });
}

function actualizarTableroConPieza(data) {
  const dummyState = {};
  (data.superficies || []).forEach((s) => { dummyState[s.cara] = s.condicion_key || s.condicion; });
  dummyState._estado = data.estado_general || 'presente';
  estadoOdontograma[piezaActualModal] = dummyState;
  const wrapper = document.querySelector(`.diente-wrapper[data-diente="${piezaActualModal}"]`);
  if (wrapper) {
    const viejo = wrapper.querySelector('svg');
    const nuevo = crearDienteSVG(piezaActualModal);
    wrapper.replaceChild(nuevo, viejo);
  }
}

function guardarEstadoGeneral() {
  fetchGuardar(`/odontograma/api/${ODONTOGRAMA_ID}/pieza/${piezaActualModal}/estado/`, {
    estado_general: document.getElementById('select-estado-general').value,
    observacion: document.getElementById('observacion-pieza')?.value || '',
  });
}

function guardarSuperficie() {
  fetchGuardar(`/odontograma/api/${ODONTOGRAMA_ID}/pieza/${piezaActualModal}/superficie/`, {
    cara: document.getElementById('select-cara').value,
    condicion: document.getElementById('select-condicion-cara').value,
    observacion: document.getElementById('observacion-superficie')?.value || '',
  });
}

function guardarRaiz() {
  fetchGuardar(`/odontograma/api/${ODONTOGRAMA_ID}/pieza/${piezaActualModal}/raiz/`, {
    raiz: document.getElementById('select-raiz').value,
    tercio: document.getElementById('select-tercio').value,
    condicion: document.getElementById('select-condicion-raiz').value,
    observacion: document.getElementById('observacion-raiz')?.value || '',
  });
}

function guardarPeriodonto() {
  fetchGuardar(`/odontograma/api/${ODONTOGRAMA_ID}/pieza/${piezaActualModal}/periodonto/`, {
    movilidad: document.getElementById('perio-movilidad').value,
    furca: document.getElementById('perio-furca').value,
    profundidad_sondaje: document.getElementById('perio-sondaje').value,
    recesion: document.getElementById('perio-recesion').value,
    sangrado: document.getElementById('perio-sangrado').checked,
    placa: document.getElementById('perio-placa').checked,
    supuracion: document.getElementById('perio-supuracion').checked,
    observacion: document.getElementById('perio-observacion')?.value || '',
  });
}

function guardarDescripcion() {
  if (!modoEdicionOdontograma) {
    mostrarEstado('Este odontograma esta en modo solo lectura.', 'warning');
    return;
  }
  const texto = document.getElementById('desc-general-text').value;
  fetch(`/odontograma/api/${ODONTOGRAMA_ID}/descripcion/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify({ descripcion_general: texto }),
  })
    .then((res) => res.json().then((data) => ({ ok: res.ok, data })))
    .then(({ ok, data }) => {
      if (!ok || !data.success) throw new Error(data.error || 'No se pudo guardar la descripcion.');
      mostrarEstado('Descripcion guardada correctamente.', 'success');
    })
    .catch((err) => mostrarEstado(err.message, 'danger'));
}

function mostrarEstado(mensaje, tipo) {
  const status = document.getElementById('odontograma-status');
  if (!status) {
    if (tipo === 'danger') alert(mensaje);
    return;
  }
  status.className = `alert alert-${tipo} py-2 px-3 mb-3`;
  status.textContent = mensaje;
  status.hidden = false;
  if (tipo === 'success' || tipo === 'info') {
    window.setTimeout(() => { status.hidden = true; }, 2500);
  }
}
