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

El conjunto (2,7 MB) se versiona directamente en `F1/data/raw/`, sin modificar.

## Estructura del repositorio
F1/ Definición del problema y entorno reproducible
F2/ Obtención, limpieza y transformación de datos
F3/ Núcleo algorítmico: programación estructurada, recursiva y POO
F4/ Análisis, visualización y comunicación de resultados

## Requisitos y ejecución
Python 3.13.15 
    python -m venv 
    .venv source 
    .venv/Scripts/activate             # Windows, Git Bash 
    # .venv\Scripts\Activate.ps1       # Windows, PowerShell 
    # source .venv/bin/activate        # macOS y Linux 
    python -m pip install -r requirements.txt

Ejecutar los notebooks en orden desde la raíz del proyecto.

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
