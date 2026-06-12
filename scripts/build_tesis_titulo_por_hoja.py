"""Create a final thesis variant where each main title starts a new page.

This script does not alter the canonical final LaTeX. It reads the already
generated robust thesis and writes a separate deliverable with the rule:
after the cover/front matter, every top-level section begins on a fresh page.
"""

from __future__ import annotations

from pathlib import Path


SOURCE = Path("docs/deliverables/tesis_final_tamayo_etf_electre.tex")
OUT = Path("docs/deliverables/tesis_final_tamayo_etf_electre_titulo_por_hoja.tex")


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    marker = "\\end{titlepage}"
    if marker not in text:
        raise SystemExit("No se encontró el cierre de portada en el LaTeX fuente")

    prefix, suffix = text.split(marker, 1)
    suffix = suffix.replace("\\section{", "\\clearpage\n\\section{")
    out_text = prefix + marker + suffix

    OUT.write_text(out_text, encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
