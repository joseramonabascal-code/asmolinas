from fpdf import FPDF
from collections import defaultdict

# ============================================================
# AS MOLINAS — Generador de Catalogo PDF de Mayoreo
# ============================================================
# Estructura de precios: 4 rangos de volumen por producto
#   10-19.9 kg   → Entrada
#   20-24.9 kg   → Intermedio
#   25-399.9 kg  → Bulto cerrado (25 kg)
#   400 kg+      → Mayoreo
# Precios se dejan como [PRECIO_PENDIENTE] hasta llenarlos.
# ============================================================

FOREST  = (45, 74, 62)
TERRA   = (196, 112, 75)
CREAM   = (251, 248, 243)
WHITE   = (255, 255, 255)
MUTED   = (107, 107, 107)
LIGHT   = (232, 221, 208)
GOLD    = (212, 160, 23)

CATS = {
    "Especias":      (TERRA,           "Especias y Chiles"),
    "Tes":           ((58, 122, 48),   "Tes Artesanales"),
    "Deshidratados": ((112, 48, 160),  "Deshidratados"),
    "Semillas":      ((160, 112, 8),   "Semillas y Nueces"),
    "Sales":         ((192, 88, 64),   "Sales Gourmet"),
    "Superfoods":    (FOREST,          "Superfoods"),
}

# Placeholder que se muestra en el PDF hasta que llenes precios reales
PP = "[PRECIO_PENDIENTE]"

# Cada producto: (nombre, descripcion, categoria, tag)
# Los precios se calculan al render como 4 columnas con placeholder
products = [
    ("Canela en raja",         "Canela ceylan premium, aroma intenso",       "Especias",      "Popular"),
    ("Canela molida",          "Molida fina para panaderia de volumen",       "Especias",      ""),
    ("Pimienta negra entera",  "Grano entero seleccionado para molino",       "Especias",      ""),
    ("Pimienta negra molida",  "Molida gruesa, sabor intenso",                "Especias",      ""),
    ("Comino entero",          "Semilla entera, base de adobos y moles",      "Especias",      ""),
    ("Chile ancho seco",       "Poblano seco, base de moles y adobos",        "Especias",      ""),
    ("Chile guajillo seco",    "Rojo intenso, salsas rojas y caldos",         "Especias",      ""),
    ("Oregano molido",         "Oregano mexicano, aroma fresco",              "Especias",      ""),
    ("Clavo de olor",          "Grano entero muy aromatico",                  "Especias",      "Premium"),
    ("Curcuma en polvo",       "Molienda propia, color dorado intenso",       "Superfoods",    ""),
    ("Manzanilla premium",     "Flor entera, cosecha reciente",               "Tes",           "Popular"),
    ("Hierbabuena",            "Hojas secas, aroma refrescante",              "Tes",           ""),
    ("Te de limon",            "Hojas de limon natural",                      "Tes",           ""),
    ("Moringa en hoja",        "Hojas secas, insumo wellness",                "Superfoods",    "Superfood"),
    ("Flor de Jamaica",        "Flor entera, agua fresca y kombucha",         "Superfoods",    ""),
    ("Chia",                   "Semilla entera",                              "Superfoods",    ""),
    ("Quinoa",                 "Grano entero, insumo bowls y menu wellness",  "Superfoods",    ""),
    ("Jengibre",               "Deshidratado o en polvo",                     "Superfoods",    ""),
    ("Arandano deshidratado",  "Fruta entera, sabor dulce-acido",             "Deshidratados", "Popular"),
    ("Mango rodaja",           "Rodajas deshidratadas, sin azucar",           "Deshidratados", ""),
    ("Mango cubo",             "Cubos deshidratados, snack natural",          "Deshidratados", ""),
    ("Fresa deshidratada",     "Rodaja entera, color intenso",                "Deshidratados", "Premium"),
    ("Pina rodaja",            "Rodajas naturales deshidratadas",             "Deshidratados", ""),
    ("Pina cubo",              "Cubos practicos para granola",                "Deshidratados", ""),
    ("Papaya deshidratada",    "Trozos dulces y suaves",                      "Deshidratados", ""),
    ("Manzana rodaja",         "Rodajas crujientes, sin azucar",              "Deshidratados", ""),
    ("Cereza deshidratada",    "Sabor intenso, insumo reposteria",            "Deshidratados", ""),
    ("Orejon (chabacano)",     "Chabacano deshidratado premium",              "Deshidratados", "Premium"),
    ("Almendra natural",       "Entera con cuticula, seleccionada",           "Semillas",      "Popular"),
    ("Almendra fileteada",     "Corte fino para reposteria y panaderia",      "Semillas",      ""),
    ("Almendra sin cuticula",  "Pelada, para mazapan y harina de almendra",   "Semillas",      ""),
    ("Nuez de la India",       "Cashew entero, tostado natural",              "Semillas",      ""),
    ("Avellana",               "Entera con cuticula, grado premium",          "Semillas",      "Premium"),
    ("Ajonjoli natural",       "Semilla limpia, panaderia y moles",           "Semillas",      ""),
    ("Coco rallado",           "Rallado fino, sin azucar",                    "Semillas",      ""),
    ("Sal del Himalaya fina",  "Sal rosa molida fina, 84 minerales",          "Sales",         "Popular"),
    ("Sal del Himalaya gruesa","Grano grueso, para molino",                   "Sales",         ""),
    ("Sal de mar gruesa",      "Cosechada naturalmente, sin refinar",         "Sales",         ""),
]


class CatalogPDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_fill_color(*FOREST)
        self.rect(0, 0, 210, 12, "F")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*WHITE)
        self.set_y(3)
        self.cell(0, 6, "AS MOLINAS  |  Catalogo de Mayoreo 2026", align="C")
        self.set_text_color(0, 0, 0)
        self.ln(10)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 5, f"Pagina {self.page_no()}", align="C")
        self.cell(0, 5, "asmolinas.com  |  WhatsApp 748 166 0295  |  info@asmolinas.com", align="R")
        self.set_text_color(0, 0, 0)

    def cover(self):
        # Full-page dark green background
        self.set_fill_color(*FOREST)
        self.rect(0, 0, 210, 297, "F")

        # Brand name
        self.set_font("Helvetica", "B", 42)
        self.set_text_color(*WHITE)
        self.set_y(70)
        self.cell(0, 16, "AS MOLINAS", align="C")

        # Separator line
        self.set_draw_color(*GOLD)
        self.set_line_width(1.4)
        self.line(60, 92, 150, 92)

        # Tagline
        self.set_font("Helvetica", "I", 13)
        self.set_text_color(200, 220, 210)
        self.set_y(96)
        self.cell(0, 8, "Especias, Chiles, Semillas, Tes y Superfoods", align="C")
        self.set_y(103)
        self.cell(0, 8, "Solo mayoreo y medio mayoreo para HORECA y foodservice", align="C")

        # Catalog title box
        self.set_fill_color(*TERRA)
        self.set_y(122)
        self.set_x(35)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*WHITE)
        self.cell(140, 14, "CATALOGO DE MAYOREO 2026", align="C", fill=True)

        # Pricing structure block
        self.set_fill_color(30, 55, 45)
        self.rect(25, 148, 160, 62, "F")
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*WHITE)
        self.set_y(154)
        self.cell(0, 6, "Estructura de precios por volumen (por kg)", align="C")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(200, 220, 210)
        self.set_y(164)
        self.multi_cell(0, 6,
            "  10 - 19.9 kg    Precio de entrada\n"
            "  20 - 24.9 kg    Precio de entrada intermedio\n"
            "  25 - 399.9 kg   Precio medio mayoreo (bulto 25 kg)\n"
            "  400 kg y mas    Precio mayoreo",
            align="C")
        self.set_font("Helvetica", "I", 9)
        self.set_y(200)
        self.cell(0, 5, "Pedido minimo: 10 kg por producto", align="C")

        # Contact block
        self.set_fill_color(30, 55, 45)
        self.rect(25, 230, 160, 44, "F")
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*WHITE)
        self.set_y(236)
        self.cell(0, 6, "Contacto para cotizacion", align="C")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(200, 220, 210)
        self.ln(8)
        self.cell(0, 5, "WhatsApp: 748 166 0295", align="C")
        self.ln(6)
        self.cell(0, 5, "Email: info@asmolinas.com", align="C")
        self.ln(6)
        self.cell(0, 5, "Web: asmolinas.com", align="C")

    def category_header(self, label, color):
        self.set_fill_color(*color)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*WHITE)
        self.cell(0, 10, f"  {label}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        self.set_text_color(0, 0, 0)

    def price_table_header(self):
        # Header de columnas de precios
        self.set_fill_color(*LIGHT)
        self.set_draw_color(*MUTED)
        self.set_line_width(0.2)
        self.set_font("Helvetica", "B", 7.5)
        self.set_text_color(*FOREST)
        # Producto | Entrada | Interm | Bulto25 | Mayoreo | Tag
        cols = [
            ("Producto",         76),
            ("10-19.9 kg",       22),
            ("20-24.9 kg",       22),
            ("25-399.9 kg",      22),
            ("400 kg +",         22),
            ("",                 26),
        ]
        for label, w in cols:
            self.cell(w, 7, label, border=1, align="C", fill=True)
        self.ln(7)

    def product_row(self, name, desc, tag):
        self.set_draw_color(*LIGHT)
        self.set_line_width(0.2)
        y_start = self.get_y()

        # Columna producto (nombre + descripcion en 2 lineas)
        self.set_font("Helvetica", "B", 8.5)
        self.set_text_color(*FOREST)
        self.set_xy(10, y_start)
        self.cell(76, 5, name, border="LT")
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*MUTED)
        self.set_xy(10, y_start + 5)
        self.cell(76, 5, desc[:60], border="LB")

        # 4 columnas de precio
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*TERRA)
        for i in range(4):
            x = 86 + i * 22
            self.set_xy(x, y_start)
            self.cell(22, 10, PP, border=1, align="C")

        # Columna tag
        self.set_xy(86 + 4 * 22, y_start)
        if tag:
            self.set_fill_color(*TERRA)
            self.set_font("Helvetica", "B", 6.5)
            self.set_text_color(*WHITE)
            self.cell(26, 10, tag.upper(), border=1, align="C", fill=True)
        else:
            self.cell(26, 10, "", border=1)

        self.set_text_color(0, 0, 0)
        self.set_y(y_start + 10)


def build_pdf(output_path):
    pdf = CatalogPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(10, 18, 10)

    # Cover
    pdf.add_page()
    pdf.cover()

    # Group by category
    by_cat = defaultdict(list)
    for p in products:
        by_cat[p[2]].append(p)

    cat_order = ["Especias", "Superfoods", "Semillas", "Deshidratados", "Tes", "Sales"]

    for cat_key in cat_order:
        prods = by_cat.get(cat_key, [])
        if not prods:
            continue
        color, label = CATS[cat_key]
        pdf.add_page()
        pdf.category_header(label, color)
        pdf.price_table_header()
        for name, desc, _, tag in prods:
            if pdf.get_y() > 260:
                pdf.add_page()
                pdf.category_header(label + " (cont.)", color)
                pdf.price_table_header()
            pdf.product_row(name, desc, tag)

    # Notas finales
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*FOREST)
    pdf.cell(0, 10, "Notas importantes", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    notas = [
        "- Todos los precios son por kilo (MXN) e IVA no incluido.",
        "- Pedido minimo: 10 kg por producto. No manejamos venta menudeo por debajo de 10 kg.",
        "- El precio por kg baja segun el rango de volumen (entrada, intermedio, bulto 25 kg, mayoreo 400 kg+).",
        "- El bulto cerrado equivale a 25 kg. Aplica el rango 25 - 399.9 kg.",
        "- Los precios pueden ajustarse por cosecha y tipo de cambio; tu cotizacion vigente se confirma por WhatsApp.",
        "- Emitimos CFDI en todos los pedidos de mayoreo.",
        "- Entrega en CDMX y Area Metropolitana en 1 a 3 dias habiles. Envios foraneos por paqueteria o transporte segun volumen.",
        "- Puedes combinar varios productos en un mismo pedido siempre que cada uno alcance 10 kg minimo.",
    ]
    for n in notas:
        pdf.multi_cell(0, 6, n)
        pdf.ln(1)

    pdf.output(output_path)
    print(f"PDF generado OK -> {output_path}")


if __name__ == "__main__":
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    build_pdf(os.path.join(here, "catalogo-asmolinas.pdf"))
