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
    fig.tight_layout(rect=(0, 0.03, 1, 0.88))
    return fig


def figura_zona_tramo(visual):
    """Resolución: ¿el riesgo nocturno se mantiene al separar por zona?"""
    celdas = (visual.groupby(["Zona", "Tramo_horario"], observed=True)["Es_Fatal"]
              .agg(n="size", tasa="mean").reset_index())
    celdas["tasa"] *= 100
    tasa = celdas.pivot(index="Zona", columns="Tramo_horario", values="tasa")
    n = celdas.pivot(index="Zona", columns="Tramo_horario", values="n")
    etiquetas = tasa.round(0).astype(int).astype(str) + " %\n(n=" + n.astype(int).astype(str) + ")"

    noche = visual["Hora_limpia"].isin([22, 23, 0, 1, 2, 3, 4, 5])
    por = visual.assign(noche=noche).groupby(["Zona", "noche"])["Es_Fatal"].mean() * 100

    fig, eje = plt.subplots(figsize=(9, 3.8))
    sns.heatmap(tasa, annot=etiquetas, fmt="", cmap="Reds", vmin=0, linewidths=0.6,
                cbar_kws={"label": "% con fallecido"}, ax=eje)
    eje.set_xlabel("Tramo horario")
    eje.set_ylabel("Zona")
    eje.tick_params(axis="y", rotation=0)

    _titulo(fig, f"El riesgo nocturno (22-05 h) se mantiene al separar por zona: "
                 f"rural {por['Rural', True]:.0f} % de noche frente a {por['Rural', False]:.0f} % de día; "
                 f"urbana {por['Urbana', True]:.0f} % frente a {por['Urbana', False]:.0f} %")
    fig.text(0.01, 0.005, FUENTE + " Porcentaje calculado por celda (zona × tramo).", fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 0.86))
    return fig
