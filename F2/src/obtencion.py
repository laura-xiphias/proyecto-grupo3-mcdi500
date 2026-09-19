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