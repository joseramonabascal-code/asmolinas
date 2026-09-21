# Pedido en la web → cotización automática desde el ERP

La página `pedido.html` deja que un negocio arme su pedido (productos y
kilos), deje sus datos y reciba la cotización sin que nadie la capture a mano.
El sitio es estático: todo lo que "piensa" vive en el ERP. Este documento es
el contrato entre los dos.

```
asmolinas.com/pedido.html                  ERP (Next.js, intranet.asmolinas.com)
┌──────────────────────────┐   POST JSON   ┌──────────────────────────────────┐
│ 1. elige productos       │ ────────────▶ │ /api/public/pedidos               │
│ 2. kilos por producto    │               │  · valida y filtra spam           │
│ 3. datos del negocio     │ ◀──────────── │  · alta/lookup de cliente (MOL42) │
│ 4. "Solicitar cotización"│  {ok, folio}  │  · precio vigente por volumen     │
└──────────────────────────┘               │  · crea COT 2026-0018             │
        │ si el ERP no responde            │  · PDF con imprimibles/           │
        ▼                                  │  · envía WhatsApp / correo        │
   WhatsApp con el pedido                  └──────────────────────────────────┘
```

Si el ERP no contesta en 9 s o devuelve error, la página abre WhatsApp con el
pedido completo ya redactado. Nada se pierde; sólo se cotiza a mano.

---

## 1. Lo que manda la página

`POST https://intranet.asmolinas.com/api/public/pedidos`
`Content-Type: application/json`

```json
{
  "origen": "asmolinas.com",
  "version": 1,
  "fecha": "2026-09-21T18:40:12.000Z",
  "pagina_origen": "/pedido.html",
  "cliente": {
    "empresa": "Cocina Central Ejemplo",
    "giro": "Comedor industrial",
    "contacto": "Nombre Apellido",
    "whatsapp": "5512345678",
    "correo": "compras@ejemplo.com",
    "ciudad": "CDMX, 06700",
    "rfc": "",
    "requiereCfdi": false
  },
  "partidas": [
    { "producto": "Chile guajillo seco", "presentacion": "Bulto cerrado 25 kg", "cantidad": 50, "unidad": "kg", "enCatalogo": true },
    { "producto": "Achiote en pasta",    "presentacion": "Según disponibilidad", "cantidad": 10, "unidad": "kg", "enCatalogo": false }
  ],
  "entrega": { "modo": "recoleccion" },
  "frecuencia": "Quincenal",
  "canal": "whatsapp",
  "comentarios": "Lo necesito para el viernes",
  "consentimiento": true
}
```

- `whatsapp` viene sólo con dígitos (10). El ERP le antepone `52`.
- `enCatalogo: false` marca productos escritos a mano: el ERP los casa por
  nombre normalizado o los deja como partida "por confirmar".
- `canal`: `whatsapp` · `correo` · `ambos`.
- `entrega.modo`: `recoleccion` · `flete`. El flete nunca se cotiza en
  automático: la cotización lo deja "a cargo del cliente; se cotiza aparte".

## 2. Lo que contesta el ERP

```json
{ "ok": true, "folio": "COT 2026-0018", "canal": ["whatsapp"], "ajustes": ["Comino entero: mínimo 25 kg"], "mensaje": "" }
```

- `folio`: el de la cotización creada. La página lo muestra grande.
- `canal`: por dónde se envió realmente (si no había correo, sólo WhatsApp).
- `ajustes`: partidas que subieron al mínimo por producto, en texto para el
  cliente. Vacío si no hubo.
- `mensaje`: texto libre opcional (p. ej. "Un producto se cotizará aparte").

Errores: `400` con `{ ok: false, error: "…" }` para datos inválidos; `429`
si el mismo origen manda más de N pedidos por hora. Cualquier código ≠ 2xx
dispara el respaldo por WhatsApp en la página.

**CORS.** La ruta debe responder `Access-Control-Allow-Origin:
https://asmolinas.com` (y `www.`) y atender el `OPTIONS` previo con
`Access-Control-Allow-Headers: Content-Type`.

## 3. Lo que hace el ERP con cada pedido

1. **Filtro.** Rechaza si falta empresa, contacto, WhatsApp o partidas; si
   `consentimiento` no es `true`; o si el campo trampa `sitio_web` llegara
   con valor (la página no lo manda, pero un bot que rellene todo sí).
   Límite por IP: 10 pedidos por hora.
2. **Cliente.** Busca por WhatsApp; si no existe, lo da de alta con número
   secuencial y clave `MOL` + número (`MOL42`). Guarda giro, ciudad y RFC.
3. **Precio.** Para cada partida: casa el producto con el catálogo (nombre
   normalizado), toma la lista de precios pública y elige el rango por
   volumen (10–19.9 / 20–24.9 / 25–399.9 / 400+ kg). Si la cantidad está por
   debajo del mínimo del SKU, la sube al mínimo y lo anota en `ajustes`. Si
   el producto no existe o no tiene precio vigente, la partida entra con
   precio 0 y la cotización lleva la nota "se confirma al cotizar"; el pedido
   se marca para revisión humana.
4. **Cotización.** Crea `COT AAAA-NNNN` con vigencia de 7 días, `atendio:
   "Cotización automática"`, y la misma estructura de datos que
   `imprimibles/imprimibles.js` espera (`cliente`, `partidas` con
   `cantidad`/`precio`/`iva`, `flete`, `nota`).
5. **PDF.** Renderiza `renderCotizacion(datos)` en Chromium (Playwright,
   `page.pdf({ format: 'Letter', printBackground: true })`) con
   `imprimibles.css`. Es el mismo HTML que se ve en `imprimibles/cotizacion.html`.
6. **Envío.** WhatsApp con el PDF adjunto y el texto corto (folio, total,
   vigencia, "responde a este mensaje para confirmar"), o correo con el PDF.
   El mensaje sale del número de la casa (748 166 0295) vía proveedor
   (WhatsApp Cloud API / Whapi / Twilio, el mismo que usa `agent/`).
7. **Bitácora.** `registrarActividad('cotizacion.automatica', …)` con el
   payload recibido y el folio; los pedidos con partidas sin precio quedan
   en la bandeja "Por revisar" del panel comercial.

## 4. Referencia de la ruta (Next.js App Router)

Esqueleto para `src/app/api/public/pedidos/route.ts` en la copia limpia del
ERP. Las funciones de `lib/` son las del sistema; aquí sólo se muestra el
orden y las decisiones.

```ts
import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { buscarOCrearCliente } from "@/lib/clientes";
import { precioVigente, minimoSku } from "@/lib/precios";
import { crearCotizacion } from "@/lib/cotizaciones";
import { renderCotizacionPdf } from "@/lib/imprimibles";
import { enviarWhatsApp, enviarCorreo } from "@/lib/mensajeria";
import { registrarActividad } from "@/lib/actividad";
import { limitarPorIp } from "@/lib/rateLimit";

const ORIGENES = ["https://asmolinas.com", "https://www.asmolinas.com"];
const cors = (req: NextRequest) => ({
  "Access-Control-Allow-Origin": ORIGENES.includes(req.headers.get("origin") ?? "") ? req.headers.get("origin")! : ORIGENES[0],
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
});

const Pedido = z.object({
  origen: z.literal("asmolinas.com"),
  version: z.literal(1),
  cliente: z.object({
    empresa: z.string().min(2), giro: z.string().min(2), contacto: z.string().min(2),
    whatsapp: z.string().regex(/^\d{10}$/), correo: z.string().email().or(z.literal("")),
    ciudad: z.string().min(2), rfc: z.string().max(13), requiereCfdi: z.boolean(),
  }),
  partidas: z.array(z.object({
    producto: z.string().min(2), presentacion: z.string(), cantidad: z.number().positive(),
    unidad: z.literal("kg"), enCatalogo: z.boolean(),
  })).min(1).max(40),
  entrega: z.object({ modo: z.enum(["recoleccion", "flete"]) }),
  frecuencia: z.string(), canal: z.enum(["whatsapp", "correo", "ambos"]),
  comentarios: z.string().max(1000), consentimiento: z.literal(true),
  sitio_web: z.string().max(0).optional(),        // trampa para bots
});

export async function OPTIONS(req: NextRequest) { return new NextResponse(null, { headers: cors(req) }); }

export async function POST(req: NextRequest) {
  const h = cors(req);
  if (!(await limitarPorIp(req, { porHora: 10 }))) return NextResponse.json({ ok: false, error: "Demasiados pedidos" }, { status: 429, headers: h });
  const parse = Pedido.safeParse(await req.json().catch(() => null));
  if (!parse.success) return NextResponse.json({ ok: false, error: "Datos incompletos" }, { status: 400, headers: h });
  const p = parse.data;

  const cliente = await buscarOCrearCliente({ whatsapp: "52" + p.cliente.whatsapp, ...p.cliente }); // asigna MOL42 si es nuevo
  const ajustes: string[] = [];
  let revisar = false;
  const partidas = [];
  for (const x of p.partidas) {
    const precio = await precioVigente(x.producto, x.cantidad);           // { productoId, precio, rango } | null
    const minimo = precio ? await minimoSku(precio.productoId, x.presentacion) : null;
    let cantidad = x.cantidad;
    if (minimo && cantidad < minimo) { cantidad = minimo; ajustes.push(`${x.producto}: mínimo ${minimo} kg`); }
    if (!precio) revisar = true;
    partidas.push({ producto: x.producto, presentacion: x.presentacion, cantidad, precio: precio?.precio ?? 0, iva: precio?.iva ?? 0, lote: null });
  }

  const cot = await crearCotizacion({
    clienteId: cliente.id, vigenciaDias: 7, atendio: "Cotización automática",
    flete: p.entrega.modo === "flete" ? "A cargo del cliente; se cotiza aparte según destino" : "Recolección en bodega",
    nota: revisar ? "Una o más partidas se confirman al cotizar." : "",
    partidas, origen: "web", revisar,
  });                                                                        // devuelve { folio: "COT 2026-0018", datosImprimible }

  const pdf = await renderCotizacionPdf(cot.datosImprimible);              // imprimibles/ → Chromium → Buffer
  const canal: string[] = [];
  if (p.canal !== "correo") { await enviarWhatsApp(cliente.whatsapp, textoCorto(cot), pdf); canal.push("whatsapp"); }
  if (p.canal !== "whatsapp" && p.cliente.correo) { await enviarCorreo(p.cliente.correo, `Cotización ${cot.folio} · AS Molinas`, textoCorto(cot), pdf); canal.push("correo"); }

  await registrarActividad("cotizacion.automatica", { folio: cot.folio, clienteId: cliente.id, revisar, payload: p });
  return NextResponse.json({ ok: true, folio: cot.folio, canal, ajustes, mensaje: revisar ? "Una partida se confirma con nuestro equipo; el resto ya está cotizado." : "" }, { headers: h });
}

const textoCorto = (c: { folio: string; total: number; vence: string }) =>
  `AS Molinas · ${c.folio}\nTotal cotizado: ${c.total.toLocaleString("es-MX", { style: "currency", currency: "MXN" })}\nVigente hasta el ${c.vence}.\nResponde a este mensaje para confirmar tu pedido.`;
```

## 5. Lo que ya existe y se reutiliza

- `GET /api/public/productos` → `[{ nombre, activo, stock }]`. La página lo
  usa para ocultar productos agotados (mismo comportamiento que el
  catálogo del inicio). Si no responde, muestra la lista completa.
- `imprimibles/imprimibles.js` y `.css`: el ERP renderiza la cotización con
  ellos; no hay un segundo diseño.
- Clave de cliente `MOL42`: la asigna `buscarOCrearCliente` al primer pedido
  y aparece en la cotización, en el concepto SPEI y en el recibo.
- `agent/` (WhatsApp con IA): comparte proveedor de mensajería. Cuando el
  cliente responde "confirmo" al mensaje de la cotización, el agente puede
  convertir la COT en REM; eso es un paso posterior.

## 6. Lo que la página promete y lo que no

- Promete: cotización con precio vigente por volumen, enviada por WhatsApp o
  correo; mínimo según producto; flete aparte; SPEI con CFDI.
- No promete tiempos de entrega ni de respuesta, ni precios en la página.
- Si el ERP no está, lo dice y manda el pedido por WhatsApp. El cliente
  nunca ve un error sin salida.

## 7. Medición

Eventos `dataLayer` que emite la página (GTM los recoge si se agrega el
contenedor a esta página): `envio_pedido` (productos, kilos, giro, canal),
`pedido_confirmado` (folio) y `pedido_fallback_whatsapp`.
