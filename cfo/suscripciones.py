from collections import defaultdict

from cfo.modelos import (
    Transaccion, Suscripcion, RecomendacionSuscripcion,
    SUSCRIPCIONES_CONOCIDAS,
)


def detectar_suscripciones(transacciones: list[Transaccion]) -> list[Suscripcion]:
    """Identifica todas las suscripciones activas en las transacciones."""
    suscripciones = []
    cargos = [t for t in transacciones if t.tipo == "cargo"]

    # Buscar suscripciones conocidas
    encontradas: dict[str, list[Transaccion]] = defaultdict(list)
    for txn in cargos:
        desc = txn.descripcion.lower()
        for clave, info in SUSCRIPCIONES_CONOCIDAS.items():
            if clave in desc:
                encontradas[clave].append(txn)
                txn.es_suscripcion = True
                break

    for clave, txns in encontradas.items():
        info = SUSCRIPCIONES_CONOCIDAS[clave]
        montos = [t.monto for t in txns]
        costo_promedio = sum(montos) / len(montos)

        suscripciones.append(Suscripcion(
            nombre=info["nombre"],
            costo_mensual=round(costo_promedio, 2),
            costo_anual=round(costo_promedio * 12, 2),
            categoria_servicio=info["categoria"],
            frecuencia_cobro=len(txns),
        ))

    # Buscar cargos recurrentes no identificados como suscripción
    por_monto_desc: dict[str, list[Transaccion]] = defaultdict(list)
    for txn in cargos:
        if txn.es_suscripcion:
            continue
        clave = f"{txn.monto:.0f}_{txn.descripcion.lower()[:15]}"
        por_monto_desc[clave].append(txn)

    for clave, txns in por_monto_desc.items():
        if len(txns) < 2:
            continue
        txns.sort(key=lambda t: t.fecha)
        if len(txns) >= 2:
            intervalos = [(txns[i + 1].fecha - txns[i].fecha).days for i in range(len(txns) - 1)]
            prom_intervalo = sum(intervalos) / len(intervalos) if intervalos else 0
            if 20 <= prom_intervalo <= 40:
                monto = txns[0].monto
                suscripciones.append(Suscripcion(
                    nombre=f"Recurrente: {txns[0].descripcion[:25]}",
                    costo_mensual=round(monto, 2),
                    costo_anual=round(monto * 12, 2),
                    categoria_servicio="no_identificado",
                    frecuencia_cobro=len(txns),
                    nota="Detectado automáticamente por patrón recurrente",
                ))

    suscripciones.sort(key=lambda s: s.costo_mensual, reverse=True)
    return suscripciones


def detectar_redundancias(suscripciones: list[Suscripcion]) -> list[tuple[Suscripcion, Suscripcion, str]]:
    """Detecta servicios redundantes (ej: Spotify + YouTube Music)."""
    redundancias = []

    grupos_redundantes = {
        "streaming": ["Netflix", "Disney+", "HBO Max", "Max", "Amazon Prime",
                       "Apple TV+", "Paramount+", "Crunchyroll"],
        "musica": ["Spotify", "Apple Music", "YouTube Music"],
        "almacenamiento": ["iCloud+", "Google One", "Dropbox"],
        "ia": ["ChatGPT Plus", "OpenAI", "Midjourney"],
    }

    for grupo_nombre, nombres in grupos_redundantes.items():
        grupo = [s for s in suscripciones if s.nombre in nombres]
        if len(grupo) >= 2:
            for i, s1 in enumerate(grupo):
                for s2 in grupo[i + 1:]:
                    redundancias.append((
                        s1, s2,
                        f"Servicios similares de {grupo_nombre}: {s1.nombre} (${s1.costo_mensual:,.0f}/mes) "
                        f"y {s2.nombre} (${s2.costo_mensual:,.0f}/mes)",
                    ))

    return redundancias


def evaluar_suscripciones(suscripciones: list[Suscripcion], ingreso_mensual: float) -> list[Suscripcion]:
    """Evalúa y asigna recomendaciones a cada suscripción."""
    total_subs = sum(s.costo_mensual for s in suscripciones)
    porcentaje = (total_subs / ingreso_mensual * 100) if ingreso_mensual > 0 else 0

    for sub in suscripciones:
        peso = sub.costo_mensual / ingreso_mensual * 100 if ingreso_mensual > 0 else 0

        if sub.costo_mensual > 500:
            sub.recomendacion = RecomendacionSuscripcion.NEGOCIAR
            sub.nota = f"Costo alto ({peso:.1f}% del ingreso). Buscar plan más económico o compartir."
        elif sub.frecuencia_cobro <= 1 and sub.costo_mensual > 100:
            sub.recomendacion = RecomendacionSuscripcion.CANCELAR
            sub.nota = "Solo 1 cobro detectado. Posiblemente poco uso — evaluar cancelación."
        elif sub.categoria_servicio == "no_identificado":
            sub.recomendacion = RecomendacionSuscripcion.CANCELAR
            sub.nota = "Suscripción no identificada. Verificar si es necesaria."
        else:
            sub.recomendacion = RecomendacionSuscripcion.MANTENER
            sub.nota = "Parece un servicio activo con uso regular."

    return suscripciones


def resumen_suscripciones(suscripciones: list[Suscripcion]) -> dict:
    """Genera un resumen del gasto en suscripciones."""
    total_mensual = sum(s.costo_mensual for s in suscripciones)
    total_anual = sum(s.costo_anual for s in suscripciones)
    por_cancelar = [s for s in suscripciones if s.recomendacion == RecomendacionSuscripcion.CANCELAR]
    por_negociar = [s for s in suscripciones if s.recomendacion == RecomendacionSuscripcion.NEGOCIAR]
    ahorro_potencial_mensual = sum(s.costo_mensual for s in por_cancelar)

    return {
        "total_suscripciones": len(suscripciones),
        "costo_mensual_total": total_mensual,
        "costo_anual_total": total_anual,
        "por_cancelar": len(por_cancelar),
        "por_negociar": len(por_negociar),
        "ahorro_potencial_mensual": ahorro_potencial_mensual,
        "ahorro_potencial_anual": ahorro_potencial_mensual * 12,
    }
