# Validación de la versión final LaTeX/PDF

## Archivos finales

- Fuente LaTeX: `docs/deliverables/tesis_final_tamayo_etf_electre.tex`
- PDF compilado: `docs/deliverables/tesis_final_tamayo_etf_electre.pdf`
- DOCX editable: `docs/deliverables/tesis_final_tamayo_etf_electre_editable.docx`
- Recursos gráficos: `docs/deliverables/tesis_final_assets/`
- Generador reproducible: `scripts/build_tesis_final_latex.py`
- Enriquecimiento argumental reproducible: `scripts/enrobustecer_tesis_final.py`
- Generador DOCX editable: `scripts/build_tesis_final_docx.py`
- Motor LaTeX portable: `.tools/tectonic/tectonic`

## Instalación del motor LaTeX

No había `pdflatex`, `xelatex`, `lualatex` ni `latexmk` disponibles en el entorno, y `sudo` requería contraseña. Se instaló Tectonic 0.16.9 como motor LaTeX portable dentro del proyecto, verificando el SHA256 del binario descargado.

Comando de versión:

```bash
.tools/tectonic/tectonic --version
```

Resultado: `Tectonic 0.16.9`.

## Compilación

La compilación se realizó desde `docs/deliverables` con:

```bash
../../.tools/tectonic/tectonic tesis_final_tamayo_etf_electre.tex
```

Resultado: PDF generado correctamente. La compilación emitió únicamente advertencias de tipo `Underfull \hbox`, asociadas a ajuste de líneas en portada y tablas. No se presentaron errores de compilación ni imágenes faltantes.

## Estructura validada

Se conservaron los títulos originales del documento fuente:

1. Situación Problemática
2. Revisión de Literatura (marco de referencia)
3. Objetivos
4. Metodología
5. Cronograma de Proyecto
6. Alcance y Limitaciones
7. Implementación del Sistema de Clasificación Multicriterio
8. Bibliografía

## Métricas del PDF

- Páginas: 28
- Tamaño de página: carta, 612 x 792 puntos
- Tamaño de archivo: aproximadamente 1.6 MB
- Figuras incluidas: 10
- Tablas/elementos con caption: 16
- Imágenes faltantes: 0
- Palabras estimadas en fuente LaTeX: 8953
- Subsecciones: 14

## Corrección del pie de página

Se ajustó el pie de página para aproximarlo al diseño original suministrado por el usuario: barra horizontal roja en la parte superior del pie, texto “Escuela de Ingeniería Industrial” debajo de la barra y número de página debajo del texto, alineado hacia la izquierda. Esta corrección reemplaza el pie anterior que tenía el número centrado y una barra roja parcial hacia la derecha.

## DOCX editable

Se generó una versión editable en Word a partir del LaTeX final robustecido. Validación del DOCX:

- Párrafos no vacíos: 152
- Encabezados: 22
- Tablas: 7
- Imágenes: 10
- Encabezados con comandos LaTeX visibles: 0

El DOCX conserva la estructura argumental y permite edición manual, aunque el PDF/LaTeX sigue siendo la versión principal de control de formato.

## Validaciones automáticas

- Citas LaTeX sin resolver: 0
- `bibitem` duplicados: 0
- Placeholders reales (`Pendiente`, `TODO`, `[cita]`, `[año]`, `[benchmark]`): 0
- Términos genéricos en títulos como `dashboard` o `scatter`: 0
- Frases de tono interno como `corridas finales`, `La labor conserva`, `generado por IA`: 0
- Fórmulas metodológicas clave incluidas: 10

## Enriquecimiento argumental aplicado

Después de la primera compilación se robusteció el documento porque la versión semántica inicial había quedado más corta que el archivo fuente. La expansión mantuvo los títulos originales y conservó el planteamiento base, añadiendo desarrollo gradual en los siguientes frentes:

- situación problemática ampliada desde la lógica fenómeno → ineficiencias → riesgos → aporte de Ingeniería Industrial;
- marco teórico enriquecido con métodos de outranking, programación por metas, AHP/ANP y TOPSIS;
- metodología reforzada como proceso con entradas, transformación y salidas;
- fases de datos, selección, optimización y validación ampliadas;
- alcance y limitaciones explicados con mayor contexto;
- implementación presentada como desarrollo incremental y trazable;
- resultados negativos explicados como evidencia metodológica, no como falla oculta;
- cierre por objetivos, respondiendo directamente qué se cumplió, qué quedó parcial y qué no se validó empíricamente.

## Cambios metodológicos aplicados

Se reforzó la metodología con fórmulas para:

- retorno diario;
- CAGR;
- volatilidad anualizada;
- Sharpe Ratio;
- tracking error;
- concordancia ELECTRE;
- credibilidad ELECTRE;
- pesos equiponderados;
- retorno del portafolio;
- optimización de mínima varianza.

También se añadió una tabla de parámetros de implementación que aclara frecuencia de rebalanceo, asignación ELECTRE, cobertura mínima, costos de transacción, restricciones de pesos y benchmarks.

## Cambios en objetivos y resultados

Se añadió una tabla de relación entre objetivos, evidencia obtenida y nivel de cumplimiento. El documento ya no presenta los resultados negativos como una debilidad aislada, sino como una validación empírica de la hipótesis bajo la configuración evaluada. La conclusión metodológica queda así:

- el sistema sí fue implementado y validado de forma reproducible;
- no se confirma superioridad robusta frente a SPY, 60/40 ni equiponderación del universo;
- el cumplimiento del objetivo general es parcial por ausencia completa de tracking error y expense ratio en las ejecuciones empíricas;
- el objetivo de cardinalidad 10--25 no queda cerrado operacionalmente en las pruebas finales;
- la contribución principal es metodológica, diagnóstica y de trazabilidad.

## Naturalidad y estilo

Se eliminaron expresiones con tono de bitácora o asistente, tales como referencias a “corridas finales” o comentarios meta sobre el documento. Los títulos de figuras y tablas se dejaron en español y con formulaciones naturales, por ejemplo:

- Evolución del capital en la prueba principal
- Caídas acumuladas durante la prueba principal
- Relación entre riesgo y rentabilidad en la prueba principal
- Número de ETFs seleccionados en cada rebalanceo
- Estado de cumplimiento de los objetivos del trabajo

El texto conserva el estilo académico del documento fuente, incluyendo el uso de formulaciones como “se adoptó”, “se implementó”, “se constituye” y “esta metodología”, pero con mayor precisión frente a los resultados reales del desarrollo. También se corrigieron expresiones con tono de bitácora o comentario interno, tales como referencias directas a archivos extensos dentro del cuerpo del documento, frases defensivas y formulaciones prematuras sobre el resultado.
