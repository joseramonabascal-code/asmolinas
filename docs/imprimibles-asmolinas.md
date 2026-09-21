# Imprimibles y referencias de AS Molinas

Diseño y formato propios de los documentos que AS Molinas entrega a sus
clientes: cotización, remisión, recibo de pago y estado de cuenta, más el
esquema de folios y de referencias de pago.

Están hechos a propósito para **no parecerse** a los del sistema de Grupo
Abascal. Si el ERP se monta para AS Molinas a partir de una copia limpia,
estos son los formatos que sustituyen a los suyos.

Archivos:

```
imprimibles/
├── imprimibles.css     ← identidad visual (papel crema, verde bosque, terracota)
├── imprimibles.js      ← EMPRESA, folios, clave de cliente, concepto SPEI, render*()
├── cotizacion.html     ← COT
├── remision.html       ← REM
├── recibo-pago.html    ← REC
└── estado-cuenta.html  ← EDC
```

Las páginas cargan un ejemplo y tienen dos botones: **Imprimir o guardar PDF**
y **Cargar JSON** (el JSON que exporta el sistema por documento). No están
enlazadas desde el sitio, llevan `noindex` y `robots.txt` las bloquea.

---

## 1. En qué se diferencian del sistema de Grupo Abascal

| | Grupo Abascal | AS Molinas |
|---|---|---|
| Fondo y color | Tema oscuro, azul de marca | Papel crema, tinta verde bosque, acento terracota, filete oro |
| Tipografía | Sans, PDF **en mayúsculas** | Titulares en serif (DM Serif Display), texto DM Sans, **frase normal** |
| Tablas | jsPDF con rejilla completa | Sin rejilla: filetes horizontales finos y aire |
| Composición | Membrete arriba, tabla, totales | Cinta de marca; **resumen en verde** con tipo, folio, total y vencimiento; **una sola lista** de datos del cliente; tabla; totales; **"Cómo pagar" en 3 pasos**; condiciones breves |
| Folio | Número corrido | `COT 2026-0018`, `REM 2026-0031`, `REC 2026-0009`, `EDC 2026-09` |
| Clave del cliente | `AB####`, hash del nombre (puede repetirse) | `MOL-0042-69`: número de cliente + 2 dígitos de control mod 97 (única y verificable) |
| Concepto de pago | Sólo la clave | **Folio + clave**: el depósito identifica cliente y documento |
| Cantidad con letra | — | En remisión y recibo |
| Verificación | — | Código de 6 caracteres al pie (huella de folio + total + fecha) |
| Documentos | Remisión, relación del día (3 hojas), LIBRO | Cotización, remisión, recibo de pago, estado de cuenta |
| Unidades | Kilos y piezas en paralelo | **Kg** como unidad de venta; la presentación (saco 25 kg, bolsa 10 kg) es texto |
| Estado | — | Sello redondo: "Vigencia 7 días", "Crédito 15 días", "Contado", "Pago recibido", "Con saldo vencido" |

## 2. Identidad visual

Tomada del sitio (`index.html`), para que web y papel sean la misma marca:

| Uso | Token | Valor |
|---|---|---|
| Papel | `--crema` | `#FBF8F3` |
| Tarjetas | `--calido` | `#F5EDE3` |
| Filetes suaves | `--arena` | `#E8DDD0` |
| Texto | `--tinta` | `#1B3028` |
| Titulares, filete fuerte | `--bosque` | `#2D4A3E` |
| Rótulos, secundario | `--salvia` | `#7A9E8E` |
| Folio, total, sello, clave | `--terracota` | `#C4704B` |
| Filete decorativo | `--oro` | `#C9A96E` |

Reglas:

- Nunca bloques de texto en mayúsculas. La única mayúscula permitida son los
  rótulos de una o dos palabras (`CLIENTE`, `FORMA DE PAGO`).
- Los números van con cifras tabulares y alineados a la derecha.
- Tamaño carta, márgenes de 16 mm. En pantalla se ve la hoja sobre fondo gris;
  al imprimir se quita todo lo que no sea la hoja.
- Los datos que no existen no se inventan ni se dejan en blanco: si no hay
  CLABE configurada, el bloque dice "los datos bancarios se comparten por
  WhatsApp al confirmar el pedido".

## 3. Folios

```
<TIPO> <AÑO>-<CONSECUTIVO de 4 dígitos>     COT 2026-0018
<TIPO> <AÑO>-<MES>                          EDC 2026-09   (estado de cuenta mensual)
```

Tipos: `COT` cotización · `REM` remisión · `REC` recibo de pago · `EDC` estado
de cuenta. El consecutivo reinicia cada año. Funciones: `folio(tipo, año, n)`
y `folioMensual(tipo, año, mes)`.

## 4. Clave de cliente (referencia de pago)

```
MOL-NNNN-CC
NNNN  número de cliente (1-9999), lo asigna el sistema al dar de alta
CC    dígitos de control: 98 − ((NNNN × 100) mod 97)
```

Validación: `(NNNN × 100 + CC) mod 97 == 1`. Es el esquema ISO 7064 mod
97-10 del IBAN: detecta cualquier error de un dígito y casi todas las
transposiciones. A diferencia del hash del nombre, la clave es única por
construcción y no cambia si el cliente se renombra.

Funciones: `claveCliente(numero)` → `"MOL-0042-69"`, `validarClave(str)`.

## 5. Concepto SPEI

```
<folio> <clave>          REM 2026-0031 MOL-0042-69     (25 caracteres, límite 40)
```

Con folio y clave en el concepto, el depósito llega ya casado con el cliente y
con el documento que paga; no hay que adivinar. En el estado de cuenta, que
cubre varios documentos, el bloque de pago pide el folio de la remisión que se
liquida más la clave.

## 6. Código de verificación

Al pie de cada documento: 6 caracteres en base 36 de una huella FNV-1a sobre
`folio|total|fecha`. Sirve para cotejar un documento reenviado o reimpreso
contra el sistema. No es una firma criptográfica.

## 7. Modelo de datos (JSON que exporta el sistema)

Cotización / remisión:

```json
{
  "anio": 2026, "consecutivo": 31, "fecha": "2026-09-21",
  "vigenciaDias": 7,                       // COT
  "cotizacion": "COT 2026-0018", "diasCredito": 15,   // REM
  "cliente": { "numero": 42, "nombre": "…", "rfc": "", "contacto": "", "telefono": "", "direccion": "" },
  "entrega": { "lugar": "", "fecha": "2026-09-22", "transporte": "", "recibe": "", "bultos": 5 },  // REM
  "partidas": [
    { "producto": "Chile guajillo seco", "presentacion": "Saco de 25 kg", "lote": "L-2609-07",
      "cantidad": 50, "precio": 100, "iva": 0 }
  ]
}
```

Recibo de pago: `monto`, `forma`, `referencia`, `aplicaciones[{documento,
descripcion, saldoAnterior, monto}]`. Lo no aplicado queda como saldo a favor.

Estado de cuenta: `mes`, `corte`, `periodo`, `documentos[{folio, descripcion,
fecha, diasCredito, importe, abonos}]`. El saldo, el vencimiento y la
antigüedad se calculan al renderizar, nunca se guardan.

`cantidad` siempre en kg; `precio` por kg; `iva` como tasa por partida (0 o
0.16) porque en un mismo pedido conviven productos gravados y exentos.

## 8. Cómo portarlo al ERP (copia limpia)

1. **Generación de PDF.** Sustituir `lib/pdfBranding.ts` + `lib/tablaPdf.ts`
   (jsPDF) por render de HTML: en el servidor, Playwright/Chromium con
   `page.pdf({ format: 'Letter', printBackground: true })` sobre el HTML que
   producen `render*()`; en el navegador, `window.print()`. El CSS y el JS de
   `imprimibles/` se copian tal cual a `public/imprimibles/` o se portan a
   TypeScript sin cambiar formatos.
2. **Referencias.** Reemplazar `lib/referencias.ts` (hash `AB####`) por
   `claveCliente(numero)`; la clave se guarda en `Cliente` al darlo de alta y
   `validarClave` se usa al leer conceptos bancarios (`bancosMeta.quienEs`).
3. **Folios.** Un contador por tipo y año en `AppConfig` (`folios:2026:REM`).
4. **`src/config/empresa.ts`.** Los datos de `EMPRESA` de `imprimibles.js`
   son los mismos campos; ahí se llenan RFC, CLABE y logo cuando existan.
5. **Nombres.** El sistema deja de hablar de "RD" de cara al cliente: en los
   documentos se imprime **lote**. Internamente puede seguir siendo RD.

## 9. Lo que estos documentos no son

- No son CFDI. La remisión y el recibo lo dicen expresamente; la factura se
  emite por separado con los datos fiscales registrados.
- No publican precios en el sitio: viven fuera del sitemap, con `noindex`,
  y sólo muestran precios cuando el sistema les carga un JSON real.
