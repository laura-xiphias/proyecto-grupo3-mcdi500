"""Pruebas del pipeline de la Fase 4: casos normales, límite y excepciones.

Ejecutar desde la carpeta F4:
    python -m unittest discover -s tests -v
"""
import sys
import unittest
from pathlib import Path

import pandas as pd

F4 = Path(__file__).resolve().parents[1]
for ruta in (F4 / "src", F4.parent / "F3" / "src", F4.parent / "F2" / "src"):
    sys.path.insert(0, str(ruta))

import limpieza        # noqa: E402
import mediciones      # noqa: E402
import transformacion  # noqa: E402
import obtencion       # noqa: E402
import pipeline        # noqa: E402

RAW = F4.parent / "F1" / "data" / "raw" / "Atropellos_2023.csv"
PROCESADO_F2 = F4.parent / "F1" / "data" / "processed" / "atropellos_2023_features.csv"


def _mini(**cambios):
    """DataFrame mínimo con las columnas que usan las funciones probadas."""
    base = {
        "Ruta": ["", "R-5"], "Calle_Uno": ["A", " "], "Calle_Dos": ["", ""],
        "Intersecci": ["", "B"], "Condición": ["SECO", ""], "Ubicación": ["x", "y"],
        "Fecha": ["2023-01-01", "2023-01-02"], "Hora_texto": ["00:00:00", "23:59:59"],
        "Lat": [-33.0, -34.0], "Lon": [-70.0, -71.0],
    }
    base.update(cambios)
    return pd.DataFrame(base)


@unittest.skipUnless(RAW.exists(), "Falta el CSV crudo en F1/data/raw/ (ver README)")
class CasosNormales(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = pipeline.preparar_dataset(RAW)

    def test_no_pierde_ni_duplica_filas(self):
        self.assertEqual(len(self.df), 5541)

    def test_variable_objetivo_conserva_los_fatales(self):
        self.assertEqual(int(self.df["Es_Fatal"].sum()), 407)

    def test_hora_corregida_cubre_24_valores_en_rango(self):
        self.assertTrue(self.df["Hora_limpia"].between(0, 23).all())
        self.assertEqual(self.df["Hora_limpia"].nunique(), 24)

    def test_columnas_de_texto_sin_blancos(self):
        for col in pipeline.COLUMNAS_TEXTO:
            self.assertEqual((self.df[col].astype(str).str.strip() == "").sum(), 0, col)

    def test_huella_del_dato_de_origen(self):
        self.assertEqual(pipeline.huella_sha256(RAW), pipeline.HUELLA_SHA256)

    def test_corregir_hora_solo_modifica_hora_limpia(self):
        # Regresión: la corrección no debe alterar ninguna otra columna de F2.
        base = transformacion.generar_nuevas_variables(
            limpieza.limpiar_datos(obtencion.cargar_crudo(RAW)))
        pd.testing.assert_frame_equal(base.drop(columns="Hora_limpia"),
                                      self.df.drop(columns="Hora_limpia"))
        self.assertEqual(base["Hora_limpia"].nunique(), 1)   # el error original de F2

    def test_salida_guardada_de_f2_esta_actualizada(self):
        if not PROCESADO_F2.exists():
            self.skipTest("No hay salida de F2 guardada (ejecutar F2 primero)")
        guardada = pd.read_csv(PROCESADO_F2)
        for col in pipeline.COLUMNAS_TEXTO:
            blancos = (guardada[col].astype(str).str.strip() == "").sum()
            self.assertEqual(blancos, 0,
                             f"{col}: la salida guardada de F2 es anterior a la corrección "
                             "de limpieza.py; volver a ejecutar F2")

    def test_matriz_sin_fuga_ni_nulos(self):
        A_tr, A_te, y_tr, y_te, nombres = pipeline.construir_matriz_analisis(self.df)
        self.assertEqual(A_tr.shape[1], A_te.shape[1])
        self.assertEqual(len(nombres), A_tr.shape[1])
        self.assertFalse(pd.isna(A_tr).any() or pd.isna(A_te).any())
        self.assertAlmostEqual(abs(A_tr[:, 0].mean()), 0, places=6)   # media 0 en train
        self.assertAlmostEqual(y_tr.mean(), y_te.mean(), places=2)    # estratificado


class CasosLimite(unittest.TestCase):
    def test_limpieza_es_idempotente(self):
        una = limpieza.limpiar_datos(_mini())
        dos = limpieza.limpiar_datos(una)
        pd.testing.assert_frame_equal(una, dos)

    def test_limpieza_sin_blancos_no_cambia_el_texto(self):
        sin_blancos = _mini(Ruta=["R-1", "R-2"], Calle_Uno=["A", "B"], Calle_Dos=["C", "D"],
                            Intersecci=["E", "F"], Condición=["SECO", "SECO"])
        limpio = limpieza.limpiar_datos(sin_blancos)
        self.assertEqual(limpio["Ruta"].tolist(), ["R-1", "R-2"])

    def test_blancos_y_espacios_pasan_a_desconocido(self):
        limpio = limpieza.limpiar_datos(_mini())
        self.assertEqual(limpio["Ruta"].iloc[0], "Desconocido")
        self.assertEqual(limpio["Calle_Uno"].iloc[1], "Desconocido")

    def test_hora_en_los_extremos_del_dia(self):
        horas = pipeline.corregir_hora(_mini())["Hora_limpia"].tolist()
        self.assertEqual(horas, [0, 23])

    def test_una_sola_fila(self):
        self.assertEqual(len(pipeline.corregir_hora(_mini().head(1))), 1)

    def test_conjunto_vacio_se_conserva_vacio(self):
        vacio = _mini().iloc[0:0]
        self.assertEqual(len(limpieza.limpiar_datos(vacio)), 0)
        self.assertEqual(len(pipeline.corregir_hora(vacio)), 0)

    def test_tasa_excluye_grupos_pequenos_y_acepta_cero_fatales(self):
        visual = pd.DataFrame({"g": ["a"] * 40 + ["b"] * 5, "Es_Fatal": [0] * 40 + [1] * 5})
        tabla = pipeline.tasa_fatalidad(visual, "g", minimo_n=30)
        self.assertEqual(tabla["g"].tolist(), ["a"])
        self.assertEqual(float(tabla["tasa"].iloc[0]), 0.0)


class Excepciones(unittest.TestCase):
    def test_archivo_inexistente(self):
        with self.assertRaises(FileNotFoundError):
            obtencion.cargar_crudo(Path("no_existe.csv"))

    def test_falta_una_de_las_seis_columnas_de_texto(self):
        with self.assertRaisesRegex(KeyError, "Ubicación"):
            pipeline.validar_columnas(_mini().drop(columns="Ubicación"), pipeline.COLUMNAS_TEXTO)

    def test_esquema_con_columna_faltante(self):
        with self.assertRaises(AssertionError):
            obtencion.verificar_esquema(_mini())

    def test_hora_sin_hora_texto(self):
        with self.assertRaisesRegex(KeyError, "Hora_texto"):
            pipeline.corregir_hora(_mini().drop(columns="Hora_texto"))

    def test_hora_con_formato_invalido(self):
        with self.assertRaises(ValueError):
            pipeline.corregir_hora(_mini(Hora_texto=["99:99:99", "00:00:00"]))


class Mediciones(unittest.TestCase):
    def test_polimorfismo_misma_llamada_para_las_tres_hijas(self):
        df = pd.DataFrame({"Hora_texto": ["10:00:00"] * 50, "COMUNA1": ["X", "Y"] * 25,
                           "Es_Fatal": [0, 1] * 25})
        for medicion in (mediciones.MedicionHora([10, 50], repeticiones=2),
                         mediciones.MedicionBusqueda([10, 50], repeticiones=2),
                         mediciones.MedicionRecorrido([20, 40], repeticiones=2)):
            tabla = medicion.ejecutar(df)
            self.assertEqual(len(tabla), 2)
            self.assertTrue((tabla["tiempo_a_s"] > 0).all())

    def test_detiene_si_a_y_b_no_coinciden(self):
        class Defectuosa(mediciones.Medicion):
            def preparar(self, df, n): return n
            def version_a(self, entrada): return 1
            def version_b(self, entrada): return 2
        with self.assertRaises(AssertionError):
            Defectuosa([1], repeticiones=1).ejecutar()

    def test_parametros_invalidos(self):
        with self.assertRaises(ValueError):
            mediciones.MedicionHora([], repeticiones=1)
        with self.assertRaises(ValueError):
            mediciones.MedicionHora([10], repeticiones=0)

    def test_resultados_devuelve_copia(self):
        m = mediciones.MedicionRecorrido([20, 40], repeticiones=1)
        m.ejecutar()
        m.resultados.loc[0, "n"] = -1
        self.assertEqual(m.resultados.loc[0, "n"], 20)


class IntervaloYJornada(unittest.TestCase):
    """Intervalo de Wilson y tasa por zona y jornada (figura 3)."""

    def test_wilson_valor_conocido(self):
        # 50 de 100 con z = 1,96: [0,404; 0,596] (valor de referencia de la fórmula de Wilson)
        inf, sup = pipeline.intervalo_wilson(50, 100)
        self.assertAlmostEqual(inf, 0.4038, places=3)
        self.assertAlmostEqual(sup, 0.5962, places=3)

    def test_wilson_no_sale_de_cero_y_uno(self):
        inf, sup = pipeline.intervalo_wilson(0, 5)
        self.assertEqual(inf, 0.0)
        self.assertLess(sup, 1.0)
        inf, sup = pipeline.intervalo_wilson(5, 5)
        self.assertGreater(inf, 0.0)
        self.assertAlmostEqual(sup, 1.0)

    def test_wilson_rechaza_n_invalido(self):
        with self.assertRaises(ValueError):
            pipeline.intervalo_wilson(0, 0)
        with self.assertRaises(ValueError):
            pipeline.intervalo_wilson(6, 5)

    def test_tasa_zona_jornada_separa_dia_y_noche(self):
        visual = pd.DataFrame({
            "Zona": ["Rural"] * 4 + ["Urbana"] * 2,
            "Hora_limpia": [19, 20, 6, 7, 12, 23],
            "Es_Fatal": [0, 1, 1, 0, 0, 1],
        })
        t = pipeline.tasa_zona_jornada(visual).set_index(["Zona", "Jornada"])
        self.assertEqual(t.loc[("Rural", pipeline.ORDEN_JORNADAS[1]), "n"], 2)
        self.assertEqual(t.loc[("Rural", pipeline.ORDEN_JORNADAS[0]), "n"], 2)
        self.assertAlmostEqual(t.loc[("Rural", pipeline.ORDEN_JORNADAS[1]), "tasa"], 100.0)
        self.assertAlmostEqual(t.loc[("Urbana", pipeline.ORDEN_JORNADAS[1]), "tasa"], 100.0)


if __name__ == "__main__":
    unittest.main()
