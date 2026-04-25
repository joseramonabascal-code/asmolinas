from fpdf import FPDF

FOREST  = (45, 74, 62)
TERRA   = (196, 112, 75)
CREAM   = (251, 248, 243)
WHITE   = (255, 255, 255)
MUTED   = (107, 107, 107)
LIGHT   = (232, 221, 208)

CATS = {
    "Especias":      (TERRA,  "Especias y Chiles"),
    "Tes":           ((58,122,48),  "Tés Artesanales"),
    "Deshidratados": ((112,48,160), "Deshidratados"),
    "Semillas":      ((160,112,8),  "Semillas y Nueces"),
    "Sales":         ((192,88,64),  "Sales Gourmet"),
    "Kits":          (FOREST, "Kits y Paquetes"),
}

products = [
    ("Canela en raja",         "Canela ceylan premium, aroma intenso",       180, "kg", "Especias",      "Popular"),
    ("Canela molida",          "Molida fina, ideal para reposteria",          190, "kg", "Especias",      ""),
    ("Pimienta negra entera",  "Grano entero seleccionado",                   220, "kg", "Especias",      ""),
    ("Pimienta negra molida",  "Molida gruesa, sabor intenso",                230, "kg", "Especias",      ""),
    ("Comino entero",          "Semilla entera de alta calidad",              160, "kg", "Especias",      ""),
    ("Chile ancho seco",       "Deshidratado, limpio y seleccionado",         140, "kg", "Especias",      ""),
    ("Chile guajillo seco",    "Seleccionado, color rojo intenso",            130, "kg", "Especias",      ""),
    ("Oregano molido",         "Oregano mexicano, aroma fresco",              120, "kg", "Especias",      ""),
    ("Clavo de olor",          "Grano entero, muy aromatico",                 350, "kg", "Especias",      "Premium"),
    ("Curcuma en polvo",       "Raiz molida, color dorado intenso",           170, "kg", "Especias",      ""),
    ("Manzanilla premium",     "Flor entera, cosecha reciente",               180, "kg", "Tes",           "Popular"),
    ("Hierbabuena",            "Hojas secas, aroma refrescante",              140, "kg", "Tes",           ""),
    ("Te de limon",            "Hojas de limon natural",                      120, "kg", "Tes",           ""),
    ("Moringa",                "Hojas secas, alto valor nutricional",         250, "kg", "Tes",           "Superfood"),
    ("Flor de Jamaica",        "Flor entera, ideal para agua fresca",         130, "kg", "Tes",           ""),
    ("Mezcla relajante",       "Manzanilla, lavanda y pasiflora",             220, "kg", "Tes",           "Nuevo"),
    ("Arandano deshidratado",  "Fruta entera, sabor dulce-acido",             90,  "kg", "Deshidratados", "Popular"),
    ("Mango rodaja",           "Rodajas deshidratadas, sin azucar",           135, "kg", "Deshidratados", ""),
    ("Mango cubo",             "Cubos deshidratados, snack natural",          135, "kg", "Deshidratados", ""),
    ("Fresa deshidratada",     "Rodaja entera, color intenso",                200, "kg", "Deshidratados", "Premium"),
    ("Pina rodaja",            "Rodajas naturales deshidratadas",             180, "kg", "Deshidratados", ""),
    ("Pina cubo",              "Cubos practicos para granola",                135, "kg", "Deshidratados", ""),
    ("Papaya deshidratada",    "Trozos dulces y suaves",                      110, "kg", "Deshidratados", ""),
    ("Manzana rodaja",         "Rodajas crujientes, sin azucar",              120, "kg", "Deshidratados", ""),
    ("Cereza deshidratada",    "Sabor intenso, ideal reposteria",             170, "kg", "Deshidratados", ""),
    ("Orejon (chabacano)",     "Chabacano deshidratado premium",              250, "kg", "Deshidratados", "Premium"),
    ("Almendra natural",       "Entera con cuticula, seleccionada",           190, "kg", "Semillas",      "Popular"),
    ("Almendra fileteada",     "Corte fino para reposteria",                  200, "kg", "Semillas",      ""),
    ("Almendra sin cuticula",  "Pelada, lista para usar",                     200, "kg", "Semillas",      ""),
    ("Nuez de la India",       "Cashew entero, tostado natural",              210, "kg", "Semillas",      ""),
    ("Avellana",               "Entera con cuticula, grado premium",          370, "kg", "Semillas",      "Premium"),
    ("Ajonjoli natural",       "Semilla limpia, ideal para pan",              65,  "kg", "Semillas",      ""),
    ("Coco rallado",           "Rallado fino, sin azucar",                    80,  "kg", "Semillas",      ""),
    ("Sal del Himalaya fina",  "Sal rosa molida fina, 84 minerales",          85,  "kg", "Sales",         "Popular"),
    ("Sal del Himalaya gruesa","Grano grueso, ideal para molino",             80,  "kg", "Sales",         ""),
    ("Sal de mar gruesa",      "Cosechada naturalmente, sin refinar",         45,  "kg", "Sales",         ""),
    ("Kit Cocina Mexicana",    "Chile ancho + guajillo + comino + oregano, 250g c/u", 199, "kit", "Kits", "Bestseller"),
    ("Kit Reposteria",         "Canela + vainilla + nuez + almendra, 250g c/u",       249, "kit", "Kits", ""),
    ("Kit Tes Relajantes",     "Manzanilla + lavanda + pasiflora, 100g c/u",          179, "kit", "Kits", ""),
    ("Kit Superfoods",         "Chia + quinoa + curcuma + jengibre, 250g c/u",        229, "kit", "Kits", ""),
    ("Paquete Prueba",         "5 especias bestseller en sobres de 100g",             149, "paq", "Kits", ""),
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
        self.cell(0, 6, "AS MOLINAS  |  Catalogo de Productos 2026", align="C")
        self.set_text_color(0, 0, 0)
        self.ln(8)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 5, f"Pagina {self.page_no()}", align="C")
        self.cell(0, 5, "asmolinas.com  |  748 166 0295  |  info@asmolinas.com", align="R")
        self.set_text_color(0, 0, 0)

    def cover(self):
        # Full-page dark green background
        self.set_fill_color(*FOREST)
        self.rect(0, 0, 210, 297, "F")

        # Brand name
        self.set_font("Helvetica", "B", 42)
        self.set_text_color(*WHITE)
        self.set_y(80)
        self.cell(0, 16, "AS MOLINAS", align="C")

        # Separator line
        self.set_draw_color(*TERRA)
        self.set_line_width(1.2)
        self.line(60, 102, 150, 102)

        # Tagline
        self.set_font("Helvetica", "I", 13)
        self.set_text_color(200, 220, 210)
        self.set_y(106)
        self.cell(0, 8, "Especias, Tes y Productos Naturales", align="C")

        # Catalog title box
        self.set_fill_color(*TERRA)
        self.set_y(130)
        self.set_x(45)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*WHITE)
        self.cell(120, 14, "CATALOGO DE PRODUCTOS 2026", align="C", fill=True)

        # Description
        self.set_font("Helvetica", "", 10)
        self.set_text_color(200, 220, 210)
        self.set_y(160)
        self.multi_cell(0, 6,
            "Mayoreo y menudeo  |  CDMX y Area Metropolitana\n"
            "100% naturales, sin conservadores\n"
            "Pedido minimo $300 MXN",
            align="C")

        # Contact block
        self.set_fill_color(30, 55, 45)
        self.rect(30, 220, 150, 44, "F")
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*WHITE)
        self.set_y(228)
        self.cell(0, 6, "Contacto", align="C")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(200, 220, 210)
        self.ln(8)
        self.cell(0, 5, "WhatsApp: 748 166 0295", align="C")
        self.ln(6)
        self.cell(0, 5, "Email: info@asmolinas.com", align="C")
        self.ln(6)
        self.cell(0, 5, "Instagram: @asmolinas_especias", align="C")

    def category_header(self, label, color):
        self.set_fill_color(*color)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*WHITE)
        self.cell(0, 10, f"  {label}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)
        self.set_text_color(0, 0, 0)

    def product_row(self, name, desc, price, unit, tag, col):
        x_start = self.get_x()
        y_start = self.get_y()
        col_w = 90
        x = 10 + col * (col_w + 5)

        # Card background
        self.set_fill_color(*CREAM)
        self.set_draw_color(*LIGHT)
        self.set_line_width(0.3)
        self.rect(x, y_start, col_w, 26, "FD")

        # Tag badge
        if tag:
            self.set_fill_color(*TERRA)
            self.set_font("Helvetica", "B", 6)
            self.set_text_color(*WHITE)
            self.set_xy(x + col_w - 24, y_start + 2)
            self.cell(22, 4, tag.upper(), align="C", fill=True)

        # Name
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*FOREST)
        self.set_xy(x + 3, y_start + 3)
        self.cell(col_w - 30, 5, name)

        # Desc
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*MUTED)
        self.set_xy(x + 3, y_start + 9)
        self.multi_cell(col_w - 6, 4, desc)

        # Price
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*TERRA)
        self.set_xy(x + 3, y_start + 19)
        self.cell(col_w - 6, 5, f"${price} MXN/{unit}")

        self.set_text_color(0, 0, 0)
        return y_start + 29  # next y after card


pdf = CatalogPDF(orientation="P", unit="mm", format="A4")
pdf.set_auto_page_break(auto=True, margin=18)
pdf.set_margins(10, 18, 10)

# Cover page
pdf.add_page()
pdf.cover()

# Group products by category
from collections import defaultdict
by_cat = defaultdict(list)
for p in products:
    by_cat[p[4]].append(p)

cat_order = ["Especias", "Tes", "Deshidratados", "Semillas", "Sales", "Kits"]

for cat_key in cat_order:
    prods = by_cat[cat_key]
    color, label = CATS[cat_key]
    pdf.add_page()
    pdf.category_header(label, color)

    col = 0
    row_y = pdf.get_y()
    for p in prods:
        name, desc, price, unit, _, tag = p
        next_y = pdf.product_row(name, desc, price, unit, tag, col)
        if col == 0:
            col = 1
        else:
            col = 0
            row_y = next_y
            pdf.set_xy(10, row_y)
            if pdf.get_y() > 265:
                pdf.add_page()
                pdf.category_header(label + " (cont.)", color)
                row_y = pdf.get_y()

    # Last odd product leaves col=1, advance row
    if col == 1:
        pdf.set_xy(10, next_y)

pdf.output("C:/Users/jraba/Links/asmolinas-repo/assets/catalogo-asmolinas.pdf")
print("PDF generado OK")
