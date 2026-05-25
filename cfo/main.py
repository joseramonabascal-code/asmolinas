#!/usr/bin/env python3
"""
CFO Financiero Personal — Interfaz de línea de comandos.
Analiza estados de cuenta, detecta anomalías y genera reportes ejecutivos.
"""

import os
import sys
import glob

from cfo.importador import importar_csv, importar_directorio
from cfo.analizador import analizar
from cfo.reportes import generar_reporte, guardar_reporte


BANNER = """
======================================================================
   CFO FINANCIERO PERSONAL
   Director Financiero | Auditor | Controller | Estratega Patrimonial
======================================================================
"""

MENU = """
  Opciones:
  1. Analizar archivo CSV específico
  2. Analizar todos los CSV en datos/transacciones/
  3. Ver archivos disponibles
  4. Salir

  Selecciona una opción: """


def listar_archivos():
    """Lista los archivos CSV disponibles."""
    directorio = "datos/transacciones"
    if not os.path.exists(directorio):
        print(f"\n  No existe el directorio '{directorio}'.")
        print(f"  Créalo y coloca tus archivos CSV ahí.\n")
        return []

    archivos = glob.glob(os.path.join(directorio, "*.csv"))
    if not archivos:
        print(f"\n  No hay archivos CSV en '{directorio}'.")
        print(f"  Coloca tus estados de cuenta en formato CSV ahí.\n")
        return []

    print(f"\n  Archivos CSV encontrados en {directorio}/:")
    print(f"  {'-' * 50}")
    for i, archivo in enumerate(sorted(archivos), 1):
        nombre = os.path.basename(archivo)
        tamano = os.path.getsize(archivo) / 1024
        print(f"  {i}. {nombre} ({tamano:.1f} KB)")
    print()
    return sorted(archivos)


def analizar_archivo(ruta: str):
    """Analiza un archivo CSV y genera el reporte."""
    print(f"\n  Importando: {ruta}")
    try:
        transacciones = importar_csv(ruta)
    except Exception as e:
        print(f"  Error al importar: {e}")
        return

    if not transacciones:
        print("  No se encontraron transacciones en el archivo.")
        print("  Verifica que el CSV tenga columnas de fecha, descripción y monto.")
        return

    print(f"  Transacciones encontradas: {len(transacciones)}")

    fechas = [t.fecha for t in transacciones]
    periodo = f"{min(fechas).strftime('%d/%m/%Y')} — {max(fechas).strftime('%d/%m/%Y')}"
    print(f"  Periodo: {periodo}")
    print("\n  Analizando...")

    resumen = analizar(transacciones, periodo)
    reporte = generar_reporte(resumen)
    print(reporte)

    ruta_reporte = guardar_reporte(reporte)
    print(f"\n  Reporte guardado en: {ruta_reporte}")


def analizar_directorio():
    """Analiza todos los CSV del directorio de transacciones."""
    print("\n  Importando todos los CSV de datos/transacciones/...")
    transacciones = importar_directorio()

    if not transacciones:
        print("  No se encontraron transacciones.")
        print("  Coloca archivos CSV en datos/transacciones/")
        return

    print(f"  Total de transacciones: {len(transacciones)}")

    fechas = [t.fecha for t in transacciones]
    periodo = f"{min(fechas).strftime('%d/%m/%Y')} — {max(fechas).strftime('%d/%m/%Y')}"
    print(f"  Periodo combinado: {periodo}")
    print("\n  Analizando...")

    resumen = analizar(transacciones, periodo)
    reporte = generar_reporte(resumen)
    print(reporte)

    ruta_reporte = guardar_reporte(reporte)
    print(f"\n  Reporte guardado en: {ruta_reporte}")


def main():
    print(BANNER)

    # Si se pasa un archivo como argumento, analizarlo directamente
    if len(sys.argv) > 1:
        ruta = sys.argv[1]
        if os.path.isfile(ruta):
            analizar_archivo(ruta)
        elif os.path.isdir(ruta):
            transacciones = importar_directorio(ruta)
            if transacciones:
                fechas = [t.fecha for t in transacciones]
                periodo = f"{min(fechas).strftime('%d/%m/%Y')} — {max(fechas).strftime('%d/%m/%Y')}"
                resumen = analizar(transacciones, periodo)
                reporte = generar_reporte(resumen)
                print(reporte)
                guardar_reporte(reporte)
        else:
            print(f"  Archivo no encontrado: {ruta}")
        return

    # Menú interactivo
    while True:
        try:
            opcion = input(MENU).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  Hasta luego.\n")
            break

        if opcion == "1":
            archivos = listar_archivos()
            if archivos:
                try:
                    sel = input("  Número de archivo (o ruta completa): ").strip()
                    if sel.isdigit() and 1 <= int(sel) <= len(archivos):
                        analizar_archivo(archivos[int(sel) - 1])
                    elif os.path.isfile(sel):
                        analizar_archivo(sel)
                    else:
                        print("  Selección inválida.")
                except (EOFError, KeyboardInterrupt):
                    continue

        elif opcion == "2":
            analizar_directorio()

        elif opcion == "3":
            listar_archivos()

        elif opcion == "4":
            print("\n  Hasta luego.\n")
            break

        else:
            print("  Opción inválida. Elige 1-4.")


if __name__ == "__main__":
    main()
