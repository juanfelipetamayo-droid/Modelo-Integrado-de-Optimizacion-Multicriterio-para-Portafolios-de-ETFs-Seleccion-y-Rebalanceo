**Programa de Ingeniería Industrial** Informe Practica Profesional 

## **Modelo Integrado de Optimización Multicriterio para Portafolios de ETFs: Selección y** 

## **Rebalanceo** 

Presentado por: 

## **Juan Felipe Tamayo Mejía** 

Director(a/es) del Trabajo 

## **PhD. Diego Fernando Manotas Duque** 

## **PhD. Orlando Joaqui Barandica** 

Escuela de Ingeniería Industrial, Universidad del Valle Diciembre de 2025 

## **Resumen** 

Con miles de Exchange-Traded Funds (ETFs) en los mercados financieros, la elaboración de carteras eficientes demanda metodologías sistemáticas que superen los enfoques tradicionales, orientados a dos objetivos que involucran la rentabilidad y el riesgo, y que resultan insuficientes para captar la complejidad multidimensional de este tipo de instrumentos. El presente trabajo tiene como propósito el desarrollo de un modelo integrado de optimización multicriterio, que combine selección sistemática de ETFs aplicando ELECTRE Tri con estrategias de rebalanceo dinámico, y que permita identificar activos óptimos, construir portafolios eficientes y adaptarse a condiciones de mercado cambiantes. La labor cubre la aplicación de clasificación multicriterio para aproximadamente 200 ETFs del mercado estadounidense haciendo uso de técnicas de optimización. Se desarrollará un estudio cuantitativo utilizando datos históricos (2021-2024) mediante técnicas MCDM, optimización y validación exhaustiva a través de _backtesting walkforward_ con análisis estadístico frente a los _benchmarks_ tradicionales. Esta contribución proporciona un marco metodológico flexible para seleccionar un conjunto preliminar de fondos y luego optimizarlos, mitiga los errores de estimación, permite incorporar múltiples criterios de decisión, y otorga una herramienta de código abierto que puede potencialmente democratizar el acceso a técnicas cuantitativas avanzadas de gestión de inversiones. 

**Palabras clave:** ETFs, ELECTRE Tri, optimización multicriterio, rebalanceo de portafolios, gestión de riesgo, _backtesting_ , _Sharpe Ratio_ . 

Escuela de Ingeniería Industrial 

1 

## **1. Situación Problemática** 

Los _Exchange-Traded Funds_ (ETFs) han transformado fundamentalmente la inversión global desde su introducción en 1993, experimentando un crecimiento exponencial que los ha consolidado como instrumentos financieros fundamentales para la democratización del acceso a los mercados financieros. Para 2023 el número de ETFs a nivel mundial superó los diez mil, con activos superiores a los 11 billones de dólares estadounidenses, representando una innovación significativa en la gestión de portafolios y la diversificación de riesgo (Konsta Vuorela, 2024). 

Esta transformación no ha sido casual. Estos activos surgieron como respuesta a las limitaciones de los fondos mutuos tradicionales, ofreciendo mayor flexibilidad de negociación, menores costos operativos y transparencia en tiempo real sobre sus posiciones.  Su estructura única permite a los inversores acceder a mercados completos, sectores específicos o estrategias de inversión sofisticadas con una sola transacción, eliminando las barreras tradicionales que limitaban el acceso a la diversificación institucional. (Xidonas, Mavrotas and Psarras, 2009) 

Los ETFs se han convertido en instrumentos muy atractivos para inversores gracias a su propuesta de valor inicial: la diversificación y solidez a cambio de un mínimo esfuerzo por parte del inversor. Su condición de inversión pasiva y relativamente segura los hace un activo común y recurrente en los portafolios de inversores, su popularidad ha dado lugar a un nuevo campo de estudio donde se proponen diversas técnicas y metodologías para cuantificar y minimizar riesgos en la gestión de tales portafolios. Si bien los ETFs parecen instrumentos simples y fáciles de entender, existe una realidad mucho más compleja detrás de esa apariencia. 

Aunque originalmente fueron creados para seguir índices de manera pasiva, la aparición de ETFs especializados, temáticos y con estrategias activas ha transformado el panorama, haciendo que elegir el más adecuado sea todo un reto. Hoy en día, los inversores se enfrentan a decisiones difíciles, incluso cuando varios de estos activos replican el mismo índice, ya que cada uno puede tener metodologías, costos y niveles de eficiencia diferentes. Esto demanda un análisis más detallado y cuidadoso para tomar la mejor decisión. 

Los instrumentos de renta variable cotizados han experimentado un crecimiento explosivo, alcanzando más de $10 billones en activos globales con más de 8,000 fondos disponibles mundialmente. (Cohen and Del Valle, 2025) Esta proliferación masiva presenta tanto 

Escuela de Ingeniería Industrial 2 

oportunidades como desafíos: mientras que la diversidad permite construcción de portafolios altamente especializados, la saturación del mercado genera condiciones de análisis estadísticamente complejas (Xidonas, Mavrotas and Psarras, 2009) 

Las optimizaciones de portafolios mal condicionadas generan portafolios con rendimientos por debajo de estrategias muy básicas, debido a errores en la estimación de parámetros, por lo que la primera etapa de análisis y selección de valores es de vital importancia, (DeMiguel, Garlappi and Uppal, 2009) 

El problema de evaluar estos vehículos financieros se constituye inherentemente como un problema multicriterio, a diferencia de la optimización multi-varianza clásica (Markowitz, 1952)) que contempla solo dos dimensiones, la selección de ETFs debe considerar múltiples factores de naturaleza diversa, retornos, volatilidades, costos, volúmenes de negociación y spreads por mencionar algunos (Xidonas, Mavrotas and Psarras, 2009). 

Aunque tienen una aparente simplicidad, es clave que un portafolio que consista de ETFs tenga una gestión adecuada a lo largo del tiempo para garantizar la máxima rentabilidad a su propietario, por lo que es necesario optimizar los activos que hacen parte del portafolio con el pasar del tiempo debido a las condiciones cambiantes del mercado. La volatilidad inherente de los mercados financieros, cambios en correlaciones entre activos, y eventos de mercado extraordinarios, crea la necesidad de estrategias de rebalanceo de portafolios para maximizar su eficiencia (Brandt, 2010). 

La naturaleza multidimensional y potencialmente conflictiva de estos criterios de optimización hace que los enfoques de optimización uni-objetivo sean insuficientes para capturar la complejidad del problema. Como señalan (Steuer and Na, 2003) en su revisión bibliográfica exhaustiva, los enfoques de toma de decisiones multicriterio (MCDM) proporcionan el marco metodológico apropiado para resolver problemas financieros con estas características, permitiendo la incorporación explícita de las preferencias del inversionista y el manejo de criterios inconmensurables. 

La selección adecuada entre miles de opciones disponibles y la gestión dinámica de carteras requieren metodologías de análisis avanzadas mucho más complejas que los enfoques convencionales bi-objetivo de la teoría de Markowitz. La complejidad multidimensional de los criterios de evaluación (riesgo/retorno, liquidez, costos, tracking error) motiva a considerar marcos de decisión multicriterio que reflejen la complejidad del problema. 

Escuela de Ingeniería Industrial 3 

A pesar de la extensa literatura sobre optimización de portafolios y de la creciente aplicación de métodos MCDM en finanzas (Zopounidis and Doumpos, 2013; (Spronk, Steuer and Zopounidis, 2005), (Xidonas, Mavrotas and Psarras, 2009) existe una brecha metodológica significativa en lo que respecta a la selección sistemática de ETFs como clase de activo específica. 

Encontramos en este vehículo económico una oportunidad especial para aplicar estas metodologías ya que cuentan con un universo es suficientemente amplio en la cantidad de activos disponibles para requerir selección previa, pero suficientemente estructurado en sus propiedades para permitir una clasificación sistemática. 

Se detecta un vacío en la literatura en cuanto uso de una metodología de toma de decisiones multicriterio específicamente diseñada para la selección de ETFs que considere estas particularidades, integre múltiples criterios de evaluación relevantes para esta clase de activo, y se conecte explícitamente con la fase posterior de optimización de portafolio. 

En el orden de ideas que deja el trabajo de Xidonas et al, se clasificaran con MCDM 200 ETFs que sean categorizables en tres grupos según su desempeño multicriterio: excelentes, aceptables y rechazados, adaptando la metodología ELECTRE Tri originalmente aplicada a acciones individuales al contexto específico de fondos cotizados en bolsa. 

Todo esto lleva a la pregunta que motiva este trabajo escrito. ¿Cómo diseñar e implementar una metodología que combine selección sistemática mediante ELECTRE Tri y estrategias de rebalanceo dinámico, mejorar significativamente el rendimiento ajustado por riesgo en portafolios de ETFs comparado con estrategias de inversión tradicionales? 

Escuela de Ingeniería Industrial 4 

## **2. Revisión de Literatura (marco de referencia)** 

## **2.1 Teoría de Portafolios** 

La Teoría Moderna de Portafolios de Markowitz (1952) estableció los fundamentos conceptuales para la optimización de carteras mediante la minimización de la varianza del portafolio sujeta a un rendimiento esperado objetivo, su implementación práctica presenta limitaciones significativas en el contexto de gestión de ETFs. La formulación original de Markowitz establece que los inversionistas racionales buscan maximizar el retorno esperado para un nivel dado de riesgo, o equivalentemente, minimizar el riesgo para un retorno esperado dado. Este framework bi-objetivo genera la frontera eficiente de portafolios, sobre la cual ningún portafolio puede mejorar en una dimensión sin empeorar en la otra. La contribución seminal de Markowitz fue demostrar que la diversificación reduce el riesgo del portafolio por debajo del promedio ponderado de los riesgos individuales, siempre que los activos no estén perfectamente correlacionados. Requiere la especificación a priori de un rendimiento deseado, esto es un problema a la hora de comparar la eficiencia relativa de múltiples activos con distintos perfiles riesgo-rendimiento de un mismo portafolio. 

Seguidos a este primer acercamiento de Markowitz en su teoría de análisis financiero de portafolios se han venido desarrollando nuevas metodologías sobre su trabajo, estas metodologías se ven recopiladas en el trabajo de (Elton et al, 2014) Algunas refinaciones de este modelo fueron el CAPM (Sharpe, 1964), un enfoque bayesiano de combinar equilibrio de mercado con opiniones subjetivas del inversionista (Black and Litterman, no date) y la _resampled optimization_ para mitigar la inestabilidad en precios (Richard O. Michaud, 1998) Estos trabajos mantienen el paradigma inicial bi-objetivo, la relación retorno-riesgo y asumen que el universo de inversión esta predefinido. 

DeMiguel et al (2009) demostró empíricamente que la optimización media-varianza tiene un rendimiento general menor a una estratégica básica equiponderada, cuando se tiene un numero de activos grande en un portafolio. El problema radica en que la matriz de covarianza tiende a condicionarse erróneamente cuando la cantidad de activos es grande, introduciendo un error de estimación que opaca cualquier beneficio que ofrezca esta optimización. 

Escuela de Ingeniería Industrial 5 

En esto encontramos una táctica de acercamiento al problema, una selección previa que reduzca el universo de activos a alrededor de 25 activos puede reducir el error de estimación, volviendo viable y robusta la optimización del portafolio. 

El paradigma bi-objetivo presenta otro desafío a superar dado que reducir todo a retorno y riesgo es una simplificación excesiva que ignora múltiples factores que se tienen en cuenta en la realidad, como: liquidez, costos, spreads de demanda e incluso factores que caen dentro de Environmental, Social and Governance (ESG). Por dar un ejemplo, los portafolios que tienen como objetivo de optimización solo factores ESG como base, pueden alcanzar hasta un 95% de retorno (Ballestero _et al._ , 2012), lo que muestra el valor que tienen otros factores aparte del retorno y riesgo. 

Por lo que la utilización de modelos multicriterio es una oportunidad de incorporar estrategias y metodologías que reflejen preferencias reales de inversionistas, sin forzar su reducción a una función de utilidad unidimensional. 

La literatura de optimización de portafolios asume de manera implícita que el conjunto de activos posibles esta predefinido. Sin embargo, este conjunto de universo de inversión es una decisión en si misma que carga mucho peso en los resultados obtenidos del estudio. La diversificación efectiva de un portafolio depende no solo de los pesos asignados, sino crucialmente de qué activos se incluyen. (Kritzman, Page and Turkington, 2010) 

Debido a esto podemos considerar que una metodología sistemática de selección que maximice los “números efectivos de apuestas” con un número limitado de activos puede lograr una diversificación más efectiva que portafolios construidos de manera no estructurada, incluso si estos incluyen una mayor cantidad de activos. 

## **2.2 Estado del Arte en MCDM en Selección de Activos Financieros** 

La aplicación de métodos de toma de decisiones multicriterio o MCDM a problemas financieros tiene mas de tres décadas de antigüedad, para el año 2003 Steuer y Na ya registraban en su multianalisis mas de 250 estudios que combinaban MCDM con el mundo financiero, categorizándolos en: a) selección y gestión de portafolios, b) evaluación de performance corporativa, c) gestión de riesgo, d) decisiones de presupuesto de capital y e) otros problemas financieros. 

Escuela de Ingeniería Industrial 6 

En esta sección se ahondara en las distintas metodologías de toma de decisiones multicriterio que se han descubierto por medio de la literatura, sus funciones y como se han aplicado en el campo de estudio de las finanzas cuantitativas. 

## **2.2.1 Métodos de** _**Outranking**_ **: ELECTRE y PROMETHEE** 

Los métodos que consisten en comparaciones pareadas de alternativas para construir relaciones de preferencia que no requieren la agregación completa en una función de utilidad se les conoce como métodos de _outranking_ . Esta característica los hace particularmente apropiados para problemas donde los criterios son heterogéneos o computacionalmente pesados, donde existe incertidumbre en las evaluaciones y donde las preferencias del decisor son difíciles de expresar mediante funciones. 

En esta familia por así decirle, se encuentra el ELECTRE Tri, un método de clasificación que asigna alternativas a categorías predefinidas a través de comparar perfiles de referencia. Encontramos una aplicación relevante en el trabajo de Xidonas et al 2009 quienes desarrollan una metodología para selección de acciones a través de análisis financiero. Este ELECTRE Tri es versátil a la hora de manejar incomparabilidad, queriendo decir, cuando una alternativa tiene un performance que supera a las demás en algún criterio pero que tenga un desempeño muy malo en otros criterios, ELECTRE Tri tiene la capacidad de declararlo “incomparable” con perfiles de referencia. (Xidonas, 2019) 

Este método también contempla dos procedimientos, por así decirlo, entregando un escenario optimista y otro pesimista, dándole la capacidad de generar clasificaciones distintas para una misma alternativa, lo que aumenta la robustez de la clasificación. Adicionalmente la modelación de la imprecisión se hace a través de umbrales de indiferencia, preferencia y veto. En el trabajo de Xidonas y compañía se aplicó esta metodología a 200 acciones de la Bolsa de Atenas, clasificándolas en tres categorías: aceptables, a estudiar y no aceptables; todo esto con base en ratios financieros. 

La metodología usada por los investigadores fue la siguiente: clasificaron los sectores de manera previa, llegando a un total de 8 sectores que les permitiera agrupar industrias con estructuras financieras en común, el rango temporal de estudio y análisis fue de 3 años para validar 

Escuela de Ingeniería Industrial 7 

la consistencia de sus clasificaciones, también hubo participación de analistas financieros expertos durante la duración de todas las fases del estudio. 

Detectamos una limitación de esta metodología y es que en el estudio se le aplica a acciones individuales, para los que los criterios son ratios financieros de las empresas emisoras (ROE, deuda a equidad, _current ratio_ , etc.). Los ETFs, al ser instrumentos replicadores de índices, requieren una serie de criterios distintos. 

PROMETHEE II es otro método de _outranking_ ampliamente utilizado en finanzas, a diferencia del ELECTRE Tri que usa categorías para clasificar, genera un ranking completo de alternativas. (Brans and Mareschal, 2005). 

Encontramos múltiples aplicaciones relevantes para este método: Selección de proyectos de inversión en investigación y desarrollo (Albadvi, Chaharsooghi and Esfahanipour, 2006), inversión socialmente responsable (Ballestero _et al._ , 2012), evaluación de opciones financieras (Zopounidis and Doumpos, 2013). 

Una ventaja que ofrece este modelo es que es conceptualmente más simple que ELECTRE y puede producir rankings completos. Sin embargo, para el problema de selección de ETFs, donde el objetivo es clasificar en categorías (seleccionados/no seleccionados) más que rankear completamente, ELECTRE Tri parece más apropiado. 

## **2.2.2 Métodos de Programación por Metas** 

El _Goal Programaming_ (GP) permite al decisor especificar niveles de aspiración ( _goals_ ) para múltiples objetivos, y minimiza las desviaciones de estos _goals_ . El GP también contribuye al proceso de construcción de portafolios socialmente responsables, teniendo en cuenta como metas: su retorno esperado superior o igual a 12% anuales, una volatilidad inferior o igual a 18%, puntaje ESG superior o igual a 7 de 10 máximo y numero de activos entre 15-25. La función objetivo minimiza las desviaciones ponderadas de estas metas o _goals_ . 

## **2.2.3 Métodos de Análisis Jerárquico (AHP) y ANP** 

El _Analytic Hierarchy Process_ (AHP) de Saaty (1980) estructura el problema de decisión como una jerarquía de criterios y sub-criterios, y utiliza comparaciones pareadas para derivar pesos. En 

Escuela de Ingeniería Industrial 8 

la literatura el AHP se aplica para selección de portafolios por medio de conjuntos difusos (Tiryaki and Ahlatcioglu, 2009). Se aprovecha su naturaleza intuitiva y ampliamente conocida. Las comparaciones pareadas son naturales para decisores. 

Este acercamiento cuenta con varias limitaciones, considerando más de cien ETFs se requiere más de 4,950 comparaciones pareadas, lo que resulta en un problema computacionalmente pesado, la inconsistencia es una posibilidad pues las comparaciones pareadas tienen la posibilidad de violar la transitividad; la adición o eliminación de una alternativa puede cambiar el ranking de alternativas no afectadas de manera que viola la independencia. 

Por estas razones, AHP no resulta ser la metodología apropiada para abarcar el problema de selección de ETFs con universo amplio. 

## **2.2.4 Métodos de Distancia Ideal: TOPSIS** 

El método TOPSIS o _Technique for Order Preference by Similarity to Ideal Solution_ (Hwang and Yoon, 1981), rankea alternativas basándose en su distancia a una solución ideal positiva, que es el mejor valor de todos los criterios, a su vez rankea una solución ideal negativa, que es la peor en todos los criterios. 

TOPSIS es una metodología computacionalmente simple y produce rankings completos, aunque no maneja incomparabilidad y es sensible a la normalización de criterios. No proporciona información sobre robustez de rankings. Su primera implementación en la selección de activos para portafolio fue en el año 2000 por 

**Tabla 1.** Clasificación de la revisión de literatura a usar 

|Temática|Autor(es)|Año|Titulo|Aporte|
|---|---|---|---|---|
||Markowitz,|1952<br>|Portfolio Selection|Fundamentos de la teoría moderna|
||H.|||de portafolios.|
||Sharpe, W.F.|1964|Capital Asset Prices: A Theory|CAPM|
|Teoría de|||of Market Equilibrium under||
|Portafolios|||Conditions of Risk||



Escuela de Ingeniería Industrial 9 

||Black, F. &|1992|Global Portfolio Optimization|Optimización media-varianza puede|
|---|---|---|---|---|
||Litterman, R.|||ser inferior a estrategias|
|||||equiponderadas|
||Tsalikis, E.|2019|ETFS – performance, tracking|_Tracking error_del SPY,|
||&||errors and their determinants in|complejidad en la medición de|
||Papadopoulo||Europe and the USA|riesgo.|
||s, S.||||
|Limitaciones|DeMiguel, V.|2009|Optimal versus Naive|Optimización media-varianza puede|
|Optimización|et al.||Diversification: How Inefficient|ser inferior a estrategias|
|Clásica|||Is the 1/N Portfolio Strategy?|equiponderadas|
||Kritzman, M.|2010|In Defense of Optimization: The|Defensa de optimización con|
||et al.||Fallacy of 1/N|selección previa de activos|
||Bányai, T. et|2024|The Impact of Rebalancing|Impacto de costos de transacción y|
||al.||Strategies on ETF Portfolio|_tracking errors_en rebalanceo|
|Optimización|||Performance.||
|de Portafolios|||||
||Jaffri, A.A. et|2025|Optimizing Portfolios with|Enfoque en datos internos para una|
||al.||Pakistan-Exposed Exchange-|optimización dirigida, ausencia de|
||||Traded Funds: Risk and|algoritmos con restricciones|
||||Performance Insight|múltiples|
|Métodos|Roy, B.|1993|Decision science or decision-aid|Marco conceptual para ciencia de|
|MCDM|||science?|apoyo a la decisión|
||Brans, J.P. &|1985|A Preference Ranking|Introducción del método|
||Vincke, Ph.||Organisation Method|PROMETHEE|
||Hwang, C.-L.|1981|Methods for Multiple Attribute|Desarrollo del método TOPSIS|
||& Yoon, K.||Decision Making||
|Liquidez y|Khomyn, M.,|2024|The Value of ETF Liquidity|La liquidez es fundamental para|
|Mercado|Putniņs , T.J.|||determinar comisiones, impacta la|
||& Zoican,|||atracción de inversores|
||M.A.||||



Escuela de Ingeniería Industrial 10 

||Boido, C. &|2025|Artificial Intelligence Exchange-|Corralacion inversa entre el Alpha y|
|---|---|---|---|---|
||Aliano, M.||Traded Funds: The Intersection|la reducción de riesgo|
|Inteligencia|||of Finance, Technology and||
|Artificial en|||Sustainability||
|ETFs|||||
||Vuorela, T.|2024|Assessing the Impact of AI-|ETFs relacionados o administrados|
||||Managed ETFs on Investment|por IA muestran mejor gestión de|
||||Performance and Risk|riesgo que los índices tradicionales|
||||Compared to Benchmark Index||
|Selección de|Xidonas, P.|2009|A multicriteria methodology for|Aplicación de ELECTRE Tri para|
|Activos|et al.||equity selection using financial|selección de acciones|
||||analysis||
||Samaras,|2003|A multicriteria DSS for a global|Sistema multicriterio para|
||G.D. et al.||stock evaluation|evaluación de acciones|
||Ballestero, E.|2012|Socially Responsible|Integración de criterios ESG con|
||et al.||Investment: A multicriteria|objetivos financieros|
||||approach to portfolio selection||
|Análisis|Khan, S. &|2024|The Dynamic Influence of|Interrelaciones de los ETFs|
|Sectorial y|Khan, U.||Uncertainty on Sector Equity|sectoriales estadounidenses|
|Volatilidad|||Funds: A Time-Frequency||
||||Analysis of Oil, Gold, and||
||||Market Volatility||
|Definiciones y|Elton, E.J. et|2014|Modern Portfolio Theory and|Texto fundamental de teoría de|
|datos|al.||Investment Analysis|portafolios|
||Richard O.|2015|Efficient Asset Management|Gestión eficiente de activos|
||Michaud||||
|Métodos|Saaty, T.L.|1980|The analytic hierarchy process|Desarrollo del AHP|
|Alternativos|||||



Escuela de Ingeniería Industrial 11 

Tiryaki, F. & 2009 Fuzzy portfolio selection using AHP difuso en selección de Ahlatcioglu, fuzzy analytic hierarchy process portafolios B. Cohen, S. & 2025 Decoding active ETFs Crecimiento de ETFs activos Del Valle, J. 

Fuente: construido por los autores 

Escuela de Ingeniería Industrial 12 

La investigación y recopilación de conocimiento se hizo por medio de plataformas como ScienceDirect, SpringerLink, LUTPub, ResearchSquare, WebOfScience; a través de las licencias provistas por la Universidad del Valle. La gestión bibliográfica se realizó a través de Mendeley Reference Manager. Se enfoco en dar una idea de la importancia de la resolución de la pregunta problematizadora, dando contexto en los factores a considerar en cuanto a la selección de los activos que harán parte de los portafolios a estudiar. Así como también sustentar las formulas utilizadas en el modelo de optimización en Python. 

Desde los trabajos seminales de Markowitz (1952, 1959) sobre optimización media-varianza, la teoría de portafolios ha evolucionado considerablemente. Los desarrollos en MCDM aplicado a finanzas, documentados comprehensivamente por Steuer y Na, 2003, Zopounidis y Doumpos, 2013, y (Spronk, Steuer and Zopounidis, 2005), han demostrado que la selección de activos es inherentemente un problema multicriterio que trasciende la dicotomía retorno-riesgo del modelo de Markowitz. 

Las metodologías ELECTRE (Roy, 1968; (Roy, 1993), PROMETHEE (Brans and Vincke, 1985), AHP (Saaty, 1980), y TOPSIS (Hwang & Yoon, 1981) han sido aplicadas exitosamente a diversos problemas de decisión financiera, incluyendo selección de acciones (Xidonas et al., 2009; Samaras et al, 2003), evaluación de fondos mutuos (Pendaraki, Zopounidis and Doumpos, 2005) e inversión socialmente responsable (Ballestero et al., 2012). 

No obstante estos avances, persisten brechas significativas que limitan la aplicabilidad práctica de estas metodologías al contexto específico de ETFs: Ninguno de los estudios revisados desarrolla un _framework_ MCDM que incorpore sistemáticamente estas características específicas de ETFs. 

Dado que el mercado de ETFs ha experimentado crecimiento exponencial, alcanzando más de 3000 instrumentos en Estados Unidos y más de 8000 globalmente (Investment Company Institute, 2025), con activos bajo gestión superiores a $10.3 trillones (Investment Company Institute, 2025), la interacción entre selección MCDM previa y estas técnicas de optimización modernas no ha sido explorada dentro del mundo relativamente nuevo de estos vehículos financieros. 

Se nota un especial interés en el trabajo de Xidonas et al, el acercamiento que se hace con ELECTRE Tri, las brechas identificadas convergen en una oportunidad de investigación clara: se requiere el desarrollo, implementación y validación empírica de un marco de trabajo MCDM específicamente diseñado para selección de ETFs 

Escuela de Ingeniería Industrial 13 

## **3. Objetivos** 

La revisión exhaustiva de la literatura presentada en las secciones precedentes permite identificar tanto los avances significativos como las brechas persistentes en la intersección entre teoría de portafolios, metodologías de decisión multicriterio (MCDM) y gestión de inversiones pasivas mediante ETFs. Que nos llevan a plantear el siguiente objetivo general, acompañado de tres objetivos específicos. 

**Objetivo general:** Desarrollar un modelo de optimización de portafolios de inversión basado en ETFs mediante análisis multicriterio, considerando rendimiento, volatilidad, Sharpe Ratio, liquidez, _tracking error_ y _expense ratio_ , que sirva como herramienta de toma de decisiones de inversión. 

**Objetivo específico número uno:** Diseñar e implementar un sistema de clasificación multicriterio que reduzca el universo del mercado estadounidense a un conjunto de 10-25 activos sobre datos del 2021-2024. 

**Objetivo específico número dos:** Analizar el desempeño histórico de los ETFs clasificados como elegibles mediante indicadores financieros clave durante el período 2021-2024, con el propósito de caracterizar sus perfiles de riesgo-retorno y validar la consistencia 

de la selección multicriterio. 

**Objetivo específico número tres:** Desarrollar e implementar un modelo de optimización de portafolios que maximice la rentabilidad ajustada por riesgo, con el propósito de construir portafolios eficientes y validar que el enfoque multicriterio genera mejores rentabilidades ajustadas por riesgo comparado con estrategias de inversión tradicionales. 

Escuela de Ingeniería Industrial 14 

## **4. Metodología** 

Se adoptará una metodología empírica basa en análisis cuantitativo de data financiera histórica y la implementación practica de modelos de optimización para maximizar retornos, de esta manera se permite validar las teorías financieras trabajadas en este escrito usando datos de mercado reales, tangibles y observables. El diseño metodológico esta basado en los trabajos de Xidonas et al. (2009) sobre selección multicriterio de acciones, Roy y Bouyssou (1993) sobre fundamentos de métodos outranking, y DeMiguel et al. (2009) sobre problemas de error de estimación en optimización de portafolios, adaptando estas metodologías al contexto específico de ETFs como clase de activo. Cabe resaltar que los resultados serán contrastados con el comportamiento real del mercado y permitiendo comparar la estrategia resultante del modelo con otros métodos de inversión relativamente seguros. 

La investigación adopta un enfoque cuantitativo-empírico con diseño experimental y validación _out-of-sample_ , orientado al desarrollo, implementación y validación de una metodología de decisión multicriterio basada en ELECTRE Tri para la selección óptima de ETFs y construcción de portafolios eficientes. El diseño metodológico integra técnicas avanzadas de análisis de decisiones multicriterio (MCDM), optimización de portafolios, y validación empírica rigurosa mediante _backtesting_ con datos reales de la bolsa americana. 

El desarrollo metodológico se inspira fuertemente en el trabajo de Xidonas et al. (2009) sobre selección multicriterio de acciones mediante ELECTRE Tri, Roy y Bouyssou (1993) sobre fundamentos de métodos _outranking_ , Markowitz (1952, 1959) sobre teoría moderna de portafolios, DeMiguel et al. (2009) sobre problemas de error de estimación en optimización de portafolios y un poco de López de Prado (2016) sobre técnicas avanzadas de construcción de portafolios mediante _machine learning_ . Todo esto a modo de un acercamiento a las opciones que un inversionista que ha sido recientemente introducido a este tipo de activo pueda verse enfrentado. 

El lenguaje de elección para el código de implementación de la metodología es Python, ya que es el que más se especializa en cálculos avanzados para el sector financiero y ofrece librerías muy valiosas a cambio de ningún costo, perfecto para nuestro enfoque, algunas de estas son: 

_**yfinance:**_ Es la librería estándar para obtener datos financieros gratuitos de Yahoo Finance de manera programática. 

Escuela de Ingeniería Industrial 15 

_**numpy:**_ Es la base fundamental para computación científica en Python, especialmente para operaciones con arrays multidimensionales. 

_**scipy.optimize**_ : Proporciona algoritmos de optimización numérica para resolver problemas de minimización/maximización. 

_**pandas:**_ Proporciona estructuras de datos y herramientas de análisis de datos de alto nivel, especialmente para datos tabulares. 

Utilizar Python para este trabajo, aparte de que permite que el código sea de libre acceso y replicable sin ningún costo, también representa una opción con alta accesibilidad para los realizadores ya que se cuenta con experiencia en el uso de estas librerías para el cálculo de indicadores económicos utilizando los datos financieros en la base de datos de Yahoo Finance. 

Las librerías utilizadas nos dan cobertura completa, desde la adquisición de datos hasta su optimización final de manera que es adaptable a cualquier portafolio sin ningún tipo de costo y con mucho soporte, documentación y posibilidad de escalabilidad en futuros proyectos. 

El “universo” de inversión inicial comprenderá todos los ETFs listados en bolsas estadounidenses que cumplan criterios mínimos de liquidez y tamaño, específicamente aquellos con activos bajo gestión superiores a cien millones de dólares estadounidenses y volumen promedio diario de negociación superior a quinientas mil acciones. Estos filtros preliminares garantizan que los ETFs considerados sean suficientemente líquidos para permitir ejecución de órdenes sin impacto significativo en los precios y suficientemente establecidos para contar con historiales de datos confiables. Estimaciones iniciales nos da un universo de inversión de alrededor de 250 ETFs, este volumen de activos es similar al trabajado por Xidonas et al (2009), aunque todo esto depende de las condiciones específicas del mercado en cada momento del período de análisis. 

El desarrollo se estructura en cuatro fases secuenciales de duración total de ocho meses, cada una con objetivos específicos, metodologías particulares y criterios de validación claramente definidos. La implementación se realizará en Python utilizando librerías especializadas que garantizan tanto la robustez computacional como la replicabilidad de los resultados. 

El desarrollo se estructura en cuatro fases secuenciales de duración total de ocho meses, cada una con objetivos específicos, metodologías particulares y criterios de validación claramente definidos. La implementación se realizará mediante Python usando librerías especializadas que garantizan tanto la robustez computacional como la replicabilidad de los resultados 

Escuela de Ingeniería Industrial 16 

El estudio implementa un diseño experimental con validación temporal out-of-sample que divide el período total 2021-2025 en dos ventanas claramente diferenciadas: período de desarrollo y calibración (2021-2024) y período de validación empírica (2025). Esta separación temporal estricta garantiza que ninguna información del período de validación influya en las decisiones de diseño del modelo, eliminando el sesgo de _look-ahead_ que frecuentemente compromete la validez de estudios en finanzas cuantitativas. 

## **4.1 Primera Fase: Adquisición, Preparación y Análisis Exploratorio de Datos** 

La primera fase de recopilación y análisis cuantitativo estadístico de los datos históricos obtenidos. Se realizará una limpieza y estructuración de la base de datos de ETFs incluyendo precios diarios, volúmenes, spreads y activos bajo gestión, con un foco especial en sus resultados al final del año en cuanto a rentabilidad, volatilidad, Sharpe Ratio y retorno acumulado. Esta fase durara máximo un mes pues solo es realizar un curado a los datos ofrecidos por Yahoo Finance. 

## **4.2 Segunda Fase: Selección Multicriterio mediante ELECTRE Tri** 

La segunda fase es donde realizamos la selección de los ETF a estudiar por medio de un modelo multicriterio, se implementará las métricas empíricas descritas en el marco teórico, calculadas directamente de los datos históricos. La rentabilidad anual se medirá mediante el CAGR ( _Compound Annual Growth Rate_ ), la volatilidad como la desviación estándar anualizada de los retornos diarios, el Sharpe Ratio como la relación entre exceso de retorno y volatilidad, el retorno acumulado como el retorno total del período, y la liquidez mediante un score basado en volumen promedio y spreads _bid-ask_ . 

La metodología que nos permitirá seleccionar los activos mediante multicriterio es ELECTRE Tri, que reducirá el universo amplio de ETFs a un conjunto manejable de entre diez y veinticinco activos óptimos para la construcción del portafolio. La metodología ELECTRE Tri fue seleccionada por su capacidad para manejar criterios heterogéneos sin requerir su agregación forzada en una función de utilidad única, su tratamiento explícito de la incomparabilidad entre alternativas cuando ninguna domina claramente a la otra, y su robustez ante imprecisiones en las evaluaciones mediante el uso de umbrales de indiferencia, preferencia y veto. 

Se categorizaran estos activos en una de tres categorías predefinidas, los que superan estándares de excelencia en sus criterios, los que son aceptables mas no excepcionales y por ultimo los que son rechazados que no cumplen con estándares mínimos. 

Escuela de Ingeniería Industrial 17 

Los seis criterios de evaluación fueron seleccionados para capturar las dimensiones más relevantes del desempeño y viabilidad de los ETFs como vehículos de inversión. El primer criterio es el CAGR de tres años, calculado como la tasa de crecimiento anual compuesta durante el período más reciente de treinta y seis meses, que mide la capacidad del ETF para generar retornos consistentes a lo largo del tiempo. El segundo criterio es el Sharpe Ratio, calculado como el exceso de retorno sobre la tasa libre de riesgo dividido por la volatilidad anualizada, que mide la eficiencia con la que el ETF genera retornos por unidad de riesgo asumido. El tercer criterio es la volatilidad anualizada, calculada como la desviación estándar de los retornos diarios multiplicada por la raíz cuadrada de doscientos cincuenta y dos días de negociación, que mide la estabilidad del ETF y su contribución potencial al riesgo total del portafolio. El cuarto criterio es un score de liquidez. El quinto criterio es el tracking error anualizado, calculado como la desviación estándar de la diferencia entre los retornos del ETF y los retornos de su índice de referencia, que mide qué tan fielmente el ETF replica su _benchmark_ y refleja la eficiencia de su gestión. El sexto criterio es el _expense ratio_ , osease los gastos operativos del fondo 

El proceso de selección empírica aplicará filtros basados en evidencia, incluyendo análisis de supervivencia para ETFs con historia superior a tres años, validación empírica de liquidez mínima, y expense ratios por debajo del percentil 75 del universo. Se implementará un sistema de scoring empírico ponderado con pesos determinados mediante análisis de componentes principales, seguido de _backtesting_ para validar la selección de ETFs. 

## **4.3 Tercera Fase: Optimización de Portafolios y Estrategias de Rebalanceo** 

Se estima que esta fase durara de dos a tres meses mientras se procesan los ETFs, se construye el modelo multicriterio que asigne los pesos apropiados a los activos dentro del portafolio a estudiar, usando la data histórica y la metodología elegida. 

El modelo integrado de selección ELECTRE Tri con optimización y rebalanceo dinámico superará significativamente el rendimiento ajustado por riesgo (Sharpe Ratio) de estrategias _benchmark_ tradicionales en al menos 0.15 puntos durante el período de validación 2021-2025. 

Esta fase desarrollará el modelo de optimización basado en datos históricos, maximizando la función objetivo de media-varianza donde el retorno esperado del portafolio se calcula como la media histórica y la varianza mediante la matriz de covarianza empírica ajustada con el método de Ledoit-Wolf. La optimización incluirá restricciones fundamentales como la suma de pesos igual a 

Escuela de Ingeniería Industrial 18 

uno, pesos no negativos, aun no se ha considerado considerar un limite máximo de tamaño a un activo individual dentro del portafolio con fines de experimentar. 

El período de validación empírica corresponde al año completo 2025, constituyendo una ventana temporal genuinamente _out-of-sample_ que no fue utilizada en ninguna fase de desarrollo o calibración del modelo. Esta separación estricta entre datos de entrenamiento y validación es fundamental para evaluar la capacidad predictiva real del modelo y evitar el sobreajuste que frecuentemente afecta estudios de optimización de portafolios. 

Se implementará un sistema de rebalanceo basado en evidencia, comparando frecuencias mensual, trimestral y anual, incorporando análisis de costos de transacción reales y tracking error empírico. La validación se realizará mediante _backtesting_ empírico completo, utilizando análisis _walk-forward_ con ventanas móviles para evaluar el desempeño del modelo. Hay un interés especial en lograr implementar rebalanceo de alguna manera dentro del modelo ya que esto permitiría aprovechar los casos en los que “comprar barato y vender caro” beneficiaria al portafolio, también tomando provecho de que el valor del ETF suele exceder el del índice que sigue. 

Se estima que esta etapa será la más duradera, considerando una duración de 4 meses en los que se aprovecharan librerías gratuitas, cursos y toda fuente de información que pueda ser pertinente a la materia en estudio, se espera una colaboración con los conocimientos de los directores de trabajo de grado, así como del Grupo de Investigación en Finanzas Cuantitativas (GIFINC) de la Universidad del Valle para alcanzar el mayor flujo de información posible. 

## **4.4 Cuarta Fase: Validación Empírica y Análisis de Resultados** 

La cuarta fase es la final, se concentrará en validar los resultados obtenidos del modelo, implementa el protocolo de validación empírica rigurosa que evaluará el desempeño del modelo integrado durante el período _out-of-sample_ del año 2025 y realizará comparaciones estadísticas contra estrategias _benchmark_ establecidas. Proporcionando evidencia sobre cómo el modelo habría funcionado en condiciones reales de mercado sin el beneficio de información futura,  los resultados se compararan con estrategias conocidas y populares a modo de _benchmarking,_ como el S&P 500 (SPY), portafolio 60/40 tradicional, _equal-weight portfolio_ y _minimum variance portfolio_ . 

La implementación del backtesting respetará estrictamente el principio de no anticipación, asegurando que todas las decisiones tomadas en cada punto del tiempo se basen únicamente en 

Escuela de Ingeniería Industrial 19 

información que habría estado disponible para un inversionista real en ese momento. Específicamente, cuando el modelo se ejecute el primer día de enero de 2025 para determinar los pesos iniciales del portafolio, utilizará únicamente datos históricos hasta diciembre de 2024 para la selección de ETFs mediante ELECTRE Tri, la estimación de retornos esperados y matriz de covarianza, y la solución del problema de optimización. En cada fecha de rebalanceo subsecuente durante 2025, el modelo se re-ejecutará utilizando únicamente datos disponibles hasta ese momento, simulando fielmente el proceso de toma de decisiones que habría seguido un inversionista implementando la estrategia en tiempo real. 

Se espera una mejora en el _Sharpe Ratio_ , volatilidad, _tracking error_ y costos de transacción, aunque la cantidad de esta mejora es desconocida, se espera una mejora en alguna medida. Todo esto detallado en el trabajo escrito final, que será redactado por el autor en colaboración de guía por los directores del trabajo de grado. 

Se hará una publicación del código usado en este trabajo de grado en la plataforma GitHub con la finalidad de que los resultados sean replicables ya sea con fines de inversión o educativos y que sea un modelo de código abierto, que pueda ser implementado y copiado libremente por otras personas afines a las finanzas cuantitativas. 

Se espera que la duración de esta fase sea de dos meses aproximadamente mientras se pule el trabajo hasta alcanzar un estándar aceptable tanto por la universidad como por los colaboradores y el grupo de investigación. 

Esta metodología empírica garantiza que todos los resultados estén fundamentados en evidencia real del mercado, con validación estadística rigurosa que demuestre la aplicabilidad práctica del modelo de optimización de portafolios de ETFs desarrollado. 

Escuela de Ingeniería Industrial 20 

## **5. Cronograma de Proyecto** 

**Figura 1** . Diagrama de Gantt 

**Fuente.** Elaboración propia 

## **6. Alcance y Limitaciones** 

El trabajo de grado se limita a un universo especifico de los activos financieros, siendo estos los ETFs listados y negociados en la bolsa americana en el periodo 2021-2024, por lo que solo se trabajaran con estos activos, el autor se ve sujeto a la disponibilidad de los datos históricos confiables y gratuitos a través de plataformas como Yahoo Finance, y la estandarización regulatoria bajo la supervisión de la _Securities and Exchange Commission_ que garantiza transparencia y comparabilidad entre instrumentos. 

El horizonte temporal del estudio abarca cinco años completos desde enero de 2021 hasta diciembre de 2025, que aporta una estimación relevante y robusta de parámetros para el estudio, el periodo elegido captura múltiples etapas del mercado como la post-pandemia del 2021, la corrección posterior en el 2022 que represento un alza y su subsecuente estabilización en los años 2023 y 2024. La extensión de cinco años es suficiente para evaluar el desempeño del modelo a través de ciclos completos de mercado sin extenderse tanto que los datos antiguos pierdan relevancia para las condiciones contemporáneas. 

~~OO~~ Escuela de Ingeniería Industrial 21 

El modelo desarrollado está diseñado específicamente para inversionistas individuales o institucionales con horizontes de inversión de mediano a largo plazo, típicamente superiores a un año, que buscan construir portafolios diversificados de ETFs sin capacidad o interés en realizar trading activo de alta frecuencia. El perfil de usuario objetivo incluye inversionistas con capital suficiente para mantener posiciones en diez a veinte ETFs diferentes sin que los costos fijos de transacción representen una proporción excesiva del capital invertido. 

El alcance del modelo resultante solo contempla posiciones largas, otras operaciones como ventas en corto o opciones no se tienen en cuenta, pues es desde la perspectiva de un inversor individual con un portafolio ajustado. 

Escuela de Ingeniería Industrial 22 

## **7. Implementación del Sistema de Clasificación Multicriterio** 

El desarrollo del sistema de clasificación multicriterio mediante ELECTRE Tri constituye el centro metodológico del primer objetivo específico de esta investigación. La implementación se fundamenta en la adaptación de la metodología propuesta por Xidonas et al. (2009) al mercado específico de _Exchange-Traded Funds (ETFs),_ considerando las particularidades e idiosincrasias estructurales y operativas de estos instrumentos financieros que los diferencian de las acciones individuales tradicionalmente analizadas en la literatura MCDM. 

La arquitectura del sistema se estructura en torno a seis criterios de evaluación cuidadosamente seleccionados para capturar las dimensiones más relevantes del desempeño de los ETFs: 

## **Tabla 2.** Criterios de Evaluación 

|**Tabla 2.**Criterios de|Evaluación|
|---|---|
|Criterios de Evaluación|Peso|
|Compound Annual Growth Rate|25%|
|Sharpe Ratio|20%|
|Volatilidad Anualizada|15%|
|Liquidez|15%|
|Tracking Error|15%|
|Expense ratio|10%|



Fuente: construido por los autores 

Esta ponderación refleja la jerarquía de importancia establecida en la literatura especializada, donde el rendimiento y la eficiencia de riesgo mantienen la mayor relevancia para la toma de decisiones de inversión. 

## **7.1. Definición de Categorías y Umbrales de Clasificación** 

Se siguen los lineamientos de la metodología ELECTRE Tri donde se determinan a priori categorías de clasificación, en este caso se establecieron tres categorías ordenadas que reflejan la calidad relativa de los ETFs en el universo de análisis: "Excelentes", "Aceptables" y "Rechazados". 

Escuela de Ingeniería Industrial 23 

Estas categorías vienen definidas en el método expuesto en el trabajo de Xidonas et al, los umbrales que determinan a que categoría pertenece cada activo se definen en el código de la siguiente manera. 

**Tabla 3.** Categorías y Umbrales 

|Criterios de Evaluación|Excelentes|Aceptables|Rechazados|
|---|---|---|---|
|Compound Annual Growth Rate|8%>|5%>|>5%|
|Sharpe Ratio|0.8>|0.4>|>0.2|
|Volatilidad Anualizada|>25%|>35%|50%>|
|Liquidez|0.6>|0.4>|>0.2|
|Tracking Error|>6%|>8%|15%>|
|Expense ratio|>2%|>3%|5%>|



Fuente: construido por los autores 

Se implementó el sistema ELECTRE Tri a través de Python utilizando las librerías _numpy, pandas_ y _scipy_ , garantizando tanto la eficiencia computacional como la replicabilidad de los resultados a través de su publicación libre por medio de GitHub. El algoritmo implementa los procedimientos de asignación pesimista y optimista característicos de ELECTRE Tri, calculando índices de concordancia y discordancia para cada alternativa respecto a los perfiles de referencia, y derivando índices de credibilidad que determinan la clasificación final. 

Los umbrales de indiferencia, preferencia y veto se determinaron a través de análisis estadístico del universo de ETFs, estableciendo valores que reflejan la variabilidad natural de cada criterio en el mercado estadounidense. Para el CAGR se definieron umbrales de indiferencia de 3%, preferencia de 5% y veto de 8%; para el Sharpe Ratio, umbrales de 0.2, 0.4 y 0.8 respectivamente, y así sucesivamente para cada criterio, asegurando que los umbrales capturen tanto las diferencias significativas como las variaciones menores entre alternativas. 

Escuela de Ingeniería Industrial 24 

## **8. Bibliografía** 

Albadvi, A., Chaharsooghi, S.K. and Esfahanipour, A. (2006) ‘Decision making in stock trading: An application of PROMETHEE’, _European Journal of Operational Research_ , 177(2), pp. 673– 683. Available at: https://doi.org/10.1016/j.ejor.2005.11.022. Ballestero, E. _et al._ (2012) ‘Socially Responsible Investment: A multicriteria approach to portfolio selection combining ethical and financial objectives’, _European Journal of Operational Research_ , 216(2), pp. 487–494. Available at: https://doi.org/10.1016/j.ejor.2011.07.011. Black, F.; and Litterman, R. (no date) _Global Portfolio Optimization ABI/INFORM Global pg. 28_ , _Financial Analysts Journal_ . 

Brans, J.-P. and Mareschal, B. (2005) _Chapter 5 PROMETHEE METHODS_ . Brans, J.P. and Vincke, Ph. (1985) ‘Note—A Preference Ranking Organisation Method’, _Management Science_ , 31(6), pp. 647–656. Available at: https://doi.org/10.1287/mnsc.31.6.647. Cohen, S. and Del Valle, J. (2025) ‘Decoding active ETFs How the growth of active ETFs is unlocking innovation and opportunity for investors’, _BlackRock_ [Preprint]. Demiguel, V., Garlappi, L. and Uppal, R. (2009) _Optimal versus Naive Diversification: How Inefficient Is the 1/N Portfolio Strategy?_ , _Source: The Review of Financial Studies_ . Elton, E.J. and G.M.J. and B.S.J. and G.W.N. (2014) _Modern Portfolio Theory and Investment Analysis_ . 9th ed. 

Hwang, C.-L. and Yoon, K. (1981) ‘Methods for Multiple Attribute Decision Making’, in, pp. 58–191. Available at: https://doi.org/10.1007/978-3-642-48318-9_3. Investment Company Institute (2025) _Investment Company Fact Book A Review of Trends and Activities in the Investment Company Industry_ . Konsta Vuorela (2024) _Assessing the Impact of AI-Managed ETFs on Investment Performance and Risk Compared to Benchmark Index_ . Kritzman, M., Page, S. and Turkington, D. (no date) _In Defense of Optimization: The Fallacy of 1/ N_ , _Financial Analysts Journal_ . Markowitz, H. (1952) _Portfolio Selection_ , _Source: The Journal of Finance_ . Pendaraki, K., Zopounidis, C. and Doumpos, M. (2005) ‘On the construction of mutual fund portfolios: A multicriteria methodology and an application to the Greek market of equity mutual funds’, _European Journal of Operational Research_ , 163(2), pp. 462–481. Available at: https://doi.org/10.1016/j.ejor.2003.10.022. 

Richard O. Michaud (no date) _EFFICIENT ASSET MANAGEMENT_ . 

Roy, B. (1968) ‘Classement et choix en présence de points de vue multiples’, _Revue française d’informatique et de recherche opérationnelle_ , 2(8), pp. 57–75. Available at: https://doi.org/10.1051/ro/196802V100571. 

Roy, B. (1993) ‘Decision science or decision-aid science?’, _European Journal of Operational Research_ , 66(2), pp. 184–203. Available at: https://doi.org/10.1016/0377-2217(93)90312-B. Saaty, T.L. (1980) ‘The analytic hierarchy process’, _McGraw-Hill_ [Preprint]. Samaras, G.D., Matsatsinis, N.F. and Zopounidis, C. (2003) ‘A multicriteria DSS for a global stock evaluation’, _Operational Research_ , 3(3), pp. 281–306. Available at: https://doi.org/10.1007/BF02936406. 

Sharpe, W.F. (1964) _Capital Asset Prices: A Theory of Market Equilibrium under Conditions of Risk_ , _Source: The Journal of Finance_ . 

Escuela de Ingeniería Industrial 25 

Spronk, J., Steuer, R.E. and Zopounidis, C. (2005) ‘Multicriteria decision aid/analysis in finance’, in _International Series in Operations Research and Management Science_ . Springer New York LLC, pp. 799–857. Available at: https://doi.org/10.1007/0-387-23081-5_20. Steuer, R.E. and Na, P. (2003) ‘Multiple criteria decision making combined with finance: A categorized bibliographic study’, _European Journal of Operational Research_ , 150(3), pp. 496– 515. Available at: https://doi.org/10.1016/S0377-2217(02)00774-9. 

Tiryaki, F. and Ahlatcioglu, B. (2009) ‘Fuzzy portfolio selection using fuzzy analytic hierarchy process’, _Information Sciences_ , 179(1–2), pp. 53–69. Available at: https://doi.org/10.1016/j.ins.2008.07.023. 

Xidonas, P., Mavrotas, G. and Psarras, J. (2009) ‘A multicriteria methodology for equity selection using financial analysis’, _Computers and Operations Research_ , 36(12), pp. 3187–3203. Available at: https://doi.org/10.1016/j.cor.2009.02.009. 

Zopounidis, C. and Doumpos, M. (2013) ‘Multicriteria decision systems for financial problems’, _TOP_ , 21(2), pp. 241–261. Available at: https://doi.org/10.1007/s11750-013-0279-7. 

Escuela de Ingeniería Industrial 26 

