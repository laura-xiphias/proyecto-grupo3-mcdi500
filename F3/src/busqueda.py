"""Medición 3 · Atropellos fatales por comuna.

Para responder la pregunta del proyecto hay que consultar cifras por comuna
muchas veces (284 comunas en el conjunto). Se comparan dos formas:
- Versión A: para cada comuna, filtrar la tabla completa y sumar Es_Fatal.
  La tabla se recorre una vez por comuna.
- Versión B: agrupar la tabla una sola vez, guardar el resultado en un
  diccionario y después solo consultarlo.
"""
import pandas as pd


def fatales_filtrando(df, comunas):
    """Versión A: filtra la tabla una vez por cada comuna."""
    resultado = {}
    for comuna in comunas:
        filas = df[df["COMUNA1"] == comuna]
        resultado[comuna] = int(filas["Es_Fatal"].sum())
    return resultado


def fatales_agrupando(df, comunas):
    """Versión B: agrupa una sola vez y consulta el diccionario resultante."""
    totales = df.groupby("COMUNA1")["Es_Fatal"].sum().to_dict()
    return {comuna: int(totales[comuna]) for comuna in comunas}
