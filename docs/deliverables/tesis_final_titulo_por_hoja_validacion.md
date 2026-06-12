# Validación — tesis final con título por hoja

Fecha: 2026-06-12

## Archivos generados

- LaTeX: `docs/deliverables/tesis_final_tamayo_etf_electre_titulo_por_hoja.tex`
- PDF: `docs/deliverables/tesis_final_tamayo_etf_electre_titulo_por_hoja.pdf`
- DOCX editable: `docs/deliverables/tesis_final_tamayo_etf_electre_titulo_por_hoja_editable.docx`
- Validación: `docs/deliverables/tesis_final_titulo_por_hoja_validacion.md`

## Regla incorporada

Después de la portada, cada sección principal inicia en una hoja nueva mediante `\clearpage` antes de cada `\section{...}`.

## Validaciones

- La portada conserva `\begin{titlepage}` / `\end{titlepage}`.
- Secciones dentro de la portada: `0`.
- Secciones principales detectadas después de portada: `8`.
- Secciones principales con salto explícito `\clearpage`: `8`.
- Secciones principales sin salto explícito: `0`.
- PDF compilado correctamente con Tectonic.
- Advertencias de compilación: únicamente `Underfull \hbox`; no bloquean la generación.
- Tamaño de página PDF: carta, `612 x 792 pts`.
- Páginas PDF: `31`.
- DOCX editable generado con saltos de página antes de títulos principales.
- DOCX: `22` encabezados, `7` tablas, `10` imágenes.

## Títulos principales verificados

1. Situación Problemática
2. Revisión de Literatura (marco de referencia)
3. Objetivos
4. Metodología
5. Cronograma de Proyecto
6. Alcance y Limitaciones
7. Implementación del Sistema de Clasificación Multicriterio
8. Bibliografía

## Resultado

La variante compila correctamente y aplica la regla solicitada sin modificar la portada ni reemplazar los archivos principales anteriores.
