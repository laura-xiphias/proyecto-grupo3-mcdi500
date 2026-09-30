"""Medición 1 · Recorrido de la estructura del proyecto.

Compara dos formas de listar las carpetas del repositorio:
- Versión A (la de F1): rglob recorre TODO, incluido .venv, y filtra al final.
- Versión B: función recursiva que PODA las carpetas excluidas y nunca entra.

Es el caso del proyecto donde la recursión se justifica: el número de niveles
de carpetas no es fijo (cambia cada vez que alguien crea una carpeta).
"""
from pathlib import Path

EXCLUIR = {".venv", ".git", ".ipynb_checkpoints", "source", "__pycache__"}


def encontrar_raiz(desde=None):
    """Sube desde la carpeta actual hasta encontrar la que contiene .git."""
    inicio = Path(desde) if desde else Path.cwd()
    for carpeta in [inicio, *inicio.parents]:
        if (carpeta / ".git").exists():
            return carpeta
    raise FileNotFoundError("No se encontró la raíz del repositorio (carpeta .git).")


def arbol_rglob(raiz, excluir=EXCLUIR):
    """Versión A: recorre todo el árbol con rglob y descarta lo excluido al final."""
    lineas = []
    for item in sorted(raiz.rglob("*")):
        if any(parte in item.parts for parte in excluir):
            continue
        nivel = len(item.relative_to(raiz).parts) - 1
        lineas.append("  " * nivel + item.name + ("/" if item.is_dir() else ""))
    return lineas


def arbol_recursivo(carpeta, nivel=0, excluir=EXCLUIR):
    """Versión B: recursiva con poda.

    - Poda: si el elemento está en `excluir`, se salta sin entrar.
    - Caso recursivo: si es una carpeta, se vuelve a llamar un nivel más abajo.
    - Caso base: una carpeta sin subcarpetas no genera nuevas llamadas.
    """
    lineas = []
    for item in sorted(carpeta.iterdir()):
        if item.name in excluir:
            continue                                            # poda
        lineas.append("  " * nivel + item.name + ("/" if item.is_dir() else ""))
        if item.is_dir():
            lineas += arbol_recursivo(item, nivel + 1, excluir)  # caso recursivo
    return lineas                                               # caso base


def profundidad(lineas):
    """Cantidad de niveles del árbol listado."""
    return max((len(l) - len(l.lstrip(" "))) // 2 for l in lineas) + 1
