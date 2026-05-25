"""Tests para el sistema CFO Financiero Personal."""

import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cfo.modelos import Transaccion, TipoGasto, NivelRiesgo
from cfo.importador import importar_csv, parsear_fecha, limpiar_monto, detectar_columnas
from cfo.categorias import categorizar_transaccion, categorizar_todas, calcular_totales_categoria, top_comercios
from cfo.detector import detectar_duplicados, detectar_montos_anormales, ejecutar_deteccion_completa
from cfo.suscripciones import detectar_suscripciones, detectar_redundancias
from cfo.analizador import analizar
from cfo.score import calcular_score
from cfo.benchmark import evaluar_benchmarks, evaluar_tasa_ahorro
from cfo.reportes import generar_reporte


class TestParseoFechas(unittest.TestCase):
    def test_formato_dd_mm_yyyy(self):
        self.assertEqual(parsear_fecha("15/05/2026"), date(2026, 5, 15))

    def test_formato_yyyy_mm_dd(self):
        self.assertEqual(parsear_fecha("2026-05-15"), date(2026, 5, 15))

    def test_formato_invalido(self):
        self.assertIsNone(parsear_fecha("no-es-fecha"))

    def test_espacios(self):
        self.assertEqual(parsear_fecha("  15/05/2026  "), date(2026, 5, 15))


class TestLimpiarMonto(unittest.TestCase):
    def test_monto_simple(self):
        self.assertEqual(limpiar_monto("1500.00"), 1500.00)

    def test_monto_con_signo(self):
        self.assertEqual(limpiar_monto("$1,500.00"), 1500.00)

    def test_monto_negativo(self):
        self.assertEqual(limpiar_monto("-500.00"), 500.00)

    def test_monto_vacio(self):
        self.assertEqual(limpiar_monto(""), 0.0)

    def test_monto_con_moneda(self):
        self.assertEqual(limpiar_monto("$2,350.50 MXN"), 2350.50)


class TestDetectarColumnas(unittest.TestCase):
    def test_encabezados_espanol(self):
        enc = ["Fecha", "Descripcion", "Cargo", "Abono", "Referencia"]
        mapa = detectar_columnas(enc)
        self.assertEqual(mapa["fecha"], 0)
        self.assertEqual(mapa["descripcion"], 1)
        self.assertEqual(mapa["cargo"], 2)
        self.assertEqual(mapa["abono"], 3)

    def test_encabezados_ingles(self):
        enc = ["Date", "Description", "Amount"]
        mapa = detectar_columnas(enc)
        self.assertEqual(mapa["fecha"], 0)
        self.assertEqual(mapa["descripcion"], 1)
        self.assertEqual(mapa["monto"], 2)


class TestCategorizacion(unittest.TestCase):
    def test_categorizar_supermercado(self):
        txn = Transaccion(date(2026, 5, 1), "WALMART SUPER", 500, "cargo")
        resultado = categorizar_transaccion(txn)
        self.assertEqual(resultado.categoria, "alimentacion")

    def test_categorizar_netflix(self):
        txn = Transaccion(date(2026, 5, 1), "NETFLIX MENSUAL", 219, "cargo")
        resultado = categorizar_transaccion(txn)
        self.assertTrue(resultado.es_suscripcion)

    def test_categorizar_ingreso(self):
        txn = Transaccion(date(2026, 5, 1), "DEPOSITO NOMINA", 45000, "abono")
        resultado = categorizar_transaccion(txn)
        self.assertEqual(resultado.tipo_gasto, TipoGasto.INGRESO)

    def test_gasto_hormiga(self):
        txn = Transaccion(date(2026, 5, 1), "OXXO COMPRA", 45, "cargo")
        resultado = categorizar_transaccion(txn)
        self.assertEqual(resultado.tipo_gasto, TipoGasto.HORMIGA)


class TestDetectorDuplicados(unittest.TestCase):
    def test_detectar_cargo_duplicado(self):
        txns = [
            Transaccion(date(2026, 5, 9), "SEGURO GNP AUTO", 2100, "cargo"),
            Transaccion(date(2026, 5, 9), "SEGURO GNP AUTO", 2100, "cargo"),
        ]
        duplicados = detectar_duplicados(txns)
        self.assertTrue(len(duplicados) > 0)

    def test_no_duplicado_diferentes_montos(self):
        txns = [
            Transaccion(date(2026, 5, 9), "SEGURO GNP", 2100, "cargo"),
            Transaccion(date(2026, 5, 9), "SEGURO GNP", 1500, "cargo"),
        ]
        duplicados = detectar_duplicados(txns)
        self.assertEqual(len(duplicados), 0)


class TestSuscripciones(unittest.TestCase):
    def test_detectar_suscripciones_conocidas(self):
        txns = [
            Transaccion(date(2026, 5, 3), "NETFLIX MENSUAL", 219, "cargo"),
            Transaccion(date(2026, 5, 4), "SPOTIFY PREMIUM", 115, "cargo"),
        ]
        subs = detectar_suscripciones(txns)
        nombres = [s.nombre for s in subs]
        self.assertIn("Netflix", nombres)
        self.assertIn("Spotify", nombres)

    def test_detectar_redundancia_musica(self):
        from cfo.modelos import Suscripcion
        subs = [
            Suscripcion("Spotify", 115, 1380, "musica", 1),
            Suscripcion("Apple Music", 99, 1188, "musica", 1),
        ]
        redundancias = detectar_redundancias(subs)
        self.assertTrue(len(redundancias) > 0)


class TestScore(unittest.TestCase):
    def test_score_sano(self):
        from cfo.modelos import ResumenFinanciero
        resumen = ResumenFinanciero(
            periodo="test",
            ingreso_neto=50000,
            gasto_total=35000,
            gasto_fijo=15000,
            gasto_variable=10000,
            gasto_discrecional=5000,
            gasto_financiero=3000,
            gasto_hormiga=500,
            gasto_suscripciones=1500,
            flujo_libre=15000,
            tasa_ahorro=30,
            tasa_gasto_fijo=30,
            score=0,
            clasificacion_score="",
            gastos_por_categoria={"vivienda": 12000, "alimentacion": 5000, "transporte": 3000},
        )
        score, clasificacion, _ = calcular_score(resumen)
        self.assertGreaterEqual(score, 60)

    def test_score_riesgo(self):
        from cfo.modelos import ResumenFinanciero
        resumen = ResumenFinanciero(
            periodo="test",
            ingreso_neto=30000,
            gasto_total=29000,
            gasto_fijo=22000,
            gasto_variable=4000,
            gasto_discrecional=2000,
            gasto_financiero=10000,
            gasto_hormiga=3000,
            gasto_suscripciones=2000,
            flujo_libre=1000,
            tasa_ahorro=3.3,
            tasa_gasto_fijo=73,
            score=0,
            clasificacion_score="",
            gastos_por_categoria={"vivienda": 15000, "deuda": 10000},
        )
        score, clasificacion, _ = calcular_score(resumen)
        self.assertLess(score, 60)


class TestImportarCSV(unittest.TestCase):
    def test_importar_ejemplo(self):
        ruta = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datos", "transacciones", "ejemplo_estado_cuenta.csv")
        if os.path.exists(ruta):
            txns = importar_csv(ruta)
            self.assertGreater(len(txns), 0)
            # Verificar que hay tanto cargos como abonos
            cargos = [t for t in txns if t.tipo == "cargo"]
            abonos = [t for t in txns if t.tipo == "abono"]
            self.assertGreater(len(cargos), 0)
            self.assertGreater(len(abonos), 0)


class TestAnalisisCompleto(unittest.TestCase):
    def test_analisis_ejemplo(self):
        ruta = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datos", "transacciones", "ejemplo_estado_cuenta.csv")
        if os.path.exists(ruta):
            txns = importar_csv(ruta)
            resumen = analizar(txns, "Mayo 2026")
            self.assertGreater(resumen.ingreso_neto, 0)
            self.assertGreater(resumen.gasto_total, 0)
            self.assertGreater(resumen.score, 0)

    def test_reporte_generado(self):
        ruta = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datos", "transacciones", "ejemplo_estado_cuenta.csv")
        if os.path.exists(ruta):
            txns = importar_csv(ruta)
            resumen = analizar(txns, "Mayo 2026")
            reporte = generar_reporte(resumen)
            self.assertIn("RESUMEN EJECUTIVO", reporte)
            self.assertIn("SCORE FINANCIERO", reporte)
            self.assertIn("OPORTUNIDADES DE AHORRO", reporte)


class TestBenchmarks(unittest.TestCase):
    def test_benchmark_excedido(self):
        gastos = {"vivienda": 20000}
        resultados = evaluar_benchmarks(gastos, 50000)
        vivienda = [r for r in resultados if r["categoria"] == "Vivienda"]
        self.assertTrue(len(vivienda) > 0)
        self.assertEqual(vivienda[0]["estado"], "EXCEDIDO")

    def test_benchmark_ok(self):
        gastos = {"vivienda": 10000}
        resultados = evaluar_benchmarks(gastos, 50000)
        vivienda = [r for r in resultados if r["categoria"] == "Vivienda"]
        self.assertTrue(len(vivienda) > 0)
        self.assertEqual(vivienda[0]["estado"], "OK")

    def test_tasa_ahorro(self):
        resultado = evaluar_tasa_ahorro(10000, 50000)
        self.assertEqual(resultado["estado"], "Muy bien")


if __name__ == "__main__":
    unittest.main()
