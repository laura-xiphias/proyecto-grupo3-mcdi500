# Changelog

Registro de cambios por fase. Cada entrada indica fecha, descripción, commit y justificación.

## [F4] 2026-10-04

### Agregado
- Clase base `Medicion` y tres hijas (`MedicionHora`, `MedicionBusqueda`, `MedicionRecorrido`) en `F4/src/mediciones.py` (commit 72d9e8b).
  Responde a la observación de la Sumativa 2 (implementar clases): formaliza `comparar()` como patrón Strategy.
- Mediciones con `timeit` y `tracemalloc` sobre tamaños crecientes, con exponente empírico (commit 72d9e8b).
  Una medición en un solo tamaño no permitía inferir la complejidad.
- Pruebas de caso normal, límite y excepción en `F4/tests/test_pipeline.py`, 28 pruebas reejecutables (commit 72d9e8b).
  Responde a la observación de la Sumativa 1 sobre casos límite y excepciones.
- Tres visualizaciones analíticas en `F4/src/visualizacion.py` y `F4/figuras/` (commit 72d9e8b). Comunican los hallazgos del objetivo 5.
- Notebook integrador `F4/F4_Integrador.ipynb` (commit 72d9e8b).
- Evidencia de ejecución: HTML de los cuatro notebooks ejecutados en `docs/evidencia/` (commit edab2a6).
  Responde a las observaciones de las sumativas 1 y 2.
- Archivo `.mailmap` en la rama principal (commit 2381051). Unifica las identidades duplicadas de Git (sumativas 1 y 2).

### Cambiado
- Figura 3 (zona y jornada) rediseñada como barras agrupadas con intervalo de confianza de Wilson (95 %), con día 7:00–19:59 y noche 20:00–6:59; se agregan `intervalo_wilson` y `tasa_zona_jornada` con 4 pruebas nuevas (commit ad521e7). Diseño propuesto por Karim Zaid, reimplementado en el pipeline para que la figura se genere desde el notebook.
- Los CSV dejan de versionarse: `*.csv` en `.gitignore`; el README documenta cómo obtener el dato y su SHA-256 (commit aee6a3d). Sumativa 1.
- Notebook de F1 movido a la raíz de la carpeta F1 y módulos de F2 renombrados a minúscula, para unificar estructura y nomenclatura entre fases (commit 511fa0e). Sumativa 1.
- `F2/src/exploracion.py` y `F2/src/transformacion.py` renombrados con `git mv`: Git en Windows no registraba el cambio de mayúsculas y el import fallaba en Linux y macOS (commit 511fa0e).

### Corregido
- `Hora_limpia` valía 0 en todo el conjunto (se calculaba desde `Hora`, constante). `pipeline.corregir_hora` la calcula desde `Hora_texto`, con prueba de regresión (commit 72d9e8b). Hallazgo de la Fase 3.
- La salida procesada de F2 guardada en el repositorio era anterior a la corrección de `limpieza.py` y conservaba las 7.981 celdas en blanco; se retiró del repositorio (commit aee6a3d), se volvió a ejecutar F2 (evidencia en commit edab2a6) y una prueba lo verifica (commit 72d9e8b).
