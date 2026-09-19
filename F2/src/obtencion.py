"""Etapa 1 del pipeline de la Fase 2: obtención del conjunto crudo.

Carga el archivo tal como viene y verifica que trajo lo que esperábamos.
No limpia, no imputa y no transforma: eso es de las etapas siguientes.
"""

from pathlib import Path

import pandas as pd


def cargar_crudo(ruta: Path, sep: str = ",", encoding: str = "utf-8-sig") -> pd.DataFrame:
    """Carga el CSV crudo sin modificarlo.

    El encoding por defecto es utf-8-sig y no utf-8 porque el archivo de
    CONASET empieza con un BOM (los bytes EF BB BF). Leído como utf-8
    corriente, esos tres bytes se pegan al nombre de la primera columna, que
    pasa a llamarse '\\ufeffX' en vez de 'X'. El DataFrame se imprime igual,
    pero cualquier df["X"] posterior falla con KeyError. El sufijo -sig le
    dice a Python que descarte la marca.

    El separador va explícito en vez de sep=None. Inferirlo obliga a pandas a
    usar el motor de Python, más lento, y deja el formato del archivo sin
    documentar. Sabemos que son comas: dejémoslo dicho.
    """
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo crudo en {ruta}. "
            "La ruta debe ser relativa a la raíz del repositorio."
        )
    return pd.read_csv(ruta, sep=sep, encoding=encoding)


def verificar_esquema(df: pd.DataFrame, columnas_esperadas: list[str] | None = None) -> None:
    """Comprueba que el conjunto trajo exactamente las columnas declaradas.

    Existe por un desfase real de este proyecto: el README del grupo enumeraba
    42 columnas y el archivo trae 45 — X, Y y FID nunca se documentaron. Un
    desfase así no rompe nada al cargar; revienta tres etapas después con un
    KeyError que no dice de dónde viene. Acá falla en el punto de entrada, que
    es donde todavía se puede arreglar.

    La lista esperada se declara a mano en COLUMNAS_ESPERADAS y no se deriva
    del archivo: comparar el archivo consigo mismo siempre da verdadero.

    Raises:
        AssertionError: si falta alguna columna declarada o llega alguna no
            declarada. El mensaje nombra cuáles, no solo que hubo diferencia.
    """
    if columnas_esperadas is None:
        columnas_esperadas = COLUMNAS_ESPERADAS = [
    "X", "Y", "FID", "Año", "IdAccident", "Fecha", "Mes", "Dia_mes",
    "Dia_semana", "Hora", "Hora_texto", "Hora_aprox", "Región", "Comuna",
    "Tipo_Accid", "Tipo__CONA", "Zona", "Ubicación", "Causa__CON",
    "Causa_Acci", "Calle_Uno", "Calle_Dos", "Intersecci", "Número", "Ruta",
    "Ubicaci_1", "Calzada", "Tipo_Calza", "Estado_Cal", "Condición",
    "Estado_Atm", "Fallecidos", "Graves", "Menos_Grav", "Leves", "CUT_REG",
    "CUT_PROV", "CUT_COM", "REGION", "PROVINCIA", "COMUNA1", "Tipo_direc",
    "Direccion", "Lat", "Lon",
]

    llegaron = set(df.columns)
    esperadas = set(columnas_esperadas)

    faltantes = esperadas - llegaron
    sobrantes = llegaron - esperadas

    assert not faltantes, f"Faltan {len(faltantes)} columnas declaradas: {sorted(faltantes)}"
    assert not sobrantes, f"Llegaron {len(sobrantes)} columnas no declaradas: {sorted(sobrantes)}"

def resumen_dimensional(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve una fila por variable con su tipo, cobertura y cardinalidad.

    Es la fotografía del "antes" del pipeline. El criterio 10 pide un
    diagnóstico previo, y todo lo que las etapas siguientes afirmen sobre
    cuántos datos se descartaron o se imputaron se mide contra esta tabla.

    Advertencia sobre no_nulos y pct_nulos: pandas cuenta como presente toda
    celda que no sea NaN, y en este archivo la ausencia no se codificó como
    NaN sino como blancos y ceros. Por eso la tabla muestra cobertura completa
    en las 45 variables. No es un error de la función: es lo que pandas ve.
    Medir la ausencia real es trabajo de la etapa de exploración.
    """
    return pd.DataFrame({
        "variable": df.columns,
        "dtype": [str(t) for t in df.dtypes],
        "no_nulos": df.notna().sum().values,
        "pct_nulos": (df.isna().mean() * 100).round(2).values,
        "unicos": [df[c].nunique() for c in df.columns],
        "memoria_kb": (df.memory_usage(deep=True, index=False) / 1024).round(1).values,
    })