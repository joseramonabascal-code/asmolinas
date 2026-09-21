# AS MOLINAS — Guía del repositorio para Claude Code

Sitio web de **AS MOLINAS**, proveedor mayorista B2B/HORECA de especias, chiles secos, semillas, tés y superfoods en México. Este archivo documenta cómo trabajar con el repositorio y las reglas de negocio que Claude Code debe respetar en cualquier cambio.

---

## 1. Qué es este repositorio

- **Sitio en producción:** https://asmolinas.com
- **Hosting:** GitHub Pages (deploy automático desde rama `main`)
- **DNS:** apunta a IPs de GitHub Pages (185.199.108–111.153) vía CNAME (`asmolinas.com`)
- **Tipo de sitio:** landing + catálogo estático, sin backend
- **Público objetivo:** exclusivamente **B2B / HORECA**: restaurantes, hoteles, cafeterías, distribuidores, marcas de alimentos, tiendas naturistas, panaderías, jugueras, spas

**No hay backend, ni base de datos, ni build step.** Los archivos HTML/CSS/JS son servidos tal cual por GitHub Pages.

---

## 2. Estructura del repositorio

```
asmolinas/
├── index.html                        ← Homepage (hero, catálogo, HORECA, contacto)
├── mayoreo.html                      ← Página general de mayoreo (rangos de precio, FAQ)
├── especias-al-mayoreo.html          ← Landing SEO: especias
├── chiles-secos-por-mayoreo.html     ← Landing SEO: chiles secos
├── semillas-a-granel.html            ← Landing SEO: semillas y nueces
├── superfoods-mayoreo.html           ← Landing SEO: superfoods
├── envios.html                       ← Info de envíos y cobertura
├── terminos.html                     ← Términos y condiciones
├── aviso-de-privacidad.html          ← Aviso de privacidad
├── blog.html                         ← Índice del blog
├── as_molinas_tienda_6.html          ← Redirect legacy → /#catalogo (noindex)
├── financial-dashboard.html          ← Dashboard financiero interno (ejemplo/demo)
│
├── blog/                             ← Artículos SEO
│   ├── achiote-vs-achiote-molido.html
│   ├── beneficios-curcuma-que-dice-la-ciencia.html
│   ├── beneficios-epazote.html
│   ├── como-conservar-especias-mas-tiempo.html
│   ├── especias-esenciales-cocina-mexicana.html
│   ├── moringa-propiedades-beneficios.html
│   ├── recetas-con-canela.html
│   ├── sal-del-himalaya-beneficios.html
│   └── articulo-{1..8}.html          ← Redirects legacy (Disallow en robots.txt)
│
├── assets/
│   ├── catalogo-asmolinas.pdf        ← Catálogo descargable de mayoreo
│   ├── gen_catalog.py                ← Generador del PDF (fpdf2)
│   ├── copy-ideas.md                 ← Notas de copywriting
│   └── img/                          ← Imágenes locales
│
├── imprimibles/                      ← Documentos internos (noindex, bloqueados en robots.txt)
│   ├── imprimibles.css               ← Identidad de papel: crema, verde bosque, terracota
│   ├── imprimibles.js                ← Folios, clave de cliente MOL42, concepto SPEI, render*()
│   ├── cotizacion.html               ← COT 2026-0001
│   ├── remision.html                 ← REM 2026-0001
│   ├── recibo-pago.html              ← REC 2026-0001
│   └── estado-cuenta.html            ← EDC 2026-09
│
├── docs/
│   └── imprimibles-asmolinas.md      ← Especificación de imprimibles y referencias (y cómo portarlas al ERP)
│
├── CNAME                             ← "asmolinas.com" (custom domain de Pages)
├── favicon.svg
├── robots.txt                        ← Reglas de crawl (Disallow legacy pages)
├── sitemap.xml                       ← Sitemap para Google
├── .htaccess                         ← Legacy Apache config (IGNORADO por Pages)
└── CLAUDE.md                         ← Este archivo
```

**Nota sobre `.htaccess`:** existe por herencia de un hosting anterior en cPanel/GoDaddy. **GitHub Pages lo ignora completamente.** Cualquier regla de redirect o cache debe implementarse por otro medio (etiquetas `<meta>`, JS, o dejar que GitHub Pages sirva 404 por default).

---

## 3. Reglas de negocio (CRÍTICAS — respeta siempre)

### 3.1 Solo mayoreo y medio mayoreo — nada de menudeo

- **El pedido mínimo cambia según el producto y la presentación.** No existe un mínimo único: se confirma al cotizar. Frase canónica: *"mínimo según producto y presentación"*
- **Prohibido:** afirmar un mínimo fijo ("pedido mínimo 10 kg") — fue la regla anterior y ya no aplica
- **Prohibido en toda la web:** presentaciones de 500 g, 1 kg individual, sobres de 100 g, kits pequeños, "paquete prueba"
- **Prohibido:** mencionar mínimos monetarios ($300, $1,500, $2,000 MXN) — el mínimo es en volumen, no en dinero

### 3.2 Estructura de precios (4 rangos por producto)

Todos los precios se cotizan **por kg** y bajan según el volumen del pedido:

| Rango de volumen | Nivel de precio | Uso típico |
|---|---|---|
| **10 – 19.9 kg** | Precio de entrada | Cocinas medianas, prueba de rotación |
| **20 – 24.9 kg** | Precio de entrada intermedio | Cocinas de mayor consumo semanal |
| **25 – 399.9 kg** | Precio medio mayoreo (bulto cerrado 25 kg) | Restaurantes de alto consumo, distribuidores medianos, tiendas |
| **400 kg en adelante** | Precio mayoreo | Distribuidores, marcas de alimentos, foodservice a escala |

Estos 4 rangos describen **cómo escala el precio con el volumen**, no un piso de compra: el mínimo real depende del producto y la presentación (ver 3.1).

**No se publican precios en el sitio.** Nunca inventar cifras y nunca dejar placeholders visibles (`[PRECIO_PENDIENTE]` fue retirado de todo el sitio). La frase canónica es **"Cotiza precio vigente por volumen"**.

### 3.3 Regla de evidencia (la más importante)

Del reporte maestro del 15-sep-2026: *no publicar ni vender una promesa que no pueda demostrarse con producto, documento, lote, muestra, proceso o evidencia operativa.*

Claims **prohibidos** hasta que exista documentación lote a lote:

| Prohibido | Usar en su lugar |
|---|---|
| "100% natural", "libre de pesticidas", "certificado", "comercio justo" | Presentación, origen declarado por el proveedor, ficha técnica cuando exista |
| "Proveedor directo, sin intermediarios", "compramos en origen" | "Comercializamos y abastecemos ingredientes secos para negocio" |
| "Molienda propia", "molemos por lote" | "Presentación según disponibilidad del proveedor" |
| "Existencia permanente todo el año" | "Disponibilidad sujeta a cosecha y existencia; confirmamos lote al cotizar" |
| "Documentamos cada pedido" | Nada, hasta que exista bitácora formal de recepción y lote |
| "Entrega 1-3 días", envío nacional genérico | "Flete a cargo del cliente; costo y tiempo se confirman en la cotización" |
| Pago con tarjeta, crédito automático | Sólo SPEI y depósito; CFDI en todos los pedidos |
| "+200 negocios surtidos", "47 reseñas", testimonios, `aggregateRating` | Sólo evidencia comprobable: "Atención B2B", "Factura CFDI" |

### 3.4 Tono y público del copy

- **Público único:** B2B / HORECA / foodservice
- **PROHIBIDO** copy dirigido a consumidor final: "cada familia mexicana", "para tu hogar", "amas de casa", "para tu cocina" en sentido individual
- **Usa** términos como: "para tu operación", "cocinas de restaurante", "abasto para tu negocio", "cotiza mayoreo"
- El idioma es **español (México)** en todo el sitio

### 3.5 CTAs

- CTA principal: **"Solicitar cotización B2B"** por WhatsApp (secundario: "Ver productos disponibles")
- Número: `748 166 0295` (link `https://wa.me/527481660295`)
- Nunca uses lenguaje transaccional de e-commerce ("Comprar ahora", "Añadir al carrito") — no hay tienda online, solo cotización

---

## 4. Deploy y publicación

### 4.1 Cómo se publica

1. Cualquier commit a la rama `main` dispara automáticamente un workflow "pages build and deployment"
2. El build tarda 1-2 minutos
3. GitHub Pages sirve el sitio en https://asmolinas.com
4. Ver estado de builds: https://github.com/joseramonabascal-code/asmolinas/actions

### 4.2 Flujo estándar de cambios

```bash
# Editar archivos localmente
git add -A
git commit -m "descripción del cambio"
git push origin main
# Espera 1-2 min y verifica en https://asmolinas.com (Ctrl+F5 para evitar caché)
```

### 4.3 Ramas de trabajo

- **`main`** — rama de producción, publica en asmolinas.com
- Las ramas `claude/*` (ej. `claude/financial-dashboard-html-q17hk`) son ramas de trabajo generadas por sesiones de Claude Code Remote; se mergean a `main` cuando el cambio está listo
- **No hay** ramas `develop`, `staging`, etc.

### 4.4 Nota sobre permisos de push desde Claude

En sesiones de **Claude Code Remote** (nube), el push a GitHub puede requerir que la Claude GitHub App esté instalada con acceso al repo `asmolinas`. Si el push falla con `403 Forbidden`:

1. Ir a https://github.com/settings/installations
2. Configurar la app "Claude" con acceso a `asmolinas`
3. Guardar y **abrir una sesión nueva** (los tokens no se refrescan en la sesión activa)

En Claude Code local (equipo del usuario), el push usa las credenciales de git del usuario y funciona sin este paso.

---

## 5. Convenciones al editar archivos

### 5.1 HTML

- Mantener la estructura semántica existente (`<header>`, `<section>`, `<nav>`, `<article>`, `<footer>`)
- Cada página tiene sus propios estilos inline en `<style>` — no hay archivo CSS global
- Cada página incluye:
  - `<meta name="description">` optimizado para SEO
  - Etiquetas Open Graph y Twitter Card
  - `<script type="application/ld+json">` con **Schema.org** (Organization, LocalBusiness, FAQPage, Product)
  - Google Tag Manager (`GTM-TDZPL9W4`) con carga diferida
- **Al cambiar un mensaje del sitio (mínimos, precios, presentaciones)**, actualizar también el schema JSON-LD equivalente en la misma página — Google los indexa y aparecen en resultados de búsqueda como FAQs enriquecidos

### 5.2 Actualización coordinada

Cuando cambies una regla de negocio (ej. mínimo de pedido), verifica **todas** estas ubicaciones en la página que edites:

- Texto visible del cuerpo (`<p>`, `<h2>`, listas)
- Meta descriptions (`<meta name="description">`, `<meta property="og:description">`, `<meta name="twitter:description">`)
- FAQ Schema (`"@type": "Question"` con `acceptedAnswer`)
- Bloque de FAQ visible con `<details><summary>...</summary>`

Y en el catálogo:
- Tabla de precios de la landing del producto
- `assets/gen_catalog.py` (fuente del PDF)
- `assets/catalogo-asmolinas.pdf` (regenerar tras cambios)

### 5.3 Product data (index.html)

Los productos del catálogo del homepage están en un array JS dentro de `index.html` (buscar `const products = [`). El renderer usa un CTA a WhatsApp por producto, **no muestra precios individuales** (los precios reales viven en las páginas de mayoreo y en el PDF).

### 5.4 SEO

- El sitemap está en `sitemap.xml` y se actualiza manualmente si agregas o quitas páginas
- `robots.txt` bloquea explícitamente páginas legacy (`articulo-1` a `articulo-8`, `as_molinas_tienda_6.html`) — mantener este bloqueo
- Todas las páginas nuevas deben incluir `<link rel="canonical">` apuntando a su URL final

---

## 6. Regenerar el PDF del catálogo

El catálogo descargable `assets/catalogo-asmolinas.pdf` se genera con Python + fpdf2:

```bash
# Requisito: pip install fpdf2 cffi
cd assets
python3 gen_catalog.py
# El PDF queda en assets/catalogo-asmolinas.pdf
```

**Cuando editar `gen_catalog.py`:**
- Alta/baja de productos
- Cambio de categorías
- Cambio de la estructura de rangos de precio
- Ajustes de diseño de portada o header/footer

Después de editar, siempre regenerar el PDF y commitearlo junto con el script.

---

## 7. Cambios que hacer con cuidado (checklist antes de commit)

Antes de commitear cualquier cambio en HTML de las páginas de catálogo/mayoreo:

- [ ] ¿Publico algún precio o mínimo en dinero (`$XXX MXN`)? → **quitar**
- [ ] ¿Afirmo un mínimo fijo ("10 kg por producto")? → **quitar**, el mínimo es por SKU
- [ ] ¿Menciono presentaciones de menudeo (500 g, 1 kg individual)? → **quitar**
- [ ] ¿Algún claim de la tabla 3.3 sin evidencia documentada? → **quitar**
- [ ] ¿El copy suena B2C (familia, hogar, cada mexicano)? → **reescribir a B2B**
- [ ] ¿Actualicé el schema JSON-LD además del texto visible?
- [ ] ¿La meta description sigue siendo coherente con el cambio?
- [ ] Si cambié precios: ¿actualicé `gen_catalog.py` y regeneré el PDF?

---

## 8. Contacto del negocio (para copy y schemas)

- **WhatsApp:** `748 166 0295` → `https://wa.me/527481660295`
- **Email:** `info@asmolinas.com`
- **Instagram:** `@asmolinas_especias`
- **Horario:** Lunes a Sábado, 9 AM – 7 PM
- **Ubicación:** CDMX y Área Metropolitana (con envíos a todo México)

Nunca inventes teléfonos, correos ni direcciones distintas.

---

## 8b. Imprimibles y referencias (carpeta `imprimibles/`)

Cotización, remisión, recibo de pago y estado de cuenta tienen identidad
propia, distinta a propósito del sistema de Grupo Abascal (que es tema
oscuro, azul, PDF en mayúsculas y claves `AB####` por hash del nombre).
Especificación completa en `docs/imprimibles-asmolinas.md`. Reglas fijas:

- Papel crema, tinta verde bosque, acento terracota; serif en titulares; **frase normal, nunca bloques en mayúsculas**
- Folios `COT|REM|REC 2026-0001` y `EDC 2026-09`
- Clave de cliente `MOL` + número de cliente: 2 dígitos (`MOL01`–`MOL99`), 3 a partir del 100 (`MOL100`–`MOL999`); nunca hash del nombre, nunca más de 3 dígitos
- Concepto SPEI = folio + clave (`REM 2026-0031 MOL42`)
- `EMPRESA` en `imprimibles.js` es el único lugar con datos de la casa; RFC y CLABE vacíos hasta que existan (nunca inventarlos)
- Los precios sólo aparecen cuando el sistema carga un JSON real; los ejemplos son ficticios
- La remisión a crédito lleva leyenda de **pagaré** (acreedor, plaza, vencimiento, importe en número y letra); la tasa moratoria sólo si está configurada en `EMPRESA.pagare`
- El catálogo PDF (`assets/gen_catalog.py`) sigue la misma identidad y **no publica precios**

## 9. Sobre `financial-dashboard.html`

Este archivo es un dashboard financiero interno/demo, **no está enlazado desde el navbar público** y no forma parte del sitio comercial. Si el usuario pide cambios al sitio de venta, ignora este archivo. Si pide cambios al dashboard, es un artefacto separado.

---

## 10. Comandos útiles de referencia

```bash
# Estado del repo
git status
git log --oneline -10

# Editar y publicar
git add -A
git commit -m "mensaje descriptivo"
git push origin main

# Regenerar el PDF del catálogo
cd assets && python3 gen_catalog.py

# Buscar residuos B2C o precios viejos antes de commit
grep -rn -iE '\$300|\$1,?500|\$2,?000|500\s?g|familia mexicana|bolsa de 1 kg' *.html blog/*.html

# Auditar claims sin evidencia (regla 3.3) y mínimos fijos
grep -rn -iE 'PRECIO_PENDIENTE|100% natural|pesticida|comercio justo|molienda propia|sin intermediarios|existencia permanente|1-3 días|mínimo.{0,12}10 kg' *.html blog/*.html
```

---

**Última actualización:** tras aplicar la Fase P0 del reporte maestro (15-sep-2026) — retiro de claims sin evidencia y MOQ por SKU.
