# Revisión de literatura: sesgos de universo en backtests de ETFs

**Tema:** survivorship bias, look-ahead bias e incumbent-only bias al construir universos ETF para backtesting.  
**Pregunta:** ¿es irresoluble el problema de parcialidad si se usa una base estática?  
**Conclusión corta:** no es irresoluble, pero tampoco se resuelve con una base estática. El estándar defendible es un universo dinámico *point-in-time* (`constituents_as_of(date)`) con entradas, salidas, fechas de inicio/listado, filtros de investibilidad y tratamiento explícito de fondos cerrados o desaparecidos.

---

## 1. Diagnóstico del problema

En el optimizador ETF hay tres sesgos distintos que deben separarse:

1. **Survivorship / current-universe bias**  
   Usar en 2018 una lista de ETFs descargada en 2026. Esto introduce activos que no existían o no eran observables en 2018 y excluye ETFs cerrados antes de 2026.

2. **Look-ahead bias**  
   Usar información que no estaba disponible en la fecha de decisión: tickers futuros, AUM futuro, clasificación futura, volumen futuro, historial completo posterior, o conocimiento de que un ETF sobrevivió.

3. **Incumbent-only bias**  
   Usar solo el universo 2018 para todo 2018-2025. Esto evita tickers futuros al inicio, pero sesga el backtest contra ETFs que sí entraron legítimamente al mercado después.

La solución correcta no es `static_current` ni `static_start`, sino:

```python
universe_t = provider.constituents_as_of(rebalance_date)
```

---

## 2. Trabajos fundacionales sobre survivorship bias

### Brown, Goetzmann, Ibbotson & Ross (1992)

**Trabajo:** *Survivorship Bias in Performance Studies*, Review of Financial Studies. DOI: `10.1093/rfs/5.4.553`.

**Aporte:** formaliza que los estudios de performance se inflan si solo observan entidades sobrevivientes. El punto central para nuestro caso es que la muestra observada al final del período no es equivalente a la muestra invertible al inicio o en cada fecha histórica.

**Implicación para ETFs:** un ETF que existe hoy tiene una condición implícita de supervivencia. Si se usa una lista actual, se está condicionando el universo histórico a haber sobrevivido.

---

### Elton, Gruber & Blake (1996)

**Trabajo:** *Survivor Bias and Mutual Fund Performance*, Review of Financial Studies. DOI: `10.1093/rfs/9.4.1097`.

**Aporte:** mide empíricamente cómo la exclusión de fondos desaparecidos distorsiona las estimaciones de performance. Aunque el objeto son mutual funds, la analogía con ETFs es directa: los ETFs también cierran, se fusionan, cambian ticker o desaparecen.

**Cómo lo tratan:** incluyen fondos no sobrevivientes o corrigen la muestra para no estimar performance solo con fondos vivos.

**Implicación:** para backtests ETF largos, el dataset debe incluir fondos cerrados/deslistados o, al menos, registrar `last_seen_date` y eventos de salida.

---

### Carhart, Carpenter, Lynch & Musto (2002)

**Trabajo:** *Mutual Fund Survivorship*, Review of Financial Studies. DOI: `10.1093/rfs/15.5.1439`.

**Aporte:** analiza la dinámica de desaparición de fondos y cómo la supervivencia está relacionada con performance. No es un evento aleatorio neutral: los fondos malos tienden a desaparecer más.

**Implicación:** excluir ETFs cerrados puede sobreestimar retornos, Sharpe y estabilidad, porque los cierres no son completamente exógenos.

---

### Elton, Gruber & Blake / CRSP-Morningstar database accuracy literature

**Trabajo relacionado:** *A First Look at the Accuracy of the CRSP Mutual Fund Database and a Comparison of the CRSP and Morningstar Mutual Fund Databases*, Journal of Finance. DOI: `10.1111/0022-1082.00410`.

**Aporte:** muestra que incluso bases profesionales requieren validación y que la elección de fuente afecta los resultados.

**Implicación:** no basta decir “uso una fuente”. Hay que documentar cobertura, sobrevivientes/no sobrevivientes, identificadores, fechas efectivas y errores de mapping.

---

## 3. Estado del arte práctico en investigación financiera

### 3.1. Bases survivor-bias-free

El estándar académico/comercial para mutual funds y, en parte, ETFs, es usar bases con historial de fondos vivos y muertos. Ejemplos:

- CRSP Survivorship-Bias-Free US Mutual Fund Database.
- Morningstar Direct / Morningstar historical funds.
- Lipper / Refinitiv.
- Bloomberg fund datasets.
- Bases institucionales con identificadores permanentes y eventos de liquidación/fusión.

**Cómo tratan el problema:**

- identificadores persistentes de fondo/clase;
- fondos vivos y muertos;
- fechas de inicio y fin;
- retornos históricos por clase;
- cambios de nombre/ticker;
- liquidaciones/fusiones;
- en algunos casos, retornos de delisting/liquidación.

**Desventaja para este proyecto:** suelen ser pagos/licenciados y no siempre cubren ETFs/ETPs con el nivel requerido.

---

### 3.2. Investigación de fondos con CRSP y similares

Trabajos posteriores sobre skill/luck/performance de fondos, por ejemplo Barras, Scaillet & Wermers (2010) y Fama & French (2010), típicamente dependen de bases tipo CRSP que incluyen fondos desaparecidos. La idea metodológica común es:

```text
No construir la muestra desde una lista final de sobrevivientes.
```

**Lección:** el estándar no es “filtrar los ETFs que tengan precio hoy”; el estándar es reconstruir qué estaba disponible en cada fecha histórica.

---

### 3.3. Literatura de backtesting y overfitting

Bailey, Borwein, López de Prado & Zhu (2016), *The Probability of Backtest Overfitting*, Journal of Computational Finance. DOI: `10.21314/jcf.2016.322`.

**Aporte:** advierte que muchos backtests aparentan funcionar por sobreajuste y selección retrospectiva.

**Relación con nuestro problema:** si además de probar muchas variantes ELECTRE/rebalanceo se usa un universo con información futura, el resultado puede ser doblemente optimista: por selección de modelos y por sesgo de datos.

**Tratamiento recomendado:**

- walk-forward real;
- separación train/OOS;
- universe-as-of;
- pruebas pareadas vs benchmarks;
- registro de experimentos;
- evitar reoptimizar después de mirar el OOS sin etiquetar la corrida como exploratoria.

---

## 4. Fuentes públicas aplicables a ETFs

### 4.1. SEC Investment Company Series and Class Information

La SEC publica archivos anuales de series/classes de investment companies. Archivo confirmado para 2018:

```text
https://www.sec.gov/files/investment/data/other/investment-company-series-and-class-information/investment_company_series_class_2018.csv
```

Columnas útiles:

```text
CIK
entity_name
series_id
series_name
class_id
class_name
class_ticker_symbol
```

**Uso propuesto:** reconstruir snapshots anuales de ETFs candidatos.

**Ventaja:** fuente oficial, pública, con tickers e identificadores SEC.

**Limitación:** no es un dataset ETF limpio; incluye mutual funds, variable annuities, money market funds y otros registros. Requiere heurísticas y validación.

---

### 4.2. SEC Form N-PORT Data Sets

Página oficial:

```text
https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets
```

Cobertura observada en la página SEC: desde **2019 Q4** hasta 2026 Q1 en la revisión actual.

**Uso propuesto:** validar fondos activos, net assets, holdings y metadata desde 2019Q4.

**Limitación:** no cubre 2018; requiere mapping `series_id`/CIK/ticker contra Series/Class.

---

### 4.3. Precios: Yahoo/Stooq/EODHD/etc.

Estas fuentes sirven para precios/volumen, pero no para definir el universo histórico. Tener precio descargable no demuestra que el ETF pertenecía al universo investible definido ni evita sesgo de supervivencia.

**Regla:** precios y universo deben ser capas separadas.

---

## 5. Cómo lo trataron trabajos similares

| Línea de trabajo | Problema | Tratamiento típico | Lección para nuestro ETF optimizer |
|---|---|---|---|
| Mutual fund performance | Fondos muertos excluidos | Bases survivor-bias-free, inclusión de fondos desaparecidos | Necesitamos `first_seen`/`last_seen` y eventos de cierre |
| Hedge fund / fund databases | Backfill y survivorship | Fechas de inclusión, corrección de backfill, muestras vivas+muertas | No usar datos anteriores a disponibilidad real |
| Equity factor backtests | Acciones deslistadas y cambios de índices | CRSP con delisting returns; constituyentes históricos | ETFs deben entrar/salir por fecha, no por lista final |
| ETF empirical studies | Muestra ETF histórica | Morningstar/CRSP/Bloomberg/Lipper o filtros por inception/listing | Si usamos público, debemos documentar menor calidad que CRSP |
| Quant ML/backtesting | Overfitting y leakage | Walk-forward, purging/embargo, OOS, control de experimentos | Universe-as-of es parte de la prevención de leakage |

---

## 6. ¿Es irresoluble?

No. Hay tres niveles de solución:

### Nivel A — Solución ideal institucional

Usar CRSP/Morningstar/Lipper/Bloomberg/Refinitiv con ETFs vivos y muertos, fechas de inicio/fin, fusiones, liquidaciones y retornos de cierre.

**Calidad:** alta.  
**Costo:** alto.  
**Estado:** thesis-grade si la licencia está disponible.

---

### Nivel B — Solución pública defendible

Reconstruir universo dinámico con:

```text
SEC Series/Class anual + N-PORT desde 2019Q4 + precios/volumen + filtros de investibilidad
```

**Calidad:** media-alta para proyecto público, no perfecta.  
**Costo:** bajo.  
**Estado:** defendible si se etiqueta como “approximate public point-in-time ETF universe”.

---

### Nivel C — Solución débil / solo piloto

Usar Nasdaq/StockAnalysis/ETF screener actual.

**Calidad:** baja para claims históricos.  
**Estado:** útil para desarrollo, no para conclusión final.

---

## 7. Diseño recomendado para el proyecto

Implementar `PointInTimeETFUniverseProvider` con esta tabla maestra:

```text
ticker
fund_id
cik
series_id
class_id
fund_name
issuer
first_seen_date
last_seen_date
inception_date
delisting_date
source
source_year
is_etf_candidate
etf_confidence
```

En cada fecha de rebalanceo:

```python
eligible = provider.constituents_as_of(
    date=rebalance_date,
    min_age_months=12,
    min_coverage_pct=0.80,
    min_avg_dollar_volume=threshold,
)
```

Reglas mínimas:

1. El ETF no puede entrar antes de `first_seen_date`/`inception_date`.
2. El ETF debe salir después de `last_seen_date`/`delisting_date` si desaparece.
3. Los criterios ELECTRE solo pueden usar datos conocidos hasta `rebalance_date`.
4. N-PORT debe usarse con lag de publicación/reporting, no como dato instantáneo del trimestre si no estaba disponible.
5. Si un ETF desaparece mientras está en cartera, registrar evento de liquidación/salida.

---

## 8. Modos metodológicos que conviene reportar

Para transparencia, dejar tres modos:

```text
static_current  -> solo desarrollo/debug; sesgado por supervivencia y look-ahead.
static_start    -> control conservador; sesgado contra nuevos ETFs.
point_in_time   -> modo principal de tesis.
```

El paper/tesis debe presentar resultados principales solo de `point_in_time`. Los otros modos sirven como sensibilidad para mostrar cuánto cambia la conclusión por el sesgo de universo.

---

## 9. Veredicto

El problema de parcialidad no es irresoluble. Lo que sí es incorrecto es pretender resolverlo con una base estática.

La solución de estado del arte es reconstruir el universo disponible en cada fecha histórica. Con datos públicos podemos aproximarlo de forma defendible mediante SEC Series/Class anual y N-PORT desde 2019Q4. Para una afirmación institucional fuerte, la alternativa superior es una base survivor-bias-free comercial/académica como CRSP/Morningstar/Lipper/Bloomberg/Refinitiv.

**Recomendación inmediata:** implementar el proveedor `point_in_time` y degradar cualquier backtest con universo actual a “piloto/no concluyente”.
