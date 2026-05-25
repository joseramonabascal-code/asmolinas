import csv
import os
import re
from datetime import date, datetime
from typing import Optional

from cfo.modelos import Transaccion


FORMATOS_FECHA = [
    "%d/%m/%Y",
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%m/%d/%Y",
    "%d/%m/%y",
    "%Y/%m/%d",
    "%d %b %Y",
    "%d-%b-%Y",
]


def parsear_fecha(texto: str) -> Optional[date]:
    texto = texto.strip()
    for fmt in FORMATOS_FECHA:
        try:
            return datetime.strptime(texto, fmt).date()
        except ValueError:
            continue
    return None


def limpiar_monto(texto: str) -> float:
    texto = texto.strip().replace("$", "").replace(",", "").replace(" ", "")
    texto = texto.replace("MXN", "").replace("mxn", "").strip()
    if not texto or texto == "-":
        return 0.0
    try:
        return abs(float(texto))
    except ValueError:
        return 0.0


def detectar_columnas(encabezados: list[str]) -> dict:
    """Detecta qué columna es fecha, descripción, monto, etc."""
    enc_lower = [h.lower().strip() for h in encabezados]
    mapa = {"fecha": None, "descripcion": None, "monto": None, "cargo": None, "abono": None}

    palabras_fecha = ["fecha", "date", "dia", "día"]
    palabras_desc = ["descripcion", "descripción", "concepto", "detalle", "description", "referencia", "movimiento"]
    palabras_monto = ["monto", "amount", "importe", "total", "valor"]
    palabras_cargo = ["cargo", "retiro", "debito", "débito", "egreso", "salida", "debit"]
    palabras_abono = ["abono", "deposito", "depósito", "credito", "crédito", "ingreso", "entrada", "credit"]

    for i, h in enumerate(enc_lower):
        if any(p in h for p in palabras_fecha) and mapa["fecha"] is None:
            mapa["fecha"] = i
        elif any(p in h for p in palabras_desc) and mapa["descripcion"] is None:
            mapa["descripcion"] = i
        elif any(p in h for p in palabras_cargo) and mapa["cargo"] is None:
            mapa["cargo"] = i
        elif any(p in h for p in palabras_abono) and mapa["abono"] is None:
            mapa["abono"] = i
        elif any(p in h for p in palabras_monto) and mapa["monto"] is None:
            mapa["monto"] = i

    return mapa


def importar_csv(ruta: str, encoding: str = "utf-8") -> list[Transaccion]:
    """Importa transacciones desde un archivo CSV de estado de cuenta bancario."""
    transacciones = []

    for enc in [encoding, "latin-1", "cp1252", "utf-8-sig"]:
        try:
            with open(ruta, "r", encoding=enc) as f:
                contenido = f.read()
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    else:
        raise ValueError(f"No se pudo leer el archivo {ruta} con ninguna codificación")

    lineas = contenido.strip().split("\n")
    if len(lineas) < 2:
        return transacciones

    # Detectar delimitador
    delimitador = ","
    if lineas[0].count(";") > lineas[0].count(","):
        delimitador = ";"
    elif lineas[0].count("\t") > lineas[0].count(","):
        delimitador = "\t"

    reader = csv.reader(lineas, delimiter=delimitador)
    filas = list(reader)

    if len(filas) < 2:
        return transacciones

    # Buscar fila de encabezados (a veces los CSV bancarios tienen líneas extra arriba)
    idx_encabezado = 0
    for i, fila in enumerate(filas):
        texto_fila = " ".join(fila).lower()
        if any(p in texto_fila for p in ["fecha", "date", "descripcion", "concepto", "monto"]):
            idx_encabezado = i
            break

    encabezados = filas[idx_encabezado]
    mapa = detectar_columnas(encabezados)

    for fila in filas[idx_encabezado + 1:]:
        if len(fila) < 2:
            continue

        # Parsear fecha
        fecha = None
        if mapa["fecha"] is not None and mapa["fecha"] < len(fila):
            fecha = parsear_fecha(fila[mapa["fecha"]])
        if fecha is None:
            for campo in fila:
                fecha = parsear_fecha(campo)
                if fecha:
                    break
        if fecha is None:
            continue

        # Parsear descripción
        descripcion = ""
        if mapa["descripcion"] is not None and mapa["descripcion"] < len(fila):
            descripcion = fila[mapa["descripcion"]].strip()
        if not descripcion:
            for i, campo in enumerate(fila):
                if i != mapa.get("fecha") and not re.match(r'^[\d$,.\-\s]+$', campo.strip()):
                    descripcion = campo.strip()
                    break

        # Parsear monto y tipo
        monto = 0.0
        tipo = "cargo"

        if mapa["cargo"] is not None and mapa["abono"] is not None:
            cargo_val = limpiar_monto(fila[mapa["cargo"]] if mapa["cargo"] < len(fila) else "0")
            abono_val = limpiar_monto(fila[mapa["abono"]] if mapa["abono"] < len(fila) else "0")
            if cargo_val > 0:
                monto = cargo_val
                tipo = "cargo"
            elif abono_val > 0:
                monto = abono_val
                tipo = "abono"
        elif mapa["monto"] is not None and mapa["monto"] < len(fila):
            texto_monto = fila[mapa["monto"]].strip()
            es_negativo = texto_monto.startswith("-") or texto_monto.startswith("(")
            monto = limpiar_monto(texto_monto)
            tipo = "cargo" if es_negativo or monto < 0 else "abono"
            monto = abs(monto)
        else:
            for campo in fila:
                val = limpiar_monto(campo)
                if val > 0:
                    monto = val
                    break

        if monto == 0:
            continue

        referencia = ""
        for i, campo in enumerate(fila):
            if i not in [mapa.get(k) for k in mapa if mapa.get(k) is not None]:
                if campo.strip() and len(campo.strip()) > 3:
                    referencia = campo.strip()
                    break

        transacciones.append(Transaccion(
            fecha=fecha,
            descripcion=descripcion,
            monto=monto,
            tipo=tipo,
            referencia=referencia,
        ))

    return transacciones


def importar_directorio(directorio: str = "datos/transacciones") -> list[Transaccion]:
    """Importa todos los CSV de un directorio."""
    todas = []
    if not os.path.exists(directorio):
        return todas

    for archivo in sorted(os.listdir(directorio)):
        if archivo.lower().endswith(".csv"):
            ruta = os.path.join(directorio, archivo)
            try:
                txns = importar_csv(ruta)
                todas.extend(txns)
            except Exception as e:
                print(f"Error al importar {archivo}: {e}")

    todas.sort(key=lambda t: t.fecha)
    return todas
