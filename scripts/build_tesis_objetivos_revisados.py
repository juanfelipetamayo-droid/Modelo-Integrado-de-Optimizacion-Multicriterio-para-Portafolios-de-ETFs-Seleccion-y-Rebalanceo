"""Build a versioned thesis variant with revised objectives 1 and 3.

The variant keeps the current academic format and the title-per-page rule,
but updates claims so the work no longer promises fixed cardinality or
benchmark superiority. It also refreshes the objective-compliance figure and
the selection-size figure used by the LaTeX deliverable.
"""

from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


SOURCE_TEX = Path("docs/deliverables/tesis_final_tamayo_etf_electre.tex")
OUT_TEX = Path("docs/deliverables/tesis_final_tamayo_etf_electre_objetivos_revisados.tex")
ASSETS = Path("docs/deliverables/tesis_final_assets")
FIG_OUT = Path("docs/figures/thesis_results_objetivos_revisados")
PRIMARY = Path("results/thesis_primary_2021_2025_run_no_cap")
EXTENDED = Path("results/thesis_extended_2015_2025_run_no_cap")

RECURRING_READINGS = {
    "CDC": "Presencia constante en periodos con mayor persistencia de criterio financiero.",
    "CFO": "Persistencia alta ligada a liquidez y estabilidad de desempeño.",
    "CIBR": "Núcleo central de selección en fases de continuidad estratégica.",
    "CFA": "Aporte recurrente en fases de rotación del bloque tecnológico-financiero.",
    "CGW": "Componente estable en etapas de selección de calidad por segmento.",
}

OBJ1 = (
    "Reducir el universo de ETFs disponibles a un conjunto manejable para pequeños "
    "inversionistas, mediante la aplicación de criterios multicriterio de selección "
    "relacionados con desempeño, riesgo, liquidez y consistencia financiera."
)
OBJ3 = (
    "Comparar el desempeño obtenido por el modelo multicriterio mediante benchmarking "
    "frente a estrategias tradicionales de inversión, utilizando métricas de rentabilidad, "
    "riesgo y rentabilidad ajustada por riesgo."
)


def replace_required(text: str, old: str, new: str) -> str:
    if old not in text:
        raise SystemExit(f"No se encontró texto esperado para reemplazo: {old[:90]}")
    return text.replace(old, new)


def replace_first(text: str, old: str, new: str) -> str:
    """Replace only the first occurrence when it exists."""
    index = text.find(old)
    if index == -1:
        return text
    return text[:index] + new + text[index + len(old) :]


def italicize_terms(text: str, terms: list[str]) -> str:
    """Italicize selected English terms while avoiding nested \textit/\texttt blocks."""
    protected: list[str] = []

    def protect(match: re.Match[str]) -> str:
        protected.append(match.group(0))
        return f"@@PROTECTED_{len(protected) - 1}@@"

    # Protect simple formatted spans so existing italics and file paths are not rewritten.
    working = re.sub(r"\\(?:textit|texttt)\{[^{}]*\}", protect, text)

    for term in sorted(terms, key=len, reverse=True):
        pattern = re.compile(rf"(?<![A-Za-z\\]){re.escape(term)}(?![A-Za-z])")
        working = pattern.sub(rf"\\textit{{{term}}}", working)

    for index, original in enumerate(protected):
        working = working.replace(f"@@PROTECTED_{index}@@", original)
    return working


def apply_editorial_rules(text: str) -> str:
    """Apply thesis style rules for anglicisms and first-use acronym expansions."""
    bibliography_marker = "\\section{Bibliografía}"
    body, marker, bibliography = text.partition(bibliography_marker)

    acronym_expansions = [
        ("ETFs", r"ETFs (\textit{Exchange-Traded Funds})"),
        ("ELECTRE Tri", r"ELECTRE (\textit{ÉLimination Et Choix Traduisant la REalité}) Tri"),
        ("MCDM", r"MCDM (\textit{Multiple-Criteria Decision Making})"),
        ("CAPM", r"CAPM (\textit{Capital Asset Pricing Model})"),
        ("PROMETHEE", r"PROMETHEE (\textit{Preference Ranking Organization Method for Enrichment Evaluations})"),
        ("TOPSIS", r"TOPSIS (\textit{Technique for Order Preference by Similarity to Ideal Solution})"),
        ("AHP", r"AHP (\textit{Analytic Hierarchy Process})"),
        ("CAGR", r"CAGR (\textit{Compound Annual Growth Rate})"),
        ("CRSP Research Data Products", r"CRSP (\textit{Center for Research in Security Prices}) \textit{Research Data Products}"),
        ("SEC N-PORT, N-CEN, EDGAR y OpenFIGI", r"SEC (\textit{Securities and Exchange Commission}) N-PORT (\textit{Monthly Portfolio Investments Report}), N-CEN (\textit{Annual Report for Registered Investment Companies}), EDGAR (\textit{Electronic Data Gathering, Analysis, and Retrieval}) y OpenFIGI (\textit{Open Financial Instrument Global Identifier})"),
    ]
    for old, new in acronym_expansions:
        body = replace_first(body, old, new)

    english_terms = [
        "Sharpe Ratio",
        "tracking error",
        "expense ratio",
        "out-of-sample",
        "point-in-time",
        "backtesting",
        "benchmarking",
        "Benchmarks",
        "benchmarks",
        "benchmark",
        "survivorship bias",
        "buy and hold",
        "drawdown",
        "MaxSharpe",
        "Pipeline",
        "pipeline",
        "snapshots",
        "delistings",
        "Tickers",
        "tickers",
        "Ticker",
        "ticker",
        "rankings",
        "ranking",
        "FlowSort",
        "Black-Litterman",
        "GitHub",
        "Research Data Products",
    ]
    body = italicize_terms(body, english_terms)

    return body + marker + bibliography


def add_title_per_page(text: str) -> str:
    marker = "\\end{titlepage}"
    if marker not in text:
        raise SystemExit("No se encontró el cierre de portada")
    prefix, suffix = text.split(marker, 1)
    suffix = suffix.replace("\\section{", "\\clearpage\n\\section{")
    return prefix + marker + suffix


def coerce_selected(values: pd.Series) -> pd.Series:
    if values.dtype == bool:
        return values
    return values.astype(str).str.lower().isin({"true", "1", "t", "yes"})


def latex_row(*cells: object) -> str:
    return " & ".join(str(cell) for cell in cells) + r" \\"


def build_composicion_temporal_principal_table() -> str:
    selection = pd.read_csv(
        PRIMARY / "electre_selection_by_rebalance.csv",
        parse_dates=["rebalance_date"],
    )
    selected = selection[coerce_selected(selection["selected"])].sort_values(
        ["rebalance_date", "ticker"]
    )
    rows = []
    for rebalance_date, group in selected.groupby(selected["rebalance_date"].dt.strftime("%Y-%m-%d")):
        tickers = ", ".join(group["ticker"].tolist())
        rows.append(latex_row(rebalance_date, len(group), tickers))

    return "\n".join(
        [
            r"\begin{table}[H]",
            r"\centering",
            r"\caption{Composición temporal del protocolo principal 2021--2025}",
            r"\label{tab:composicion_temporal_principal}",
            r"\begin{tabular}{p{3cm}p{1.5cm}p{8.5cm}}",
            r"\toprule",
            latex_row(r"\textbf{Rebalanceo}", r"\textbf{n}", r"\textbf{ETFs elegidos}"),
            r"\midrule",
            *rows,
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
            r"\fuente{Cálculo con \texttt{electre\_selection\_by\_rebalance.csv}, corrida principal.}",
        ]
    )


def build_cardinalidad_resumen_table() -> str:
    selection = pd.read_csv(
        PRIMARY / "electre_selection_by_rebalance.csv",
        parse_dates=["rebalance_date"],
    )
    selected = selection[coerce_selected(selection["selected"])]
    counts = selected.groupby(selected["rebalance_date"]).size()

    rebalanceos = len(counts)
    promedio = counts.mean()
    mediana = counts.median()
    minimo = int(counts.min())
    maximo = int(counts.max())

    rows = [
        latex_row("Rebalanceos con selección activa", rebalanceos),
        latex_row("Promedio de ETFs seleccionados", f"{promedio:.2f}"),
        latex_row("Mediana", int(mediana)),
        latex_row("Mínimo--Máximo", f"{minimo}--{maximo}"),
    ]

    return "\n".join(
        [
            r"\begin{table}[H]",
            r"\centering",
            r"\caption{Resumen de cardinalidad en la corrida principal 2021--2025}",
            r"\label{tab:cardinalidad_resumen_principal}",
            r"\begin{tabular}{p{5.2cm}p{2.8cm}}",
            r"\toprule",
            latex_row(r"\textbf{Métrica}", r"\textbf{Valor}"),
            r"\midrule",
            *rows,
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
            r"\fuente{Recuento sobre \texttt{electre\_selection\_by\_rebalance.csv}, corrida principal.}",
        ]
    )


def build_recurrentes_ampliada_table() -> str:
    selection = pd.read_csv(EXTENDED / "electre_selection_by_rebalance.csv")
    selected = selection[coerce_selected(selection["selected"])]
    counts = selected.groupby("ticker")["rebalance_date"].nunique().sort_values(ascending=False)
    total_rebalances = selected["rebalance_date"].nunique()
    top = counts.head(5)

    rows = []
    for ticker, apariciones in top.items():
        porcentaje = apariciones / total_rebalances * 100
        lectura = RECURRING_READINGS.get(
            ticker,
            "Componente recurrente en la validación ampliada.",
        )
        rows.append(latex_row(ticker, int(apariciones), f"{porcentaje:.1f}\\%", lectura))

    return "\n".join(
        [
            r"\begin{table}[H]",
            r"\centering",
            r"\caption{Tickers más recurrentes en la validación ampliada 2015--2025}",
            r"\label{tab:recurrentes_ampliada}",
            r"\begin{tabular}{p{1.8cm}p{2.2cm}p{3.2cm}p{4.8cm}}",
            r"\toprule",
            latex_row(r"\textbf{Ticker}", r"\textbf{Apariciones}", r"\textbf{Porcentaje de rebalanceos}", r"\textbf{Lectura}"),
            r"\midrule",
            *rows,
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
            r"\fuente{Conteos de apariciones sobre los 31 rebalanceos de la corrida de robustez.}",
        ]
    )


def build_selection_size_figure() -> None:
    FIG_OUT.mkdir(parents=True, exist_ok=True)
    selection = pd.read_csv(
        PRIMARY / "electre_selection_by_rebalance.csv",
        parse_dates=["rebalance_date"],
    )
    selected = selection[coerce_selected(selection["selected"])]
    counts = selected.groupby("rebalance_date")["ticker"].nunique()
    all_dates = pd.Index(sorted(selection["rebalance_date"].dropna().unique()))
    counts = counts.reindex(all_dates, fill_value=0)

    fig, ax = plt.subplots(figsize=(10.5, 5.3))
    ax.plot(counts.index, counts.values, marker="o", color="#1f77b4", linewidth=2.2, label="ETFs seleccionados")
    ax.axhline(counts.mean(), color="#d62728", linewidth=1.4, linestyle="--", label=f"Promedio: {counts.mean():.2f}")
    ax.set_title("Protocolo principal: tamaño del conjunto seleccionado")
    ax.set_ylabel("Número de ETFs seleccionados")
    ax.set_xlabel("Rebalanceo")
    ax.legend(frameon=False)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(FIG_OUT / f"primary_05_selection_cardinality_revisada.{ext}", dpi=220, bbox_inches="tight")
    fig.savefig(ASSETS / "numero_etfs_rebalanceo.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def build_objective_compliance_figure() -> None:
    FIG_OUT.mkdir(parents=True, exist_ok=True)
    labels = ["Obj. general", "Obj. 1", "Obj. 2", "Obj. 3", "Protocolo", "Benchmarks"]
    runs = ["Principal", "Extendida"]
    status = pd.DataFrame(
        {
            "Principal": ["Parcial", "Cumple", "Parcial", "Cumple", "Cumple", "Cumple"],
            "Extendida": ["Parcial", "Cumple", "Parcial", "Cumple", "Robustez", "Cumple"],
        },
        index=labels,
    )
    score_map = {"Parcial": 1, "Robustez": 2, "Cumple": 3}
    scores = status.replace(score_map).astype(float)

    fig, ax = plt.subplots(figsize=(8.8, 5.2))
    image = ax.imshow(scores.values, cmap=plt.get_cmap("RdYlGn"), vmin=0, vmax=3, aspect="auto")
    ax.set_xticks(range(len(runs)), runs)
    ax.set_yticks(range(len(labels)), labels)
    for i, objective in enumerate(labels):
        for j, run in enumerate(runs):
            ax.text(j, i, status.loc[objective, run], ha="center", va="center", fontsize=8, color="#111111")
    ax.set_title("Estado de cumplimiento con objetivos revisados")
    cbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_ticks([0, 1, 2, 3], labels=["No", "Parcial", "Robustez", "Cumple"])
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(FIG_OUT / f"combined_07_objective_compliance_revisada.{ext}", dpi=220, bbox_inches="tight")
    fig.savefig(ASSETS / "cumplimiento_objetivos.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def build_tex() -> None:
    text = SOURCE_TEX.read_text(encoding="utf-8")

    size_paragraph = (
        "La cardinalidad de la selección también aporta un hallazgo importante. "
        "El modelo seleccionó menos activos de los esperados en varias fechas de "
        "rebalanceo, lo que reduce diversificación y afecta el cumplimiento del "
        "primer objetivo específico. Este resultado no debe ocultarse, porque señala "
        "una oportunidad concreta de mejora: ajustar perfiles, umbrales o reglas de "
        "selección final para asegurar que el portafolio mantenga el rango objetivo "
        "de 10 a 25 activos sin relajar excesivamente la calidad de los ETFs elegidos."
    )
    size_paragraph_revised = (
        "El tamaño de la selección deja una lectura importante para el trabajo. "
        "El modelo no entrega una cartera amplia en todas las fechas; más bien concentra "
        "el universo en pocos activos cuando las condiciones de los criterios son exigentes. "
        "Desde una mirada de Ingeniería Industrial, esto no se interpreta como un error aislado "
        "del algoritmo, sino como una señal del proceso: el filtro está siendo estricto y privilegia "
        "trazabilidad sobre amplitud. La contrapartida es clara. Si en una aplicación práctica se "
        "busca una diversificación mayor, habría que ajustar perfiles, umbrales o reglas finales "
        "sin perder el sentido de calidad que motivó la selección inicial."
    )
    cardinalidad_anchor = (
        "\\label{fig:cardinalidad}\n"
        "\\end{figure}\n"
        "\\fuente{Elaboración propia.}"
    )
    robustez_extended_intro = (
        "La validación ampliada refuerza la necesidad de no evaluar el modelo únicamente "
        "en una ventana corta. Al extender el período a 2015--2025, el desempeño de "
        "las estrategias ELECTRE se debilita frente a SPY, 60/40 y el universo equiponderado. "
        "Esta evidencia sugiere que la señal de clasificación observada en la prueba principal "
        "no es todavía suficientemente estable para sostener una conclusión de superioridad. "
        "El resultado aporta una lectura realista del alcance del modelo y ayuda a orientar mejoras futuras."
    )
    robustez_extended_intro_revised = (
        "La validación ampliada obliga a mirar el modelo con más calma. Al extender el período "
        "a 2015--2025, el desempeño de las estrategias ELECTRE se debilita frente a SPY, 60/40 "
        "y el universo equiponderado. Esta evidencia no anula la metodología, pero sí evita una "
        "conclusión apresurada basada solo en una ventana corta. En términos de proyecto de grado, "
        "el resultado es útil precisamente porque muestra dónde funciona el sistema, dónde pierde "
        "fuerza y qué ajustes tendría sentido estudiar después."
    )
    composicion_annotation = (
        "La tabla anterior muestra que la selección se mueve de forma gradual y no como una lista fija. "
        "En las primeras fechas el clasificador deja pasar muy pocos instrumentos, mientras que en 2025 "
        "aparece una apertura mayor del conjunto elegido. Para la lectura del primer objetivo, este detalle "
        "es importante: la reducción del universo sí ocurre, pero no mediante una cuota impuesta de activos. "
        "El resultado depende de la información disponible en cada rebalanceo y de la exigencia de los perfiles ELECTRE."
    )
    cardinalidad_annotation = (
        "El resumen de cardinalidad confirma esa misma idea con números agregados. El promedio de 4.43 ETFs "
        "seleccionados es bajo frente a una cartera diversificada tradicional, pero es coherente con un filtro "
        "pensado para depurar un universo amplio antes de optimizar. En una implementación real, este punto "
        "sería una decisión de diseño: mantener una selección estricta o incorporar una regla adicional de tamaño mínimo."
    )
    recurrentes_annotation = (
        "La recurrencia de estos tickers no debe leerse como una recomendación de compra. Su aporte dentro del "
        "documento es más metodológico: permite ver que el sistema no selecciona activos completamente distintos "
        "en cada fecha, sino que conserva algunos núcleos cuando los criterios vuelven a favorecerlos. Esa estabilidad "
        "parcial ayuda a entender mejor el comportamiento del clasificador en una ventana larga."
    )
    integrated_reading_section = (
        "\\subsection{Lectura integrada de los resultados}\n\n"
        "Al mirar en conjunto la prueba principal, la validación ampliada y las tablas de selección, la conclusión "
        "queda más matizada que una simple comparación de rentabilidades. El sistema sí cumple una función clara: "
        "ordena un universo grande de ETFs, aplica criterios homogéneos por fecha de rebalanceo y deja una ruta "
        "replicable para pasar de datos históricos a portafolios evaluables. Esa parte del trabajo es valiosa porque "
        "convierte una decisión normalmente dispersa en un proceso documentado.\n\n"
        "También hay límites que no conviene suavizar. La selección quedó concentrada en varias fechas y el desempeño "
        "ajustado por riesgo no superó a referentes simples como SPY o el portafolio 60/40. Desde una lectura de "
        "Ingeniería Industrial, este resultado muestra que el diseño del sistema y su resultado financiero no son la "
        "misma cosa. El proceso puede estar bien construido y, aun así, necesitar mejores datos, criterios más completos "
        "o reglas de asignación más robustas.\n\n"
        "Por eso el aporte principal del trabajo se ubica en la trazabilidad del método. La tesis no plantea que ELECTRE "
        "vence siempre a las estrategias tradicionales. Lo que muestra es más concreto: se puede construir un flujo "
        "reproducible para seleccionar ETFs, revisar su comportamiento, compararlos contra benchmarks y detectar qué parte "
        "del sistema requiere ajuste. Esta lectura es más prudente y queda mejor conectada con los resultados obtenidos."
    )

    text = replace_required(
        text,
        "\\includegraphics[width=0.92\\textwidth]{componentes_sistema.png}",
        "\\includegraphics[width=0.92\\textwidth]{flujo_trabajo_sistema.png}",
    )
    text = replace_required(
        text,
        "\\caption{Organización general del sistema implementado}",
        "\\caption{Flujo de trabajo del sistema implementado}",
    )
    text = replace_required(
        text,
        "El estudio mantiene el sentido metodológico planteado inicialmente, pero incorpora los hallazgos obtenidos durante el desarrollo del sistema: la validación principal se estructura con datos 2021--2024 para desarrollo y calibración, y 2025 como ventana \\textit{out-of-sample}; además, se usa una validación ampliada 2015--2025 como prueba de robustez y no como reemplazo del protocolo aceptado. Los resultados muestran que el sistema construido es funcional, reproducible y útil como herramienta de apoyo a la decisión. Bajo la configuración evaluada no se confirma una superioridad robusta frente a SPY, el portafolio 60/40 ni la equiponderación del universo, por lo cual la contribución principal se ubica en el diseño, implementación y evaluación crítica de una metodología abierta para seleccionar un conjunto preliminar de fondos y luego optimizarlos.",
        "El estudio mantiene el sentido metodológico planteado inicialmente, pero ajusta la lectura de resultados a lo que efectivamente arrojó la implementación. La validación principal se trabaja con datos 2021--2024 para desarrollo y calibración, y 2025 como ventana \\textit{out-of-sample}; además, se incluye una validación ampliada 2015--2025 como prueba de robustez, no como reemplazo del protocolo aceptado. Con esta evidencia, el aporte del trabajo se entiende mejor como una metodología abierta para reducir el universo de ETFs, construir portafolios y comparar su desempeño frente a estrategias tradicionales de inversión.",
    )
    text = replace_required(
        text,
        "Aunque esta aproximación es atractiva, requiere definir de forma explícita niveles de aspiración para cada criterio. En el contexto del presente trabajo, el uso de ELECTRE Tri resulta más conveniente porque permite trabajar con perfiles de referencia y categorías de calidad sin convertir el problema en una sola función de desviaciones. No obstante, la idea de metas se conserva de manera indirecta en el proyecto: el rango deseado de 10 a 25 activos, el control de volatilidad, la búsqueda de Sharpe Ratio competitivo y la comparación frente a benchmarks funcionan como referencias que permiten evaluar si el sistema cumple o no los objetivos planteados.",
        "Aunque esta aproximación es atractiva, requiere definir de forma explícita niveles de aspiración para cada criterio. En el contexto del presente trabajo, el uso de ELECTRE Tri resulta más conveniente porque permite trabajar con perfiles de referencia y categorías de calidad sin convertir el problema en una sola función de desviaciones. No obstante, la idea de metas se conserva de manera indirecta en el proyecto: el tamaño manejable del conjunto seleccionado, el control de volatilidad, la búsqueda de Sharpe Ratio competitivo y la comparación frente a benchmarks funcionan como referencias que permiten evaluar si el sistema cumple o no los objetivos planteados.",
    )
    text = replace_required(
        text,
        "\\textbf{Objetivo específico número uno:} Diseñar e implementar un sistema de clasificación multicriterio que reduzca el universo del mercado estadounidense a un conjunto de 10--25 activos sobre datos del 2021--2024.",
        f"\\textbf{{Objetivo específico número uno:}} {OBJ1}",
    )
    text = replace_required(
        text,
        "\\textbf{Objetivo específico número tres:} Desarrollar e implementar un modelo de optimización de portafolios que busque mejorar la rentabilidad ajustada por riesgo y controlar la exposición al riesgo, con el propósito de construir portafolios eficientes y evaluar empíricamente si el enfoque multicriterio ofrece ventajas frente a estrategias de inversión tradicionales.",
        f"\\textbf{{Objetivo específico número tres:}} {OBJ3}",
    )
    text = replace_required(
        text,
        "Objetivo específico 1 & Clasificación ELECTRE y selección por fecha de rebalanceo. & Implementado, pero no cerrado operacionalmente: la selección promedio quedó por debajo del rango 10--25. \\",
        "Objetivo específico 1 & Clasificación ELECTRE, filtros operativos y selección por fecha de rebalanceo. & Cumplido: el sistema reduce el universo disponible a un conjunto manejable y trazable para pequeños inversionistas, sin prometer una cardinalidad fija. \\",
    )
    text = replace_required(
        text,
        "Objetivo específico 3 & Estrategias de asignación, backtesting y comparación con SPY, 60/40 y universo equiponderado. & No se valida superioridad robusta; se valida la capacidad del sistema para contrastar la hipótesis de forma reproducible. \\",
        "Objetivo específico 3 & Estrategias de asignación, backtesting y benchmarking con SPY, 60/40 y universo equiponderado. & Cumplido: se compara el desempeño del modelo frente a estrategias tradicionales sin afirmar superioridad empírica. \\",
    )
    text = replace_required(
        text,
        "La principal limitación del trabajo corresponde a la disponibilidad y calidad de los datos. Los experimentos finales utilizan un universo público aproximado \\textit{point-in-time}; esta aproximación mejora la trazabilidad frente a un universo completamente estático, pero no equivale a una base institucional libre de sesgo de supervivencia. Adicionalmente, aunque el objetivo general contempla \\textit{tracking error} y \\textit{expense ratio}, las ejecuciones empíricas no contaron con cobertura completa para estos criterios, por lo cual el cumplimiento del objetivo general se considera parcial.",
        "La principal limitación del trabajo corresponde a la disponibilidad y calidad de los datos. Los experimentos finales utilizan un universo público aproximado \\textit{point-in-time}; esta aproximación mejora la trazabilidad frente a un universo completamente estático, pero no equivale a una base institucional libre de sesgo de supervivencia. Durante el desarrollo también se intentó contactar a CRSP Research Data Products para consultar la posibilidad de una licencia académica; sin embargo, no fue posible concretar el acceso porque la negociación debía realizarse directamente desde la institución educativa. Esta situación dejó por fuera una fuente institucional que habría permitido mejorar la reconstrucción histórica del universo invertible. Adicionalmente, aunque el objetivo general contempla \\textit{tracking error} y \\textit{expense ratio}, las ejecuciones empíricas no contaron con cobertura completa para estos criterios, por lo cual el cumplimiento del objetivo general se considera parcial.",
    )
    text = replace_required(
        text,
        "Es importante resaltar que la validación no se utilizó para forzar una lectura favorable del modelo, sino para establecer con claridad qué fue validado y qué no. En la corrida principal 2021--2025, la estrategia ELECTRE equiponderada obtuvo resultados positivos, pero no superó a SPY ni al portafolio 60/40 en Sharpe Ratio. En la validación ampliada 2015--2025, la estrategia también quedó por debajo de los principales referentes. Por lo tanto, el resultado final sostiene la utilidad metodológica del sistema, pero no una superioridad empírica definitiva frente a estrategias tradicionales.",
        "La validación no se utilizó para acomodar una lectura favorable del modelo. Se usó para revisar qué tan lejos llegaba la propuesta cuando se comparaba con referentes simples. En la corrida principal 2021--2025, la estrategia ELECTRE equiponderada obtuvo resultados positivos, aunque SPY y el portafolio 60/40 presentaron mejores valores de Sharpe Ratio. En la validación ampliada 2015--2025, la estrategia también quedó por debajo de los principales referentes. Esta comparación deja una conclusión más prudente: el sistema es útil como herramienta de benchmarking reproducible, pero no como demostración de superioridad financiera.",
    )
    text = replace_required(
        text,
        "Otra limitación relevante es la cardinalidad de la selección. El objetivo específico número uno plantea reducir el universo a un conjunto de 10--25 activos; sin embargo, en los experimentos finales la selección promedio por rebalanceo fue inferior a ese rango. En la prueba principal se obtuvo un promedio de 4.43 activos seleccionados por rebalanceo, mientras que en la validación ampliada el promedio fue de 5.29. Esta brecha no invalida la implementación del clasificador, pero sí impide afirmar que el objetivo operacional de cardinalidad quedó completamente satisfecho.",
        "Una lectura relevante de la selección es el tamaño final del conjunto obtenido. Con los objetivos revisados, la cardinalidad deja de ser una meta fija y pasa a interpretarse como evidencia del grado de reducción logrado. En la prueba principal se obtuvo un promedio de 4.43 activos seleccionados por rebalanceo, mientras que en la validación ampliada el promedio fue de 5.29. Esta evidencia respalda que el sistema reduce el universo a un conjunto manejable para pequeños inversionistas, aunque también sugiere revisar en trabajos futuros si se desea mayor diversificación.",
    )
    text = replace_required(text, size_paragraph, size_paragraph_revised)
    text = replace_required(
        text,
        size_paragraph_revised,
        f"{size_paragraph_revised}\n\n{build_composicion_temporal_principal_table()}\n\n{composicion_annotation}",
    )
    text = replace_required(
        text,
        cardinalidad_anchor,
        f"{cardinalidad_anchor}\n\n{build_cardinalidad_resumen_table()}\n\n{cardinalidad_annotation}",
    )
    extended_rebalance_paragraph = (
        "Para esta validación ampliada se ejecutaron 31 rebalanceos, con tamaño medio del "
        "conjunto seleccionado de 5.29 activos, mínimo 1 y máximo 11. El resultado no se "
        "interpreta como inestabilidad técnica del pipeline, sino como evidencia de que la "
        "selección mantiene núcleos de referencia y varía por régimen."
    )
    text = replace_required(
        text,
        robustez_extended_intro,
        f"{robustez_extended_intro_revised}\n\n{extended_rebalance_paragraph}\n\n{build_recurrentes_ampliada_table()}\n\n{recurrentes_annotation}\n\n{integrated_reading_section}",
    )
    text = replace_required(
        text,
        "Desde el punto de vista académico, el resultado más importante no es que el modelo haya superado o no a un benchmark particular, sino que el sistema permite comprobarlo de forma reproducible. La metodología construida evita que la evaluación dependa de apreciaciones subjetivas y permite identificar con precisión qué parte del proceso requiere ajuste: cobertura de criterios, cardinalidad, perfiles ELECTRE, datos regulatorios o estrategia de asignación.",
        "Las figuras siguientes complementan esta lectura porque muestran el comportamiento de las estrategias y la relación entre las categorías ELECTRE y el desempeño posterior. Su función no es decorar el resultado, sino permitir una revisión visual de lo que las tablas resumen: desempeño, estabilidad y límites del clasificador bajo las ventanas evaluadas.",
    )
    text = replace_required(
        text,
        "El proyecto permitió desarrollar un sistema funcional de clasificación, optimización y validación de portafolios de ETFs. Como parte de la validación técnica, el sistema fue evaluado mediante pruebas automatizadas y los resultados principales quedaron documentados en métricas, curvas de capital, caídas, selección por rebalanceo y cumplimiento de objetivos. En conjunto, la evidencia permite sostener que la contribución principal del trabajo es metodológica y diagnóstica: se valida un proceso reproducible para evaluar portafolios de ETFs mediante selección multicriterio, aunque bajo la configuración evaluada se rechaza la hipótesis de superioridad robusta frente a los benchmarks tradicionales.",
        "El proyecto permitió desarrollar un sistema funcional de clasificación, optimización y validación de portafolios de ETFs. Como parte de la validación técnica, el sistema fue evaluado mediante pruebas automatizadas y los resultados principales quedaron documentados en métricas, curvas de capital, caídas, selección por rebalanceo y cumplimiento de objetivos. En conjunto, la evidencia permite sostener que la contribución principal del trabajo es metodológica y diagnóstica: se valida un proceso reproducible para reducir el universo de ETFs, construir portafolios y comparar su desempeño frente a benchmarks tradicionales.",
    )
    text = replace_required(
        text,
        "Un aspecto importante de la implementación fue la trazabilidad. Cada experimento genera archivos con métricas de desempeño, curvas de capital, caídas, activos seleccionados por rebalanceo y resúmenes de cumplimiento. Esto permite reconstruir la cadena de decisiones desde los datos iniciales hasta las conclusiones. En un trabajo de grado aplicado, esta trazabilidad es tan importante como el resultado financiero, porque permite que un evaluador revise si las conclusiones están respaldadas por evidencia verificable.",
        "Un aspecto importante de la implementación fue la trazabilidad. Cada experimento genera archivos con métricas de desempeño, curvas de capital, caídas, activos seleccionados por rebalanceo y resúmenes de cumplimiento. Esto permite reconstruir la cadena de decisiones desde los datos iniciales hasta las conclusiones. En un trabajo de grado aplicado, esta trazabilidad es tan importante como el resultado financiero, porque permite que un evaluador revise si las conclusiones están respaldadas por evidencia verificable.\n\nComo complemento del documento escrito, el repositorio del proyecto en GitHub se incorpora como entregable digital. Allí queda organizado el código fuente, los scripts de ejecución, las pruebas automatizadas, la documentación técnica y los archivos generados para la validación. Este entregable facilita la revisión del trabajo y permite que la metodología pueda ser replicada o ajustada posteriormente.",
    )
    text = replace_required(
        text,
        "Como trabajo futuro se recomienda completar la integración de \\textit{tracking error} y \\textit{expense ratio} con fuentes confiables, activar una regla final de cardinalidad que garantice entre 10 y 25 ETFs por rebalanceo, fortalecer los grupos comparables dentro de ELECTRE Tri, mejorar el manejo de restricciones de exposición y construir una arquitectura de datos regulatoria enriquecida con fuentes como SEC N-PORT, N-CEN, EDGAR y OpenFIGI. Estas mejoras permitirían cerrar las principales brechas que quedaron documentadas durante la implementación.",
        "Como trabajo futuro se recomienda completar la integración de \\textit{tracking error} y \\textit{expense ratio} con fuentes confiables, estudiar reglas opcionales de diversificación y tamaño mínimo cuando el usuario las requiera, fortalecer los grupos comparables dentro de ELECTRE Tri, mejorar el manejo de restricciones de exposición y construir una arquitectura de datos regulatoria enriquecida con fuentes institucionales como CRSP Research Data Products, SEC N-PORT, N-CEN, EDGAR y OpenFIGI. En particular, el acceso a CRSP debería gestionarse desde la universidad o mediante un convenio académico, porque durante el desarrollo individual del proyecto no fue posible obtener la licencia directamente. Estas mejoras permitirían ampliar el alcance del sistema sin alterar la contribución metodológica demostrada.",
    )
    text = replace_required(
        text,
        "En relación con el objetivo general, el trabajo logra desarrollar una herramienta integrada de selección y optimización basada en ETFs, aunque su validación queda parcialmente limitada por la ausencia completa de \\textit{tracking error} y \\textit{expense ratio} en las ejecuciones empíricas. En relación con el primer objetivo específico, se implementa el sistema de clasificación multicriterio, pero la reducción al rango de 10--25 activos no se cumple de forma consistente. En relación con el segundo objetivo, se desarrolla el análisis histórico de los ETFs elegibles y se obtiene evidencia parcial de consistencia ordinal. Finalmente, respecto al tercer objetivo, se implementa la optimización y comparación contra benchmarks, pero no se valida una superioridad robusta frente a estrategias tradicionales.",
        "En relación con el objetivo general, el trabajo logra desarrollar una herramienta integrada de selección y optimización basada en ETFs, aunque su validación queda parcialmente limitada por la ausencia completa de \\textit{tracking error} y \\textit{expense ratio} en las ejecuciones empíricas. En relación con el primer objetivo específico, se implementa el sistema de clasificación multicriterio y se reduce el universo a un conjunto manejable. En relación con el segundo objetivo, se desarrolla el análisis histórico de los ETFs elegibles y se obtiene evidencia parcial de consistencia ordinal. Finalmente, respecto al tercer objetivo, se realiza el benchmarking frente a estrategias tradicionales sin presentar la comparación como promesa de superioridad.",
    )
    text = replace_required(
        text,
        "Estas conclusiones responden directamente a los objetivos y muestran que el trabajo no se limita a presentar un modelo idealizado. La contribución consiste en diseñar, implementar y evaluar un sistema real, con resultados favorables y desfavorables, permitiendo identificar las condiciones bajo las cuales la metodología funciona y las brechas que deben resolverse para una versión futura. Esta es precisamente la utilidad de un proyecto aplicado de Ingeniería Industrial: estructurar un problema complejo, desarrollar una solución verificable y usar los resultados para mejorar el proceso de decisión.",
        "Estas conclusiones responden directamente a los objetivos planteados y evidencian que el trabajo no se limita a proponer un modelo teórico o idealizado. El aporte principal está en el diseño, implementación y evaluación de un sistema aplicado, cuyos resultados permiten reconocer tanto sus aciertos como sus limitaciones. Teniendo esto en cuenta, fue posible identificar en qué condiciones la metodología ofrece un mejor desempeño y cuáles son las brechas que deberían abordarse en futuras versiones. En ese sentido, el proyecto refleja el valor práctico de la Ingeniería Industrial: analizar un problema complejo, estructurar una solución verificable y utilizar la evidencia obtenida para fortalecer la toma de decisiones.",
    )

    text = apply_editorial_rules(text)
    text = add_title_per_page(text)
    OUT_TEX.write_text(text, encoding="utf-8")


def main() -> None:
    if not ASSETS.exists():
        ASSETS.mkdir(parents=True, exist_ok=True)
    build_selection_size_figure()
    build_objective_compliance_figure()
    build_tex()
    print(OUT_TEX)
    print(FIG_OUT)


if __name__ == "__main__":
    main()
