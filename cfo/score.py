from cfo.modelos import ResumenFinanciero, NivelRiesgo


def calcular_score(resumen: ResumenFinanciero) -> tuple[int, str, dict]:
    """
    Calcula el score financiero personal (0-100).
    Retorna (score, clasificación, detalle_por_componente).
    """
    componentes = {}

    # 1. Flujo de efectivo (20 puntos)
    if resumen.ingreso_neto > 0:
        ratio_flujo = resumen.flujo_libre / resumen.ingreso_neto
        if ratio_flujo >= 0.20:
            pts = 20
        elif ratio_flujo >= 0.10:
            pts = 15
        elif ratio_flujo >= 0.05:
            pts = 10
        elif ratio_flujo >= 0:
            pts = 5
        else:
            pts = 0
    else:
        pts = 0
    componentes["flujo_efectivo"] = pts

    # 2. Tasa de ahorro (15 puntos)
    if resumen.tasa_ahorro >= 20:
        pts = 15
    elif resumen.tasa_ahorro >= 15:
        pts = 12
    elif resumen.tasa_ahorro >= 10:
        pts = 9
    elif resumen.tasa_ahorro >= 5:
        pts = 6
    elif resumen.tasa_ahorro > 0:
        pts = 3
    else:
        pts = 0
    componentes["tasa_ahorro"] = pts

    # 3. Control de gasto fijo (15 puntos)
    if resumen.tasa_gasto_fijo <= 40:
        pts = 15
    elif resumen.tasa_gasto_fijo <= 50:
        pts = 12
    elif resumen.tasa_gasto_fijo <= 60:
        pts = 8
    elif resumen.tasa_gasto_fijo <= 70:
        pts = 4
    else:
        pts = 0
    componentes["control_gasto_fijo"] = pts

    # 4. Salud de suscripciones (10 puntos)
    if resumen.ingreso_neto > 0:
        ratio_subs = resumen.gasto_suscripciones / resumen.ingreso_neto * 100
        if ratio_subs <= 3:
            pts = 10
        elif ratio_subs <= 5:
            pts = 7
        elif ratio_subs <= 8:
            pts = 4
        else:
            pts = 1
    else:
        pts = 5
    componentes["salud_suscripciones"] = pts

    # 5. Dependencia de deuda (10 puntos)
    if resumen.ingreso_neto > 0:
        ratio_deuda = resumen.gasto_financiero / resumen.ingreso_neto * 100
        if ratio_deuda <= 10:
            pts = 10
        elif ratio_deuda <= 20:
            pts = 7
        elif ratio_deuda <= 30:
            pts = 4
        elif ratio_deuda <= 40:
            pts = 2
        else:
            pts = 0
    else:
        pts = 5
    componentes["dependencia_deuda"] = pts

    # 6. Anomalías detectadas (10 puntos)
    num_altas = sum(1 for a in resumen.anomalias if a.riesgo == NivelRiesgo.ALTO)
    num_medias = sum(1 for a in resumen.anomalias if a.riesgo == NivelRiesgo.MEDIO)
    if num_altas == 0 and num_medias == 0:
        pts = 10
    elif num_altas == 0 and num_medias <= 2:
        pts = 7
    elif num_altas <= 1:
        pts = 4
    else:
        pts = 1
    componentes["riesgo_anomalias"] = pts

    # 7. Eficiencia del gasto (10 puntos)
    if resumen.ingreso_neto > 0:
        ratio_hormiga = resumen.gasto_hormiga / resumen.ingreso_neto * 100
        if ratio_hormiga <= 2:
            pts = 10
        elif ratio_hormiga <= 5:
            pts = 7
        elif ratio_hormiga <= 10:
            pts = 4
        else:
            pts = 1
    else:
        pts = 5
    componentes["eficiencia_gasto"] = pts

    # 8. Diversificación / concentración (10 puntos)
    if resumen.gastos_por_categoria:
        total_gasto = sum(resumen.gastos_por_categoria.values())
        if total_gasto > 0:
            max_cat = max(resumen.gastos_por_categoria.values())
            concentracion = max_cat / total_gasto * 100
            if concentracion <= 30:
                pts = 10
            elif concentracion <= 40:
                pts = 7
            elif concentracion <= 50:
                pts = 4
            else:
                pts = 2
        else:
            pts = 5
    else:
        pts = 5
    componentes["diversificacion"] = pts

    score_total = sum(componentes.values())
    score_total = max(0, min(100, score_total))

    if score_total >= 90:
        clasificacion = "Excelente"
    elif score_total >= 80:
        clasificacion = "Muy sano"
    elif score_total >= 70:
        clasificacion = "Mejorable"
    elif score_total >= 60:
        clasificacion = "Riesgo moderado"
    else:
        clasificacion = "Riesgo financiero"

    return score_total, clasificacion, componentes
