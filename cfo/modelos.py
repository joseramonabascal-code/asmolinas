from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


class TipoGasto(Enum):
    FIJO = "fijo"
    VARIABLE = "variable"
    DISCRECIONAL = "discrecional"
    FINANCIERO = "financiero"
    HORMIGA = "hormiga"
    SUSCRIPCION = "suscripcion"
    INGRESO = "ingreso"


class NivelRiesgo(Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"


class RecomendacionSuscripcion(Enum):
    MANTENER = "Mantener"
    NEGOCIAR = "Negociar"
    DOWNGRADE = "Downgrade"
    COMPARTIR = "Compartir"
    CANCELAR = "Cancelar"


class ImpactoDificultad(Enum):
    ALTO_FACIL = "Alto impacto + Fácil → Ejecutar hoy"
    ALTO_DIFICIL = "Alto impacto + Difícil → Plan estratégico"
    BAJO_FACIL = "Bajo impacto + Fácil → Optimización secundaria"
    BAJO_DIFICIL = "Bajo impacto + Difícil → Ignorar"


CATEGORIAS = {
    "vivienda": {
        "tipo": TipoGasto.FIJO,
        "palabras": [
            "renta", "hipoteca", "predial", "mantenimiento", "condominio",
            "agua", "luz", "gas", "cfe", "telmex", "internet", "izzi",
            "totalplay", "megacable", "axtel", "altan",
        ],
        "benchmark_max": 0.30,
    },
    "alimentacion": {
        "tipo": TipoGasto.VARIABLE,
        "palabras": [
            "super", "walmart", "soriana", "chedraui", "costco", "sam",
            "heb", "la comer", "comercial mexicana", "bodega", "aurrera",
            "mercado", "abarrotes", "carniceria", "verduleria", "fruteria",
            "oxxo", "7eleven", "7-eleven", "circle k",
        ],
        "benchmark_max": 0.15,
    },
    "restaurantes": {
        "tipo": TipoGasto.DISCRECIONAL,
        "palabras": [
            "restaurant", "rest ", "cafe", "coffee", "starbucks", "mcdonalds",
            "burger", "subway", "dominos", "pizza", "sushi", "tacos",
            "uber eats", "ubereats", "didi food", "rappi", "cornershop",
        ],
        "benchmark_max": 0.05,
    },
    "transporte": {
        "tipo": TipoGasto.VARIABLE,
        "palabras": [
            "gasolina", "gas ", "pemex", "bp ", "shell", "mobil",
            "uber", "didi", "cabify", "taxi", "estacionamiento",
            "parquimetro", "caseta", "peaje", "tag", "televia",
            "autobus", "metro", "metrobus",
        ],
        "benchmark_max": 0.10,
    },
    "salud": {
        "tipo": TipoGasto.VARIABLE,
        "palabras": [
            "farmacia", "guadalajara", "ahorro", "similares", "benavides",
            "sanborns", "doctor", "medico", "hospital", "clinica", "consultorio",
            "laboratorio", "dentista", "optica", "lentes",
        ],
        "benchmark_max": 0.05,
    },
    "educacion": {
        "tipo": TipoGasto.FIJO,
        "palabras": [
            "colegio", "escuela", "universidad", "inscripcion", "colegiatura",
            "libros", "papeleria", "curso", "capacitacion", "udemy",
            "coursera", "platzi", "domestika",
        ],
        "benchmark_max": 0.10,
    },
    "seguros": {
        "tipo": TipoGasto.FIJO,
        "palabras": [
            "seguro", "gnp", "axa", "metlife", "qualitas", "mapfre",
            "zurich", "allianz", "chubb", "inbursa", "hdi",
        ],
        "benchmark_max": 0.05,
    },
    "entretenimiento": {
        "tipo": TipoGasto.DISCRECIONAL,
        "palabras": [
            "cine", "cinepolis", "cinemex", "netflix", "spotify", "amazon",
            "prime", "disney", "hbo", "max", "youtube", "apple tv",
            "xbox", "playstation", "steam", "nintendo", "videojuego",
        ],
        "benchmark_max": 0.10,
    },
    "suscripciones_digitales": {
        "tipo": TipoGasto.SUSCRIPCION,
        "palabras": [
            "netflix", "spotify", "apple", "google", "microsoft", "adobe",
            "dropbox", "icloud", "canva", "notion", "slack", "zoom",
            "chatgpt", "openai", "midjourney", "github", "figma",
            "crunchyroll", "twitch", "patreon", "substack",
        ],
        "benchmark_max": 0.03,
    },
    "ropa_y_calzado": {
        "tipo": TipoGasto.DISCRECIONAL,
        "palabras": [
            "zara", "h&m", "shein", "liverpool", "palacio", "sears",
            "suburbia", "c&a", "bershka", "pull&bear", "nike", "adidas",
            "amazon", "mercadolibre", "mercado libre",
        ],
        "benchmark_max": 0.05,
    },
    "deuda": {
        "tipo": TipoGasto.FINANCIERO,
        "palabras": [
            "credito", "tarjeta", "pago minimo", "intereses", "prestamo",
            "financiamiento", "mensualidad", "abono", "banamex", "bbva",
            "santander", "hsbc", "banorte", "scotiabank", "infonavit",
            "fonacot", "coppel credito",
        ],
        "benchmark_max": 0.20,
    },
    "transferencias": {
        "tipo": TipoGasto.VARIABLE,
        "palabras": [
            "transferencia", "spei", "traspaso", "envio", "deposito",
        ],
        "benchmark_max": None,
    },
    "retiros_efectivo": {
        "tipo": TipoGasto.VARIABLE,
        "palabras": [
            "retiro", "cajero", "atm", "disposicion", "efectivo",
        ],
        "benchmark_max": None,
    },
    "sin_categorizar": {
        "tipo": TipoGasto.DISCRECIONAL,
        "palabras": [],
        "benchmark_max": None,
    },
}


SUSCRIPCIONES_CONOCIDAS = {
    "netflix": {"nombre": "Netflix", "costo_estimado": 219, "categoria": "streaming"},
    "spotify": {"nombre": "Spotify", "costo_estimado": 115, "categoria": "musica"},
    "amazon prime": {"nombre": "Amazon Prime", "costo_estimado": 99, "categoria": "streaming"},
    "disney": {"nombre": "Disney+", "costo_estimado": 159, "categoria": "streaming"},
    "hbo": {"nombre": "HBO Max", "costo_estimado": 149, "categoria": "streaming"},
    "max": {"nombre": "Max", "costo_estimado": 149, "categoria": "streaming"},
    "apple tv": {"nombre": "Apple TV+", "costo_estimado": 99, "categoria": "streaming"},
    "youtube premium": {"nombre": "YouTube Premium", "costo_estimado": 129, "categoria": "streaming"},
    "youtube music": {"nombre": "YouTube Music", "costo_estimado": 79, "categoria": "musica"},
    "crunchyroll": {"nombre": "Crunchyroll", "costo_estimado": 79, "categoria": "streaming"},
    "paramount": {"nombre": "Paramount+", "costo_estimado": 79, "categoria": "streaming"},
    "apple music": {"nombre": "Apple Music", "costo_estimado": 99, "categoria": "musica"},
    "icloud": {"nombre": "iCloud+", "costo_estimado": 29, "categoria": "almacenamiento"},
    "google one": {"nombre": "Google One", "costo_estimado": 49, "categoria": "almacenamiento"},
    "dropbox": {"nombre": "Dropbox", "costo_estimado": 199, "categoria": "almacenamiento"},
    "microsoft 365": {"nombre": "Microsoft 365", "costo_estimado": 150, "categoria": "productividad"},
    "adobe": {"nombre": "Adobe CC", "costo_estimado": 550, "categoria": "productividad"},
    "canva": {"nombre": "Canva Pro", "costo_estimado": 129, "categoria": "productividad"},
    "notion": {"nombre": "Notion", "costo_estimado": 80, "categoria": "productividad"},
    "chatgpt": {"nombre": "ChatGPT Plus", "costo_estimado": 399, "categoria": "ia"},
    "openai": {"nombre": "OpenAI", "costo_estimado": 399, "categoria": "ia"},
    "midjourney": {"nombre": "Midjourney", "costo_estimado": 199, "categoria": "ia"},
    "github": {"nombre": "GitHub", "costo_estimado": 79, "categoria": "desarrollo"},
    "figma": {"nombre": "Figma", "costo_estimado": 199, "categoria": "desarrollo"},
    "platzi": {"nombre": "Platzi", "costo_estimado": 299, "categoria": "educacion"},
    "udemy": {"nombre": "Udemy", "costo_estimado": 0, "categoria": "educacion"},
    "gym": {"nombre": "Gimnasio", "costo_estimado": 500, "categoria": "salud"},
    "smart fit": {"nombre": "Smart Fit", "costo_estimado": 499, "categoria": "salud"},
}


@dataclass
class Transaccion:
    fecha: date
    descripcion: str
    monto: float
    tipo: str  # "cargo" o "abono"
    categoria: str = "sin_categorizar"
    tipo_gasto: TipoGasto = TipoGasto.DISCRECIONAL
    es_suscripcion: bool = False
    es_duplicado: bool = False
    riesgo: NivelRiesgo = NivelRiesgo.BAJO
    notas: str = ""
    referencia: str = ""


@dataclass
class Suscripcion:
    nombre: str
    costo_mensual: float
    costo_anual: float
    categoria_servicio: str
    frecuencia_cobro: int  # veces al mes que aparece
    uso_estimado: str = "Desconocido"
    roi: str = "Por evaluar"
    alternativa: str = ""
    recomendacion: RecomendacionSuscripcion = RecomendacionSuscripcion.MANTENER
    nota: str = ""


@dataclass
class Anomalia:
    tipo: str
    descripcion: str
    transacciones: list = field(default_factory=list)
    impacto_mensual: float = 0.0
    impacto_anual: float = 0.0
    riesgo: NivelRiesgo = NivelRiesgo.BAJO
    accion_sugerida: str = ""


@dataclass
class OportunidadAhorro:
    descripcion: str
    ahorro_mensual: float
    ahorro_anual: float
    dificultad: str  # "Fácil", "Media", "Difícil"
    impacto: str  # "Alto", "Medio", "Bajo"
    prioridad: ImpactoDificultad = ImpactoDificultad.BAJO_FACIL
    accion: str = ""


@dataclass
class ResumenFinanciero:
    periodo: str
    ingreso_neto: float
    gasto_total: float
    gasto_fijo: float
    gasto_variable: float
    gasto_discrecional: float
    gasto_financiero: float
    gasto_hormiga: float
    gasto_suscripciones: float
    flujo_libre: float
    tasa_ahorro: float
    tasa_gasto_fijo: float
    score: int
    clasificacion_score: str
    suscripciones: list[Suscripcion] = field(default_factory=list)
    anomalias: list[Anomalia] = field(default_factory=list)
    oportunidades: list[OportunidadAhorro] = field(default_factory=list)
    gastos_por_categoria: dict = field(default_factory=dict)
    top_comercios: list = field(default_factory=list)
