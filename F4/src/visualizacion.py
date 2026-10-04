"""Tres visualizaciones analíticas (Fase 4).

Todas trabajan sobre `df_visual` (categorías y unidades originales) y usan
tasas de fatalidad con su n, porque los grupos son de tamaños muy distintos y
las cifras absolutas llevarían a conclusiones equivocadas.
Cada título comunica el hallazgo y se calcula desde los datos.
"""
import textwrap

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

import pipeline

DESTACADO = "#AC212E"   # aquello sobre lo que se dirige la mirada
NEUTRO = "#9FB6C8"      # el contexto
FUENTE = "Fuente: CONASET (2023), registro de atropellos; elaboración propia."


def configurar_tema():
    """Define el tema una sola vez para que las tres figuras sean consistentes."""
    sns.set_theme(style="whitegrid", palette="deep")
    plt.rcParams.update({"figure.dpi": 110, "axes.titleweight": "bold",
                         "axes.axisbelow": True})


def _n(valor, decimales=0):
    """Formatea un número con coma decimal, como en el informe."""
    return f"{valor:.{decimales}f}".replace(".", ",")


def _miles(valor):
    """Entero con punto como separador de miles (5541 -> 5.541)."""
    return format(int(valor), ",").replace(",", ".")


def _titulo(fig, texto):
    fig.suptitle("\n".join(textwrap.wrap(texto, 78)), fontsize=11.5,
                 fontweight="bold", x=0.01, ha="left")


def figura_hora(visual):
    """Contexto: cuántos atropellos hay por hora y qué tan letales son."""
    por_hora = visual.groupby("Hora_limpia")["Es_Fatal"].agg(n="size", tasa="mean")
    por_hora["tasa"] *= 100
    general = visual["Es_Fatal"].mean() * 100
    madrugada = visual.loc[visual["Hora_limpia"].between(0, 5), "Es_Fatal"].mean() * 100
    dia = visual.loc[visual["Hora_limpia"].between(6, 17), "Es_Fatal"].mean() * 100
    hora_pico = int(por_hora["n"].idxmax())

    fig, (arriba, abajo) = plt.subplots(2, 1, figsize=(9, 6.2), sharex=True,
                                        gridspec_kw={"height_ratios": [1, 1.1]})
    arriba.bar(por_hora.index, por_hora["n"], color=NEUTRO, width=0.8)
    arriba.annotate(f"Máximo en cantidad: {hora_pico}:00 h ({int(por_hora['n'].max())} casos)",
                    xy=(hora_pico, por_hora["n"].max()),
                    xytext=(hora_pico - 11.5, por_hora["n"].max() * 0.93),
                    arrowprops=dict(arrowstyle="->", color="#333333"), fontsize=9, ha="left")
    arriba.set_ylabel("Atropellos (n)")

    for eje in (arriba, abajo):
        eje.axvspan(-0.5, 5.5, color=DESTACADO, alpha=0.07)
        eje.axvspan(21.5, 23.5, color=DESTACADO, alpha=0.07)
    abajo.plot(por_hora.index, por_hora["tasa"], marker="o", linewidth=2.2, color=DESTACADO)
    abajo.axhline(general, color="#444444", linestyle="--", linewidth=1)
    abajo.text(7, general + 1.4, f"Promedio general: {_n(general, 2)} %", fontsize=8.5)
    abajo.set_ylabel("Atropellos con fallecido (%)")
    abajo.set_xlabel("Hora del día (0-23 h)")
    abajo.set_xticks(range(0, 24, 2))
    abajo.set_ylim(0, por_hora["tasa"].max() * 1.15)

    _titulo(fig, f"La letalidad se dispara de madrugada: {_n(madrugada)} % de los atropellos "
                 f"entre 0 y 5 h tiene un fallecido, frente a {_n(dia)} % entre 6 y 17 h")
    fig.text(0.01, 0.005, FUENTE + " Franjas sombreadas: 22-05 h.", fontsize=8)
    fig.tight_layout(rect=(0, 0.02, 1, 0.9))
    return fig


def figura_causa(visual, minimo_n=30):
    """Contraste: qué causas, según Carabineros, se asocian a mayor letalidad."""
    tabla = pipeline.tasa_fatalidad(visual, "Causa", minimo_n).sort_values("tasa")
    general = visual["Es_Fatal"].mean() * 100
    excluidas = visual["Causa"].nunique() - len(tabla)

    fig, eje = plt.subplots(figsize=(9, 4.8))
    colores = [DESTACADO if t > general else NEUTRO for t in tabla["tasa"]]
    barras = eje.barh(tabla["Causa"], tabla["tasa"], color=colores)
    eje.bar_label(barras, labels=[f"{_n(t, 1)} %  (n={n})" for t, n in zip(tabla["tasa"], tabla["n"])],
                  padding=3, fontsize=8.5,
                  bbox=dict(facecolor="white", edgecolor="none", pad=1.2))
    eje.axvline(general, color="#444444", linestyle="--", linewidth=1)
    eje.text(general + 0.4, -0.65, f"Promedio general: {_n(general, 2)} %", fontsize=8.5)
    eje.set_xlim(0, tabla["tasa"].max() * 1.3)
    eje.set_xlabel("Atropellos con al menos un fallecido (%)")
    eje.set_ylabel("")

    top = tabla.sort_values("tasa", ascending=False).head(2)
    _titulo(fig, f"{top.iloc[0]['Causa']} ({_n(top.iloc[0]['tasa'], 1)} %) y "
                 f"{top.iloc[1]['Causa'].lower()} ({_n(top.iloc[1]['tasa'], 1)} %) son las causas "
                 f"con mayor letalidad; en rojo, las que superan el promedio general")
    fig.text(0.01, 0.005, FUENTE + f" Causa asignada por Carabineros. Se excluyen {excluidas} "
             f"causas con n < {minimo_n}.", fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 0.93))
    return fig


def figura_zona_jornada(visual):
    """Resolución: ¿el riesgo nocturno se mantiene al separar por zona?

    Barras agrupadas con intervalo de confianza de Wilson (95 %). El diseño
    sigue la propuesta de Karim Zaid para la figura de zona y jornada.
    """
    tabla = pipeline.tasa_zona_jornada(visual)
    colores = {"Urbana": "#2B7BD6", "Rural": "#EC6A34"}
    ancho = 0.38
    fig, eje = plt.subplots(figsize=(9, 5.2))
    for k, zona in enumerate(["Urbana", "Rural"]):
        fila = tabla[tabla["Zona"] == zona].set_index("Jornada").loc[pipeline.ORDEN_JORNADAS]
        x = np.arange(len(fila)) + (k - 0.5) * (ancho + 0.02)
        eje.bar(x, fila["tasa"], width=ancho, color=colores[zona], label=zona)
        eje.errorbar(x, fila["tasa"], yerr=[fila["tasa"] - fila["inf"], fila["sup"] - fila["tasa"]],
                     fmt="none", ecolor="#444444", capsize=3, linewidth=1.2)
        for xi, (_, r) in zip(x, fila.iterrows()):
            eje.text(xi, r["sup"] + 1.2, f"{_n(r['tasa'], 1)} %", ha="center", fontweight="bold", fontsize=10)
            eje.text(xi, r["sup"] + 4.6, f"n = {_miles(r['n'])}", ha="center", fontsize=8, color="#555555")
    eje.set_xticks(np.arange(len(pipeline.ORDEN_JORNADAS)))
    eje.set_xticklabels(pipeline.ORDEN_JORNADAS)
    eje.set_ylabel("Atropellos fatales (%)")
    eje.set_ylim(0, tabla["sup"].max() + 12)
    eje.legend(title="Zona", loc="upper left", frameon=False)
    eje.grid(axis="x", visible=False)
    sns.despine(ax=eje)

    t = tabla.set_index(["Zona", "Jornada"])["tasa"]
    rural_noche, urbana_dia = t["Rural", pipeline.ORDEN_JORNADAS[1]], t["Urbana", pipeline.ORDEN_JORNADAS[0]]
    _titulo(fig, f"De noche en zona rural, {_n(rural_noche, 0)} % de los atropellos son fatales; "
                 f"de día en zona urbana, {_n(urbana_dia, 1)} % (una tasa {_n(rural_noche / urbana_dia, 0)} veces menor)")
    n_total = int(tabla["n"].sum())
    fig.text(0.01, 0.005, "Fuente: elaboración propia con datos de CONASET y Carabineros de Chile, Siniestros de tipo atropello 2023 "
             f"(n = {_miles(n_total)}). Barras de error: IC 95 % (Wilson).", fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 0.93))
    return fig
