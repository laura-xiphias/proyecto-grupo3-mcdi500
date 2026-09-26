#Obtención del conjunto crudo.

from pathlib import Path

import pandas as pd

COLUMNAS_ESPERADAS = [
    "X", "Y", "FID", "Año", "IdAccident", "Fecha", "Mes", "Dia_mes",
    "Dia_semana", "Hora", "Hora_texto", "Hora_aprox", "Región", "Comuna",
    "Tipo_Accid", "Tipo__CONA", "Zona", "Ubicación", "Causa__CON",
    "Causa_Acci", "Calle_Uno", "Calle_Dos", "Intersecci", "Número", "Ruta",
    "Ubicaci_1", "Calzada", "Tipo_Calza", "Estado_Cal", "Condición",
    "Estado_Atm", "Fallecidos", "Graves", "Menos_Grav", "Leves", "CUT_REG",
    "CUT_PROV", "CUT_COM", "REGION", "PROVINCIA", "COMUNA1", "Tipo_direc",
    "Direccion", "Lat", "Lon",
]

def cargar_crudo(ruta: Path, sep: str = ",", encoding: str = "utf-8-sig") -> pd.DataFrame:

    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo crudo en {ruta}. "
            )
    return pd.read_csv(ruta, sep=sep, encoding=encoding)


def verificar_esquema(df: pd.DataFrame, columnas_esperadas: list[str] | None = None) -> None:

    if columnas_esperadas is None:
        columnas_esperadas = COLUMNAS_ESPERADAS

    llegaron = set(df.columns)
    esperadas = set(columnas_esperadas)

    faltantes = esperadas - llegaron
    sobrantes = llegaron - esperadas

    assert not faltantes, f"Faltan {len(faltantes)} columnas declaradas: {sorted(faltantes)}"
    assert not sobrantes, f"Llegaron {len(sobrantes)} columnas no declaradas: {sorted(sobrantes)}"

def resumen_dimensional(df: pd.DataFrame) -> pd.DataFrame:
    #Devuelve una fila por variable con su tipo, cobertura y cardinalidad.
    return pd.DataFrame({
        "variable": df.columns,
        "dtype": [str(t) for t in df.dtypes],
        "no_nulos": df.notna().sum().values,
        "pct_nulos": (df.isna().mean() * 100).round(2).values,
        "unicos": [df[c].nunique() for c in df.columns],
        "memoria_kb": (df.memory_usage(deep=True, index=False) / 1024).round(1).values,
    })