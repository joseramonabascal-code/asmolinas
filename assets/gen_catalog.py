from fpdf import FPDF
from collections import defaultdict

# ============================================================
# AS MOLINAS — Generador del catálogo PDF de mayoreo
# ============================================================
# Misma identidad que los imprimibles (imprimibles/imprimibles.css):
# papel crema, tinta verde bosque, acento terracota, filete oro,
# frase normal (sin bloques en mayúsculas) y sin rejilla.
#
# Reglas de negocio (CLAUDE.md):
#   - No se publican precios: "Cotiza precio vigente por volumen".
#   - El mínimo cambia según producto y presentación.
#   - Sin claims sin evidencia (natural, origen, molienda propia, tiempos).
#
# Requiere: pip install fpdf2
# ============================================================

TINTA   = (27, 48, 40)
BOSQUE  = (45, 74, 62)
SALVIA  = (122, 158, 142)
CREMA   = (251, 248, 243)
CALIDO  = (245, 237, 227)
ARENA   = (232, 221, 208)
TERRA   = (196, 112, 75)
ORO     = (201, 169, 110)
GRIS    = (107, 107, 107)
BLANCO  = (255, 255, 255)

CATS = {
    "Especias":      "Especias y chiles secos",
    "Superfoods":    "Superfoods",
    "Semillas":      "Semillas y nueces",
    "Deshidratados": "Frutas deshidratadas",
    "Tes":           "Tés e infusiones",
    "Sales":         "Sales",
}

# Cada producto: (nombre, descripción, categoría, etiqueta)
# La descripción dice qué es y para qué se usa; no afirma origen, pureza,
# proceso ni certificación.
products = [
    ("Canela en raja",          "Raja entera, aroma intenso",                     "Especias",      "Alta rotación"),
    ("Canela molida",           "Molida fina para panadería de volumen",           "Especias",      ""),
    ("Pimienta negra entera",   "Grano entero para molino",                        "Especias",      ""),
    ("Pimienta negra molida",   "Molida gruesa, sabor intenso",                    "Especias",      ""),
    ("Comino entero",           "Semilla entera, base de adobos y moles",          "Especias",      ""),
    ("Chile ancho seco",        "Poblano seco, base de moles y adobos",            "Especias",      ""),
    ("Chile guajillo seco",     "Rojo intenso, salsas rojas y caldos",             "Especias",      ""),
    ("Chile de árbol seco",     "Picor alto, salsas y aceites",                    "Especias",      ""),
    ("Orégano molido",          "Orégano mexicano, aroma fresco",                  "Especias",      ""),
    ("Ajo en polvo",            "Polvo fino para sazonadores y marinados",         "Especias",      ""),
    ("Pimentón dulce",          "Color y sabor suave para embutidos y salsas",     "Especias",      ""),
    ("Clavo de olor",           "Grano entero muy aromático",                      "Especias",      ""),
    ("Cúrcuma en polvo",        "Polvo, color dorado intenso",                     "Superfoods",    ""),
    ("Manzanilla",              "Flor entera para infusión",                       "Tes",           "Alta rotación"),
    ("Hierbabuena",             "Hojas secas, aroma refrescante",                  "Tes",           ""),
    ("Té de limón",             "Hojas secas para infusión",                       "Tes",           ""),
    ("Moringa en hoja",         "Hojas secas, insumo wellness",                    "Superfoods",    ""),
    ("Flor de Jamaica",         "Flor entera, agua fresca y kombucha",             "Superfoods",    ""),
    ("Chía",                    "Semilla entera",                                  "Superfoods",    ""),
    ("Quinoa",                  "Grano entero, bowls y menú wellness",             "Superfoods",    ""),
    ("Jengibre",                "Deshidratado o en polvo",                         "Superfoods",    ""),
    ("Arándano deshidratado",   "Fruta entera, sabor dulce-ácido",                 "Deshidratados", "Alta rotación"),
    ("Mango rodaja",            "Rodajas deshidratadas",                           "Deshidratados", ""),
    ("Mango cubo",              "Cubos deshidratados para snack y granola",        "Deshidratados", ""),
    ("Fresa deshidratada",      "Rodaja entera, color intenso",                    "Deshidratados", ""),
    ("Piña rodaja",             "Rodajas deshidratadas",                           "Deshidratados", ""),
    ("Piña cubo",               "Cubos para granola",                              "Deshidratados", ""),
    ("Papaya deshidratada",     "Trozos dulces y suaves",                          "Deshidratados", ""),
    ("Manzana rodaja",          "Rodajas crujientes",                              "Deshidratados", ""),
    ("Cereza deshidratada",     "Sabor intenso, insumo repostería",                "Deshidratados", ""),
    ("Orejón (chabacano)",      "Chabacano deshidratado",                          "Deshidratados", ""),
    ("Almendra natural",        "Entera con cutícula",                             "Semillas",      "Alta rotación"),
    ("Almendra fileteada",      "Corte fino para repostería y panadería",          "Semillas",      ""),
    ("Almendra sin cutícula",   "Pelada, para mazapán y harina de almendra",       "Semillas",      ""),
    ("Nuez de la India",        "Entera, tostado natural",                         "Semillas",      ""),
    ("Avellana",                "Entera con cutícula",                             "Semillas",      ""),
    ("Ajonjolí natural",        "Semilla limpia, panadería y moles",               "Semillas",      ""),
    ("Coco rallado",            "Rallado fino, sin azúcar añadida",                "Semillas",      ""),
    ("Sal del Himalaya fina",   "Sal rosa molida fina",                            "Sales",         ""),
    ("Sal del Himalaya gruesa", "Grano grueso, para molino",                       "Sales",         ""),
    ("Sal de mar gruesa",       "Grano grueso",                                    "Sales",         ""),
]

CONTACTO = "asmolinas.com  ·  WhatsApp 748 166 0295  ·  info@asmolinas.com"


class CatalogPDF(FPDF):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        # Fuente Unicode para acentos (DejaVu viene con fpdf2 en la mayoría de
        # instalaciones; si no está, se usa Helvetica y se pierden acentos).
        try:
            import os
            base = "/usr/share/fonts/truetype/dejavu/"
            self.add_font("Sans", "", os.path.join(base, "DejaVuSans.ttf"))
            self.add_font("Sans", "B", os.path.join(base, "DejaVuSans-Bold.ttf"))
            self.add_font("Serif", "", os.path.join(base, "DejaVuSerif.ttf"))
            self.add_font("Serif", "B", os.path.join(base, "DejaVuSerif-Bold.ttf"))
            self.sans, self.serif = "Sans", "Serif"
        except Exception:
            self.sans, self.serif = "Helvetica", "Times"

    # Fondo de papel en todas las páginas
    def _papel(self):
        self.set_fill_color(*CREMA)
        self.rect(0, 0, 216, 279, "F")

    def header(self):
        self._papel()
        if self.page_no() == 1:
            return
        self.set_y(10)
        self.set_font(self.serif, "B", 11)
        self.set_text_color(*BOSQUE)
        self.cell(60, 6, "AS Molinas")
        self.set_font(self.sans, "", 8)
        self.set_text_color(*SALVIA)
        self.cell(0, 6, "Catálogo de mayoreo 2026", align="R")
        self.set_draw_color(*BOSQUE)
        self.set_line_width(0.5)
        self.line(16, 18, 200, 18)
        self.set_y(24)

    def footer(self):
        self.set_y(-16)
        self.set_draw_color(*ARENA)
        self.set_line_width(0.2)
        self.line(16, self.get_y(), 200, self.get_y())
        self.set_y(-13)
        self.set_font(self.sans, "", 7.5)
        self.set_text_color(*GRIS)
        self.cell(120, 5, CONTACTO)
        self.cell(0, 5, f"Página {self.page_no()}", align="R")

    def cover(self):
        # Marca
        self.set_y(70)
        self.set_font(self.serif, "B", 40)
        self.set_text_color(*BOSQUE)
        w_as = self.get_string_width("AS ")
        w_mol = self.get_string_width("Molinas")
        x = (216 - w_as - w_mol) / 2
        self.set_x(x)
        self.cell(w_as, 18, "AS ")
        self.set_text_color(*TERRA)
        self.cell(w_mol, 18, "Molinas")
        self.ln(20)

        self.set_font(self.sans, "", 11)
        self.set_text_color(*SALVIA)
        self.cell(0, 7, "Especias, chiles secos y semillas al mayoreo para negocios", align="C")
        self.ln(12)

        self.set_draw_color(*ORO)
        self.set_line_width(0.8)
        self.line(78, self.get_y(), 138, self.get_y())
        self.ln(10)

        self.set_font(self.serif, "", 20)
        self.set_text_color(*TINTA)
        self.cell(0, 10, "Catálogo de mayoreo 2026", align="C")
        self.ln(16)

        # Tarjeta: cómo se cotiza
        self._tarjeta(30, self.get_y(), 156, 58, "Cómo cotizamos", [
            "Precio por kg en MXN; baja según el volumen del pedido.",
            "Rangos: 10-19.9 kg  ·  20-24.9 kg  ·  25-399.9 kg  ·  400 kg y más.",
            "Mínimo según producto y presentación; se confirma al cotizar.",
            "Disponibilidad sujeta a cosecha y existencia; confirmamos lote.",
            "Pago por SPEI o depósito. CFDI en todos los pedidos.",
        ])
        self.set_y(self.get_y() + 10)

        # Tarjeta: contacto
        self._tarjeta(30, self.get_y(), 156, 40, "Solicita tu cotización B2B", [
            "WhatsApp 748 166 0295",
            "info@asmolinas.com",
            "asmolinas.com",
        ], centrado=True)

    def _tarjeta(self, x, y, w, h, titulo, lineas, centrado=False):
        self.set_fill_color(*CALIDO)
        self.rect(x, y, w, h, "F")
        self.set_xy(x + 8, y + 6)
        self.set_font(self.sans, "B", 8)
        self.set_text_color(*SALVIA)
        self.cell(w - 16, 5, titulo.upper(), align="C" if centrado else "L")
        self.set_font(self.sans, "", 9.5)
        self.set_text_color(*TINTA)
        yy = y + 14
        for l in lineas:
            self.set_xy(x + 8, yy)
            self.cell(w - 16, 6, l, align="C" if centrado else "L")
            yy += 7
        self.set_y(y + h)

    def category_header(self, label):
        self.set_font(self.serif, "B", 16)
        self.set_text_color(*BOSQUE)
        self.cell(0, 10, label, new_x="LMARGIN", new_y="NEXT")
        self.set_font(self.sans, "", 8.5)
        self.set_text_color(*GRIS)
        self.cell(0, 5, "Precio por kg según volumen. Cotiza el precio vigente por WhatsApp; el mínimo depende del producto y la presentación.",
                  new_x="LMARGIN", new_y="NEXT")
        self.ln(3)
        # Encabezado de columnas
        self.set_font(self.sans, "B", 7.5)
        self.set_text_color(*SALVIA)
        self.cell(8, 6, "")
        self.cell(112, 6, "Producto")
        self.cell(44, 6, "Precio", align="L")
        self.cell(20, 6, "", align="R")
        self.ln(6)
        self.set_draw_color(*BOSQUE)
        self.set_line_width(0.5)
        self.line(16, self.get_y(), 200, self.get_y())
        self.ln(1)

    def product_row(self, i, name, desc, tag):
        y = self.get_y()
        self.set_font(self.sans, "", 7.5)
        self.set_text_color(*GRIS)
        self.cell(8, 6, str(i))
        self.set_font(self.sans, "B", 9.5)
        self.set_text_color(*TINTA)
        self.cell(112, 6, name)
        self.set_font(self.sans, "", 8)
        self.set_text_color(*TERRA)
        self.cell(44, 6, "Cotiza precio vigente")
        if tag:
            self.set_font(self.sans, "B", 6.5)
            self.set_text_color(*BOSQUE)
            self.cell(20, 6, tag, align="R")
        self.ln(5)
        self.set_font(self.sans, "", 7.5)
        self.set_text_color(*GRIS)
        self.cell(8, 5, "")
        self.cell(0, 5, desc)
        self.ln(6)
        self.set_draw_color(*ARENA)
        self.set_line_width(0.2)
        self.line(16, self.get_y(), 200, self.get_y())
        self.ln(1.5)


def build_pdf(output_path):
    pdf = CatalogPDF(orientation="P", unit="mm", format="Letter")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(16, 24, 16)

    pdf.add_page()
    pdf.cover()

    by_cat = defaultdict(list)
    for p in products:
        by_cat[p[2]].append(p)

    for cat_key, label in CATS.items():
        prods = by_cat.get(cat_key, [])
        if not prods:
            continue
        pdf.add_page()
        pdf.category_header(label)
        for i, (name, desc, _, tag) in enumerate(prods, 1):
            if pdf.get_y() > 245:
                pdf.add_page()
                pdf.category_header(label + " (continúa)")
            pdf.product_row(i, name, desc, tag)

    # Notas
    pdf.add_page()
    pdf.set_font(pdf.serif, "B", 16)
    pdf.set_text_color(*BOSQUE)
    pdf.cell(0, 10, "Condiciones", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font(pdf.sans, "", 9.5)
    pdf.set_text_color(*TINTA)
    notas = [
        "Los precios se cotizan por kg en MXN y no se publican en este catálogo: pide el precio vigente por WhatsApp.",
        "El precio por kg baja con el volumen. Rangos de referencia: 10-19.9 kg, 20-24.9 kg, 25-399.9 kg (bulto cerrado de 25 kg) y 400 kg en adelante.",
        "El pedido mínimo cambia según el producto y la presentación; se confirma al cotizar.",
        "Disponibilidad sujeta a cosecha y existencia. Confirmamos lote y presentación al cotizar.",
        "Presentación y origen según disponibilidad del proveedor; ficha técnica cuando exista.",
        "Flete a cargo del cliente. Costo y tiempo de entrega se confirman en la cotización.",
        "Pago por transferencia SPEI o depósito. Emitimos CFDI en todos los pedidos.",
        "Puedes combinar varios productos en un mismo pedido; cada uno se cotiza en su rango de volumen.",
    ]
    for n in notas:
        pdf.set_x(20)
        pdf.set_text_color(*TERRA)
        pdf.cell(5, 6, "·")
        pdf.set_text_color(*TINTA)
        pdf.multi_cell(0, 6, n)
        pdf.ln(1)

    pdf.output(output_path)
    print(f"PDF generado OK -> {output_path}")


if __name__ == "__main__":
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    build_pdf(os.path.join(here, "catalogo-asmolinas.pdf"))
