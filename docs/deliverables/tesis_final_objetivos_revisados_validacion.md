# Validación — tesis final con objetivos revisados

Fecha: 2026-06-12

## Archivos generados

- LaTeX: `docs/deliverables/tesis_final_tamayo_etf_electre_objetivos_revisados.tex`
- PDF: `docs/deliverables/tesis_final_tamayo_etf_electre_objetivos_revisados.pdf`
- DOCX editable: `docs/deliverables/tesis_final_tamayo_etf_electre_objetivos_revisados_editable.docx`
- Validación: `docs/deliverables/tesis_final_objetivos_revisados_validacion.md`

## Figuras revisadas

- Gráfica de cumplimiento de objetivos: `docs/figures/thesis_results_objetivos_revisados/combined_07_objective_compliance_revisada.png`
- Gráfica de tamaño del conjunto seleccionado: `docs/figures/thesis_results_objetivos_revisados/primary_05_selection_cardinality_revisada.png`

## Objetivos incorporados

**Objetivo específico 1:** Reducir el universo de ETFs disponibles a un conjunto manejable para pequeños inversionistas, mediante la aplicación de criterios multicriterio de selección relacionados con desempeño, riesgo, liquidez y consistencia financiera.

**Objetivo específico 3:** Comparar el desempeño obtenido por el modelo multicriterio mediante benchmarking frente a estrategias tradicionales de inversión, utilizando métricas de rentabilidad, riesgo y rentabilidad ajustada por riesgo.

## Cambios metodológicos aplicados

- Se eliminó la promesa de cardinalidad fija para el objetivo específico 1.
- La cardinalidad ahora se interpreta como evidencia del grado de reducción del universo, no como condición de cumplimiento.
- El objetivo específico 3 se reformuló como comparación mediante benchmarking, no como promesa de superar benchmarks.
- La tabla de objetivos fue actualizada para marcar como cumplidos los objetivos 1 y 3 bajo su formulación revisada.
- La gráfica de cumplimiento fue actualizada con los objetivos revisados.
- La gráfica de selección fue reemplazada por una versión sin banda de rango fijo 10--25.
- Se mantuvo la regla previa de “título por hoja” después de la portada.

## Validaciones técnicas

- PDF compilado correctamente con Tectonic.
- Advertencias LaTeX: únicamente `Underfull \hbox`; no bloquean la generación.
- Tamaño de página PDF: carta, `612 x 792 pts`.
- Páginas PDF: `31`.
- Portada preservada: sí.
- Secciones principales detectadas después de portada: `8`.
- Secciones principales con salto `\clearpage`: `8`.
- DOCX editable generado: sí.
- DOCX: `22` encabezados, `7` tablas, `10` imágenes.

## Validaciones de contenido

- Nuevo objetivo específico 1 presente: sí.
- Nuevo objetivo específico 3 presente: sí.
- Texto antiguo `10--25 activos`: ausente.
- Texto antiguo `10 a 25 activos`: ausente.
- Texto antiguo `rango objetivo`: ausente.
- Texto antiguo `no cerrado operacionalmente`: ausente.
- La mención restante a “superioridad empírica” aparece únicamente en sentido cautelar: no se afirma superioridad empírica frente a benchmarks.

## Resultado

La nueva versión queda alineada con el desarrollo actual: reduce el universo de ETFs a un conjunto manejable, construye portafolios y compara su desempeño mediante benchmarking, sin prometer cardinalidad fija ni superioridad frente a estrategias tradicionales.
