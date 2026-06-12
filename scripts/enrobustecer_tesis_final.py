"""Expand the final thesis LaTeX with a fuller argumentative development.

This script is intentionally applied after `build_tesis_final_latex.py` so the
base document remains reproducible while the final defense version keeps the
original titles and visual identity but has a more gradual academic development.
"""

from __future__ import annotations

from pathlib import Path


TEX = Path("docs/deliverables/tesis_final_tamayo_etf_electre.tex")


SITUACION_EXTRA = r"""

Desde la mirada de la Ingeniería Industrial, esta situación problemática puede entenderse como un proceso de decisión con exceso de alternativas, información incompleta y múltiples criterios de desempeño. No se trata únicamente de escoger el ETF que tuvo mejor rentabilidad en el pasado, sino de estructurar un procedimiento que permita filtrar, comparar, priorizar y validar alternativas de forma consistente. Cuando el proceso de selección se realiza de manera manual o con rankings aislados, se incrementa el riesgo de construir portafolios poco trazables, dependientes de preferencias subjetivas o excesivamente sensibles a un solo indicador financiero.

Esta situación genera ineficiencias concretas para el inversionista y para el analista. En primer lugar, se pierde tiempo revisando instrumentos que no cumplen condiciones mínimas de liquidez, estabilidad o eficiencia de costos. En segundo lugar, se corre el riesgo de seleccionar activos por comportamiento reciente sin evaluar si ese desempeño se sostuvo bajo distintas condiciones de mercado. En tercer lugar, al llevar un universo demasiado amplio directamente a un modelo de optimización, se pueden amplificar errores de estimación en retornos esperados y covarianzas, generando soluciones matemáticamente óptimas pero financieramente poco robustas. Por esta razón, el problema no es solamente financiero; también es un problema de diseño de proceso, control de información y toma de decisiones bajo múltiples criterios.

La Ingeniería Industrial ofrece herramientas adecuadas para analizar este tipo de situaciones porque combina modelación cuantitativa, análisis de sistemas, optimización, evaluación multicriterio y validación de procesos. En este trabajo, dichas herramientas se aplican al problema de selección y rebalanceo de portafolios de ETFs, proponiendo una metodología que organiza el flujo de decisión desde la adquisición de datos hasta la comparación empírica frente a estrategias tradicionales. De esta manera, el aporte del proyecto no se limita al cálculo de indicadores financieros, sino que consiste en construir un procedimiento ordenado, reproducible y auditable para apoyar una decisión que normalmente se aborda de manera fragmentada.

El fenómeno estudiado también tiene una dimensión de control y seguimiento. Un portafolio de ETFs no permanece estable en el tiempo: sus retornos cambian, sus volatilidades se modifican, las correlaciones entre activos se alteran y las condiciones de liquidez pueden variar según el régimen de mercado. Por ello, una metodología de selección inicial debe conectarse con una estrategia de rebalanceo y con una validación fuera de muestra. Si la selección multicriterio no se evalúa posteriormente mediante \textit{backtesting}, no es posible distinguir entre un conjunto de activos que luce atractivo en el período de calibración y una estrategia que realmente conserva utilidad bajo información nueva.

En consecuencia, el trabajo propone una solución aplicada que integra tres momentos. Primero, la clasificación multicriterio reduce el universo amplio de ETFs a grupos interpretables. Segundo, la optimización y asignación de pesos convierten la selección en portafolios implementables. Tercero, la validación empírica compara esos portafolios contra referentes tradicionales, permitiendo aceptar, matizar o rechazar la hipótesis de mejora. Esta lógica gradual es la que permite pasar de la situación problemática inicial a un sistema evaluable, con resultados que pueden ser defendidos incluso cuando no todos los objetivos se cumplen de forma total.
"""


MARCO_EXTRA = r"""

\subsection{Métodos de \textit{Outranking}: ELECTRE y PROMETHEE}

Los métodos de \textit{outranking} se fundamentan en la construcción de relaciones de preferencia entre alternativas, sin exigir que todos los criterios se reduzcan necesariamente a una función de utilidad única. Esta característica es relevante para el problema de ETFs porque los criterios considerados no tienen la misma naturaleza: algunos se desean maximizar, como la rentabilidad o la liquidez; otros se desean minimizar, como la volatilidad, el \textit{tracking error} o los costos operativos. Adicionalmente, un ETF puede ser fuerte en un criterio y débil en otro, lo cual hace inconveniente depender únicamente de un promedio ponderado simple.

ELECTRE Tri pertenece a esta familia de métodos y se utiliza como una herramienta de clasificación. A diferencia de otros enfoques que producen un ranking completo, ELECTRE Tri asigna cada alternativa a categorías previamente definidas mediante la comparación con perfiles de referencia. Esta lógica coincide con el propósito del presente trabajo: no se busca ordenar todos los ETFs disponibles del mejor al peor, sino identificar un grupo de activos suficientemente elegibles para pasar a una etapa posterior de construcción de portafolio. La existencia de categorías como excelentes, aceptables y rechazados permite comunicar mejor el resultado y evita una falsa precisión en diferencias pequeñas entre alternativas.

PROMETHEE también ha sido utilizado en problemas financieros y ofrece una lógica de preferencia más orientada al ranking completo de alternativas. Su ventaja principal es que produce una ordenación clara y relativamente intuitiva; sin embargo, para el problema abordado en este trabajo, la clasificación por categorías resulta más natural que un ranking total. Esto se debe a que el portafolio final no se construye necesariamente con el ETF número uno, dos o tres del ranking, sino con un conjunto diversificado de activos que cumplen criterios mínimos y que posteriormente son ponderados por una estrategia de asignación.

\subsection{Métodos de Programación por Metas}

La programación por metas constituye otra familia de métodos útil cuando el decisor puede establecer niveles de aspiración para varios objetivos simultáneamente. En selección de portafolios, por ejemplo, podría definirse una meta mínima de rentabilidad, una meta máxima de volatilidad, un rango de número de activos y restricciones de exposición sectorial. El modelo buscaría minimizar las desviaciones respecto a estas metas, priorizando aquellas que el decisor considere más importantes.

Aunque esta aproximación es atractiva, requiere definir de forma explícita niveles de aspiración para cada criterio. En el contexto del presente trabajo, el uso de ELECTRE Tri resulta más conveniente porque permite trabajar con perfiles de referencia y categorías de calidad sin convertir el problema en una sola función de desviaciones. No obstante, la idea de metas se conserva de manera indirecta en el proyecto: el rango deseado de 10 a 25 activos, el control de volatilidad, la búsqueda de Sharpe Ratio competitivo y la comparación frente a benchmarks funcionan como referencias que permiten evaluar si el sistema cumple o no los objetivos planteados.

\subsection{Métodos de Análisis Jerárquico: AHP y ANP}

El Analytic Hierarchy Process (AHP) y su extensión Analytic Network Process (ANP) son métodos ampliamente conocidos para estructurar problemas de decisión mediante jerarquías de criterios y comparaciones pareadas. Su principal fortaleza es que permiten incorporar preferencias del decisor de manera explícita, traduciéndolas en pesos relativos para cada criterio. En un problema con pocos criterios y alternativas, esta aproximación puede ser muy útil porque obliga a justificar la importancia relativa de cada dimensión evaluada.

Sin embargo, para un universo amplio de ETFs, el uso directo de comparaciones pareadas entre alternativas se vuelve poco práctico. Si se consideran cientos de ETFs, la cantidad de comparaciones necesarias crece rápidamente y puede hacer el proceso difícil de sostener. Además, la consistencia de los juicios se vuelve más compleja a medida que aumenta el número de alternativas. Por esta razón, en este trabajo se opta por una metodología que permite calcular criterios de forma empírica y clasificar alternativas contra perfiles de referencia, sin exigir comparaciones manuales entre todos los ETFs del universo.

\subsection{Métodos de Distancia Ideal: TOPSIS}

TOPSIS ordena las alternativas según su cercanía a una solución ideal positiva y su distancia frente a una solución ideal negativa. En términos generales, una alternativa será preferible si se aproxima al mejor valor posible de cada criterio y se aleja de los peores valores observados. Esta lógica resulta intuitiva y ha sido aplicada en distintos problemas de selección financiera.

No obstante, TOPSIS depende de la normalización de criterios y no maneja de la misma manera la idea de incomparabilidad o veto que caracteriza a ELECTRE. Para el problema de ETFs, esta diferencia es importante. Un fondo puede tener una rentabilidad alta pero una liquidez baja o costos elevados; en estos casos, no siempre conviene compensar completamente una debilidad crítica con una fortaleza en otro criterio. ELECTRE Tri permite incorporar esta sensibilidad mediante umbrales y relaciones de sobreclasificación, lo que justifica su elección como método central de clasificación.
"""


METODOLOGIA_EXTRA = r"""

La metodología se desarrolla siguiendo una secuencia gradual que responde al esquema general del problema. Primero se reconoce un fenómeno con exceso de alternativas y criterios de decisión; luego se estructura la información disponible; posteriormente se aplica una herramienta de clasificación multicriterio; después se construyen portafolios con reglas de asignación; finalmente se validan los resultados frente a benchmarks. Esta secuencia es importante porque evita saltar directamente desde los datos históricos hacia una conclusión de desempeño, y obliga a documentar cada decisión metodológica.

En términos de ingeniería, el sistema se entiende como un proceso con entradas, transformación y salidas. Las entradas corresponden a precios, volúmenes, universo de activos y parámetros de evaluación. La transformación incluye limpieza de datos, cálculo de criterios, clasificación ELECTRE, selección de activos, optimización de pesos y simulación de rebalanceo. Las salidas corresponden a portafolios, métricas, curvas de capital, caídas máximas, diagnósticos de clasificación y reportes de cumplimiento. Esta lectura permite evaluar el modelo no solo como una fórmula financiera, sino como un sistema completo de apoyo a la decisión.

La separación entre desarrollo, validación principal y robustez ampliada fue una decisión metodológica central. El período 2021--2024 se conserva como referencia de desarrollo y calibración porque coincide con el alcance aprobado inicialmente. El año 2025 funciona como ventana de validación fuera de muestra, permitiendo evaluar cómo se comporta la metodología con información posterior. Finalmente, el período 2015--2025 se utiliza como análisis ampliado de robustez, ya que permite observar el desempeño bajo más regímenes de mercado, pero no reemplaza la validación principal aceptada en los objetivos del trabajo.
"""


FASE_DATOS_EXTRA = r"""

Durante esta fase también se definieron reglas de tratamiento de información faltante y cobertura mínima. La intención fue evitar que un ETF entrara a la evaluación con una historia insuficiente o con series de precios demasiado incompletas. En este tipo de estudios, la disponibilidad de datos no es un detalle menor, pues una metodología aparentemente sofisticada puede producir resultados engañosos si los activos evaluados no tienen información comparable. Por esta razón, la cobertura mínima se convirtió en un filtro operativo antes de calcular criterios y ejecutar el clasificador.

El universo utilizado se aproxima a una lógica \textit{point-in-time} pública, usando snapshots disponibles del universo invertible. Esta decisión busca reducir el sesgo de supervivencia que aparece cuando se evalúa retrospectivamente un conjunto de ETFs existentes al final del período. Aun así, se reconoce que la aproximación no equivale a una reconstrucción institucional completa del universo histórico, ya que no incorpora con total precisión delistings, fusiones, cierres de fondos ni todos los cambios de composición que pudieron ocurrir durante el período. Esta limitación se conserva explícitamente en el documento para evitar sobreafirmar el alcance de la evidencia.
"""


ELECTRE_EXTRA = r"""

El procedimiento de clasificación se ejecuta por fecha de rebalanceo. En cada punto del tiempo, el sistema calcula las métricas disponibles con información histórica previa y clasifica los ETFs contra perfiles de referencia. Esto respeta el principio de no anticipación: un activo no debe ser seleccionado usando información futura. La salida del clasificador no es todavía un portafolio, sino un subconjunto de activos elegibles que representa la materia prima para la etapa de asignación.

La ponderación de criterios refleja la intención de privilegiar desempeño y eficiencia ajustada por riesgo, sin descuidar estabilidad, liquidez y costos. La rentabilidad anual compuesta y el Sharpe Ratio reciben mayor peso porque expresan la capacidad del ETF para generar retornos y hacerlo de manera eficiente respecto al riesgo asumido. La volatilidad permite controlar la estabilidad del instrumento. La liquidez reduce el riesgo de seleccionar activos difíciles de negociar. El \textit{tracking error} y el \textit{expense ratio} son criterios propios de ETFs, porque capturan eficiencia de réplica y costos operativos; sin embargo, en la ejecución empírica final quedaron como criterios parcialmente cubiertos por falta de datos completos.
"""


OPT_EXTRA = r"""

La optimización se interpreta como una etapa posterior e independiente de la selección multicriterio. ELECTRE Tri no determina cuánto capital invertir en cada ETF; únicamente clasifica y filtra alternativas. Una vez definido el conjunto elegible, las estrategias de asignación construyen portafolios que pueden ser comparados entre sí. Esta separación metodológica es importante porque permite identificar si un resultado se debe a la calidad de la selección, a la regla de asignación de pesos o al comportamiento del mercado durante la ventana evaluada.

La estrategia equiponderada se usa como una regla base porque evita introducir supuestos fuertes sobre retornos esperados y covarianzas. La estrategia de mínima varianza busca reducir la exposición al riesgo total del portafolio, mientras que MaxSharpe intenta maximizar la relación entre retorno esperado y volatilidad. En la práctica, estas estrategias permiten revisar tres enfoques distintos: una asignación simple, una asignación conservadora y una asignación orientada a eficiencia ajustada por riesgo. El contraste entre ellas aporta información sobre la sensibilidad de los resultados a la etapa de asignación.
"""


VALIDACION_EXTRA = r"""

La validación empírica se diseñó para responder directamente a los objetivos del trabajo. Para el primer objetivo, se revisa si la clasificación reduce el universo a un conjunto manejable de activos. Para el segundo objetivo, se analiza si las categorías ELECTRE presentan una relación razonable con el desempeño posterior. Para el tercer objetivo, se comparan las estrategias construidas contra benchmarks tradicionales. De esta manera, cada resultado reportado tiene una relación explícita con una pregunta metodológica y no se presenta únicamente como una tabla de rentabilidades.

El uso de benchmarks cumple una función de control. SPY representa una alternativa simple de exposición al mercado accionario estadounidense; el portafolio 60/40 SPY-BND representa una asignación tradicional balanceada; y el universo equiponderado permite revisar si la selección ELECTRE aporta valor frente a mantener todos los activos disponibles con el mismo peso. Esta comparación es exigente, pero necesaria para evitar que el modelo se evalúe únicamente contra sí mismo.
"""


ALCANCE_EXTRA = r"""

El alcance también se delimita desde el punto de vista del usuario esperado. El sistema está pensado como una herramienta académica y de apoyo exploratorio para inversionistas o analistas con interés en construir portafolios diversificados de ETFs, no como una plataforma de asesoría financiera personalizada. Por esta razón, los resultados no deben interpretarse como recomendación de compra o venta, sino como evidencia de comportamiento histórico bajo reglas específicas de selección y rebalanceo.

La interpretación de los resultados debe considerar que el mercado estadounidense durante 2021--2025 tuvo condiciones particulares, incluyendo recuperación postpandemia, cambios en tasas de interés, episodios de volatilidad y una fuerte concentración de retornos en algunos segmentos del mercado. Estos elementos afectan la comparación frente a SPY y al portafolio 60/40. Por ello, el hecho de que la estrategia multicriterio no supere a dichos benchmarks no implica que el enfoque carezca de valor metodológico; indica que, bajo la configuración evaluada, la clasificación y asignación implementadas no generaron una ventaja robusta frente a alternativas simples.
"""


IMPLEMENTACION_EXTRA = r"""

La implementación se desarrolló de manera incremental. Primero se construyeron funciones para cargar datos y calcular métricas financieras. Después se integró la clasificación ELECTRE Tri con perfiles y criterios de decisión. Posteriormente se conectó la selección con estrategias de portafolio y rebalanceo. Finalmente se agregaron reportes, figuras y validaciones de cumplimiento de objetivos. Esta evolución refleja un desarrollo gradual propio de un proyecto aplicado: cada fase dependía de que la anterior produjera salidas consistentes.

Un aspecto importante de la implementación fue la trazabilidad. Cada experimento genera archivos con métricas de desempeño, curvas de capital, caídas, activos seleccionados por rebalanceo y resúmenes de cumplimiento. Esto permite reconstruir la cadena de decisiones desde los datos iniciales hasta las conclusiones. En un trabajo de grado aplicado, esta trazabilidad es tan importante como el resultado financiero, porque permite que un evaluador revise si las conclusiones están respaldadas por evidencia verificable.
"""


RESULTADOS_EXTRA = r"""

La lectura de la prueba principal debe hacerse con cuidado. En términos absolutos, ELECTRE equiponderado alcanza una rentabilidad positiva y un drawdown similar al de SPY, lo cual muestra que el sistema sí construye portafolios operativos. Sin embargo, el Sharpe Ratio queda por debajo de SPY, del portafolio 60/40 y del universo equiponderado. Esta diferencia indica que la selección multicriterio, en su configuración actual, no logró transformar la reducción del universo en una mejora suficiente de rentabilidad ajustada por riesgo.

La cardinalidad de la selección también aporta un hallazgo importante. El modelo seleccionó menos activos de los esperados en varias fechas de rebalanceo, lo que reduce diversificación y afecta el cumplimiento del primer objetivo específico. Este resultado no debe ocultarse, porque señala una oportunidad concreta de mejora: ajustar perfiles, umbrales o reglas de selección final para asegurar que el portafolio mantenga el rango objetivo de 10 a 25 activos sin relajar excesivamente la calidad de los ETFs elegidos.
"""


ROBUSTEZ_EXTRA = r"""

La validación ampliada refuerza la necesidad de no evaluar el modelo únicamente en una ventana corta. Al extender el período a 2015--2025, el desempeño de las estrategias ELECTRE se debilita frente a SPY, 60/40 y el universo equiponderado. Esta evidencia sugiere que la señal de clasificación observada en la prueba principal no es todavía suficientemente estable para sostener una conclusión de superioridad. El resultado aporta una lectura realista del alcance del modelo y ayuda a orientar mejoras futuras.

Desde el punto de vista académico, el resultado más importante no es que el modelo haya superado o no a un benchmark particular, sino que el sistema permite comprobarlo de forma reproducible. La metodología construida evita que la evaluación dependa de apreciaciones subjetivas y permite identificar con precisión qué parte del proceso requiere ajuste: cobertura de criterios, cardinalidad, perfiles ELECTRE, datos regulatorios o estrategia de asignación.
"""


CIERRE_EXTRA = r"""

En relación con el objetivo general, el trabajo logra desarrollar una herramienta integrada de selección y optimización basada en ETFs, aunque su validación queda parcialmente limitada por la ausencia completa de \textit{tracking error} y \textit{expense ratio} en las ejecuciones empíricas. En relación con el primer objetivo específico, se implementa el sistema de clasificación multicriterio, pero la reducción al rango de 10--25 activos no se cumple de forma consistente. En relación con el segundo objetivo, se desarrolla el análisis histórico de los ETFs elegibles y se obtiene evidencia parcial de consistencia ordinal. Finalmente, respecto al tercer objetivo, se implementa la optimización y comparación contra benchmarks, pero no se valida una superioridad robusta frente a estrategias tradicionales.

Estas conclusiones responden directamente a los objetivos y muestran que el trabajo no se limita a presentar un modelo idealizado. La contribución consiste en diseñar, implementar y evaluar un sistema real, con resultados favorables y desfavorables, permitiendo identificar las condiciones bajo las cuales la metodología funciona y las brechas que deben resolverse para una versión futura. Esta es precisamente la utilidad de un proyecto aplicado de Ingeniería Industrial: estructurar un problema complejo, desarrollar una solución verificable y usar los resultados para mejorar el proceso de decisión.
"""


def insert_after(text: str, marker: str, addition: str) -> str:
    if addition.strip() in text:
        return text
    if marker not in text:
        raise SystemExit(f"Marker not found: {marker[:80]}")
    return text.replace(marker, marker + addition, 1)


def insert_before(text: str, marker: str, addition: str) -> str:
    if addition.strip() in text:
        return text
    if marker not in text:
        raise SystemExit(f"Marker not found: {marker[:80]}")
    return text.replace(marker, addition + "\n" + marker, 1)


def main() -> None:
    text = TEX.read_text(encoding="utf-8")

    text = insert_before(text, "\\section{Revisión de Literatura (marco de referencia)}", SITUACION_EXTRA)
    text = insert_before(text, "\\begin{longtable}{p{3.2cm}p{3.2cm}p{6.4cm}}", MARCO_EXTRA)
    text = insert_after(text, "\\fuente{Elaboración propia.}\n\n\\subsection{Primera Fase: Adquisición, Preparación y Análisis Exploratorio de Datos}", METODOLOGIA_EXTRA)
    text = insert_after(text, "Los filtros operativos aplicados exigieron cobertura mínima de datos de 80\\%, frecuencia de rebalanceo trimestral y costos aproximados de transacción de 10 puntos básicos.", FASE_DATOS_EXTRA)
    text = insert_after(text, "La segunda fase realiza la selección de los ETFs por medio de un modelo multicriterio. Se implementaron métricas empíricas calculadas directamente desde datos históricos: rentabilidad anual compuesta, volatilidad anualizada, Sharpe Ratio y liquidez. El modelo también contempla \\textit{tracking error} y \\textit{expense ratio}; sin embargo, las ejecuciones empíricas no contaron con cobertura completa para estos dos criterios, por lo que se reportan como brechas de datos y no como resultados plenamente validados.", ELECTRE_EXTRA)
    text = insert_after(text, "En la variante MaxSharpe se busca maximizar el retorno ajustado por riesgo del portafolio, sujeto igualmente a pesos no negativos y suma de pesos igual a uno. Esta variante se conservó como comparación experimental, aunque en los resultados finales no fue el motor más sólido de desempeño. El rebalanceo se ejecutó de manera trimestral, con deriva de pesos tipo \\textit{buy and hold} entre fechas de rebalanceo y costos de transacción aproximados de 10 puntos básicos.", OPT_EXTRA)
    text = insert_after(text, "Es importante resaltar que la validación no se utilizó para forzar una lectura favorable del modelo, sino para establecer con claridad qué fue validado y qué no. En la corrida principal 2021--2025, la estrategia ELECTRE equiponderada obtuvo resultados positivos, pero no superó a SPY ni al portafolio 60/40 en Sharpe Ratio. En la validación ampliada 2015--2025, la estrategia también quedó por debajo de los principales referentes. Por lo tanto, el resultado final sostiene la utilidad metodológica del sistema, pero no una superioridad empírica definitiva frente a estrategias tradicionales.", VALIDACION_EXTRA)
    text = insert_before(text, "\\section{Implementación del Sistema de Clasificación Multicriterio}", ALCANCE_EXTRA)
    text = insert_after(text, "Esta estructura permite separar la clasificación ELECTRE de la asignación de pesos, evitando confundir el método multicriterio con un optimizador de portafolios.", IMPLEMENTACION_EXTRA)
    text = insert_after(text, "La ejecución principal se realizó sobre el período 2021--2025, conservando la separación conceptual entre desarrollo 2021--2024 y validación 2025. La estrategia ELECTRE equiponderada obtuvo un CAGR agregado de 12.88\\%, Sharpe Ratio de 1.198 y máximo \\textit{drawdown} de -7.54\\%. Aunque este resultado es positivo en términos absolutos, queda por debajo de SPY y del portafolio 60/40 en desempeño ajustado por riesgo. Por esta razón, el resultado debe leerse como evidencia de funcionamiento y comparación reproducible del sistema, no como confirmación de superioridad del enfoque multicriterio.", RESULTADOS_EXTRA)
    text = insert_after(text, "La validación ampliada 2015--2025 se ejecutó para revisar la estabilidad del enfoque fuera del período principal. En esta prueba, ELECTRE equiponderado obtuvo un CAGR de 3.78\\%, Sharpe Ratio de 0.332 y caída máxima de -20.45\\%, quedando por debajo de SPY, del portafolio 60/40 y del universo equiponderado. Esta lectura confirma que la metodología construida es útil para evaluar y documentar decisiones, pero que su configuración actual no demuestra una ventaja robusta frente a estrategias simples.", ROBUSTEZ_EXTRA)
    text = insert_after(text, "Como trabajo futuro se recomienda completar la integración de \\textit{tracking error} y \\textit{expense ratio} con fuentes confiables, activar una regla final de cardinalidad que garantice entre 10 y 25 ETFs por rebalanceo, fortalecer los grupos comparables dentro de ELECTRE Tri, mejorar el manejo de restricciones de exposición y construir una arquitectura de datos regulatoria enriquecida con fuentes como SEC N-PORT, N-CEN, EDGAR y OpenFIGI. Estas mejoras permitirían cerrar las principales brechas que quedaron documentadas durante la implementación.", CIERRE_EXTRA)

    TEX.write_text(text, encoding="utf-8")
    print(f"Enriched {TEX}")


if __name__ == "__main__":
    main()
