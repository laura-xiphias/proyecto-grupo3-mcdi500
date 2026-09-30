"""Medición 2 · Hora del siniestro.

Problema detectado al revisar el código de la Fase 2: `Hora_limpia` se calculó
desde la columna `Hora`, que en el crudo vale 1899/12/30 00:00 en todas las filas
(fecha "cero" de Excel). Por eso quedó en 0 para todo el conjunto.
La hora real está en `Hora_texto`, con formato "HH:MM:SS".

Se comparan dos formas de obtenerla:
- Versión A: recorrer la columna fila por fila.
- Versión B: convertir la columna completa de una vez con pandas.
"""
import datetime as dt

import pandas as pd


def hora_bucle(df):
    """Versión A: extrae la hora (0-23) de Hora_texto recorriendo fila por fila."""
    horas = []
    for texto in df["Hora_texto"]:
        horas.append(dt.datetime.strptime(texto, "%H:%M:%S").hour)
    return horas


def hora_vectorizada(df):
    """Versión B: extrae la hora (0-23) convirtiendo toda la columna de una vez."""
    return pd.to_datetime(df["Hora_texto"], format="%H:%M:%S").dt.hour.tolist()
