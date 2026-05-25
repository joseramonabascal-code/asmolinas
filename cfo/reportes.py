import os
from datetime import datetime

from cfo.modelos import ResumenFinanciero, NivelRiesgo
from cfo.benchmark import evaluar_benchmarks, evaluar_tasa_ahorro, calcular_meses_supervivencia


def generar_reporte(resumen: ResumenFinanciero) -> str:
    """Genera el reporte CFO completo en formato texto."""
    lineas = []

    def seccion(titulo: str):
        lineas.append("")
        lineas.append("=" * 70)
        lineas.append(f"  {titulo}")
        lineas.append("=" * 70)
        lineas.append("")

    def subseccion(titulo: str):
        lineas.append("")
        lineas.append(f"--- {titulo} ---")
        lineas.append("")

    # ENCABEZADO
    lineas.append("=" * 70)
    lineas.append("  CFO FINANCIERO PERSONAL — REPORTE EJECUTIVO")
    lineas.append(f"  Periodo: {resumen.periodo}")
    lineas.append(f"  Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    lineas.append("=" * 70)

    # RESUMEN EJECUTIVO
    seccion("RESUMEN EJECUTIVO")
    lineas.append(f"  Ingresos:            ${resumen.ingreso_neto:>12,.2f}")
    lineas.append(f"  Gastos totales:      ${resumen.gasto_total:>12,.2f}")
    lineas.append(f"  Flujo libre:         ${resumen.flujo_libre:>12,.2f}")
    lineas.append(f"  Tasa de ahorro:      {resumen.tasa_ahorro:>11.1f}%")
    lineas.append(f"  Score financiero:    {resumen.score:>8}/100 ({resumen.clasificacion_score})")
    lineas.append("")
    lineas.append(f"  Anomalias detectadas:   {len(resumen.anomalias)}")
    lineas.append(f"  Suscripciones activas:  {len(resumen.suscripciones)}")
    lineas.append(f"  Oportunidades ahorro:   {len(resumen.oportunidades)}")
    if resumen.oportunidades:
        ahorro_total = sum(o.ahorro_anual for o in resumen.oportunidades)
        lineas.append(f"  Ahorro potencial anual: ${ahorro_total:>12,.2f}")

    # ESTADO FINANCIERO
    seccion("ESTADO FINANCIERO PERSONAL")
    lineas.append(f"  {'Concepto':<30} {'Monto':>15} {'% Ingreso':>10}")
    lineas.append(f"  {'-'*30} {'-'*15} {'-'*10}")
    lineas.append(f"  {'Ingreso neto':<30} ${resumen.ingreso_neto:>14,.2f} {'100.0%':>10}")
    lineas.append(f"  {'(-) Gasto fijo':<30} ${resumen.gasto_fijo:>14,.2f} {_pct(resumen.gasto_fijo, resumen.ingreso_neto):>10}")
    lineas.append(f"  {'(-) Gasto variable':<30} ${resumen.gasto_variable:>14,.2f} {_pct(resumen.gasto_variable, resumen.ingreso_neto):>10}")
    lineas.append(f"  {'(-) Gasto discrecional':<30} ${resumen.gasto_discrecional:>14,.2f} {_pct(resumen.gasto_discrecional, resumen.ingreso_neto):>10}")
    lineas.append(f"  {'(-) Gasto financiero':<30} ${resumen.gasto_financiero:>14,.2f} {_pct(resumen.gasto_financiero, resumen.ingreso_neto):>10}")
    lineas.append(f"  {'(-) Gasto hormiga':<30} ${resumen.gasto_hormiga:>14,.2f} {_pct(resumen.gasto_hormiga, resumen.ingreso_neto):>10}")
    lineas.append(f"  {'(-) Suscripciones':<30} ${resumen.gasto_suscripciones:>14,.2f} {_pct(resumen.gasto_suscripciones, resumen.ingreso_neto):>10}")
    lineas.append(f"  {'-'*30} {'-'*15} {'-'*10}")
    lineas.append(f"  {'= FLUJO LIBRE':<30} ${resumen.flujo_libre:>14,.2f} {_pct(resumen.flujo_libre, resumen.ingreso_neto):>10}")

    # ANALISIS POR CATEGORIA
    seccion("ANALISIS POR CATEGORIA")
    if resumen.gastos_por_categoria:
        lineas.append(f"  {'Categoria':<25} {'Monto':>15} {'% Ingreso':>10} {'% Gasto':>10}")
        lineas.append(f"  {'-'*25} {'-'*15} {'-'*10} {'-'*10}")
        for cat, monto in resumen.gastos_por_categoria.items():
            lineas.append(
                f"  {cat:<25} ${monto:>14,.2f} "
                f"{_pct(monto, resumen.ingreso_neto):>10} "
                f"{_pct(monto, resumen.gasto_total):>10}"
            )

    # TOP COMERCIOS
    subseccion("Top 10 comercios por gasto")
    if resumen.top_comercios:
        lineas.append(f"  {'#':<4} {'Comercio':<30} {'Total':>12} {'Txns':>6}")
        lineas.append(f"  {'-'*4} {'-'*30} {'-'*12} {'-'*6}")
        for i, (nombre, total, count) in enumerate(resumen.top_comercios, 1):
            lineas.append(f"  {i:<4} {nombre:<30} ${total:>11,.2f} {count:>6}")

    # SUSCRIPCIONES
    seccion("MAPEO DE SUSCRIPCIONES")
    if resumen.suscripciones:
        lineas.append(f"  {'Servicio':<25} {'$/Mes':>10} {'$/Ano':>12} {'Cobros':>7} {'Recomendacion':<15}")
        lineas.append(f"  {'-'*25} {'-'*10} {'-'*12} {'-'*7} {'-'*15}")
        for sub in resumen.suscripciones:
            lineas.append(
                f"  {sub.nombre:<25} ${sub.costo_mensual:>9,.2f} ${sub.costo_anual:>11,.2f} "
                f"{sub.frecuencia_cobro:>7} {sub.recomendacion.value:<15}"
            )
            if sub.nota:
                lineas.append(f"    > {sub.nota}")
        total_m = sum(s.costo_mensual for s in resumen.suscripciones)
        total_a = sum(s.costo_anual for s in resumen.suscripciones)
        lineas.append(f"  {'-'*25} {'-'*10} {'-'*12}")
        lineas.append(f"  {'TOTAL':<25} ${total_m:>9,.2f} ${total_a:>11,.2f}")
    else:
        lineas.append("  No se detectaron suscripciones.")

    # DUPLICADOS Y ANOMALIAS
    seccion("DUPLICADOS Y ANOMALIAS")
    if resumen.anomalias:
        lineas.append(f"  {'Tipo':<30} {'Impacto/Mes':>12} {'Impacto/Ano':>12} {'Riesgo':<8}")
        lineas.append(f"  {'-'*30} {'-'*12} {'-'*12} {'-'*8}")
        for a in resumen.anomalias:
            lineas.append(
                f"  {a.tipo:<30} ${a.impacto_mensual:>11,.2f} ${a.impacto_anual:>11,.2f} {a.riesgo.value:<8}"
            )
            lineas.append(f"    {a.descripcion}")
            lineas.append(f"    Accion: {a.accion_sugerida}")
            lineas.append("")
    else:
        lineas.append("  No se detectaron anomalias ni duplicados.")

    # BENCHMARK
    seccion("BENCHMARK FINANCIERO")
    benchmarks = evaluar_benchmarks(resumen.gastos_por_categoria, resumen.ingreso_neto)
    if benchmarks:
        lineas.append(f"  {'Categoria':<20} {'Actual':>8} {'Limite':>8} {'Ideal':>8} {'Estado':<12} {'Exceso':>12}")
        lineas.append(f"  {'-'*20} {'-'*8} {'-'*8} {'-'*8} {'-'*12} {'-'*12}")
        for b in benchmarks:
            exceso_str = f"${b['exceso']:>11,.0f}" if b['exceso'] > 0 else f"{'$0':>12}"
            lineas.append(
                f"  {b['categoria']:<20} {b['porcentaje']:>7.1f}% {b['limite_porcentaje']:>7.0f}% "
                f"{b['ideal_porcentaje']:>7.0f}% {b['estado']:<12} {exceso_str}"
            )

    subseccion("Tasa de ahorro")
    eval_ahorro = evaluar_tasa_ahorro(resumen.flujo_libre, resumen.ingreso_neto)
    lineas.append(f"  Tasa actual:     {eval_ahorro['tasa']:.1f}%")
    lineas.append(f"  Estado:          {eval_ahorro['estado']}")
    lineas.append(f"  Meta ideal:      ${eval_ahorro['meta_ideal_mensual']:,.0f}/mes (20% del ingreso)")
    if eval_ahorro['diferencia_vs_ideal'] > 0:
        lineas.append(f"  Faltante:        ${eval_ahorro['diferencia_vs_ideal']:,.0f}/mes para llegar al ideal")

    subseccion("Fondo de emergencia")
    fondo = calcular_meses_supervivencia(resumen.flujo_libre, resumen.gasto_fijo)
    lineas.append(f"  Gasto fijo mensual:     ${fondo['gasto_fijo_mensual']:,.0f}")
    lineas.append(f"  Fondo minimo (3 meses): ${fondo['fondo_recomendado_min']:,.0f}")
    lineas.append(f"  Fondo ideal (6 meses):  ${fondo['fondo_recomendado_ideal']:,.0f}")
    if fondo['ahorro_mensual_potencial'] > 0:
        lineas.append(f"  Tiempo para fondo 3m:   {fondo['meses_para_fondo_3']} meses ahorrando ${fondo['ahorro_mensual_potencial']:,.0f}/mes")
        lineas.append(f"  Tiempo para fondo 6m:   {fondo['meses_para_fondo_6']} meses")

    # OPORTUNIDADES DE AHORRO
    seccion("OPORTUNIDADES DE AHORRO (Mayor a menor impacto)")
    if resumen.oportunidades:
        lineas.append(f"  {'#':<4} {'Descripcion':<35} {'$/Mes':>10} {'$/Ano':>12} {'Dificultad':<10} {'Impacto':<8}")
        lineas.append(f"  {'-'*4} {'-'*35} {'-'*10} {'-'*12} {'-'*10} {'-'*8}")
        for i, op in enumerate(resumen.oportunidades, 1):
            lineas.append(
                f"  {i:<4} {op.descripcion:<35} ${op.ahorro_mensual:>9,.0f} ${op.ahorro_anual:>11,.0f} "
                f"{op.dificultad:<10} {op.impacto:<8}"
            )
            lineas.append(f"       {op.prioridad.value}")
            lineas.append(f"       Accion: {op.accion}")
            lineas.append("")

        total_ahorro_m = sum(o.ahorro_mensual for o in resumen.oportunidades)
        total_ahorro_a = sum(o.ahorro_anual for o in resumen.oportunidades)
        lineas.append(f"  AHORRO POTENCIAL TOTAL: ${total_ahorro_m:,.0f}/mes = ${total_ahorro_a:,.0f}/ano")
    else:
        lineas.append("  No se identificaron oportunidades de ahorro adicionales.")

    # PLAN DE ACCION
    seccion("PLAN DE ACCION CFO")
    faciles = [o for o in resumen.oportunidades if o.dificultad == "Fácil"]
    medias = [o for o in resumen.oportunidades if o.dificultad == "Media"]
    dificiles = [o for o in resumen.oportunidades if o.dificultad == "Difícil"]

    subseccion("Ejecutar HOY")
    if faciles:
        for o in faciles:
            lineas.append(f"  [ ] {o.descripcion} (ahorro: ${o.ahorro_mensual:,.0f}/mes)")
    else:
        lineas.append("  Ninguna accion inmediata identificada.")

    subseccion("Este mes")
    if medias:
        for o in medias:
            lineas.append(f"  [ ] {o.descripcion} (ahorro: ${o.ahorro_mensual:,.0f}/mes)")

    subseccion("Plan estrategico")
    if dificiles:
        for o in dificiles:
            lineas.append(f"  [ ] {o.descripcion} (ahorro: ${o.ahorro_mensual:,.0f}/mes)")

    # SCORE
    seccion("SCORE FINANCIERO PERSONAL")
    lineas.append(f"  Score: {resumen.score}/100 — {resumen.clasificacion_score}")
    lineas.append("")
    barra = "#" * (resumen.score // 2) + "." * (50 - resumen.score // 2)
    lineas.append(f"  [{barra}]")
    lineas.append("")
    lineas.append("  Escala:")
    lineas.append("  90-100 = Excelente | 80-89 = Muy sano | 70-79 = Mejorable")
    lineas.append("  60-69 = Riesgo moderado | <60 = Riesgo financiero")

    # PIE
    lineas.append("")
    lineas.append("=" * 70)
    lineas.append("  Reporte generado por CFO Financiero Personal v1.0")
    lineas.append("=" * 70)

    return "\n".join(lineas)


def guardar_reporte(reporte: str, directorio: str = "datos/reportes") -> str:
    """Guarda el reporte en un archivo de texto."""
    os.makedirs(directorio, exist_ok=True)
    nombre = f"reporte_cfo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    ruta = os.path.join(directorio, nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(reporte)
    return ruta


def _pct(valor: float, base: float) -> str:
    if base <= 0:
        return "0.0%"
    return f"{valor / base * 100:.1f}%"
