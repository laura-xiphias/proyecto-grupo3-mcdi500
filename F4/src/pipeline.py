"""Pipeline integrado de las Fases 1 a 3 (Fase 4).

Cada función hace una sola tarea y recibe/devuelve DataFrames sin modificar la
entrada. Reutiliza los módulos de F2 (obtención, limpieza, features) y la
corrección de la hora de F3, sin duplicar su lógica.
"""
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import hora            # F3/src
import limpieza        # F2/src
import obtencion       # F2/src
import transformacion  # F2/src

HUELLA_SHA256 = "96c94c37a1472d595a6da1b53310a53eeb12c8b4f9419dab586fed832cdca553"
COLUMNAS_TEXTO = ["Ruta", "Calle_Uno", "Calle_Dos", "Intersecci", "Condición", "Ubicación"]
ORDEN_TRAMOS = ["00-05 h", "06-11 h", "12-17 h", "18-21 h", "22-23 h"]
HORA_INICIO_NOCHE = 20   # la noche va de 20:00 a 06:59; el día, de 07:00 a 19:59
HORA_FIN_NOCHE = 6
ORDEN_JORNADAS = ["Día (7:00–19:59)", "Noche (20:00–6:59)"]


def huella_sha256(ruta):
    """SHA-256 del archivo, para comprobar que es el mismo dato de origen."""
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def validar_columnas(df, requeridas):
    """Falla con un mensaje claro si falta alguna columna requerida."""
    faltantes = [c for c in requeridas if c not in df.columns]
    if faltantes:
        raise KeyError(f"Faltan columnas requeridas: {faltantes}")


def corregir_hora(df):
    """Reemplaza Hora_limpia (que en F2 quedó en 0) por la hora de Hora_texto."""
    validar_columnas(df, ["Hora_texto"])
    df = df.copy()
    df["Hora_limpia"] = hora.hora_vectorizada(df)
    return df


def preparar_dataset(ruta_crudo):
    """Fases 1-3 encadenadas: crudo -> limpio -> variables nuevas -> hora corregida."""
    crudo = obtencion.cargar_crudo(Path(ruta_crudo))
    obtencion.verificar_esquema(crudo)
    validar_columnas(crudo, COLUMNAS_TEXTO)
    limpio = limpieza.limpiar_datos(crudo)
    return corregir_hora(transformacion.generar_nuevas_variables(limpio))


def construir_df_visual(df):
    """Copia interpretable para graficar: categorías y unidades originales.

    No se codifica ni se escala: un gráfico sobre columnas de ceros y unos
    o sobre valores estandarizados no se puede leer.
    """
    validar_columnas(df, ["Zona", "Causa__CON", "Hora_limpia", "Es_Fatal"])
    visual = df[["Zona", "Causa__CON", "Dia_semana", "Estado_Atm",
                 "Hora_limpia", "Es_Fatal"]].copy()
    visual["Zona"] = visual["Zona"].str.strip().str.capitalize()
    visual["Causa"] = (visual["Causa__CON"].str.strip().str.capitalize()
                       .str.replace("peaton", "peatón").str.replace("señalizacion", "señalización"))
    visual["Tramo_horario"] = pd.cut(
        visual["Hora_limpia"], bins=[-1, 5, 11, 17, 21, 23],
        labels=ORDEN_TRAMOS).astype("category")
    return visual.drop(columns="Causa__CON")


def tasa_fatalidad(visual, por, minimo_n=30):
    """Tasa de fatalidad (%) por categoría, excluyendo grupos con n < minimo_n."""
    validar_columnas(visual, [por, "Es_Fatal"])
    tabla = (visual.groupby(por, observed=True)["Es_Fatal"]
             .agg(n="size", fatales="sum", tasa="mean").reset_index())
    tabla["tasa"] = tabla["tasa"] * 100
    return tabla[tabla["n"] >= minimo_n].sort_values("tasa", ascending=False)


def intervalo_wilson(fatales, n, z=1.96):
    """Intervalo de confianza de Wilson (95 % por defecto) para una proporción.

    Devuelve (inferior, superior) como proporciones entre 0 y 1. Se prefiere al
    intervalo normal porque no sale de [0, 1] con n pequeño ni con proporciones
    cercanas a 0.
    """
    if n <= 0:
        raise ValueError("n debe ser positivo para calcular el intervalo")
    if not 0 <= fatales <= n:
        raise ValueError("fatales debe estar entre 0 y n")
    p = fatales / n
    denominador = 1 + z ** 2 / n
    centro = (p + z ** 2 / (2 * n)) / denominador
    margen = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / denominador
    return max(0.0, centro - margen), min(1.0, centro + margen)


def tasa_zona_jornada(visual):
    """Tasa de fatalidad (%) por zona y jornada (día/noche), con IC 95 % de Wilson."""
    validar_columnas(visual, ["Zona", "Hora_limpia", "Es_Fatal"])
    hora_ = visual["Hora_limpia"]
    es_noche = (hora_ >= HORA_INICIO_NOCHE) | (hora_ <= HORA_FIN_NOCHE)
    jornada = np.where(es_noche, ORDEN_JORNADAS[1], ORDEN_JORNADAS[0])
    tabla = (visual.assign(Jornada=jornada).groupby(["Zona", "Jornada"])["Es_Fatal"]
             .agg(n="size", fatales="sum").reset_index())
    limites = [intervalo_wilson(int(f), int(n)) for f, n in zip(tabla["fatales"], tabla["n"])]
    tabla["tasa"] = tabla["fatales"] / tabla["n"] * 100
    tabla["inf"] = [100 * i for i, _ in limites]
    tabla["sup"] = [100 * s for _, s in limites]
    return tabla


def construir_matriz_analisis(df, test_size=0.2, random_state=42):
    """Matriz para análisis: partición estratificada y transformación sin fuga.

    Los parámetros (media y desviación del escalador, categorías del codificador)
    se aprenden SOLO del conjunto de entrenamiento y se aplican al de prueba.
    """
    numericas = ["Hora_limpia", "Lat", "Lon"]
    nominales = ["Zona", "Causa__CON", "Dia_semana", "Estado_Atm"]
    validar_columnas(df, numericas + nominales + ["Es_Fatal"])
    X, y = df[numericas + nominales], df["Es_Fatal"]
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y)
    transformador = ColumnTransformer([
        ("num", StandardScaler(), numericas),
        ("nom", OneHotEncoder(handle_unknown="ignore", sparse_output=False), nominales),
    ])
    A_tr = transformador.fit_transform(X_tr)
    A_te = transformador.transform(X_te)
    nombres = list(transformador.get_feature_names_out())
    return A_tr, A_te, y_tr, y_te, nombres
