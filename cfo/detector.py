from collections import defaultdict
from datetime import timedelta

from cfo.modelos import Transaccion, Anomalia, NivelRiesgo


def detectar_duplicados(transacciones: list[Transaccion]) -> list[Anomalia]:
    """Detecta cargos que parecen duplicados."""
    anomalias = []

    # Agrupar por monto exacto en el mismo día o día siguiente
    por_monto: dict[float, list[Transaccion]] = defaultdict(list)
    for txn in transacciones:
        if txn.tipo == "abono":
            continue
        por_monto[txn.monto].append(txn)

    for monto, txns in por_monto.items():
        if len(txns) < 2:
            continue
        for i, t1 in enumerate(txns):
            for t2 in txns[i + 1:]:
                diff_dias = abs((t2.fecha - t1.fecha).days)
                if diff_dias <= 1 and t1.descripcion.lower()[:15] == t2.descripcion.lower()[:15]:
                    t1.es_duplicado = True
                    t2.es_duplicado = True
                    anomalias.append(Anomalia(
                        tipo="Cargo duplicado",
                        descripcion=f"${monto:,.2f} en '{t1.descripcion[:30]}' — {t1.fecha} y {t2.fecha}",
                        transacciones=[t1, t2],
                        impacto_mensual=monto,
                        impacto_anual=monto * 12,
                        riesgo=NivelRiesgo.ALTO,
                        accion_sugerida="Verificar con el banco y solicitar devolución si es duplicado",
                    ))

    return anomalias


def detectar_montos_anormales(transacciones: list[Transaccion]) -> list[Anomalia]:
    """Detecta montos inusualmente altos respecto al patrón del usuario."""
    anomalias = []
    cargos = [t for t in transacciones if t.tipo == "cargo"]
    if len(cargos) < 5:
        return anomalias

    montos = [t.monto for t in cargos]
    promedio = sum(montos) / len(montos)
    # Desviación estándar
    varianza = sum((m - promedio) ** 2 for m in montos) / len(montos)
    desv = varianza ** 0.5

    umbral = promedio + (2.5 * desv)

    for txn in cargos:
        if txn.monto > umbral and txn.monto > 5000:
            txn.riesgo = NivelRiesgo.MEDIO
            anomalias.append(Anomalia(
                tipo="Monto inusualmente alto",
                descripcion=f"${txn.monto:,.2f} en '{txn.descripcion[:30]}' el {txn.fecha} (promedio: ${promedio:,.2f})",
                transacciones=[txn],
                impacto_mensual=txn.monto,
                impacto_anual=txn.monto,
                riesgo=NivelRiesgo.MEDIO,
                accion_sugerida="Verificar que este cargo sea legítimo",
            ))

    return anomalias


def detectar_cargos_recurrentes_sospechosos(transacciones: list[Transaccion]) -> list[Anomalia]:
    """Detecta cargos recurrentes que podrían ser suscripciones olvidadas."""
    anomalias = []
    cargos = [t for t in transacciones if t.tipo == "cargo"]

    # Agrupar por montos iguales con descripciones similares
    grupos: dict[str, list[Transaccion]] = defaultdict(list)
    for txn in cargos:
        clave = f"{txn.monto:.2f}_{txn.descripcion.lower()[:15]}"
        grupos[clave].append(txn)

    for clave, txns in grupos.items():
        if len(txns) < 2:
            continue
        txns.sort(key=lambda t: t.fecha)
        intervalos = [(txns[i + 1].fecha - txns[i].fecha).days for i in range(len(txns) - 1)]
        if not intervalos:
            continue

        promedio_intervalo = sum(intervalos) / len(intervalos)
        # Si el intervalo es ~30 días, parece mensual
        if 25 <= promedio_intervalo <= 35:
            monto = txns[0].monto
            desc = txns[0].descripcion[:30]
            ya_suscripcion = any(t.es_suscripcion for t in txns)
            if not ya_suscripcion:
                anomalias.append(Anomalia(
                    tipo="Posible suscripción no identificada",
                    descripcion=f"${monto:,.2f} recurrente (~mensual) en '{desc}' — {len(txns)} cobros detectados",
                    transacciones=txns,
                    impacto_mensual=monto,
                    impacto_anual=monto * 12,
                    riesgo=NivelRiesgo.BAJO,
                    accion_sugerida="Verificar si es una suscripción activa y si la estás usando",
                ))

    return anomalias


def detectar_incrementos_abruptos(transacciones: list[Transaccion]) -> list[Anomalia]:
    """Detecta incrementos abruptos en un mismo comercio/servicio."""
    anomalias = []
    cargos = [t for t in transacciones if t.tipo == "cargo"]

    por_comercio: dict[str, list[Transaccion]] = defaultdict(list)
    for txn in cargos:
        nombre = txn.descripcion.lower()[:20]
        por_comercio[nombre].append(txn)

    for comercio, txns in por_comercio.items():
        if len(txns) < 3:
            continue
        txns.sort(key=lambda t: t.fecha)
        for i in range(1, len(txns)):
            anterior = txns[i - 1].monto
            actual = txns[i].monto
            if anterior > 0 and actual > anterior * 1.5 and (actual - anterior) > 100:
                anomalias.append(Anomalia(
                    tipo="Incremento abrupto de precio",
                    descripcion=f"'{txns[i].descripcion[:30]}' subió de ${anterior:,.2f} a ${actual:,.2f} (+{((actual / anterior) - 1) * 100:.0f}%)",
                    transacciones=[txns[i - 1], txns[i]],
                    impacto_mensual=actual - anterior,
                    impacto_anual=(actual - anterior) * 12,
                    riesgo=NivelRiesgo.MEDIO,
                    accion_sugerida="Verificar si el aumento de precio está justificado",
                ))

    return anomalias


def ejecutar_deteccion_completa(transacciones: list[Transaccion]) -> list[Anomalia]:
    """Ejecuta todas las detecciones y retorna anomalías ordenadas por riesgo."""
    todas = []
    todas.extend(detectar_duplicados(transacciones))
    todas.extend(detectar_montos_anormales(transacciones))
    todas.extend(detectar_cargos_recurrentes_sospechosos(transacciones))
    todas.extend(detectar_incrementos_abruptos(transacciones))

    orden_riesgo = {NivelRiesgo.ALTO: 0, NivelRiesgo.MEDIO: 1, NivelRiesgo.BAJO: 2}
    todas.sort(key=lambda a: (orden_riesgo.get(a.riesgo, 3), -a.impacto_anual))
    return todas
