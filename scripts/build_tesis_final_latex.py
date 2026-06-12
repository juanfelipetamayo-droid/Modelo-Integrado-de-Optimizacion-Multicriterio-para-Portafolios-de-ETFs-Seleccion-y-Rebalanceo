"""Build the final LaTeX thesis file preserving the original thesis structure.

The original LaTeX base in docs/tex base is a high-fidelity PDF reconstruction
with absolute coordinates. This generator keeps the visual identity and original
chapter titles, but emits an editable semantic LaTeX file suitable for final
review and future formatting.
"""

from __future__ import annotations

import shutil
from pathlib import Path


OUT_DIR = Path("docs/deliverables")
ASSET_DIR = OUT_DIR / "tesis_final_assets"
OUT_TEX = OUT_DIR / "tesis_final_tamayo_etf_electre.tex"


ASSETS = {
    "docs/tex base/figures/logo_univalle.png": "logo_univalle.png",
    "docs/tex base/figures/figura_gantt.png": "figura_gantt.png",
    "docs/figures/thesis_results/primary_01_equity_curves.png": "evolucion_capital_principal.png",
    "docs/figures/thesis_results/primary_02_drawdowns.png": "caidas_prueba_principal.png",
    "docs/figures/thesis_results/primary_03_risk_return_scatter.png": "riesgo_rentabilidad_principal.png",
    "docs/figures/thesis_results/primary_04_metric_dashboard.png": "resumen_metricas_principal.png",
    "docs/figures/thesis_results/primary_05_selection_cardinality.png": "numero_etfs_rebalanceo.png",
    "docs/figures/thesis_results/extended_01_equity_curves.png": "evolucion_capital_ampliada.png",
    "docs/figures/thesis_results/combined_06_classification_effectiveness.png": "lectura_categorias_electre.png",
    "docs/figures/thesis_results/combined_07_objective_compliance.png": "cumplimiento_objetivos.png",
    "docs/figures/thesis_system/system_11_component_diagram.png": "componentes_sistema.png",
    "docs/figures/thesis_system/system_13_activity_flow.png": "flujo_trabajo_sistema.png",
}


CITATION_REPLACEMENTS = {
    r"\cite{Xidonas2009}": "(Xidonas, Mavrotas y Psarras, 2009)",
    r"\cite{DeMiguel2009}": "(DeMiguel, Garlappi y Uppal, 2009)",
    r"\cite{Markowitz1952}": "(Markowitz, 1952)",
    r"\cite{SteuerNa2003}": "(Steuer y Na, 2003)",
    r"\cite{Spronk2005,Zopounidis2013}": "(Spronk, Steuer y Zopounidis, 2005; Zopounidis y Doumpos, 2013)",
    r"\cite{Sharpe1964}": "(Sharpe, 1964)",
    r"\cite{BlackLitterman1992}": "(Black y Litterman, 1992)",
    r"\cite{Michaud1998}": "(Michaud, 1998)",
    r"\cite{Emamat2022}": "(Emamat, Mikhailov y Alijamaat, 2022)",
    r"\cite{BransVincke1985,BransMareschal2005}": "(Brans y Vincke, 1985; Brans y Mareschal, 2005)",
    r"\cite{HwangYoon1981}": "(Hwang y Yoon, 1981)",
    r"\cite{Saaty1980}": "(Saaty, 1980)",
    r"\cite{RoyBouyssou1993}": "(Roy y Bouyssou, 1993)",
    r"\cite{Roy1968}": "(Roy, 1968)",
}


CONTENT = r"""
\documentclass[12pt,letterpaper]{article}

\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[spanish,es-tabla]{babel}
\usepackage{mathptmx}
\usepackage[scaled=0.92]{helvet}
\usepackage{geometry}
\usepackage{xcolor}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{amsmath,amssymb}
\usepackage{float}
\usepackage{caption}
\usepackage{fancyhdr}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage{url}
\usepackage{xurl}

\geometry{letterpaper,left=2.54cm,right=2.54cm,top=2.54cm,bottom=2.8cm}
\definecolor{RojoInstitucional}{RGB}{192,0,0}
\graphicspath{{tesis_final_assets/}}
\hypersetup{colorlinks=true, linkcolor=RojoInstitucional, citecolor=RojoInstitucional, urlcolor=RojoInstitucional}

\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}
\setlength{\footskip}{42pt}
\fancyfoot[L]{%
\makebox[0pt][l]{%
\begin{minipage}[t]{\dimexpr\paperwidth-2.85cm\relax}
{\color{RojoInstitucional}\rule{\linewidth}{2.0pt}}\\[-0.1em]
{\sffamily\small Escuela de Ingeniería Industrial}\\[-0.15em]
{\sffamily\small\hspace{1.18cm}\thepage}
\end{minipage}%
}%
}

\titleformat{\section}{\normalfont\bfseries\fontsize{14}{16}\selectfont\color{RojoInstitucional}}{\thesection.}{0.6em}{}
\titleformat{\subsection}{\normalfont\bfseries\fontsize{13}{15}\selectfont\color{RojoInstitucional}}{\thesubsection}{0.6em}{}
\titleformat{\subsubsection}{\normalfont\bfseries\fontsize{12}{14}\selectfont\color{RojoInstitucional}}{\thesubsubsection}{0.6em}{}
\captionsetup{font=small,labelfont=bf,justification=centering}
\setlength{\parindent}{1.25cm}
\setlength{\parskip}{0.35em}
\emergencystretch=2em
\setlist[itemize]{leftmargin=1.2cm}

\newcommand{\fuente}[1]{\begin{center}\small Fuente: #1\end{center}}
\newcommand{\apa}[1]{\begingroup\sloppy\hangindent=1.25cm\hangafter=1 #1\par\vspace{0.35em}\endgroup}

\begin{document}

\begin{titlepage}
\thispagestyle{fancy}
\begin{flushleft}
\includegraphics[width=4.0cm]{logo_univalle.png}
\end{flushleft}
\begin{flushright}
\textcolor{RojoInstitucional}{\sffamily\bfseries Programa de Ingeniería Industrial}\\
\sffamily Informe Práctica Profesional
\end{flushright}
\vspace{0.8cm}
\begin{center}
{\bfseries\color{RojoInstitucional} Modelo Integrado de Optimización Multicriterio para Portafolios de ETFs: Selección y\\ Rebalanceo}\par
\vspace{0.8cm}
Presentado por:\par
\vspace{0.2cm}
{\bfseries Juan Felipe Tamayo Mejía}\par
\vspace{0.6cm}
Directores del trabajo\par
\vspace{0.2cm}
{\bfseries PhD. Diego Fernando Manotas Duque}\par
{\bfseries PhD. Orlando Joaqui Barandica}\par
\vspace{0.6cm}
Escuela de Ingeniería Industrial, Universidad del Valle\par
Diciembre de 2025
\end{center}

\vspace{0.6cm}
\noindent\rule{\textwidth}{0.4pt}
\subsection*{Resumen}
Con miles de \textit{Exchange-Traded Funds} (ETFs) en los mercados financieros, la elaboración de carteras eficientes demanda metodologías sistemáticas que superen los enfoques tradicionales, orientados principalmente a la rentabilidad y al riesgo, y que resultan insuficientes para captar la complejidad multidimensional de este tipo de instrumentos. El presente trabajo tiene como propósito el desarrollo de un modelo integrado de optimización multicriterio, que combine selección sistemática de ETFs aplicando ELECTRE Tri con estrategias de rebalanceo dinámico, y que permita identificar activos elegibles, construir portafolios eficientes y adaptarse a condiciones de mercado cambiantes.

El estudio mantiene el sentido metodológico planteado inicialmente, pero incorpora los hallazgos obtenidos durante el desarrollo del sistema: la validación principal se estructura con datos 2021--2024 para desarrollo y calibración, y 2025 como ventana \textit{out-of-sample}; además, se usa una validación ampliada 2015--2025 como prueba de robustez y no como reemplazo del protocolo aceptado. Los resultados muestran que el sistema construido es funcional, reproducible y útil como herramienta de apoyo a la decisión. Bajo la configuración evaluada no se confirma una superioridad robusta frente a SPY, el portafolio 60/40 ni la equiponderación del universo, por lo cual la contribución principal se ubica en el diseño, implementación y evaluación crítica de una metodología abierta para seleccionar un conjunto preliminar de fondos y luego optimizarlos.

\textbf{Palabras clave:} ETFs, ELECTRE Tri, optimización multicriterio, rebalanceo de portafolios, gestión de riesgo, \textit{backtesting}, Sharpe Ratio.
\end{titlepage}

\tableofcontents
\newpage
\renewcommand{\listfigurename}{Lista de figuras}
\renewcommand{\listtablename}{Lista de tablas}
\listoffigures
\listoftables
\newpage

\section{Situación Problemática}

Los \textit{Exchange-Traded Funds} (ETFs) han transformado fundamentalmente la inversión global desde su introducción en 1993, experimentando un crecimiento que los ha consolidado como instrumentos financieros fundamentales para la democratización del acceso a los mercados financieros. Esta transformación no ha sido casual, pues estos activos surgieron como respuesta a las limitaciones de los fondos mutuos tradicionales, ofreciendo mayor flexibilidad de negociación, menores costos operativos y transparencia en tiempo real sobre sus posiciones. Su estructura única permite a los inversores acceder a mercados completos, sectores específicos o estrategias de inversión sofisticadas con una sola transacción, eliminando barreras tradicionales que limitaban el acceso a la diversificación institucional \cite{Xidonas2009}.

Aunque los ETFs parecen instrumentos simples y fáciles de entender, existe una realidad mucho más compleja detrás de esa apariencia. La aparición de ETFs especializados, temáticos, activos, sectoriales, internacionales y de renta fija ha transformado el panorama, haciendo que la selección del instrumento más adecuado sea un desafío metodológico relevante. Hoy en día, los inversores se enfrentan a decisiones difíciles incluso cuando varios fondos replican exposiciones similares, ya que cada instrumento puede tener metodologías, costos, niveles de liquidez, eficiencia de réplica y estabilidad histórica diferentes. Esto demanda un análisis más detallado y cuidadoso para tomar una decisión que no dependa únicamente de la rentabilidad reciente.

Las optimizaciones de portafolios mal condicionadas pueden generar portafolios con rendimientos por debajo de estrategias muy básicas debido a errores en la estimación de parámetros. Por esta razón, la primera etapa de análisis y selección de valores es de vital importancia \cite{DeMiguel2009}. El problema de evaluar estos vehículos financieros se constituye inherentemente como un problema multicriterio, a diferencia de la optimización media-varianza clásica \cite{Markowitz1952}, que contempla principalmente las dimensiones de retorno esperado y riesgo. En el caso de ETFs, la selección debe considerar múltiples factores de naturaleza diversa: retornos, volatilidades, costos, volúmenes de negociación, liquidez, \textit{tracking error} y \textit{expense ratio}, entre otros.

La naturaleza multidimensional y potencialmente conflictiva de estos criterios hace que los enfoques de optimización uni-objetivo sean insuficientes para capturar la complejidad del problema. Como señalan Steuer y Na \cite{SteuerNa2003}, los enfoques de toma de decisiones multicriterio proporcionan un marco metodológico apropiado para resolver problemas financieros con estas características, permitiendo la incorporación explícita de criterios heterogéneos y el manejo de preferencias que no siempre pueden reducirse a una sola medida. A pesar de la extensa literatura sobre optimización de portafolios y de la creciente aplicación de métodos MCDM en finanzas \cite{Spronk2005,Zopounidis2013}, existe una brecha metodológica significativa en lo que respecta a la selección sistemática de ETFs como clase de activo específica.

En el orden de ideas que deja el trabajo de Xidonas et al. \cite{Xidonas2009}, este proyecto adapta ELECTRE Tri al contexto de fondos cotizados en bolsa, clasificando ETFs en tres grupos según su desempeño multicriterio: excelentes, aceptables y rechazados. La pregunta que orienta el cierre del trabajo puede formularse de la siguiente manera: ¿en qué medida una metodología que combine clasificación multicriterio mediante ELECTRE Tri, optimización y rebalanceo periódico permite construir portafolios de ETFs trazables, reproducibles y competitivos frente a estrategias tradicionales?

\section{Revisión de Literatura (marco de referencia)}

\subsection{Teoría de Portafolios}

La Teoría Moderna de Portafolios de Markowitz \cite{Markowitz1952} estableció los fundamentos conceptuales para la optimización de carteras mediante la minimización de la varianza del portafolio sujeta a un rendimiento esperado objetivo. Su formulación original establece que los inversionistas racionales buscan maximizar el retorno esperado para un nivel dado de riesgo, o equivalentemente minimizar el riesgo para un retorno esperado dado. Esta formulación genera la frontera eficiente de portafolios, sobre la cual ningún portafolio puede mejorar en una dimensión sin empeorar en la otra.

Seguido a este primer acercamiento se desarrollaron nuevas metodologías, tales como el CAPM \cite{Sharpe1964}, la aproximación Black-Litterman \cite{BlackLitterman1992} y la optimización remuestreada de Michaud \cite{Michaud1998}. Estos trabajos mantienen, con distintos niveles de sofisticación, el paradigma inicial bi-objetivo centrado en la relación retorno-riesgo y usualmente asumen que el universo de inversión está predefinido. Sin embargo, en un universo amplio de ETFs esta suposición es delicada, porque la decisión sobre qué activos entran al modelo puede ser tan importante como el método utilizado para asignar pesos.

DeMiguel et al. \cite{DeMiguel2009} demostraron empíricamente que la optimización media-varianza puede tener un rendimiento inferior a una estrategia equiponderada cuando se trabaja con un número elevado de activos y estimaciones inestables. Esta observación resulta fundamental para el presente trabajo, pues justifica la necesidad de una selección previa que reduzca el universo antes de aplicar técnicas de optimización. Desde esta perspectiva, una estrategia metodológica razonable consiste en reducir el universo a un conjunto manejable, disminuyendo el error de estimación y haciendo más interpretable la construcción del portafolio.

\subsection{Estado del Arte en MCDM en Selección de Activos Financieros}

La aplicación de métodos de toma de decisiones multicriterio a problemas financieros tiene más de tres décadas de desarrollo. Steuer y Na \cite{SteuerNa2003} registran una amplia variedad de estudios que combinan MCDM con selección y gestión de portafolios, evaluación de desempeño corporativo, gestión de riesgo y decisiones de inversión. En este campo, los métodos MCDM resultan especialmente útiles cuando los criterios de evaluación son heterogéneos, tienen escalas diferentes o representan objetivos parcialmente conflictivos.

Dentro de esta familia se encuentra ELECTRE Tri, un método de clasificación que asigna alternativas a categorías predefinidas mediante la comparación con perfiles de referencia. La aplicación de Xidonas et al. \cite{Xidonas2009} a la selección de acciones constituye una referencia central para este trabajo, ya que muestra cómo los métodos de \textit{outranking} pueden ser utilizados para construir grupos de activos aceptables y no aceptables con base en criterios financieros. Emamat et al. \cite{Emamat2022} complementan esta línea al comparar ELECTRE Tri y FlowSort en selección de portafolios, reforzando la utilidad de los métodos de clasificación frente a problemas financieros donde no basta con ordenar alternativas de mejor a peor.

PROMETHEE, TOPSIS y AHP aparecen como métodos alternativos relevantes en la literatura. PROMETHEE genera rankings completos mediante flujos de preferencia \cite{BransVincke1985,BransMareschal2005}; TOPSIS ordena alternativas según distancia a una solución ideal \cite{HwangYoon1981}; y AHP estructura decisiones jerárquicas mediante comparaciones pareadas \cite{Saaty1980}. Para el problema tratado, ELECTRE Tri resulta más apropiado porque el objetivo principal no es producir un ranking completo de todos los ETFs, sino clasificar alternativas en categorías que sirvan como filtro para una etapa posterior de optimización.

\begin{longtable}{p{3.2cm}p{3.2cm}p{6.4cm}}
\caption{Autores base que soportan la metodología del trabajo}\label{tab:literatura_base}\\
\toprule
\textbf{Tema} & \textbf{Autor(es)} & \textbf{Aporte para el proyecto} \\
\midrule
Teoría de portafolios & Markowitz; Sharpe; Black y Litterman & Fundamentos de retorno, riesgo, equilibrio y optimización de portafolios. \\
Limitaciones de optimización & DeMiguel, Garlappi y Uppal; Kritzman, Page y Turkington & Discusión sobre error de estimación, equiponderación y necesidad de selección previa. \\
Métodos multicriterio & Roy; Steuer y Na; Zopounidis y Doumpos & Marco general para decisiones con criterios heterogéneos en finanzas. \\
Selección con ELECTRE & Xidonas, Mavrotas y Psarras; Emamat et al. & Referencias directas para adaptar clasificación multicriterio a activos financieros. \\
Mercado de ETFs & Investment Company Institute; Cohen y Del Valle; Vuorela & Contexto reciente sobre crecimiento, diversidad e innovación de los ETFs. \\
\bottomrule
\end{longtable}
\fuente{Elaboración propia a partir de la revisión de literatura del trabajo.}

\section{Objetivos}

La revisión de la literatura presentada en las secciones precedentes permite identificar tanto los avances significativos como las brechas persistentes en la intersección entre teoría de portafolios, metodologías de decisión multicriterio y gestión de inversiones pasivas mediante ETFs. A partir de esta revisión se plantea el siguiente objetivo general, acompañado de tres objetivos específicos.

\textbf{Objetivo general:} Desarrollar un modelo de optimización de portafolios de inversión basado en ETFs mediante análisis multicriterio, considerando rendimiento, volatilidad, Sharpe Ratio, liquidez, \textit{tracking error} y \textit{expense ratio}, que sirva como herramienta de toma de decisiones de inversión.

\textbf{Objetivo específico número uno:} Diseñar e implementar un sistema de clasificación multicriterio que reduzca el universo del mercado estadounidense a un conjunto de 10--25 activos sobre datos del 2021--2024.

\textbf{Objetivo específico número dos:} Analizar el desempeño histórico de los ETFs clasificados como elegibles mediante indicadores financieros clave durante el período 2021--2024, con el propósito de caracterizar sus perfiles de riesgo-retorno y validar la consistencia de la selección multicriterio.

\textbf{Objetivo específico número tres:} Desarrollar e implementar un modelo de optimización de portafolios que busque mejorar la rentabilidad ajustada por riesgo y controlar la exposición al riesgo, con el propósito de construir portafolios eficientes y evaluar empíricamente si el enfoque multicriterio ofrece ventajas frente a estrategias de inversión tradicionales.

La evaluación de los objetivos se realizó con base en evidencia empírica generada por el sistema, no únicamente por la descripción de la herramienta desarrollada. Por esta razón, el cumplimiento se presenta de manera diferenciada entre implementación, validación y limitaciones observadas.

\begin{table}[H]
\centering
\caption{Relación entre objetivos, evidencia obtenida y nivel de cumplimiento}
\label{tab:objetivos_evidencia}
\begin{tabular}{p{3.3cm}p{5.2cm}p{5.2cm}}
\toprule
\textbf{Objetivo} & \textbf{Evidencia desarrollada} & \textbf{Lectura final} \\
\midrule
Objetivo general & Pipeline de clasificación, optimización, rebalanceo y reportes de validación. & Cumplimiento parcial: rendimiento, volatilidad, Sharpe y liquidez fueron cubiertos; \textit{tracking error} y \textit{expense ratio} quedan como brecha de datos. \\
Objetivo específico 1 & Clasificación ELECTRE y selección por fecha de rebalanceo. & Implementado, pero no cerrado operacionalmente: la selección promedio quedó por debajo del rango 10--25. \\
Objetivo específico 2 & Métricas históricas, diagnósticos por categoría y lectura ordinal de ELECTRE. & Cumplimiento parcial: hay señal en la prueba principal, pero la robustez ampliada es limitada. \\
Objetivo específico 3 & Estrategias de asignación, backtesting y comparación con SPY, 60/40 y universo equiponderado. & No se valida superioridad robusta; se valida la capacidad del sistema para contrastar la hipótesis de forma reproducible. \\
\bottomrule
\end{tabular}
\end{table}
\fuente{Elaboración propia con base en los resultados del sistema.}

\section{Metodología}

Se adoptó una metodología empírica basada en análisis cuantitativo de datos financieros históricos y en la implementación práctica de modelos de optimización. De esta manera se permite validar las teorías financieras trabajadas en este escrito usando datos de mercado reales, tangibles y observables. El diseño metodológico está basado en Xidonas et al. \cite{Xidonas2009}, Roy y Bouyssou \cite{RoyBouyssou1993}, DeMiguel et al. \cite{DeMiguel2009} y Markowitz \cite{Markowitz1952}, adaptando estas metodologías al contexto específico de ETFs como clase de activo.

La investigación adopta un enfoque cuantitativo-empírico con diseño experimental y validación \textit{out-of-sample}, orientado al desarrollo, implementación y validación de una metodología de decisión multicriterio basada en ELECTRE Tri para la selección de ETFs y construcción de portafolios. El protocolo principal utiliza 2021--2024 como período de desarrollo y calibración, y 2025 como ventana de validación empírica. Adicionalmente, se realizó una validación ampliada 2015--2025 para revisar robustez temporal, sensibilidad a cambios de régimen y comportamiento fuera del período principal.

\begin{table}[H]
\centering
\caption{Lectura temporal del protocolo de validación}
\label{tab:protocolo_temporal}
\begin{tabular}{p{3.5cm}p{5.2cm}p{5.2cm}}
\toprule
\textbf{Período} & \textbf{Uso dentro del trabajo} & \textbf{Interpretación de resultados} \\
\midrule
2021--2024 & Desarrollo, calibración de criterios, perfiles y reglas de clasificación. & No debe interpretarse como validación independiente. \\
2025 & Ventana \textit{out-of-sample} para evaluar decisiones no usadas en la calibración inicial. & Evidencia principal de validación empírica del protocolo aceptado. \\
2021--2025 & Ejecución principal reportada por el sistema, con separación de desarrollo y evaluación. & Se presenta como resultado agregado de la prueba principal, aclarando la función de cada tramo. \\
2015--2025 & Validación ampliada para robustez temporal y cambios de régimen. & No reemplaza el protocolo aceptado; sirve para evaluar estabilidad y sensibilidad. \\
\bottomrule
\end{tabular}
\end{table}
\fuente{Elaboración propia.}

\subsection{Primera Fase: Adquisición, Preparación y Análisis Exploratorio de Datos}

La primera fase consistió en la recopilación y análisis cuantitativo de los datos históricos disponibles. Se trabajó con precios diarios y volúmenes de negociación, construyendo paneles de cierre y volumen a partir de la base local \texttt{price\_ohlcv.parquet}. Estos paneles contienen 296 tickers y 2765 fechas, con cobertura desde 2015 hasta el cierre de la ventana de validación de 2025 en la base consolidada del proyecto. Para los experimentos finales se utilizó un universo público aproximado \textit{point-in-time}, lo cual reduce parcialmente el sesgo frente a un universo estático, aunque no constituye evidencia institucional completamente libre de \textit{survivorship bias}. Los filtros operativos aplicados exigieron cobertura mínima de datos de 80\%, frecuencia de rebalanceo trimestral y costos aproximados de transacción de 10 puntos básicos.

\subsection{Segunda Fase: Selección Multicriterio mediante ELECTRE Tri}

La segunda fase realiza la selección de los ETFs por medio de un modelo multicriterio. Se implementaron métricas empíricas calculadas directamente desde datos históricos: rentabilidad anual compuesta, volatilidad anualizada, Sharpe Ratio y liquidez. El modelo también contempla \textit{tracking error} y \textit{expense ratio}; sin embargo, las ejecuciones empíricas no contaron con cobertura completa para estos dos criterios, por lo que se reportan como brechas de datos y no como resultados plenamente validados.

Las principales métricas usadas se calcularon de la siguiente manera. Si $P_t$ representa el precio de cierre del ETF en el día $t$, el retorno simple diario se define como:

\begin{equation}
r_t = \frac{P_t - P_{t-1}}{P_{t-1}}.
\label{eq:retorno_diario}
\end{equation}

El crecimiento anual compuesto para una ventana con valor inicial $P_0$, valor final $P_T$ y $n$ años de duración se expresa como:

\begin{equation}
CAGR = \left(\frac{P_T}{P_0}\right)^{1/n} - 1.
\label{eq:cagr}
\end{equation}

La volatilidad anualizada se calcula a partir de la desviación estándar de los retornos diarios, multiplicando por la raíz del número aproximado de días de negociación del año:

\begin{equation}
\sigma_{anual} = \sigma(r_t)\sqrt{252}.
\label{eq:volatilidad}
\end{equation}

El Sharpe Ratio se calcula como la relación entre el exceso de retorno y la volatilidad anualizada:

\begin{equation}
Sharpe = \frac{R_p - R_f}{\sigma_p}.
\label{eq:sharpe}
\end{equation}

Cuando se dispone del retorno del índice de referencia, el \textit{tracking error} se calcula como la desviación estándar anualizada de la diferencia entre los retornos del ETF y su referencia:

\begin{equation}
TE = \sigma(r_{ETF,t} - r_{B,t})\sqrt{252}.
\label{eq:tracking_error}
\end{equation}

En ELECTRE Tri, cada alternativa $a$ se compara contra perfiles de referencia $b_h$. La concordancia global resume qué tanto la alternativa respalda la afirmación de que $a$ supera o alcanza un perfil determinado:

\begin{equation}
C(a,b_h) = \sum_{j=1}^{m} w_j c_j(a,b_h), \qquad \sum_{j=1}^{m} w_j = 1.
\label{eq:concordancia}
\end{equation}

La concordancia parcial $c_j(a,b_h)$ compara el desempeño de la alternativa contra el perfil de referencia para cada criterio, considerando umbrales de indiferencia y preferencia. De manera simplificada, un criterio aporta mayor concordancia cuando la diferencia entre la alternativa y el perfil favorece claramente a la alternativa, aporta concordancia intermedia cuando la diferencia es pequeña, y aporta baja concordancia cuando el perfil supera a la alternativa.

La discordancia se activa cuando un criterio presenta una desventaja suficientemente fuerte como para cuestionar la asignación favorable de la alternativa. Para cada criterio se define un umbral de veto $v_j$, que permite controlar casos donde un ETF tiene buen desempeño general, pero falla de forma marcada en una dimensión crítica como volatilidad, liquidez o costos. La credibilidad de la relación de sobreclasificación puede expresarse, de forma resumida, como una concordancia global ajustada por posibles discordancias:

\begin{equation}
\sigma(a,b_h) = C(a,b_h) \prod_{j \in D(a,b_h)} \frac{1-d_j(a,b_h)}{1-C(a,b_h)}.
\label{eq:credibilidad}
\end{equation}

Donde $D(a,b_h)$ representa el conjunto de criterios en los que la discordancia supera la concordancia global. A partir de esta credibilidad y de un nivel de corte, ELECTRE Tri asigna cada ETF a una categoría ordenada. En el sistema desarrollado se utilizó la asignación pesimista como configuración principal, ya que resulta más conservadora para seleccionar activos destinados a un portafolio.

La clasificación final se obtiene a partir de la combinación de concordancia, discordancia y umbrales de credibilidad, siguiendo la lógica de \textit{outranking} desarrollada por Roy \cite{Roy1968} y aplicada en selección financiera por Xidonas et al. \cite{Xidonas2009}. Esta metodología fue seleccionada por su capacidad para manejar criterios heterogéneos sin requerir su agregación forzada en una función de utilidad única.

\begin{table}[H]
\centering
\caption{Criterios de evaluación utilizados para clasificar los ETFs}
\label{tab:criterios_evaluacion}
\begin{tabular}{p{7cm}p{3cm}p{4cm}}
\toprule
\textbf{Criterio de evaluación} & \textbf{Peso base} & \textbf{Sentido esperado} \\
\midrule
Rentabilidad anual compuesta & 25\% & Mayor es mejor \\
Sharpe Ratio & 20\% & Mayor es mejor \\
Volatilidad anualizada & 15\% & Menor es mejor \\
Liquidez & 15\% & Mayor es mejor \\
Tracking error & 15\% & Menor es mejor \\
Expense ratio & 10\% & Menor es mejor \\
\bottomrule
\end{tabular}
\end{table}
\fuente{Construido por el autor a partir de la propuesta metodológica del trabajo.}

\subsection{Tercera Fase: Optimización de Portafolios y Estrategias de Rebalanceo}

Después de clasificar los ETFs, se construyen portafolios con estrategias de asignación de pesos. En una estrategia equiponderada con $N$ activos seleccionados, cada ETF recibe el mismo peso:

\begin{equation}
w_i = \frac{1}{N}, \qquad i=1,2,\ldots,N.
\label{eq:equal_weight}
\end{equation}

El retorno del portafolio en cada período se calcula como la suma ponderada de los retornos de sus activos:

\begin{equation}
R_{p,t} = \sum_{i=1}^{N} w_i r_{i,t}.
\label{eq:retorno_portafolio}
\end{equation}

Para la estrategia de mínima varianza, el problema se expresa como:

\begin{equation}
\min_{w} \; w'\Sigma w
\quad \text{sujeto a} \quad
\sum_{i=1}^{N} w_i = 1, \; w_i \geq 0.
\label{eq:minvar}
\end{equation}

En la variante MaxSharpe se busca maximizar el retorno ajustado por riesgo del portafolio, sujeto igualmente a pesos no negativos y suma de pesos igual a uno. Esta variante se conservó como comparación experimental, aunque en los resultados finales no fue el motor más sólido de desempeño. El rebalanceo se ejecutó de manera trimestral, con deriva de pesos tipo \textit{buy and hold} entre fechas de rebalanceo y costos de transacción aproximados de 10 puntos básicos.

\begin{table}[H]
\centering
\caption{Parámetros principales usados en la implementación}
\label{tab:parametros_implementacion}
\begin{tabular}{p{5cm}p{8cm}}
\toprule
\textbf{Elemento} & \textbf{Configuración usada} \\
\midrule
Frecuencia de rebalanceo & Trimestral, siguiendo calendario de evaluación. \\
Asignación ELECTRE & Procedimiento pesimista como configuración principal. \\
Cobertura mínima de datos & 80\% de observaciones disponibles en la ventana evaluada. \\
Costos de transacción & 10 puntos básicos por operación como aproximación conservadora. \\
Restricciones de pesos & Suma de pesos igual a uno y posiciones largas, sin ventas en corto. \\
Benchmarks & SPY, portafolio 60/40 SPY-BND, universo equiponderado, mínima varianza y MaxSharpe. \\
\bottomrule
\end{tabular}
\end{table}
\fuente{Elaboración propia a partir de la configuración experimental.}

\subsection{Cuarta Fase: Validación Empírica y Análisis de Resultados}

La cuarta fase se concentró en validar los resultados obtenidos del modelo. La implementación del \textit{backtesting} respetó el principio de no anticipación, asegurando que cada decisión se basara únicamente en información disponible hasta el punto de evaluación correspondiente. Los resultados se compararon contra estrategias conocidas: SPY, un portafolio 60/40 SPY-BND, equiponderación del universo, mínima varianza y MaxSharpe.

Es importante resaltar que la validación no se utilizó para forzar una lectura favorable del modelo, sino para establecer con claridad qué fue validado y qué no. En la corrida principal 2021--2025, la estrategia ELECTRE equiponderada obtuvo resultados positivos, pero no superó a SPY ni al portafolio 60/40 en Sharpe Ratio. En la validación ampliada 2015--2025, la estrategia también quedó por debajo de los principales referentes. Por lo tanto, el resultado final sostiene la utilidad metodológica del sistema, pero no una superioridad empírica definitiva frente a estrategias tradicionales.

\section{Cronograma de Proyecto}

\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{figura_gantt.png}
\caption{Diagrama de Gantt del desarrollo del trabajo}
\label{fig:gantt}
\end{figure}
\fuente{Elaboración propia.}

El desarrollo se estructuró en cuatro fases secuenciales: adquisición y preparación de datos, selección multicriterio, optimización y rebalanceo, y validación empírica con análisis de resultados. Como complemento a estas fases se incorporaron actividades de trazabilidad, generación de figuras, documentación de limitaciones y reportes de cumplimiento de objetivos, ya que estas evidencias permiten presentar el trabajo de manera más verificable frente a evaluadores.

\section{Alcance y Limitaciones}

El trabajo de grado se limita a un universo específico de activos financieros, siendo estos ETFs listados y negociados en el mercado estadounidense. El modelo contempla posiciones largas, rebalanceo periódico y estrategias de portafolio adecuadas para un inversionista con horizonte de mediano o largo plazo. No se consideran ventas en corto, opciones, apalancamiento operativo, impuestos, ejecución real de órdenes ni asesoría financiera personalizada.

La principal limitación del trabajo corresponde a la disponibilidad y calidad de los datos. Los experimentos finales utilizan un universo público aproximado \textit{point-in-time}; esta aproximación mejora la trazabilidad frente a un universo completamente estático, pero no equivale a una base institucional libre de sesgo de supervivencia. Adicionalmente, aunque el objetivo general contempla \textit{tracking error} y \textit{expense ratio}, las ejecuciones empíricas no contaron con cobertura completa para estos criterios, por lo cual el cumplimiento del objetivo general se considera parcial.

Otra limitación relevante es la cardinalidad de la selección. El objetivo específico número uno plantea reducir el universo a un conjunto de 10--25 activos; sin embargo, en los experimentos finales la selección promedio por rebalanceo fue inferior a ese rango. En la prueba principal se obtuvo un promedio de 4.43 activos seleccionados por rebalanceo, mientras que en la validación ampliada el promedio fue de 5.29. Esta brecha no invalida la implementación del clasificador, pero sí impide afirmar que el objetivo operacional de cardinalidad quedó completamente satisfecho.

\section{Implementación del Sistema de Clasificación Multicriterio}

El desarrollo del sistema de clasificación multicriterio mediante ELECTRE Tri constituye el centro metodológico del primer objetivo específico de esta investigación. La implementación se fundamenta en la adaptación de la metodología propuesta por Xidonas et al. \cite{Xidonas2009} al mercado específico de ETFs, considerando las particularidades estructurales y operativas de estos instrumentos financieros que los diferencian de las acciones individuales tradicionalmente analizadas en la literatura MCDM.

La arquitectura del sistema se organizó como un flujo de trabajo en Python compuesto por módulos de datos, cálculo de características, clasificación, optimización, validación y reporte. Entre los componentes más relevantes se encuentran el cálculo de métricas financieras, la integración del pipeline de selección, la validación de cumplimiento de objetivos, el corredor experimental y la generación automática de figuras. Esta estructura permite separar la clasificación ELECTRE de la asignación de pesos, evitando confundir el método multicriterio con un optimizador de portafolios.

\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{componentes_sistema.png}
\caption{Organización general del sistema implementado}
\label{fig:componentes}
\end{figure}
\fuente{Elaboración propia a partir de la implementación en Python.}

\subsection{Definición de Categorías y Umbrales de Clasificación}

Se siguen los lineamientos de la metodología ELECTRE Tri, donde se determinan a priori categorías de clasificación. En este caso se establecieron tres categorías ordenadas que reflejan la calidad relativa de los ETFs en el universo de análisis: excelentes, aceptables y rechazados. Estas categorías permiten que el resultado del modelo sea interpretable y conectable con la etapa posterior de construcción del portafolio.

\begin{table}[H]
\centering
\caption{Categorías usadas para interpretar la clasificación ELECTRE}
\label{tab:categorias_electre}
\begin{tabular}{p{4cm}p{9cm}}
\toprule
\textbf{Categoría} & \textbf{Interpretación dentro del modelo} \\
\midrule
Excelentes & ETFs que superan los estándares multicriterio definidos y se consideran candidatos principales para el portafolio. \\
Aceptables & ETFs con desempeño razonable, pero no necesariamente superior en todos los criterios. \\
Rechazados & ETFs que no cumplen los estándares mínimos de calidad, liquidez, riesgo o eficiencia definidos para la selección. \\
\bottomrule
\end{tabular}
\end{table}
\fuente{Construido por el autor con base en ELECTRE Tri.}

\subsection{Resultados obtenidos durante la implementación}

La ejecución principal se realizó sobre el período 2021--2025, conservando la separación conceptual entre desarrollo 2021--2024 y validación 2025. La estrategia ELECTRE equiponderada obtuvo un CAGR agregado de 12.88\%, Sharpe Ratio de 1.198 y máximo \textit{drawdown} de -7.54\%. Aunque este resultado es positivo en términos absolutos, queda por debajo de SPY y del portafolio 60/40 en desempeño ajustado por riesgo. Por esta razón, el resultado debe leerse como evidencia de funcionamiento y comparación reproducible del sistema, no como confirmación de superioridad del enfoque multicriterio.

\begin{table}[H]
\centering
\caption{Resultados principales de la prueba 2021--2025}
\label{tab:resultados_principales}
\begin{tabular}{p{5.0cm}rrr}
\toprule
\textbf{Estrategia} & \textbf{CAGR} & \textbf{Sharpe} & \textbf{Caída máxima} \\
\midrule
ELECTRE equiponderado & 12.88\% & 1.198 & -7.54\% \\
ELECTRE mínima varianza & 12.47\% & 1.236 & -6.56\% \\
ELECTRE MaxSharpe & 10.97\% & 1.034 & -7.62\% \\
SPY comprar y mantener & 23.32\% & 1.932 & -7.58\% \\
Portafolio 60/40 SPY-BND & 15.85\% & 1.964 & -3.80\% \\
Universo equiponderado & 11.98\% & 1.695 & -3.48\% \\
\bottomrule
\end{tabular}
\end{table}
\fuente{Elaboración propia con base en los resultados generados por el sistema.}

\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{evolucion_capital_principal.png}
\caption{Evolución del capital en la prueba principal}
\label{fig:capital_principal}
\end{figure}
\fuente{Elaboración propia.}

\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{caidas_prueba_principal.png}
\caption{Caídas acumuladas durante la prueba principal}
\label{fig:caidas_principal}
\end{figure}
\fuente{Elaboración propia.}

\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{riesgo_rentabilidad_principal.png}
\caption{Relación entre riesgo y rentabilidad en la prueba principal}
\label{fig:riesgo_rentabilidad}
\end{figure}
\fuente{Elaboración propia.}

\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{numero_etfs_rebalanceo.png}
\caption{Número de ETFs seleccionados en cada rebalanceo}
\label{fig:cardinalidad}
\end{figure}
\fuente{Elaboración propia.}

\subsection{Validación ampliada y lectura de robustez}

La validación ampliada 2015--2025 se ejecutó para revisar la estabilidad del enfoque fuera del período principal. En esta prueba, ELECTRE equiponderado obtuvo un CAGR de 3.78\%, Sharpe Ratio de 0.332 y caída máxima de -20.45\%, quedando por debajo de SPY, del portafolio 60/40 y del universo equiponderado. Esta lectura confirma que la metodología construida es útil para evaluar y documentar decisiones, pero que su configuración actual no demuestra una ventaja robusta frente a estrategias simples.

\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{evolucion_capital_ampliada.png}
\caption{Comportamiento de las estrategias en la validación ampliada}
\label{fig:capital_ampliada}
\end{figure}
\fuente{Elaboración propia.}

\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{lectura_categorias_electre.png}
\caption{Lectura de las categorías ELECTRE frente al desempeño posterior}
\label{fig:categorias}
\end{figure}
\fuente{Elaboración propia.}

\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{cumplimiento_objetivos.png}
\caption{Estado de cumplimiento de los objetivos del trabajo}
\label{fig:cumplimiento}
\end{figure}
\fuente{Elaboración propia.}

\subsection{Cierre de implementación y trabajo futuro}

El proyecto permitió desarrollar un sistema funcional de clasificación, optimización y validación de portafolios de ETFs. Como parte de la validación técnica, el sistema fue evaluado mediante pruebas automatizadas y los resultados principales quedaron documentados en métricas, curvas de capital, caídas, selección por rebalanceo y cumplimiento de objetivos. En conjunto, la evidencia permite sostener que la contribución principal del trabajo es metodológica y diagnóstica: se valida un proceso reproducible para evaluar portafolios de ETFs mediante selección multicriterio, aunque bajo la configuración evaluada se rechaza la hipótesis de superioridad robusta frente a los benchmarks tradicionales.

Como trabajo futuro se recomienda completar la integración de \textit{tracking error} y \textit{expense ratio} con fuentes confiables, activar una regla final de cardinalidad que garantice entre 10 y 25 ETFs por rebalanceo, fortalecer los grupos comparables dentro de ELECTRE Tri, mejorar el manejo de restricciones de exposición y construir una arquitectura de datos regulatoria enriquecida con fuentes como SEC N-PORT, N-CEN, EDGAR y OpenFIGI. Estas mejoras permitirían cerrar las principales brechas que quedaron documentadas durante la implementación.

\section{Bibliografía}
\label{sec:bibliografia}

\apa{Albadvi, A., Chaharsooghi, S. K., \& Esfahanipour, A. (2006). Decision making in stock trading: An application of PROMETHEE. \textit{European Journal of Operational Research, 177}(2), 673--683. https://doi.org/10.1016/j.ejor.2005.11.022}

\apa{Ballestero, E., Bravo, M., Pérez-Gladish, B., Arenas-Parra, M., \& Plà-Santamaria, D. (2012). Socially responsible investment: A multicriteria approach to portfolio selection combining ethical and financial objectives. \textit{European Journal of Operational Research, 216}(2), 487--494. https://doi.org/10.1016/j.ejor.2011.07.011}

\apa{Black, F., \& Litterman, R. (1992). Global portfolio optimization. \textit{Financial Analysts Journal}.}

\apa{Brans, J. P., \& Mareschal, B. (2005). PROMETHEE methods. En J. Figueira, S. Greco, \& M. Ehrgott (Eds.), \textit{Multiple criteria decision analysis: State of the art surveys}.}

\apa{Brans, J. P., \& Vincke, P. (1985). A preference ranking organisation method. \textit{Management Science, 31}(6), 647--656. https://doi.org/10.1287/mnsc.31.6.647}

\apa{Cohen, S., \& Del Valle, J. (2025). \textit{Decoding active ETFs: How the growth of active ETFs is unlocking innovation and opportunity for investors}. BlackRock.}

\apa{DeMiguel, V., Garlappi, L., \& Uppal, R. (2009). Optimal versus naive diversification: How inefficient is the 1/N portfolio strategy? \textit{The Review of Financial Studies}.}

\apa{Elton, E. J., Gruber, M. J., Brown, S. J., \& Goetzmann, W. N. (2014). \textit{Modern portfolio theory and investment analysis} (9th ed.).}

\apa{Emamat, M. S. M. M., Mikhailov, L., \& Alijamaat, A. (2022). Using ELECTRE Tri and FlowSort methods in stock portfolio selection.}

\apa{Hwang, C.-L., \& Yoon, K. (1981). Methods for multiple attribute decision making. En \textit{Multiple attribute decision making} (pp. 58--191). Springer. https://doi.org/10.1007/978-3-642-48318-9\_3}

\apa{Investment Company Institute. (2025). \textit{Investment Company Fact Book: A review of trends and activities in the investment company industry}.}

\apa{Kritzman, M., Page, S., \& Turkington, D. (2010). In defense of optimization: The fallacy of 1/N. \textit{Financial Analysts Journal}.}

\apa{Ledoit, O., \& Wolf, M. (2004). A well-conditioned estimator for large-dimensional covariance matrices. \textit{Journal of Multivariate Analysis, 88}(2), 365--411.}

\apa{López de Prado, M. (2016). Building diversified portfolios that outperform out of sample.}

\apa{Markowitz, H. (1952). Portfolio selection. \textit{The Journal of Finance}.}

\apa{Markowitz, H. (1959). \textit{Portfolio selection: Efficient diversification of investments}.}

\apa{Michaud, R. O. (1998). \textit{Efficient asset management}.}

\apa{Pendaraki, K., Zopounidis, C., \& Doumpos, M. (2005). On the construction of mutual fund portfolios: A multicriteria methodology and an application to the Greek market of equity mutual funds. \textit{European Journal of Operational Research, 163}(2), 462--481. https://doi.org/10.1016/j.ejor.2003.10.022}

\apa{Roy, B. (1968). Classement et choix en présence de points de vue multiples: La méthode ELECTRE. \textit{Revue française d'informatique et de recherche opérationnelle, 2}(8), 57--75. https://doi.org/10.1051/ro/196802V100571}

\apa{Roy, B. (1993). Decision science or decision-aid science? \textit{European Journal of Operational Research}.}

\apa{Roy, B., \& Bouyssou, D. (1993). \textit{Aide multicritère à la décision: Méthodes et cas}.}

\apa{Saaty, T. L. (1980). \textit{The analytic hierarchy process}.}

\apa{Sharpe, W. F. (1964). Capital asset prices: A theory of market equilibrium under conditions of risk. \textit{The Journal of Finance}.}

\apa{Spronk, J., Steuer, R. E., \& Zopounidis, C. (2005). Multicriteria decision aid/analysis in finance.}

\apa{Steuer, R. E., \& Na, P. (2003). Multiple criteria decision making combined with finance: A categorized bibliographic study.}

\apa{Tiryaki, F., \& Ahlatcioglu, B. (2009). Fuzzy portfolio selection using fuzzy analytic hierarchy process.}

\apa{Tsalikis, E., \& Papadopoulos, S. (2019). ETFs: Performance, tracking errors and their determinants in Europe and the USA.}

\apa{Vuorela, T. (2024). Assessing the impact of AI-managed ETFs on investment performance and risk compared to benchmark index.}

\apa{Xidonas, P., Mavrotas, G., \& Psarras, J. (2009). A multicriteria methodology for equity selection using financial analysis.}

\apa{Zopounidis, C., \& Doumpos, M. (2013). Multicriteria decision systems for financial problems.}

\begin{thebibliography}{99}
\bibitem{Albadvi2006} Albadvi, A., Chaharsooghi, S. K., \& Esfahanipour, A. (2006).
\bibitem{Ballestero2012} Ballestero, E., Bravo, M., Pérez-Gladish, B., Arenas-Parra, M., \& Plà-Santamaria, D. (2012).
\bibitem{BlackLitterman1992} Black, F., \& Litterman, R. (1992).
\bibitem{BransMareschal2005} Brans, J. P., \& Mareschal, B. (2005).
\bibitem{BransVincke1985} Brans, J. P., \& Vincke, P. (1985).
\bibitem{CohenDelValle2025} Cohen, S., \& Del Valle, J. (2025).
\bibitem{DeMiguel2009} DeMiguel, V., Garlappi, L., \& Uppal, R. (2009).
\bibitem{Elton2014} Elton, E. J., Gruber, M. J., Brown, S. J., \& Goetzmann, W. N. (2014).
\bibitem{Emamat2022} Emamat, M. S. M. M., Mikhailov, L., \& Alijamaat, A. (2022).
\bibitem{HwangYoon1981} Hwang, C.-L., \& Yoon, K. (1981).
\bibitem{ICI2025} Investment Company Institute. (2025).
\bibitem{Kritzman2010} Kritzman, M., Page, S., \& Turkington, D. (2010).
\bibitem{LedoitWolf2004} Ledoit, O., \& Wolf, M. (2004).
\bibitem{LopezDePrado2016} López de Prado, M. (2016).
\bibitem{Markowitz1952} Markowitz, H. (1952).
\bibitem{Markowitz1959} Markowitz, H. (1959).
\bibitem{Michaud1998} Michaud, R. O. (1998).
\bibitem{Pendaraki2005} Pendaraki, K., Zopounidis, C., \& Doumpos, M. (2005).
\bibitem{Roy1968} Roy, B. (1968).
\bibitem{Roy1993} Roy, B. (1993).
\bibitem{RoyBouyssou1993} Roy, B., \& Bouyssou, D. (1993).
\bibitem{Saaty1980} Saaty, T. L. (1980).
\bibitem{Sharpe1964} Sharpe, W. F. (1964).
\bibitem{Spronk2005} Spronk, J., Steuer, R. E., \& Zopounidis, C. (2005).
\bibitem{SteuerNa2003} Steuer, R. E., \& Na, P. (2003).
\bibitem{Tiryaki2009} Tiryaki, F., \& Ahlatcioglu, B. (2009).
\bibitem{Tsalikis2019} Tsalikis, E., \& Papadopoulos, S. (2019).
\bibitem{Vuorela2024} Vuorela, T. (2024).
\bibitem{Xidonas2009} Xidonas, P., Mavrotas, G., \& Psarras, J. (2009).
\bibitem{Zopounidis2013} Zopounidis, C., \& Doumpos, M. (2013).
\end{thebibliography}

\end{document}
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)

    missing: list[str] = []
    for src, dest in ASSETS.items():
        src_path = Path(src)
        if src_path.exists():
            shutil.copy2(src_path, ASSET_DIR / dest)
        else:
            missing.append(src)

    content = CONTENT.strip() + "\n"
    for old, new in CITATION_REPLACEMENTS.items():
        content = content.replace(old, new)
    if "\\begin{thebibliography}" in content:
        before, rest = content.split("\\begin{thebibliography}", 1)
        _, after = rest.split("\\end{thebibliography}", 1)
        content = before.rstrip() + "\n" + after.lstrip()
    OUT_TEX.write_text(content, encoding="utf-8")
    print(f"Wrote {OUT_TEX}")
    print(f"Copied {len(ASSETS) - len(missing)} assets to {ASSET_DIR}")
    if missing:
        print("Missing assets:")
        for item in missing:
            print(f"- {item}")


if __name__ == "__main__":
    main()
