from cfo.modelos import Transaccion, TipoGasto, CATEGORIAS, SUSCRIPCIONES_CONOCIDAS


def categorizar_transaccion(txn: Transaccion) -> Transaccion:
    """Asigna categoría y tipo de gasto a una transacción."""
    desc = txn.descripcion.lower()

    if txn.tipo == "abono":
        txn.categoria = "ingreso"
        txn.tipo_gasto = TipoGasto.INGRESO
        return txn

    for cat_nombre, cat_info in CATEGORIAS.items():
        if cat_nombre == "sin_categorizar":
            continue
        for palabra in cat_info["palabras"]:
            if palabra in desc:
                txn.categoria = cat_nombre
                txn.tipo_gasto = cat_info["tipo"]
                break
        if txn.categoria != "sin_categorizar":
            break

    for clave, info in SUSCRIPCIONES_CONOCIDAS.items():
        if clave in desc:
            txn.es_suscripcion = True
            if txn.categoria == "sin_categorizar":
                txn.categoria = "suscripciones_digitales"
                txn.tipo_gasto = TipoGasto.SUSCRIPCION
            break

    tiendas_conveniencia = ["oxxo", "7eleven", "7-eleven", "circle k"]
    es_conveniencia = any(t in desc for t in tiendas_conveniencia)

    if txn.monto < 100 and txn.tipo == "cargo":
        if txn.categoria in ["sin_categorizar", "restaurantes", "entretenimiento"] or es_conveniencia:
            txn.tipo_gasto = TipoGasto.HORMIGA

    return txn


def categorizar_todas(transacciones: list[Transaccion]) -> list[Transaccion]:
    """Categoriza todas las transacciones."""
    return [categorizar_transaccion(txn) for txn in transacciones]


def agrupar_por_categoria(transacciones: list[Transaccion]) -> dict[str, list[Transaccion]]:
    """Agrupa transacciones por categoría."""
    grupos = {}
    for txn in transacciones:
        if txn.tipo == "abono":
            continue
        cat = txn.categoria
        if cat not in grupos:
            grupos[cat] = []
        grupos[cat].append(txn)
    return grupos


def calcular_totales_categoria(transacciones: list[Transaccion]) -> dict[str, float]:
    """Calcula el total gastado por categoría."""
    totales = {}
    for txn in transacciones:
        if txn.tipo == "abono":
            continue
        cat = txn.categoria
        totales[cat] = totales.get(cat, 0) + txn.monto
    return dict(sorted(totales.items(), key=lambda x: x[1], reverse=True))


def top_comercios(transacciones: list[Transaccion], limite: int = 10) -> list[tuple[str, float, int]]:
    """Top comercios por gasto total. Retorna (nombre, total, num_transacciones)."""
    comercios: dict[str, dict] = {}
    for txn in transacciones:
        if txn.tipo == "abono":
            continue
        desc = txn.descripcion.upper().strip()
        # Simplificar nombre del comercio (quitar números de referencia)
        nombre = desc.split("/")[0].strip()[:40]
        if nombre not in comercios:
            comercios[nombre] = {"total": 0, "count": 0}
        comercios[nombre]["total"] += txn.monto
        comercios[nombre]["count"] += 1

    resultado = [
        (nombre, info["total"], info["count"])
        for nombre, info in comercios.items()
    ]
    resultado.sort(key=lambda x: x[1], reverse=True)
    return resultado[:limite]
