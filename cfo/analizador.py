from cfo.modelos import (
    Transaccion, ResumenFinanciero, OportunidadAhorro, TipoGasto,
    ImpactoDificultad,
)
from cfo.categorias import categorizar_todas, calcular_totales_categoria, top_comercios
from cfo.detector import ejecutar_deteccion_completa
from cfo.suscripciones import (
    detectar_suscripciones, detectar_redundancias, evaluar_suscripciones,
)
from cfo.score import calcular_score
from cfo.benchmark import evaluar_benchmarks, evaluar_tasa_ahorro, calcular_meses_supervivencia


def analizar(transacciones: list[Transaccion], periodo: str = "") -> ResumenFinanciero:
    """Ejecuta el análisis financiero completo sobre las transacciones."""

    # Categorizar
    transacciones = categorizar_todas(transacciones)

    # Calcular ingresos y gastos
    ingresos = sum(t.monto for t in transacciones if t.tipo == "abono")
    cargos = [t for t in transacciones if t.tipo == "cargo"]

    gasto_total = sum(t.monto for t in cargos)
    gasto_fijo = sum(t.monto for t in cargos if t.tipo_gasto == TipoGasto.FIJO)
    gasto_variable = sum(t.monto for t in cargos if t.tipo_gasto == TipoGasto.VARIABLE)
    gasto_discrecional = sum(t.monto for t in cargos if t.tipo_gasto == TipoGasto.DISCRECIONAL)
    gasto_financiero = sum(t.monto for t in cargos if t.tipo_gasto == TipoGasto.FINANCIERO)
    gasto_hormiga = sum(t.monto for t in cargos if t.tipo_gasto == TipoGasto.HORMIGA)
    gasto_suscripciones = sum(t.monto for t in cargos if t.tipo_gasto == TipoGasto.SUSCRIPCION)

    flujo_libre = ingresos - gasto_total
    tasa_ahorro = (flujo_libre / ingresos * 100) if ingresos > 0 else 0
    tasa_gasto_fijo = (gasto_fijo / ingresos * 100) if ingresos > 0 else 0

    # Categorías
    gastos_por_categoria = calcular_totales_categoria(transacciones)
    comercios_top = top_comercios(transacciones)

    # Detecciones
    anomalias = ejecutar_deteccion_completa(transacciones)

    # Suscripciones
    suscripciones = detectar_suscripciones(transacciones)
    suscripciones = evaluar_suscripciones(suscripciones, ingresos)
    redundancias = detectar_redundancias(suscripciones)

    # Construir resumen
    resumen = ResumenFinanciero(
        periodo=periodo,
        ingreso_neto=ingresos,
        gasto_total=gasto_total,
        gasto_fijo=gasto_fijo,
        gasto_variable=gasto_variable,
        gasto_discrecional=gasto_discrecional,
        gasto_financiero=gasto_financiero,
        gasto_hormiga=gasto_hormiga,
        gasto_suscripciones=gasto_suscripciones,
        flujo_libre=flujo_libre,
        tasa_ahorro=tasa_ahorro,
        tasa_gasto_fijo=tasa_gasto_fijo,
        score=0,
        clasificacion_score="",
        suscripciones=suscripciones,
        anomalias=anomalias,
        gastos_por_categoria=gastos_por_categoria,
        top_comercios=comercios_top,
    )

    # Oportunidades de ahorro
    resumen.oportunidades = _generar_oportunidades(resumen, redundancias)

    # Score
    score, clasificacion, _ = calcular_score(resumen)
    resumen.score = score
    resumen.clasificacion_score = clasificacion

    return resumen


def _generar_oportunidades(
    resumen: ResumenFinanciero,
    redundancias: list,
) -> list[OportunidadAhorro]:
    """Genera oportunidades de ahorro priorizadas."""
    ops = []

    # Suscripciones por cancelar
    from cfo.modelos import RecomendacionSuscripcion
    for sub in resumen.suscripciones:
        if sub.recomendacion == RecomendacionSuscripcion.CANCELAR:
            ops.append(OportunidadAhorro(
                descripcion=f"Cancelar {sub.nombre}",
                ahorro_mensual=sub.costo_mensual,
                ahorro_anual=sub.costo_anual,
                dificultad="Fácil",
                impacto="Alto" if sub.costo_mensual > 200 else "Medio",
                prioridad=ImpactoDificultad.ALTO_FACIL if sub.costo_mensual > 200 else ImpactoDificultad.BAJO_FACIL,
                accion=f"Cancelar suscripción de {sub.nombre} ({sub.nota})",
            ))
        elif sub.recomendacion == RecomendacionSuscripcion.NEGOCIAR:
            ahorro_est = sub.costo_mensual * 0.2
            ops.append(OportunidadAhorro(
                descripcion=f"Renegociar {sub.nombre}",
                ahorro_mensual=ahorro_est,
                ahorro_anual=ahorro_est * 12,
                dificultad="Media",
                impacto="Alto" if ahorro_est > 100 else "Medio",
                prioridad=ImpactoDificultad.ALTO_DIFICIL if ahorro_est > 100 else ImpactoDificultad.BAJO_FACIL,
                accion=f"Contactar a {sub.nombre} para negociar precio o hacer downgrade",
            ))

    # Redundancias
    for s1, s2, desc in redundancias:
        menor = min(s1.costo_mensual, s2.costo_mensual)
        ops.append(OportunidadAhorro(
            descripcion=f"Eliminar redundancia: {s1.nombre} + {s2.nombre}",
            ahorro_mensual=menor,
            ahorro_anual=menor * 12,
            dificultad="Fácil",
            impacto="Alto" if menor > 100 else "Medio",
            prioridad=ImpactoDificultad.ALTO_FACIL,
            accion=f"Quedarte con uno solo. {desc}",
        ))

    # Gasto hormiga
    if resumen.gasto_hormiga > 0:
        ahorro_hormiga = resumen.gasto_hormiga * 0.5
        ops.append(OportunidadAhorro(
            descripcion="Reducir gasto hormiga a la mitad",
            ahorro_mensual=ahorro_hormiga,
            ahorro_anual=ahorro_hormiga * 12,
            dificultad="Media",
            impacto="Alto" if ahorro_hormiga > 500 else "Medio",
            prioridad=ImpactoDificultad.ALTO_DIFICIL if ahorro_hormiga > 500 else ImpactoDificultad.BAJO_FACIL,
            accion=f"Gasto hormiga actual: ${resumen.gasto_hormiga:,.0f}/mes. Reducir compras menores a $100.",
        ))

    # Benchmarks excedidos
    from cfo.benchmark import evaluar_benchmarks
    benchmarks = evaluar_benchmarks(resumen.gastos_por_categoria, resumen.ingreso_neto)
    for b in benchmarks:
        if b["estado"] == "EXCEDIDO" and b["exceso"] > 0:
            ops.append(OportunidadAhorro(
                descripcion=f"Reducir gasto en {b['categoria']} al benchmark ({b['limite_porcentaje']:.0f}%)",
                ahorro_mensual=b["exceso"],
                ahorro_anual=b["exceso"] * 12,
                dificultad="Difícil" if b["exceso"] > 2000 else "Media",
                impacto="Alto" if b["exceso"] > 1000 else "Medio",
                prioridad=ImpactoDificultad.ALTO_DIFICIL if b["exceso"] > 1000 else ImpactoDificultad.BAJO_DIFICIL,
                accion=f"{b['categoria']}: gastas {b['porcentaje']:.1f}% vs límite de {b['limite_porcentaje']:.0f}%. Exceso: ${b['exceso']:,.0f}/mes.",
            ))

    # Duplicados
    for anomalia in resumen.anomalias:
        if anomalia.tipo == "Cargo duplicado":
            ops.append(OportunidadAhorro(
                descripcion=f"Recuperar cargo duplicado: {anomalia.descripcion[:40]}",
                ahorro_mensual=anomalia.impacto_mensual,
                ahorro_anual=anomalia.impacto_mensual,
                dificultad="Fácil",
                impacto="Alto",
                prioridad=ImpactoDificultad.ALTO_FACIL,
                accion="Contactar al banco para solicitar devolución del cargo duplicado",
            ))

    ops.sort(key=lambda o: o.ahorro_anual, reverse=True)
    return ops
