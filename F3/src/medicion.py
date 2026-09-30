"""Herramientas comunes para medir y comparar implementaciones (Fase 3).

Todas las mediciones del notebook usan estas mismas funciones, para que se
hagan siempre de la misma forma y sean comparables entre sí.
"""
import timeit
import tracemalloc


def medir_tiempo(funcion, repeticiones=3):
    """Ejecuta `funcion` varias veces y devuelve el MENOR tiempo, en segundos.

    Se usa el mínimo y no el promedio porque los tiempos altos suelen deberse a
    que el computador estaba haciendo otra cosa, no al código.
    """
    return min(timeit.repeat(funcion, number=1, repeat=repeticiones))


def medir_memoria(funcion):
    """Devuelve la memoria máxima (en MB) que usa `funcion` mientras se ejecuta."""
    tracemalloc.start()
    try:
        funcion()
        _, pico = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return pico / 1024 / 1024


def comparar(nombre_a, funcion_a, nombre_b, funcion_b, repeticiones=3):
    """Compara dos versiones del mismo cálculo.

    1. Verifica que ambas entregan el MISMO resultado (si no, detiene todo).
    2. Mide tiempo y memoria de cada una.
    3. Devuelve un diccionario con las cifras, listo para el resumen final.

    Las funciones se pasan SIN paréntesis y sin argumentos, por ejemplo:
        comparar("bucle", lambda: version_a(df), "vectorizada", lambda: version_b(df))
    """
    resultado_a = funcion_a()
    resultado_b = funcion_b()
    assert _iguales(resultado_a, resultado_b), (
        f"'{nombre_a}' y '{nombre_b}' NO entregan el mismo resultado"
    )

    fila = {
        "version_a": nombre_a,
        "tiempo_a_s": medir_tiempo(funcion_a, repeticiones),
        "memoria_a_mb": medir_memoria(funcion_a),
        "version_b": nombre_b,
        "tiempo_b_s": medir_tiempo(funcion_b, repeticiones),
        "memoria_b_mb": medir_memoria(funcion_b),
    }
    fila["veces_mas_rapida"] = fila["tiempo_a_s"] / fila["tiempo_b_s"]

    print("Mismo resultado: OK")
    print(f"  A · {nombre_a:<28} {fila['tiempo_a_s']:.4f} s   {fila['memoria_a_mb']:.3f} MB")
    print(f"  B · {nombre_b:<28} {fila['tiempo_b_s']:.4f} s   {fila['memoria_b_mb']:.3f} MB")
    print(f"  B es {fila['veces_mas_rapida']:.1f} veces más rápida que A")
    return fila


def _iguales(a, b):
    """Compara resultados que pueden ser listas, diccionarios, Series o DataFrames."""
    if hasattr(a, "equals"):          # Series y DataFrame de pandas
        return a.equals(b)
    return a == b
