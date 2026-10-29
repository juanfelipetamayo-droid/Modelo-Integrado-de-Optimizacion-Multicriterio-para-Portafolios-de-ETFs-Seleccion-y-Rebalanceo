from __future__ import annotations

from pathlib import Path

import streamlit as st

from etf_optimizer.dashboard.backend import (
    CommandSpec,
    build_download_command,
    build_pipeline_command,
    build_sprint_command,
    build_target_portfolio_from_state,
    build_universe_command,
    load_dashboard_state,
    run_command,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RESULTS = REPO_ROOT / "results" / "sprint_universe_pilot"
DEFAULT_UNIVERSE = REPO_ROOT / "data" / "universe" / "etf_universe_clean.csv"
DEFAULT_PILOT_DATA = REPO_ROOT / "data" / "raw" / "yfinance_pilot"


SPANISH_LABELS = {
    "Light": "Claro",
    "Dark": "Oscuro",
    "annual": "anual",
    "quarterly": "trimestral",
    "monthly": "mensual",
    "strategy_comparison": "comparación de estrategias",
    "equity_curves": "curvas de patrimonio",
    "drawdowns": "caídas",
    "filter_funnel": "embudo de filtros",
    "fold_diagnostics": "diagnóstico de pliegues",
    "public_data_pilot": "piloto con datos públicos",
    "pilot_only_oos": "solo piloto fuera de muestra",
    "structural_test_only": "solo prueba estructural",
    "institutional_thesis_grade": "grado tesis institucional",
    "Preliminary public-data evidence only; do not claim survivorship-bias-free or statistically conclusive performance.": "Evidencia preliminar con datos públicos; no afirmar que esté libre de sesgo de supervivencia ni que el rendimiento sea estadísticamente concluyente.",
    "Build ETF universe": "Construir universo de ETF",
    "Download Yahoo Finance OHLCV data": "Descargar datos OHLCV de Yahoo Finance",
    "Run MVP pipeline": "Ejecutar pipeline MVP",
    "Run robust sprint experiment": "Ejecutar experimento sprint robusto",
    "conservador": "conservador",
    "moderado": "moderado",
    "agresivo": "agresivo",
}

SPANISH_COLUMNS = {
    "strategy": "estrategia",
    "cagr": "CAGR",
    "volatility": "volatilidad",
    "sharpe": "Sharpe",
    "sortino": "Sortino",
    "max_drawdown": "caída máxima",
    "calmar": "Calmar",
    "stage": "etapa",
    "count": "conteo",
    "pct_of_requested": "% de solicitados",
    "walk_forward_folds": "pliegues walk-forward",
    "oos_periods": "períodos OOS",
    "sufficiency_label": "etiqueta de suficiencia",
    "thesis_grade_oos": "OOS de grado tesis",
    "price_observations": "observaciones de precio",
    "return_observations": "observaciones de retorno",
    "train_size": "tamaño de entrenamiento",
    "test_size": "tamaño de prueba",
    "step_size": "tamaño de paso",
    "min_thesis_folds": "mínimo de pliegues para tesis",
    "min_thesis_oos_periods": "mínimo de períodos OOS para tesis",
    "ticker": "ticker",
    "nombre": "nombre",
    "clase_activo": "clase de activo",
    "categoría": "categoría",
    "peso": "peso",
    "valor_objetivo": "valor objetivo",
}


def _spanish_value(value: object) -> object:
    if isinstance(value, str):
        return SPANISH_LABELS.get(value, value)
    return value


def _spanish_dataframe(df):
    translated = df.copy()
    translated = translated.rename(columns={col: SPANISH_COLUMNS.get(col, col) for col in translated.columns})
    for column in translated.select_dtypes(include="object").columns:
        translated[column] = translated[column].map(_spanish_value)
    return translated


def _theme_tokens(theme: str) -> dict[str, str]:
    if theme == "Oscuro":
        return {
            "bg": "oklch(16% 0.008 255)",
            "panel": "oklch(22% 0.010 255)",
            "panel2": "oklch(26% 0.012 255)",
            "text": "oklch(94% 0.006 255)",
            "muted": "oklch(73% 0.012 255)",
            "hairline": "oklch(35% 0.014 255)",
            "accent": "oklch(70% 0.15 250)",
            "accent_soft": "oklch(30% 0.08 250)",
            "good": "oklch(75% 0.14 160)",
            "warn": "oklch(82% 0.15 80)",
            "shadow": "0 18px 60px oklch(9% 0.01 255 / 0.48)",
        }
    return {
        "bg": "oklch(98% 0.006 255)",
        "panel": "oklch(100% 0.004 255)",
        "panel2": "oklch(96% 0.008 255)",
        "text": "oklch(22% 0.012 255)",
        "muted": "oklch(48% 0.018 255)",
        "hairline": "oklch(87% 0.012 255)",
        "accent": "oklch(57% 0.18 250)",
        "accent_soft": "oklch(93% 0.05 250)",
        "good": "oklch(56% 0.14 160)",
        "warn": "oklch(64% 0.15 80)",
        "shadow": "0 18px 60px oklch(60% 0.02 255 / 0.16)",
    }


def inject_design_system(theme: str) -> None:
    tokens = _theme_tokens(theme)
    css_vars = "\n".join(f"--{name}: {value};" for name, value in tokens.items())
    st.markdown(
        f"""
        <style>
        :root {{ {css_vars} }}
        .stApp {{
            background: var(--bg);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
        }}
        [data-testid="stSidebar"] {{
            background: var(--panel2);
            border-right: 1px solid var(--hairline);
        }}
        [data-testid="stSidebar"] * {{ color: var(--text); }}
        header {{ visibility: hidden; }}
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        .block-container {{
            max-width: 1240px;
            padding-top: 2rem;
            padding-bottom: 5rem;
        }}
        h1, h2, h3 {{
            letter-spacing: -0.035em;
            color: var(--text);
        }}
        p, li, label, span {{ color: var(--text); }}
        .muted {{ color: var(--muted); }}
        .hero-shell {{
            background: var(--panel);
            border: 1px solid var(--hairline);
            border-radius: 32px;
            padding: 34px 36px;
            box-shadow: var(--shadow);
            margin-bottom: 24px;
        }}
        .eyebrow {{
            color: var(--accent);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: 12px;
        }}
        .hero-title {{
            color: var(--text);
            font-size: 3.1rem;
            line-height: 1.04;
            font-weight: 760;
            letter-spacing: -0.06em;
            margin: 0 0 16px;
        }}
        .hero-copy {{
            color: var(--muted);
            max-width: 68ch;
            font-size: 1.02rem;
            line-height: 1.62;
            margin: 0;
        }}
        .metric-row {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 14px;
            margin: 20px 0 28px;
        }}
        .metric-tile {{
            background: var(--panel);
            border: 1px solid var(--hairline);
            border-radius: 24px;
            padding: 20px 18px;
        }}
        .metric-label {{
            color: var(--muted);
            font-size: 0.76rem;
            font-weight: 650;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 12px;
        }}
        .metric-value {{
            color: var(--text);
            font-size: 1.75rem;
            line-height: 1;
            font-weight: 760;
            letter-spacing: -0.04em;
        }}
        .status-pill {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            border-radius: 999px;
            padding: 8px 12px;
            color: var(--text);
            background: var(--accent-soft);
            border: 1px solid var(--hairline);
            font-size: 0.86rem;
            font-weight: 650;
        }}
        .section-panel {{
            background: var(--panel);
            border: 1px solid var(--hairline);
            border-radius: 28px;
            padding: 24px;
            margin: 16px 0;
        }}
        .artifact-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
        }}
        .artifact {{
            border: 1px solid var(--hairline);
            border-radius: 18px;
            padding: 14px;
            background: var(--panel2);
        }}
        .artifact strong {{ color: var(--text); }}
        .artifact small {{ color: var(--muted); }}
        .stButton > button {{
            border-radius: 999px;
            border: 1px solid var(--hairline);
            background: var(--text);
            color: var(--bg);
            min-height: 44px;
            font-weight: 700;
            transition: transform 180ms cubic-bezier(.22,1,.36,1), opacity 180ms cubic-bezier(.22,1,.36,1);
        }}
        .stButton > button:hover {{ transform: translateY(-1px); opacity: 0.92; }}
        .stTextInput div[data-baseweb="input"],
        .stTextInput div[data-baseweb="base-input"],
        .stNumberInput div[data-baseweb="input"],
        .stNumberInput div[data-baseweb="base-input"],
        .stSelectbox div[data-baseweb="select"] {{
            background: var(--panel) !important;
            border: 1px solid var(--hairline) !important;
            border-radius: 16px;
            color: var(--text) !important;
        }}
        .stTextInput input, .stNumberInput input {{
            color: var(--text) !important;
            background: transparent !important;
        }}
        code, pre {{ border-radius: 16px; }}
        @media (max-width: 920px) {{
            .hero-title {{ font-size: 2.25rem; }}
            .metric-row, .artifact-grid {{ grid-template-columns: 1fr; }}
            .hero-shell {{ padding: 26px 22px; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def html_metric(label: str, value: object) -> str:
    return (
        f'<div class="metric-tile"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div></div>'
    )


def render_hero(state_ready: bool) -> None:
    status = "Resultados conectados" if state_ready else "Esperando resultados"
    st.markdown(
        f"""
        <section class="hero-shell">
            <div class="eyebrow">Panel de control del optimizador de ETF</div>
            <h1 class="hero-title">Pipeline de investigación convertido en software.</h1>
            <p class="hero-copy">
                Ejecuta el constructor de universo, la descarga de Yahoo Finance, el pipeline MVP y el experimento robusto desde un único panel. Revisa comparación de estrategias, salud del embudo, trazabilidad ELECTRE, metodología y manifiesto de reproducibilidad sin salir de la app.
            </p>
            <div style="margin-top: 22px;"><span class="status-pill">● {status}</span></div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_metric_rail(state) -> None:
    metrics = state.metrics
    st.markdown(
        "<div class='metric-row'>"
        + html_metric("Estrategias", metrics["strategies"])
        + html_metric("Elegibles finales", metrics["final_eligible"])
        + html_metric("Ventanas de rebalanceo", metrics["rebalance_windows"])
        + html_metric("Artefactos cargados", metrics["artifacts_loaded"])
        + "</div>",
        unsafe_allow_html=True,
    )


def render_overview(state) -> None:
    render_hero(state.is_ready)
    render_metric_rail(state)
    st.markdown("### Conjunto de resultados actual")
    st.write(f"Directorio de resultados: `{state.results_dir}`")
    st.write(f"Mejor estrategia por Sharpe: **{state.metrics['best_strategy']}**")
    if state.data_quality:
        verdict = state.data_quality.get("verdict", "unknown")
        claims = state.data_quality.get("allowed_claims", "")
        st.warning(f"Veredicto de calidad de datos: **{_spanish_value(verdict)}**. {_spanish_value(claims)}")
    fold_diagnostics = state.tables.get("fold_diagnostics")
    if fold_diagnostics is not None and not fold_diagnostics.empty:
        label = fold_diagnostics.loc[0, "sufficiency_label"]
        folds = fold_diagnostics.loc[0, "walk_forward_folds"]
        oos = fold_diagnostics.loc[0, "oos_periods"]
        st.warning(f"Suficiencia fuera de muestra: **{_spanish_value(label)}** — {folds} pliegues / {oos} períodos OOS.")

    comparison = state.tables.get("strategy_comparison")
    if comparison is not None and not comparison.empty:
        st.markdown("### Comparación de estrategias")
        st.dataframe(_spanish_dataframe(comparison), width="stretch", hide_index=True)
        chart_columns = [col for col in ["cagr", "volatility", "sharpe", "sortino", "max_drawdown", "calmar"] if col in comparison]
        if chart_columns:
            chart_data = comparison.set_index("strategy")[chart_columns]
            st.bar_chart(chart_data)
    else:
        st.info("Aún no hay comparación de estrategias. Ejecuta el experimento sprint o apunta el panel a un directorio de resultados existente.")

    funnel = state.tables.get("filter_funnel")
    if funnel is not None and not funnel.empty:
        st.markdown("### Embudo de elegibilidad")
        st.dataframe(_spanish_dataframe(funnel), width="stretch", hide_index=True)
        st.bar_chart(funnel.set_index("stage")["count"])


def render_results(state) -> None:
    st.markdown("## Explorador de resultados")
    table_names = sorted(state.tables)
    if not table_names:
        st.warning("No se encontraron tablas CSV de resultados en este directorio.")
        return
    selected = st.selectbox("Tabla", table_names, index=table_names.index("strategy_comparison") if "strategy_comparison" in table_names else 0, format_func=_spanish_value)
    table = state.tables[selected]
    st.dataframe(_spanish_dataframe(table), width="stretch", hide_index=True)

    if selected == "equity_curves" and not table.empty:
        st.line_chart(table.set_index(table.columns[0]) if table.columns[0].lower() in {"date", "index"} else table)
    if selected == "drawdowns" and not table.empty:
        st.line_chart(table.set_index(table.columns[0]) if table.columns[0].lower() in {"date", "index"} else table)


def render_artifacts(state) -> None:
    st.markdown("## Estado de artefactos")
    cards = []
    for artifact in state.artifacts.values():
        mark = "Listo" if artifact.exists else "Falta"
        size = f"{artifact.size_bytes:,} bytes" if artifact.exists else "no encontrado"
        cards.append(
            f"<div class='artifact'><strong>{artifact.name}</strong><br><small>{mark} · {size}</small></div>"
        )
    st.markdown("<div class='artifact-grid'>" + "".join(cards) + "</div>", unsafe_allow_html=True)


def render_methodology(state) -> None:
    st.markdown("## Informe de metodología")
    if state.methodology:
        st.markdown(state.methodology)
    else:
        st.info("No se encontró methodology_report.md para este conjunto de resultados.")


def render_manifest(state) -> None:
    st.markdown("## Manifiesto de ejecución")
    if state.manifest:
        st.json(state.manifest)
    else:
        st.info("No se encontró run_manifest.json para este conjunto de resultados.")


def render_provenance(state) -> None:
    st.markdown("## Proveniencia y registro de fuentes")
    if state.provenance:
        st.json(state.provenance)
    else:
        st.info("No se encontró provenance.json para este conjunto de resultados.")


def render_data_quality(state) -> None:
    st.markdown("## Calidad de datos y límites de afirmaciones de tesis")
    if state.data_quality:
        st.json(state.data_quality)
    else:
        st.info("No se encontró data_quality_verdict.json para este conjunto de resultados.")
    fold_diagnostics = state.tables.get("fold_diagnostics")
    if fold_diagnostics is not None and not fold_diagnostics.empty:
        st.markdown("### Diagnóstico de pliegues fuera de muestra")
        st.dataframe(_spanish_dataframe(fold_diagnostics), width="stretch", hide_index=True)


def render_portfolio_composer(state) -> None:
    st.markdown("## Componer cartera")
    st.write(
        "Convierte los pesos del optimizador ELECTRE/Max-Sharpe en una cartera objetivo accionable. "
        "Esta pantalla todavía no envía órdenes a broker: genera una propuesta auditable y descargable."
    )
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        capital = st.number_input("Capital inicial", min_value=100.0, value=10_000.0, step=500.0)
    with col_b:
        risk_profile = st.selectbox(
            "Perfil de riesgo",
            ["conservador", "moderado", "agresivo"],
            index=1,
            format_func=lambda value: str(_spanish_value(value)).capitalize(),
        )
    with col_c:
        max_positions = st.number_input("Máximo de ETF", min_value=1, max_value=20, value=5, step=1)

    target = build_target_portfolio_from_state(
        state,
        capital=float(capital),
        risk_profile=str(risk_profile),
        max_positions=int(max_positions),
    )
    if target is None:
        st.warning(
            "No hay pesos ELECTRE o universo elegible para componer una cartera. "
            "Ejecuta primero el experimento sprint robusto."
        )
        return

    st.success(target.summary_es)
    metric_html = (
        "<div class='metric-row'>"
        + html_metric("Perfil", target.profile_es)
        + html_metric("Fecha de pesos", target.as_of)
        + html_metric("ETF seleccionados", len(target.lines))
        + html_metric("Peso total", f"{target.total_weight:.0%}")
        + "</div>"
    )
    st.markdown(metric_html, unsafe_allow_html=True)

    target_df = target.to_dataframe()
    st.markdown("### Cartera objetivo")
    st.dataframe(target_df, width="stretch", hide_index=True)
    st.download_button(
        "Descargar cartera objetivo CSV",
        data=target_df.to_csv(index=False).encode("utf-8"),
        file_name="cartera_objetivo.csv",
        mime="text/csv",
    )
    st.info(
        "Siguiente frontera: conectar esta propuesta con posiciones reales de IBKR en modo solo lectura "
        "para calcular rebalanceos contra la cartera actual."
    )


def command_runner(spec: CommandSpec, key: str) -> None:
    st.code(spec.preview, language="bash")
    execute = st.checkbox("Ejecutar este comando desde el panel", key=f"{key}_confirm")
    if st.button(f"Ejecutar: {_spanish_value(spec.label)}", key=f"{key}_run", disabled=not execute):
        with st.status(f"Ejecutando {_spanish_value(spec.label)}", expanded=True) as status:
            result = run_command(spec, timeout_seconds=7200)
            st.code(result.output or "Sin salida", language="text")
            if result.succeeded:
                status.update(label="Comando completado", state="complete")
            else:
                status.update(label=f"El comando falló con salida {result.returncode}", state="error")


def render_workflows() -> None:
    st.markdown("## Flujos de trabajo")
    st.caption("Los comandos se muestran antes de ejecutarse. Marca la casilla para ejecutar uno localmente desde el panel.")

    with st.expander("1. Construir universo de ETF", expanded=False):
        universe_out = Path(st.text_input("Directorio de salida del universo", str(REPO_ROOT / "data" / "universe")))
        command_runner(build_universe_command(universe_out), "build_universe")

    with st.expander("2. Descargar datos OHLCV de Yahoo Finance", expanded=False):
        col_a, col_b = st.columns(2)
        with col_a:
            universe = Path(st.text_input("CSV del universo", str(DEFAULT_UNIVERSE), key="download_universe"))
            start = st.text_input("Inicio", "2020-12-31", key="download_start")
            batch_size = st.number_input("Tamaño de lote", min_value=1, value=25, step=1)
        with col_b:
            out = Path(st.text_input("Directorio de salida de datos", str(DEFAULT_PILOT_DATA), key="download_out"))
            end = st.text_input("Fin", "2024-12-31", key="download_end")
            max_retries = st.number_input("Reintentos máximos", min_value=0, value=3, step=1)
        limit_enabled = st.checkbox("Usar límite piloto", value=True)
        limit = st.number_input("Límite de tickers", min_value=0, value=300, step=10) if limit_enabled else None
        command_runner(
            build_download_command(
                universe=universe,
                start=start,
                end=end,
                out=out,
                batch_size=int(batch_size),
                max_retries=int(max_retries),
                limit=int(limit) if limit is not None else None,
            ),
            "download",
        )

    with st.expander("3. Ejecutar pipeline MVP", expanded=False):
        col_a, col_b = st.columns(2)
        with col_a:
            prices = Path(st.text_input("Parquet de precios", str(DEFAULT_PILOT_DATA / "close.parquet"), key="pipeline_prices"))
            volume_text = st.text_input("Parquet de volumen", str(DEFAULT_PILOT_DATA / "volume.parquet"), key="pipeline_volume")
        with col_b:
            out = Path(st.text_input("Directorio de salida del pipeline", str(REPO_ROOT / "results"), key="pipeline_out"))
        command_runner(
            build_pipeline_command(prices=prices, volume=Path(volume_text) if volume_text else None, out=out),
            "pipeline",
        )

    with st.expander("4. Ejecutar experimento sprint robusto", expanded=True):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            universe = Path(st.text_input("CSV del universo", str(DEFAULT_UNIVERSE), key="sprint_universe"))
            start = st.text_input("Inicio", "2020-12-31", key="sprint_start")
            min_coverage = st.number_input("Cobertura mínima", min_value=0.0, max_value=1.0, value=0.8, step=0.01)
        with col_b:
            prices_text = st.text_input("Parquet de precios", str(DEFAULT_PILOT_DATA / "close.parquet"), key="sprint_prices")
            end = st.text_input("Fin", "2024-12-31", key="sprint_end")
            min_volume = st.number_input("Volumen medio mínimo en dólares", min_value=0.0, value=0.0, step=100000.0)
        with col_c:
            volume_text = st.text_input("Parquet de volumen", str(DEFAULT_PILOT_DATA / "volume.parquet"), key="sprint_volume")
            rebalance = st.selectbox("Rebalanceo", ["annual", "quarterly", "monthly"], format_func=_spanish_value)
            cost_bps = st.number_input("Coste en pb", min_value=0.0, value=10.0, step=1.0)
        out = Path(st.text_input("Directorio de salida del sprint", str(DEFAULT_RESULTS), key="sprint_out"))
        command_runner(
            build_sprint_command(
                universe=universe,
                prices=Path(prices_text) if prices_text else None,
                volume=Path(volume_text) if volume_text else None,
                start=start,
                end=end,
                rebalance=rebalance,
                cost_bps=float(cost_bps),
                out=out,
                min_coverage_pct=float(min_coverage),
                min_avg_dollar_volume=float(min_volume),
            ),
            "sprint",
        )


def main() -> None:
    st.set_page_config(
        page_title="Panel del Optimizador de ETF",
        page_icon="◌",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    with st.sidebar:
        st.markdown("## ETF Optimizer")
        theme = st.radio("Tema", ["Claro", "Oscuro"], horizontal=True)
        results_dir = Path(st.text_input("Directorio de resultados", str(DEFAULT_RESULTS)))
        page = st.radio(
            "Navegar",
            [
                "Resumen",
                "Resultados",
                "Flujos de trabajo",
                "Artefactos",
                "Metodología",
                "Manifiesto",
                "Proveniencia",
                "Calidad de datos",
                "Componer cartera",
            ],
        )
        st.caption("Interfaz sobria inspirada en Apple, con ejecución local de comandos protegida por confirmación.")

    inject_design_system(theme)
    state = load_dashboard_state(results_dir)

    if page == "Resumen":
        render_overview(state)
    elif page == "Resultados":
        render_results(state)
    elif page == "Flujos de trabajo":
        render_workflows()
    elif page == "Artefactos":
        render_artifacts(state)
    elif page == "Metodología":
        render_methodology(state)
    elif page == "Manifiesto":
        render_manifest(state)
    elif page == "Proveniencia":
        render_provenance(state)
    elif page == "Calidad de datos":
        render_data_quality(state)
    else:
        render_portfolio_composer(state)


if __name__ == "__main__":
    main()
