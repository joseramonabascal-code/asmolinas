/* ============================================================
   AS MOLINAS — Renderizador de imprimibles
   ============================================================
   Un solo archivo con:
     1. EMPRESA        datos de la casa (lo único que se edita al configurar)
     2. Folios         COT 2026-0001 · REM 2026-0001 · REC 2026-0001 · EDC 2026-09
     3. Clave cliente  MOL-0042-69  (número de cliente + 2 dígitos de control mod 97)
     4. Concepto SPEI  "<folio> <clave>"  → cada pago se casa con su documento
     5. Verificación   código corto por documento (folio + total + fecha)
     6. render*()      cotización, remisión, recibo de pago, estado de cuenta

   Todo es JS puro sin dependencias, para que el ERP/intranet lo importe tal
   cual (o lo porte a TypeScript sin cambiar los formatos).
   ============================================================ */

/* 1. La casa ------------------------------------------------------------ */
// Regla: nunca inventar RFC, CLABE ni cuentas. Si un campo está vacío, el
// documento lo dice ("se comparte al confirmar") en lugar de mostrar un hueco.
const EMPRESA = {
  nombre: 'AS Molinas',
  lema: 'Especias, chiles secos y semillas al mayoreo para negocios',
  whatsapp: '748 166 0295',
  whatsappUrl: 'https://wa.me/527481660295',
  email: 'info@asmolinas.com',
  web: 'asmolinas.com',
  ubicacion: 'CDMX y Área Metropolitana · envíos a todo México',
  horario: 'Lunes a sábado, 9 a 19 h',
  fiscal: { razonSocial: '', rfc: '', regimen: '' },
  banco:  { titular: '', banco: '', clabe: '', cuenta: '' },
};

/* 2. Folios --------------------------------------------------------------- */
const TIPOS = {
  COT: 'Cotización',
  REM: 'Remisión',
  REC: 'Recibo de pago',
  EDC: 'Estado de cuenta',
};

// folio('REM', 2026, 31) → "REM 2026-0031"
function folio(tipo, anio, consecutivo) {
  if (!TIPOS[tipo]) throw new Error('Tipo de documento desconocido: ' + tipo);
  return `${tipo} ${anio}-${String(consecutivo).padStart(4, '0')}`;
}
// folioMensual('EDC', 2026, 9) → "EDC 2026-09"
function folioMensual(tipo, anio, mes) {
  return `${tipo} ${anio}-${String(mes).padStart(2, '0')}`;
}

/* 3. Clave de cliente ----------------------------------------------------- */
// MOL-NNNN-CC. NNNN es el número de cliente (secuencial, lo asigna el
// sistema al darlo de alta); CC son dos dígitos de control ISO 7064 mod 97-10,
// los mismos que usa el IBAN: detectan cualquier error de un dígito y casi
// todas las transposiciones. No es un hash del nombre: dos clientes nunca
// comparten clave y renombrar al cliente no la cambia.
function claveCliente(numeroCliente) {
  const n = Number(numeroCliente);
  if (!Number.isInteger(n) || n < 1 || n > 9999) throw new Error('Número de cliente fuera de rango (1-9999)');
  const cc = 98 - ((n * 100) % 97);
  return `MOL-${String(n).padStart(4, '0')}-${String(cc).padStart(2, '0')}`;
}
function validarClave(clave) {
  const m = /^MOL-(\d{4})-(\d{2})$/.exec(String(clave).trim().toUpperCase());
  if (!m) return false;
  return (Number(m[1]) * 100 + Number(m[2])) % 97 === 1;
}

/* 4. Concepto SPEI ---------------------------------------------------------- */
// Lo que el cliente escribe en el concepto de la transferencia. Con folio y
// clave juntos, el depósito identifica al cliente Y al documento que paga.
// Máximo 40 caracteres (límite habitual de concepto SPEI): "REM 2026-0031 MOL-0042-69" son 25.
function conceptoSpei(folioDoc, clave) {
  return `${folioDoc} ${clave}`.slice(0, 40);
}

/* 5. Código de verificación --------------------------------------------------- */
// FNV-1a de 32 bits sobre folio|total|fecha, en base 36, 6 caracteres. Sirve
// para que un documento reimpreso o reenviado se pueda cotejar contra el
// sistema sin exponer nada más. No es criptográfico: es una huella de cotejo.
function codigoVerificacion(folioDoc, total, fechaISO) {
  const s = `${folioDoc}|${Number(total).toFixed(2)}|${fechaISO}`;
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; }
  return h.toString(36).toUpperCase().padStart(6, '0').slice(-6);
}

/* Utilidades ---------------------------------------------------------------- */
const fmtMXN = new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', minimumFractionDigits: 2 });
const fmtKg  = new Intl.NumberFormat('es-MX', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
const money = (n) => fmtMXN.format(Number(n) || 0);
const kg    = (n) => `${fmtKg.format(Number(n) || 0)} kg`;

function fechaLarga(iso) {
  if (!iso) return '';
  const [y, m, d] = iso.split('-').map(Number);
  const dt = new Date(y, m - 1, d);
  return dt.toLocaleDateString('es-MX', { day: 'numeric', month: 'long', year: 'numeric' });
}
// Para tablas: "21 sep 2026" (no se parte en dos líneas)
function fechaCorta(iso) {
  if (!iso) return '';
  const [y, m, d] = iso.split('-').map(Number);
  const dt = new Date(y, m - 1, d);
  return dt.toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' }).replace('.', '');
}
function sumaDias(iso, dias) {
  const [y, m, d] = iso.split('-').map(Number);
  const dt = new Date(y, m - 1, d + Number(dias));
  return `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}-${String(dt.getDate()).padStart(2, '0')}`;
}
function diasEntre(isoA, isoB) {
  const a = new Date(isoA + 'T00:00:00'), b = new Date(isoB + 'T00:00:00');
  return Math.round((b - a) / 86400000);
}
function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

// Cantidad con letra, es-MX, para remisiones y recibos.
function cantidadConLetra(n) {
  const U = ['', 'un', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve', 'diez', 'once', 'doce', 'trece', 'catorce', 'quince', 'dieciséis', 'diecisiete', 'dieciocho', 'diecinueve', 'veinte', 'veintiún', 'veintidós', 'veintitrés', 'veinticuatro', 'veinticinco', 'veintiséis', 'veintisiete', 'veintiocho', 'veintinueve'];
  const D = ['', '', 'veinte', 'treinta', 'cuarenta', 'cincuenta', 'sesenta', 'setenta', 'ochenta', 'noventa'];
  const C = ['', 'ciento', 'doscientos', 'trescientos', 'cuatrocientos', 'quinientos', 'seiscientos', 'setecientos', 'ochocientos', 'novecientos'];
  function cientos(x) {
    if (x === 0) return '';
    if (x === 100) return 'cien';
    let s = C[Math.floor(x / 100)];
    const r = x % 100;
    if (r === 0) return s;
    if (r < 30) s += (s ? ' ' : '') + U[r];
    else s += (s ? ' ' : '') + D[Math.floor(r / 10)] + (r % 10 ? ' y ' + U[r % 10] : '');
    return s;
  }
  function entero(x) {
    if (x === 0) return 'cero';
    let s = '';
    const millones = Math.floor(x / 1e6), miles = Math.floor((x % 1e6) / 1000), resto = x % 1000;
    if (millones) s += (millones === 1 ? 'un millón' : cientos(millones) + ' millones');
    if (miles) s += (s ? ' ' : '') + (miles === 1 ? 'mil' : cientos(miles) + ' mil');
    if (resto) s += (s ? ' ' : '') + cientos(resto);
    return s;
  }
  const v = Math.round(Number(n) * 100);
  const ent = Math.floor(v / 100), cen = v % 100;
  let letras = entero(ent);
  // "un millón DE pesos" cuando la cifra es un múltiplo exacto de millón
  if (ent >= 1e6 && ent % 1e6 === 0) letras += ' de';
  letras = letras.charAt(0).toUpperCase() + letras.slice(1);
  return `(${letras} peso${ent === 1 ? '' : 's'} ${String(cen).padStart(2, '0')}/100 M.N.)`;
}

/* Piezas comunes ----------------------------------------------------------------- */
function bloqueMarca() {
  return `
    <div class="marca">
      <div class="nombre">AS <span>Molinas</span></div>
      <div class="lema">${esc(EMPRESA.lema)}</div>
      <div class="datos">
        WhatsApp ${esc(EMPRESA.whatsapp)} · ${esc(EMPRESA.email)} · ${esc(EMPRESA.web)}<br>
        ${esc(EMPRESA.ubicacion)}
        ${EMPRESA.fiscal.razonSocial ? `<br>${esc(EMPRESA.fiscal.razonSocial)}${EMPRESA.fiscal.rfc ? ' · RFC ' + esc(EMPRESA.fiscal.rfc) : ''}` : ''}
      </div>
    </div>`;
}

function bloqueDocumento(tipo, folioDoc, metaHtml, sello) {
  return `
    <div class="documento">
      <div class="tipo">${esc(TIPOS[tipo])}</div>
      <div class="folio">${esc(folioDoc)}</div>
      <div class="meta">${metaHtml}</div>
      ${sello ? `<span class="sello ${sello.clase || ''}">${esc(sello.texto)}</span>` : ''}
    </div>`;
}

function tarjetaCliente(c, titulo = 'Cliente') {
  const clave = c.clave || (c.numero ? claveCliente(c.numero) : '');
  return `
    <div class="tarjeta">
      <h3>${esc(titulo)}</h3>
      <div class="titular">${esc(c.nombre)}</div>
      <dl>
        ${c.razonSocial ? `<dt>Razón social</dt><dd>${esc(c.razonSocial)}</dd>` : ''}
        ${c.rfc ? `<dt>RFC</dt><dd>${esc(c.rfc)}</dd>` : ''}
        ${c.contacto ? `<dt>Atención</dt><dd>${esc(c.contacto)}</dd>` : ''}
        ${c.telefono ? `<dt>Teléfono</dt><dd>${esc(c.telefono)}</dd>` : ''}
        ${c.direccion ? `<dt>Entrega</dt><dd>${esc(c.direccion)}</dd>` : ''}
        ${clave ? `<dt>Clave de pago</dt><dd class="clave">${esc(clave)}</dd>` : ''}
      </dl>
    </div>`;
}

function tarjetaCondiciones(titulo, pares) {
  return `
    <div class="tarjeta">
      <h3>${esc(titulo)}</h3>
      <dl>${pares.filter(([, v]) => v !== undefined && v !== null && v !== '').map(([k, v]) => `<dt>${esc(k)}</dt><dd>${v}</dd>`).join('')}</dl>
    </div>`;
}

function calcularTotales(partidas) {
  let subtotal = 0, iva = 0;
  for (const p of partidas) {
    const importe = Number(p.cantidad) * Number(p.precio);
    subtotal += importe;
    iva += importe * (Number(p.iva) || 0);
  }
  return { subtotal, iva, total: subtotal + iva };
}

function tablaPartidas(partidas, { conLote = false, conPrecio = true } = {}) {
  const filas = partidas.map((p, i) => {
    const importe = Number(p.cantidad) * Number(p.precio);
    return `
      <tr>
        <td class="n">${i + 1}</td>
        <td><span class="prod">${esc(p.producto)}</span>${p.presentacion ? `<span class="pres">${esc(p.presentacion)}</span>` : ''}</td>
        ${conLote ? `<td class="lote">${esc(p.lote || '—')}</td>` : ''}
        <td class="num">${kg(p.cantidad)}</td>
        ${conPrecio ? `<td class="num">${money(p.precio)}</td><td class="num">${money(importe)}</td>` : ''}
      </tr>`;
  }).join('');
  return `
    <table class="partidas">
      <thead><tr>
        <th></th><th>Producto y presentación</th>
        ${conLote ? '<th>Lote</th>' : ''}
        <th class="num">Cantidad</th>
        ${conPrecio ? '<th class="num">Precio / kg</th><th class="num">Importe</th>' : ''}
      </tr></thead>
      <tbody>${filas}</tbody>
    </table>`;
}

function bloqueTotales(partidas, notaHtml, { conLetra = false } = {}) {
  const t = calcularTotales(partidas);
  const totalKg = partidas.reduce((s, p) => s + Number(p.cantidad), 0);
  return `
    <div class="totales">
      <div class="nota">${notaHtml || ''}</div>
      <table>
        <tr><td>Volumen total</td><td>${kg(totalKg)}</td></tr>
        <tr><td>Subtotal</td><td>${money(t.subtotal)}</td></tr>
        <tr><td>IVA</td><td>${money(t.iva)}</td></tr>
        <tr class="gran"><td>Total</td><td>${money(t.total)}</td></tr>
        ${conLetra ? `<tr><td colspan="2" class="letra">${esc(cantidadConLetra(t.total))}</td></tr>` : ''}
      </table>
    </div>`;
}

function bloquePago(folioDoc, clave, { generico = false } = {}) {
  const b = EMPRESA.banco;
  const datos = b.clabe
    ? `<div class="spei"><b>${esc(b.banco)}</b> · ${esc(b.titular)}<br>CLABE <b>${esc(b.clabe)}</b>${b.cuenta ? ` · Cuenta ${esc(b.cuenta)}` : ''}</div>`
    : `<div>Los datos bancarios se comparten por WhatsApp al confirmar el pedido.</div>`;
  // En un estado de cuenta no hay un solo documento que pagar: el concepto
  // lleva la clave y el folio de la remisión que se liquida.
  const concepto = generico
    ? `<div>En el concepto de tu transferencia escribe el folio de la remisión que pagas y tu clave:</div>
       <span class="concepto">REM 2026-0000 ${esc(clave)}</span>`
    : `<div>Escribe este concepto en tu transferencia:</div>
       <span class="concepto">${esc(conceptoSpei(folioDoc, clave))}</span>`;
  return `
    <div class="bloque">
      <h4>Forma de pago</h4>
      <div>Transferencia SPEI o depósito. No aceptamos tarjeta ni crédito automático.</div>
      ${datos}
      ${concepto}
      <div>Emitimos CFDI en todos los pedidos.</div>
    </div>`;
}

function bloqueCondiciones(items) {
  return `
    <div class="bloque">
      <h4>Condiciones</h4>
      <ul>${items.map((i) => `<li>${i}</li>`).join('')}</ul>
    </div>`;
}

function pie(folioDoc, total, fechaISO, extra = '') {
  return `
    <div class="pie">
      <div>${esc(EMPRESA.nombre)} · ${esc(EMPRESA.web)} · WhatsApp ${esc(EMPRESA.whatsapp)}${extra ? ' · ' + extra : ''}</div>
      <div class="verif">Verificación ${codigoVerificacion(folioDoc, total, fechaISO)}</div>
    </div>`;
}

/* 6. Documentos --------------------------------------------------------------------- */
function renderCotizacion(d) {
  const f = folio('COT', d.anio, d.consecutivo);
  const vence = sumaDias(d.fecha, d.vigenciaDias || 7);
  const clave = d.cliente.clave || claveCliente(d.cliente.numero);
  const t = calcularTotales(d.partidas);
  return `
    <div class="cabecera">
      ${bloqueMarca()}
      ${bloqueDocumento('COT', f, `Fecha <b>${esc(fechaLarga(d.fecha))}</b><br>Vigente hasta <b>${esc(fechaLarga(vence))}</b>${d.atendio ? `<br>Atendió <b>${esc(d.atendio)}</b>` : ''}`,
        { texto: `Vigencia ${d.vigenciaDias || 7} días`, clase: 'gris' })}
    </div>
    <div class="tarjetas">
      ${tarjetaCliente(d.cliente)}
      ${tarjetaCondiciones('Condiciones de la propuesta', [
        ['Precios', 'Por kg, en MXN, vigentes hasta la fecha indicada'],
        ['Mínimo', 'Según producto y presentación'],
        ['Disponibilidad', 'Sujeta a existencia; se confirma lote al cerrar'],
        ['Flete', d.flete || 'A cargo del cliente; se cotiza aparte'],
        ['Pago', 'SPEI o depósito antes de surtir'],
      ])}
    </div>
    ${tablaPartidas(d.partidas)}
    ${bloqueTotales(d.partidas, d.nota ? esc(d.nota) : 'El precio por kg baja con el volumen. Si tu operación necesita más de lo cotizado, pide el siguiente rango.')}
    <div class="pie-bloques">
      ${bloquePago(f, clave)}
      ${bloqueCondiciones([
        'Esta cotización no aparta mercancía; el pedido queda confirmado con el pago.',
        'Presentación y origen según disponibilidad del proveedor; ficha técnica cuando exista.',
        'Cantidades en kg. Diferencias por pesaje se ajustan en la remisión.',
        `Para confirmar, responde por WhatsApp con el folio <b>${esc(f)}</b>.`,
      ])}
    </div>
    ${pie(f, t.total, d.fecha)}`;
}

function renderRemision(d) {
  const f = folio('REM', d.anio, d.consecutivo);
  const clave = d.cliente.clave || claveCliente(d.cliente.numero);
  const t = calcularTotales(d.partidas);
  const credito = Number(d.diasCredito) > 0;
  const vence = credito ? sumaDias(d.fecha, d.diasCredito) : null;
  return `
    <div class="cabecera">
      ${bloqueMarca()}
      ${bloqueDocumento('REM', f, `Fecha <b>${esc(fechaLarga(d.fecha))}</b>${d.cotizacion ? `<br>Cotización <b>${esc(d.cotizacion)}</b>` : ''}${vence ? `<br>Vence <b>${esc(fechaLarga(vence))}</b>` : ''}`,
        credito ? { texto: `Crédito ${d.diasCredito} días` } : { texto: 'Contado', clase: 'ok' })}
    </div>
    <div class="tarjetas">
      ${tarjetaCliente(d.cliente)}
      ${tarjetaCondiciones('Entrega', [
        ['Lugar', esc(d.entrega?.lugar || d.cliente.direccion || 'Recolección en bodega')],
        ['Fecha', esc(fechaLarga(d.entrega?.fecha || d.fecha))],
        ['Transporte', esc(d.entrega?.transporte || 'Flete a cargo del cliente')],
        ['Recibe', esc(d.entrega?.recibe || '')],
        ['Bultos', d.entrega?.bultos ? esc(String(d.entrega.bultos)) : ''],
      ])}
    </div>
    ${tablaPartidas(d.partidas, { conLote: true })}
    ${bloqueTotales(d.partidas, 'Los lotes indicados son los que se entregan. Conserva esta remisión para cualquier aclaración: es el documento que ampara la mercancía.', { conLetra: true })}
    <div class="pie-bloques">
      ${bloquePago(f, clave)}
      ${bloqueCondiciones([
        'Revisa cantidad y estado de la mercancía al recibir; las diferencias se reportan el mismo día.',
        'Producto seco: almacenar cerrado, en lugar fresco y sin humedad.',
        credito ? `Pago a ${d.diasCredito} días, vence el ${esc(fechaLarga(vence))}.` : 'Pagado de contado.',
        'Esta remisión no es comprobante fiscal; el CFDI se emite con los datos fiscales registrados.',
      ])}
    </div>
    <div class="firmas">
      <div class="firma"><b>Entregó</b>${esc(d.entrego || EMPRESA.nombre)}</div>
      <div class="firma"><b>Recibió de conformidad</b>Nombre y firma</div>
    </div>
    ${pie(f, t.total, d.fecha)}`;
}

function renderRecibo(d) {
  const f = folio('REC', d.anio, d.consecutivo);
  const clave = d.cliente.clave || claveCliente(d.cliente.numero);
  const aplicado = d.aplicaciones.reduce((s, a) => s + Number(a.monto), 0);
  const saldoFavor = Math.max(0, Number(d.monto) - aplicado);
  const filas = d.aplicaciones.map((a, i) => `
    <tr>
      <td class="n">${i + 1}</td>
      <td><span class="prod">${esc(a.documento)}</span><span class="pres">${esc(a.descripcion || '')}</span></td>
      <td class="num">${money(a.saldoAnterior)}</td>
      <td class="num">${money(a.monto)}</td>
      <td class="num">${money(Number(a.saldoAnterior) - Number(a.monto))}</td>
    </tr>`).join('');
  return `
    <div class="cabecera">
      ${bloqueMarca()}
      ${bloqueDocumento('REC', f, `Fecha de pago <b>${esc(fechaLarga(d.fecha))}</b><br>Forma <b>${esc(d.forma)}</b>${d.referencia ? `<br>Referencia <b>${esc(d.referencia)}</b>` : ''}`,
        { texto: 'Pago recibido', clase: 'ok' })}
    </div>
    <div class="tarjetas">
      ${tarjetaCliente(d.cliente, 'Recibimos de')}
      ${tarjetaCondiciones('Importe recibido', [
        ['Monto', `<b>${money(d.monto)}</b>`],
        ['Con letra', esc(cantidadConLetra(d.monto))],
        ['Aplicado', money(aplicado)],
        ['Saldo a favor', saldoFavor > 0 ? `<b>${money(saldoFavor)}</b>` : '—'],
      ])}
    </div>
    <table class="partidas">
      <thead><tr><th></th><th>Documento que paga</th><th class="num">Saldo anterior</th><th class="num">Aplicado</th><th class="num">Saldo restante</th></tr></thead>
      <tbody>${filas}</tbody>
    </table>
    <div class="pie-bloques">
      <div class="bloque">
        <h4>Para tu control</h4>
        <div>Tu clave de pago es <span class="concepto">${esc(clave)}</span></div>
        <div>Úsala en el concepto de cada transferencia junto con el folio del documento que pagas. Así el pago se aplica el mismo día.</div>
      </div>
      ${bloqueCondiciones([
        'Este recibo confirma la aplicación del pago a los documentos listados.',
        saldoFavor > 0 ? `El saldo a favor de ${money(saldoFavor)} queda disponible para tu siguiente pedido.` : 'No queda saldo a favor.',
        'El CFDI de pago (complemento) se emite conforme a la operación.',
      ])}
    </div>
    ${pie(f, d.monto, d.fecha)}`;
}

function renderEstadoCuenta(d) {
  const f = folioMensual('EDC', d.anio, d.mes);
  const clave = d.cliente.clave || claveCliente(d.cliente.numero);
  const hoy = d.corte;
  let saldoTotal = 0, vencido = 0, porVencer = 0;
  const filas = d.documentos.map((doc) => {
    const saldo = Number(doc.importe) - Number(doc.abonos || 0);
    const vence = sumaDias(doc.fecha, doc.diasCredito || 0);
    const dias = diasEntre(vence, hoy);
    const estaVencido = saldo > 0.005 && dias > 0;
    saldoTotal += saldo;
    if (estaVencido) vencido += saldo; else porVencer += saldo;
    return `
      <tr>
        <td><span class="prod">${esc(doc.folio)}</span><span class="pres">${esc(doc.descripcion || '')}</span></td>
        <td style="white-space:nowrap">${esc(fechaCorta(doc.fecha))}</td>
        <td style="white-space:nowrap">${esc(fechaCorta(vence))}</td>
        <td class="num">${money(doc.importe)}</td>
        <td class="num">${money(doc.abonos || 0)}</td>
        <td class="num ${estaVencido ? 'vencido' : ''}">${money(saldo)}</td>
        <td class="num ${estaVencido ? 'vencido' : ''}">${saldo > 0.005 ? (dias > 0 ? `${dias} d` : 'al corriente') : 'pagado'}</td>
      </tr>`;
  }).join('');
  return `
    <div class="cabecera">
      ${bloqueMarca()}
      ${bloqueDocumento('EDC', f, `Corte al <b>${esc(fechaLarga(hoy))}</b><br>Periodo <b>${esc(d.periodo || '')}</b>`,
        vencido > 0.005 ? { texto: 'Con saldo vencido' } : { texto: 'Al corriente', clase: 'ok' })}
    </div>
    <div class="tarjetas">
      ${tarjetaCliente(d.cliente)}
      ${tarjetaCondiciones('Condiciones de crédito', [
        ['Plazo', `${esc(String(d.cliente.diasCredito ?? '—'))} días`],
        ['Pago', 'SPEI o depósito con clave y folio en el concepto'],
        ['Aclaraciones', `WhatsApp ${esc(EMPRESA.whatsapp)}`],
      ])}
    </div>
    <div class="resumen">
      <div class="kpi"><div class="et">Saldo total</div><div class="v">${money(saldoTotal)}</div></div>
      <div class="kpi ${vencido > 0.005 ? 'alerta' : ''}"><div class="et">Vencido</div><div class="v">${money(vencido)}</div></div>
      <div class="kpi"><div class="et">Por vencer</div><div class="v">${money(porVencer)}</div></div>
      <div class="kpi"><div class="et">Documentos</div><div class="v">${d.documentos.length}</div></div>
    </div>
    <table class="partidas">
      <thead><tr><th>Documento</th><th>Fecha</th><th>Vence</th><th class="num">Importe</th><th class="num">Abonos</th><th class="num">Saldo</th><th class="num">Antigüedad</th></tr></thead>
      <tbody>${filas}</tbody>
    </table>
    <div class="pie-bloques">
      ${bloquePago(f, clave, { generico: true })}
      ${bloqueCondiciones([
        'Los pagos recibidos después de la fecha de corte no aparecen en este estado.',
        'Si un pago ya fue hecho y no está aplicado, envíanos el comprobante con el folio.',
        vencido > 0.005 ? 'Los documentos marcados están vencidos; te pedimos regularizarlos para seguir surtiendo.' : 'Gracias por mantener tu cuenta al corriente.',
      ])}
    </div>
    ${pie(f, saldoTotal, hoy)}`;
}

/* Montaje en página --------------------------------------------------------------------- */
const RENDER = { COT: renderCotizacion, REM: renderRemision, REC: renderRecibo, EDC: renderEstadoCuenta };

function montar(tipo, datos) {
  const hoja = document.querySelector('.hoja');
  hoja.innerHTML = RENDER[tipo](datos);
  const folioTxt = hoja.querySelector('.folio')?.textContent || '';
  document.title = `${TIPOS[tipo]} ${folioTxt} · AS Molinas`;
}

// Barra: imprimir y cargar un JSON exportado por el sistema.
function barra(tipo, datosEjemplo) {
  const b = document.querySelector('.barra');
  if (!b) return;
  b.innerHTML = `
    <button type="button" data-imprimir>Imprimir o guardar PDF</button>
    <button type="button" class="sec" data-cargar>Cargar JSON</button>
    <input type="file" accept="application/json" hidden>
    <span>Se muestra un ejemplo. Carga el JSON del sistema para imprimir un documento real.</span>`;
  b.querySelector('[data-imprimir]').addEventListener('click', () => window.print());
  const input = b.querySelector('input');
  b.querySelector('[data-cargar]').addEventListener('click', () => input.click());
  input.addEventListener('change', async () => {
    const file = input.files[0]; if (!file) return;
    try { montar(tipo, JSON.parse(await file.text())); }
    catch (e) { alert('El archivo no es un JSON válido: ' + e.message); }
  });
  montar(tipo, datosEjemplo);
}

if (typeof module !== 'undefined') {
  module.exports = { EMPRESA, TIPOS, folio, folioMensual, claveCliente, validarClave, conceptoSpei, codigoVerificacion, cantidadConLetra, calcularTotales, renderCotizacion, renderRemision, renderRecibo, renderEstadoCuenta };
}
