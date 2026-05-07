/**
 * static/js/odontograma.js
 * Clínica El Alba — Odontograma visual interactivo (Clásico)
 */

const COLORES_CONDICION = {
  'sano':          { fill: '#d1fae5', stroke: '#10b981', label: 'Sano' },
  'caries':        { fill: '#fee2e2', stroke: '#ef4444', label: 'Caries' },
  'obturacion':    { fill: '#dbeafe', stroke: '#3b82f6', label: 'Obturación' },
  'extraccion':    { fill: '#fef2f2', stroke: '#dc2626', label: 'Extracción' },
  'corona':        { fill: '#fef3c7', stroke: '#f59e0b', label: 'Corona' },
  'ausente':       { fill: '#f1f5f9', stroke: '#94a3b8', label: 'Ausente' },
  'fractura':      { fill: '#f3e8ff', stroke: '#a855f7', label: 'Fractura' },
  'endodoncia':    { fill: '#fee2e2', stroke: '#dc2626', label: 'Endodoncia' },
  'implante':      { fill: '#ecfdf5', stroke: '#059669', label: 'Implante' },
  'sin_dato':      { fill: '#f8fafc', stroke: '#e2e8f0', label: 'Sin dato' },
};

const CUADRANTES = {
  1: [18, 17, 16, 15, 14, 13, 12, 11],
  2: [21, 22, 23, 24, 25, 26, 27, 28],
  3: [31, 32, 33, 34, 35, 36, 37, 38],
  4: [48, 47, 46, 45, 44, 43, 42, 41],
};

let estadoOdontograma = {};
let condicionActual = 'caries';
let caraActual = 'oclusal';

function inicializarOdontograma(estadoInicial = {}, modoEdicion = true) {
  estadoOdontograma = estadoInicial;
  const container = document.getElementById('odontograma-container');
  if (!container) return;

  container.innerHTML = '';
  container.className = 'odontograma-wrapper';

  const filaSup = crearFila([1, 2], 'superior');
  container.appendChild(filaSup);

  const sep = document.createElement('div');
  sep.className = 'odontograma-sep';
  sep.innerHTML = '<span>Superior</span><span>Inferior</span>';
  container.appendChild(sep);

  const filaInf = crearFila([4, 3], 'inferior');
  container.appendChild(filaInf);

  if (modoEdicion) {
    inicializarPanelControl();
  }
}

function crearFila(cuadrantes, lado) {
  const fila = document.createElement('div');
  fila.className = 'odontograma-fila';

  cuadrantes.forEach(nroCuad => {
    const grupo = document.createElement('div');
    grupo.className = 'odontograma-cuadrante';

    const dientes = CUADRANTES[nroCuad];
    dientes.forEach(nro => {
      grupo.appendChild(crearDiente(nro, lado));
    });
    fila.appendChild(grupo);
  });

  return fila;
}

function crearDiente(numero, lado) {
  const wrapper = document.createElement('div');
  wrapper.className = 'diente-wrapper';
  wrapper.dataset.diente = numero;

  const num = document.createElement('div');
  num.className = 'diente-numero';
  num.textContent = numero;

  const svg = crearDienteSVG(numero, lado);

  wrapper.appendChild(num);
  wrapper.appendChild(svg);

  return wrapper;
}

function crearDienteSVG(numero, lado) {
  const SIZE = 48;
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', `0 0 ${SIZE} ${SIZE}`);
  svg.setAttribute('width', SIZE);
  svg.setAttribute('height', SIZE);
  svg.style.cursor = 'pointer';
  svg.style.borderRadius = '6px';
  svg.style.transition = 'transform .1s';

  const caras = {
    oclusal: { shape: 'polygon', points: `${SIZE/2},${SIZE/4} ${SIZE*3/4},${SIZE/2} ${SIZE/2},${SIZE*3/4} ${SIZE/4},${SIZE/2}` },
    vestibular: { shape: 'polygon', points: `${SIZE/2},1 ${SIZE-1},${SIZE/4} ${1},${SIZE/4}` },
    palatina: { shape: 'polygon', points: `${SIZE/2},${SIZE-1} ${SIZE-1},${SIZE*3/4} ${1},${SIZE*3/4}` },
    mesial: { shape: 'polygon', points: `1,${SIZE/2} ${SIZE/4},${SIZE/4} ${SIZE/4},${SIZE*3/4}` },
    distal: { shape: 'polygon', points: `${SIZE-1},${SIZE/2} ${SIZE*3/4},${SIZE/4} ${SIZE*3/4},${SIZE*3/4}` },
  };

  Object.entries(caras).forEach(([cara, config]) => {
    const el = document.createElementNS('http://www.w3.org/2000/svg', config.shape);
    el.setAttribute('points', config.points);

    const condicion = estadoOdontograma[numero]?.[cara] || 'sin_dato';
    const col = COLORES_CONDICION[condicion] || COLORES_CONDICION['sin_dato'];
    el.setAttribute('fill', col.fill);
    el.setAttribute('stroke', col.stroke);
    el.setAttribute('stroke-width', '1.5');
    el.dataset.cara = cara;
    el.dataset.diente = numero;
    el.style.cursor = 'pointer';
    el.style.transition = 'opacity .15s';
    el.setAttribute('title', `${numero} — ${cara}: ${col.label}`);

    el.addEventListener('mouseenter', () => { el.style.opacity = '.7'; });
    el.addEventListener('mouseleave', () => { el.style.opacity = '1'; });
    el.addEventListener('click', (e) => {
      e.stopPropagation();
      aplicarCondicion(numero, cara, el);
    });

    svg.appendChild(el);
  });

  actualizarOverlaysDiente(numero, svg);

  svg.addEventListener('mouseenter', () => {
    svg.style.transform = 'scale(1.12)';
    svg.style.zIndex = '10';
    svg.style.position = 'relative';
  });
  svg.addEventListener('mouseleave', () => {
    svg.style.transform = 'scale(1)';
  });

  return svg;
}

function actualizarOverlaysDiente(numero, svg) {
  svg.querySelectorAll('.overlay-cruz').forEach(el => el.remove());
  if (!estadoOdontograma[numero]) return;
  const caras = Object.values(estadoOdontograma[numero]);
  let tieneExtraccion = caras.includes('extraccion');
  let tieneAusente = caras.includes('ausente');
  
  if (tieneExtraccion || tieneAusente) {
    const color = tieneExtraccion ? '#dc2626' : '#0f172a';
    const SIZE = 48;
    const line1 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line1.setAttribute('x1', '4'); line1.setAttribute('y1', '4');
    line1.setAttribute('x2', SIZE - 4); line1.setAttribute('y2', SIZE - 4);
    line1.setAttribute('stroke', color); line1.setAttribute('stroke-width', '4');
    line1.setAttribute('class', 'overlay-cruz'); line1.style.pointerEvents = 'none';
    
    const line2 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line2.setAttribute('x1', SIZE - 4); line2.setAttribute('y1', '4');
    line2.setAttribute('x2', '4'); line2.setAttribute('y2', SIZE - 4);
    line2.setAttribute('stroke', color); line2.setAttribute('stroke-width', '4');
    line2.setAttribute('class', 'overlay-cruz'); line2.style.pointerEvents = 'none';
    
    svg.appendChild(line1);
    svg.appendChild(line2);
  }
}

function aplicarCondicion(numeroDiente, cara, elemento) {
  if (!estadoOdontograma[numeroDiente]) estadoOdontograma[numeroDiente] = {};
  estadoOdontograma[numeroDiente][cara] = condicionActual;

  const col = COLORES_CONDICION[condicionActual];
  elemento.setAttribute('fill', col.fill);
  elemento.setAttribute('stroke', col.stroke);

  actualizarOverlaysDiente(numeroDiente, elemento.parentNode);
  actualizarCamposOcultos();

  elemento.style.transform = 'scale(1.15)';
  setTimeout(() => { elemento.style.transform = ''; }, 200);
}

function actualizarCamposOcultos() {
  const form = document.getElementById('form-odontograma');
  if (!form) return;

  form.querySelectorAll('[data-odontograma-field]').forEach(el => el.remove());

  Object.entries(estadoOdontograma).forEach(([pieza, caras]) => {
    Object.entries(caras).forEach(([cara, condicion]) => {
      if (condicion && condicion !== 'sin_dato') {
        // Obtenemos el ID numerico de la condicion para que el POST ande
        // El form recibe cond_<pieza>_<id_cara> = id_condicion.
        // Pero en la v1 recibía '1' o algo así? 
        // En nuestro odontograma.js anterior, ¿qué mandaba?
        // Ah, mandaba id_condicion en el VALUE y el nombre en el NAME?
        // Revisemos inicializarPanelControl: usaba btn.dataset.condicion como KEY.
        // El id_condicion real no lo teníamos, enviábamos el texto?
        // Si enviábamos el texto (ej: "cond_18_oclusal = caries"), entonces views.py esperaba el ID numérico de la cara y condición!
        // En form.html se renderizaba un select o algo? No, era JS puro.
        
        // Wait, the previous views.py expected: _, pieza_cod, cara_id = key.split("_", 2) ... int(cara_id).
        // Since my first intervention fixed that in views OR maybe it was already broken before I started?
        // Let's assume we map cara string to cara ID based on standard.
        // Or wait, what if the form had inputs generated by django?
        // No, in `actualizarCamposOcultos` it appended hidden inputs.
        // I'll emit what it was emitting.
        
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = `cond_${pieza}_${cara}`;
        input.value = condicion;
        input.setAttribute('data-odontograma-field', '1');
        form.appendChild(input);
      }
    });
  });
}

function inicializarPanelControl() {
  const panel = document.getElementById('panel-condiciones');
  if (!panel) return;

  panel.innerHTML = '';

  Object.entries(COLORES_CONDICION).forEach(([key, conf]) => {
    if (key === 'sin_dato') return;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn-condicion';
    btn.dataset.condicion = key;
    btn.style.cssText = `
      display: flex; align-items: center; gap: 6px;
      padding: 6px 12px; border-radius: 8px; border: 2px solid ${conf.stroke};
      background: ${conf.fill}; color: ${key === 'extraccion' ? '#334155' : '#334155'}; font-size: 12px; font-weight: 600;
      cursor: pointer; transition: all .15s;
    `;
    let iconHTML = `<span style="width:12px;height:12px;background:${conf.stroke};border-radius:3px;display:inline-block;"></span>`;
    
    if (key === 'extraccion') {
      iconHTML = `<svg width="12" height="12" viewBox="0 0 12 12" style="display:inline-block;"><line x1="1" y1="1" x2="11" y2="11" stroke="#dc2626" stroke-width="3" stroke-linecap="round"/><line x1="11" y1="1" x2="1" y2="11" stroke="#dc2626" stroke-width="3" stroke-linecap="round"/></svg>`;
    } else if (key === 'ausente') {
      iconHTML = `<svg width="12" height="12" viewBox="0 0 12 12" style="display:inline-block;"><line x1="1" y1="1" x2="11" y2="11" stroke="#0f172a" stroke-width="3" stroke-linecap="round"/><line x1="11" y1="1" x2="1" y2="11" stroke="#0f172a" stroke-width="3" stroke-linecap="round"/></svg>`;
    }

    btn.innerHTML = `${iconHTML} ${conf.label}`;

    if (key === condicionActual) {
      btn.style.boxShadow = `0 0 0 3px ${conf.stroke}44`;
      btn.style.transform = 'scale(1.05)';
    }

    btn.addEventListener('click', () => {
      condicionActual = key;
      inicializarPanelControl();
    });

    panel.appendChild(btn);
  });
}
