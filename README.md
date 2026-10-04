# Proyecto Grupo 3 — MCDI500
Se analizan 5.541 casos de atropellos georreferenciados para responder: 
¿Qué factores —de la vía, del entorno y del contexto del siniestro— determinan la probabilidad de que un atropello resulte con víctimas fatales?


## Integrantes- 
Laura Arenas (@laura-xiphias)
Daniel Herrera (@dnietoh-ctrl)
Karim Zaid (@karimzaid)
Jeremmy Díaz (@kirijota98)

## Datos
Fuente: Comisión Nacional de Seguridad de Tránsito (CONASET), con datos originales
de Carabineros de Chile — "Siniestros de tipo atropello 2023"
(https://mapas-conaset.opendata.arcgis.com/datasets/6d8fb5c2774745fd86b2e0be62c54946_0/explore).

Licencia: uso condicionado a citar a CONASET como entidad elaboradora del mapa y a
Carabineros de Chile como fuente de los datos. CONASET advierte que la geocodificación
de los siniestros puede estar incompleta o contener errores de localización (ausencia
o error en el dato de dirección, o problemas del proceso de geocodificación masiva).

Registros: 5.541 filas correspondientes a siniestros de tránsito tipo atropello
ocurridos en Chile durante 2023.

Variables: X, Y, FID, Año, IdAccident,	Fecha,	Mes,	Dia_mes,	Dia_semana,	Hora,	Hora_texto,	Hora_aprox,	Región,	Comuna,	Tipo_Accid,	Tipo__CONA,	Zona,	Ubicación,	Causa__CON,	Causa_Acci,	Calle_Uno,	Calle_Dos,	Intersecci,	Número,	Ruta,	Ubicaci_1,	Calzada,	Tipo_Calza,	Estado_Cal,	Condición,	Estado_Atm,	Fallecidos,	Graves,	Menos_Grav,	Leves,	CUT_REG,	CUT_PROV,	CUT_COM,	REGION,	PROVINCIA,	COMUNA1,	Tipo_direc,	Direccion,	Lat,	Lon.

El conjunto (2,7 MB) **no se versiona**: `*.csv` está en `.gitignore`. Para reproducir el proyecto:

1. Descargar «Siniestros de tipo atropello 2023» desde el enlace de CONASET indicado arriba, en formato CSV.
2. Guardarlo como `F1/data/raw/Atropellos_2023.csv`.
3. Verificar que es el mismo archivo con su huella SHA-256:

    sha256sum F1/data/raw/Atropellos_2023.csv
    # 96c94c37a1472d595a6da1b53310a53eeb12c8b4f9419dab586fed832cdca553

El notebook `F4/F4_Integrador.ipynb` comprueba esta huella al iniciar. El archivo procesado (`F1/data/processed/`) tampoco se versiona: se genera al ejecutar el notebook de F2.

## Estructura del repositorio
F1/ Definición del problema y entorno reproducible
F2/ Obtención, limpieza y transformación de datos
F3/ Núcleo algorítmico: programación estructurada, recursiva y POO
F4/ Análisis, visualización y comunicación de resultados

## Requisitos y ejecución
Python 3.13.7

    python -m venv .venv
    .venv\Scripts\Activate.ps1          # Windows, PowerShell
    # source .venv/Scripts/activate      # Windows, Git Bash
    # source .venv/bin/activate          # macOS y Linux
    python -m pip install -r requirements.txt

Ejecutar los notebooks en orden (F1, F2, F3) desde la carpeta de cada fase.

## Convención de commits
Prefijos usados: docs, data, feat, fix.

## Decisiones técnicas

**Reutilización de F1/data/processed/ para el output de F2.** 
En vez de crear una carpeta data/processed propia dentro de F2, se decidió aprovechar la ya existente en F1 (aún vacía), evitando duplicar la estructura de carpetas de datos procesados entre fases consecutivas del mismo pipeline.

**Train/test split proyectado para Fase 3.** 
F2 se detiene deliberadamente en la generación de features (df_features), sin particionar aún el conjunto en entrenamiento y prueba. La función `preprocesar_modelo()` que realiza ese split ya está escrita y probada en `transformacion.py`, pero su ejecución queda reservada para cuando corresponda modelar, conforme al alcance de cada fase.

**Normalización de nombres de módulos a minúsculas.** 
Los archivos `Exploracion.py` y `Transformacion.py` se renombraron a minúsculas
(`exploracion.py`, `transformacion.py`) para evitar errores de importación en sistemas operativos que sí distinguen mayúsculas de minúsculas (macOS, Linux), dado que Windows los trataba como equivalentes sin advertir el problema.

**Trabajo en ramas por integrante.** 
Cada miembro del equipo desarrolló su aporte en una rama propia (por ejemplo, f2-limpieza), integrándola a main mediante pull request una vez revisada, conforme al criterio de ramas declarado en la Fase 1 (main protegida, una rama por integrante).

## Fase 3 — Scripts y mediciones de eficiencia

En esta fase no cambiamos los datos: revisamos el código que los procesa. Tomamos algunos cálculos del proyecto, escribimos dos versiones de cada uno y medimos cuánto se demora y cuánta memoria usa cada versión.

**Cómo ejecutarlo:** abrir `F3/F3_Nucleo_Algoritmico.ipynb` con el kernel del `.venv` y usar *Restart* y *Run All*. El notebook lee el archivo procesado de la Fase 2 (`F1/data/processed/atropellos_2023_features.csv`), así que primero tiene que haberse ejecutado F2.

**Organización de `F3/src/`:**

| Archivo | Qué hace |
|---|---|
| `medicion.py` | Funciones para medir tiempo (`timeit`) y memoria (`tracemalloc`), y para revisar que las dos versiones den lo mismo |
| `recorrido.py` | Medición 1: recorrer las carpetas del proyecto con `rglob` o con una función recursiva |
| `hora.py` | Medición 2: sacar la hora del siniestro fila por fila o con `pd.to_datetime` |
| `busqueda.py` | Medición 3: contar atropellos fatales por comuna filtrando cada vez o agrupando una vez |

Dejamos las funciones en archivos separados para que el notebook quede más corto y fácil de leer, y para poder usar las mismas funciones en la Fase 4.

**Criterios que usamos para optimizar:**

- Antes de medir, revisar que las dos versiones den exactamente el mismo resultado.
- Medir 3 veces y quedarse con el tiempo menor.
- Preferir operaciones sobre la columna completa en vez de recorrer fila por fila.
- No repetir un cálculo que se puede hacer una sola vez y guardar.
- Usar recursión solo cuando no se sabe cuántos niveles tiene el problema (las carpetas del proyecto), y no en la tabla de atropellos.

**Error encontrado:** al revisar el código de la Fase 2 vimos que `Hora_limpia` quedó en 0 en todas las filas, porque se calculó desde la columna `Hora`, que viene con el mismo valor en todo el archivo. En F3 la hora se saca de `Hora_texto`. El notebook de la Fase 2 no se modificó porque ya fue entregado.
