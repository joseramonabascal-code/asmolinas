from cfo.modelos import CATEGORIAS


BENCHMARKS = {
    "vivienda": {"max": 0.30, "ideal": 0.25, "etiqueta": "Vivienda"},
    "alimentacion": {"max": 0.15, "ideal": 0.12, "etiqueta": "Alimentación"},
    "transporte": {"max": 0.10, "ideal": 0.08, "etiqueta": "Transporte"},
    "deuda": {"max": 0.20, "ideal": 0.10, "etiqueta": "Deuda / Financiero"},
    "suscripciones_digitales": {"max": 0.03, "ideal": 0.02, "etiqueta": "Suscripciones"},
    "entretenimiento": {"max": 0.10, "ideal": 0.05, "etiqueta": "Entretenimiento"},
    "restaurantes": {"max": 0.05, "ideal": 0.03, "etiqueta": "Restaurantes"},
    "salud": {"max": 0.05, "ideal": 0.03, "etiqueta": "Salud"},
    "educacion": {"max": 0.10, "ideal": 0.05, "etiqueta": "Educación"},
    "seguros": {"max": 0.05, "ideal": 0.03, "etiqueta": "Seguros"},
    "ropa_y_calzado": {"max": 0.05, "ideal": 0.03, "etiqueta": "Ropa y calzado"},
}

BENCHMARK_AHORRO = {"min": 0.10, "ideal": 0.20, "excelente": 0.30}
BENCHMARK_FONDO_EMERGENCIA_MESES = {"min": 3, "ideal": 6, "excelente": 12}


def evaluar_benchmarks(gastos_por_categoria: dict[str, float], ingreso_neto: float) -> list[dict]:
    """Evalúa cada categoría contra los benchmarks financieros sanos."""
    resultados = []

    for cat, bench in BENCHMARKS.items():
        gasto = gastos_por_categoria.get(cat, 0)
        if ingreso_neto <= 0:
            continue

        porcentaje = gasto / ingreso_neto
        limite = bench["max"]
        ideal = bench["ideal"]

        if porcentaje <= ideal:
            estado = "OK"
            emoji = "OK"
        elif porcentaje <= limite:
            estado = "Aceptable"
            emoji = "~"
        else:
            estado = "EXCEDIDO"
            emoji = "!!"

        exceso_monto = max(0, gasto - (ingreso_neto * limite))

        resultados.append({
            "categoria": bench["etiqueta"],
            "gasto": gasto,
            "porcentaje": porcentaje * 100,
            "limite_porcentaje": limite * 100,
            "ideal_porcentaje": ideal * 100,
            "estado": estado,
            "indicador": emoji,
            "exceso": exceso_monto,
        })

    resultados.sort(key=lambda r: r["porcentaje"], reverse=True)
    return resultados


def evaluar_tasa_ahorro(flujo_libre: float, ingreso_neto: float) -> dict:
    """Evalúa la tasa de ahorro contra benchmarks."""
    if ingreso_neto <= 0:
        return {"tasa": 0, "estado": "Sin ingreso", "meta_mensual": 0}

    tasa = flujo_libre / ingreso_neto

    if tasa >= BENCHMARK_AHORRO["excelente"]:
        estado = "Excelente"
    elif tasa >= BENCHMARK_AHORRO["ideal"]:
        estado = "Muy bien"
    elif tasa >= BENCHMARK_AHORRO["min"]:
        estado = "Aceptable"
    elif tasa > 0:
        estado = "Insuficiente"
    else:
        estado = "Negativo — sin capacidad de ahorro"

    meta_ideal = ingreso_neto * BENCHMARK_AHORRO["ideal"]
    diferencia = meta_ideal - flujo_libre

    return {
        "tasa": tasa * 100,
        "estado": estado,
        "flujo_libre": flujo_libre,
        "meta_ideal_mensual": meta_ideal,
        "diferencia_vs_ideal": diferencia,
    }


def calcular_meses_supervivencia(flujo_libre_mensual: float, gasto_fijo: float) -> dict:
    """Calcula cuántos meses se puede sobrevivir sin ingresos."""
    if gasto_fijo <= 0:
        return {"meses": 0, "estado": "Sin datos de gasto fijo"}

    # Asumiendo un fondo de emergencia basado en el flujo libre acumulado
    # (esto es una estimación — el usuario debería proveer su fondo real)
    return {
        "gasto_fijo_mensual": gasto_fijo,
        "ahorro_mensual_potencial": max(0, flujo_libre_mensual),
        "meses_para_fondo_3": round(gasto_fijo * 3 / max(flujo_libre_mensual, 1)),
        "meses_para_fondo_6": round(gasto_fijo * 6 / max(flujo_libre_mensual, 1)),
        "fondo_recomendado_min": gasto_fijo * 3,
        "fondo_recomendado_ideal": gasto_fijo * 6,
    }
