"""Mediciones de eficiencia con el patrón Strategy (Fase 4).

Problema que resuelve: en la Fase 3 la función `comparar()` recibía dos
implementaciones intercambiables (A y B) por medio de `lambda`. Funcionaba, pero
cada medición repetía la preparación de datos y no había un lugar único donde
declarar qué se compara, con qué entrada y cuándo dos resultados son iguales.

Solución: la clase base `Medicion` fija el procedimiento (equivalencia, tiempo,
memoria, tamaños crecientes) y cada clase hija solo declara lo propio: cómo
preparar la entrada y cuáles son sus dos estrategias, `version_a` y `version_b`.

- Herencia: las tres hijas reutilizan `ejecutar()`, `_tiempo()` y `_memoria()`.
- Polimorfismo: el notebook llama `ejecutar(df)` igual para cualquier hija.
- Encapsulamiento: repeticiones, tamaños y resultados son atributos internos;
  solo se accede a ellos por `ejecutar()` y por la propiedad `resultados`.
"""
import shutil
import tempfile
import timeit
import tracemalloc
from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np
import pandas as pd

import busqueda   # F3/src
import hora       # F3/src
import recorrido  # F3/src


class Medicion(ABC):
    """Clase base: compara dos implementaciones del mismo cálculo."""

    nombre = "medicion"
    etiqueta_a = "versión A"
    etiqueta_b = "versión B"

    def __init__(self, tamanos, repeticiones=7):
        if not tamanos:
            raise ValueError("Se necesita al menos un tamaño para medir.")
        if repeticiones < 1:
            raise ValueError("Las repeticiones deben ser al menos 1.")
        self._tamanos = tuple(tamanos)
        self._repeticiones = repeticiones
        self._filas = []                 # estado interno: lo medido hasta ahora

    # ---- contrato que cada hija debe cumplir -------------------------------
    @abstractmethod
    def preparar(self, df, n):
        """Devuelve la entrada de tamaño `n` que recibirán las dos versiones."""

    @abstractmethod
    def version_a(self, entrada):
        """Implementación A (la de referencia)."""

    @abstractmethod
    def version_b(self, entrada):
        """Implementación B (la candidata)."""

    def liberar(self, entrada):
        """Libera recursos de la entrada. Por defecto no hay nada que liberar."""

    def equivalentes(self, resultado_a, resultado_b):
        """Decide si A y B entregan lo mismo. Las hijas pueden redefinirlo."""
        if hasattr(resultado_a, "equals"):
            return resultado_a.equals(resultado_b)
        return resultado_a == resultado_b

    # ---- lógica común (no se repite en las hijas) --------------------------
    def ejecutar(self, df=None):
        """Mide A y B en cada tamaño y devuelve la tabla de resultados."""
        self._filas = []
        for n in self._tamanos:
            entrada = self.preparar(df, n)
            try:
                ra, rb = self.version_a(entrada), self.version_b(entrada)
                assert self.equivalentes(ra, rb), (
                    f"[{self.nombre}] A y B NO entregan el mismo resultado (n={n})"
                )
                t_a = self._tiempo(lambda: self.version_a(entrada))
                t_b = self._tiempo(lambda: self.version_b(entrada))
                m_a = self._memoria(lambda: self.version_a(entrada))
                m_b = self._memoria(lambda: self.version_b(entrada))
            finally:
                self.liberar(entrada)
            self._filas.append({
                "medicion": self.nombre, "n": n,
                "tiempo_a_s": t_a, "tiempo_b_s": t_b, "razon_tiempo": t_a / t_b,
                "memoria_a_mb": m_a, "memoria_b_mb": m_b,
                "razon_memoria": m_a / m_b if m_b > 0 else np.nan,
            })
        return self.resultados

    @property
    def resultados(self):
        """Copia de la tabla medida (la original no se expone)."""
        return pd.DataFrame(self._filas)

    def exponentes(self):
        """Exponente empírico k de t ≈ c·n^k para A y B (pendiente log-log)."""
        tabla = self.resultados
        if len(tabla) < 3:
            return {"k_a": np.nan, "k_b": np.nan}
        x = np.log(tabla["n"].to_numpy(dtype=float))
        k_a = np.polyfit(x, np.log(tabla["tiempo_a_s"].to_numpy()), 1)[0]
        k_b = np.polyfit(x, np.log(tabla["tiempo_b_s"].to_numpy()), 1)[0]
        return {"k_a": float(k_a), "k_b": float(k_b)}

    def _tiempo(self, funcion):
        """Menor tiempo por llamada (s). El mínimo descarta interrupciones del SO."""
        sonda = timeit.timeit(funcion, number=1)
        repeticiones_por_medida = int(min(1000, max(1, 0.02 / max(sonda, 1e-9))))
        medidas = timeit.repeat(funcion, number=repeticiones_por_medida,
                                repeat=self._repeticiones)
        return min(medidas) / repeticiones_por_medida

    @staticmethod
    def _memoria(funcion):
        """Memoria pico (MB) que reserva la función mientras se ejecuta."""
        tracemalloc.start()
        try:
            funcion()
            _, pico = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        return pico / 1024 / 1024


class MedicionHora(Medicion):
    """Hora del siniestro: bucle con strptime (A) frente a pd.to_datetime (B)."""

    nombre = "Hora del siniestro"
    etiqueta_a = "bucle con strptime"
    etiqueta_b = "pd.to_datetime vectorizada"

    def preparar(self, df, n):
        return df.head(n)

    def version_a(self, entrada):
        return hora.hora_bucle(entrada)

    def version_b(self, entrada):
        return hora.hora_vectorizada(entrada)


class MedicionBusqueda(Medicion):
    """Fatales por comuna: filtrar cada vez (A) frente a agrupar una vez (B)."""

    nombre = "Fatales por comuna"
    etiqueta_a = "filtrar cada vez"
    etiqueta_b = "agrupar una vez"

    def preparar(self, df, n):
        muestra = df.head(n)
        return muestra, muestra["COMUNA1"].unique()

    def version_a(self, entrada):
        return busqueda.fatales_filtrando(*entrada)

    def version_b(self, entrada):
        return busqueda.fatales_agrupando(*entrada)


class MedicionRecorrido(Medicion):
    """Árbol de carpetas: rglob + filtro (A) frente a recursión con poda (B).

    El tamaño `n` es la cantidad de archivos dentro de `.venv`. Se construye un
    árbol sintético en una carpeta temporal para que la medición sea reproducible
    en cualquier equipo (no depende del `.venv` de quien ejecuta).
    """

    nombre = "Recorrido de carpetas"
    etiqueta_a = "rglob + filtro"
    etiqueta_b = "recursiva con poda"

    def preparar(self, df, n):
        raiz = Path(tempfile.mkdtemp(prefix="arbol_medicion_"))
        for carpeta in ("F1", "F2", "F3", "F4"):
            (raiz / carpeta / "src").mkdir(parents=True)
            (raiz / carpeta / "src" / "modulo.py").touch()
        for i in range(10):
            sub = raiz / ".venv" / f"paquete_{i}"
            sub.mkdir(parents=True)
            for j in range(n // 10):
                (sub / f"archivo_{j}.py").touch()
        return raiz

    def version_a(self, entrada):
        return recorrido.arbol_rglob(entrada)

    def version_b(self, entrada):
        return recorrido.arbol_recursivo(entrada)

    def liberar(self, entrada):
        shutil.rmtree(entrada, ignore_errors=True)
