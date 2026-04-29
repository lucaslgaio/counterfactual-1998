# Historical data — Etapa 5 calibration

CSVs in this folder are the empirical signal that calibration optimizes the
engine against. Each CSV has columns:

```
turn_label,turn_index,value,metric_key,block,confidence,source_url,notes
```

Series are aligned to the engine's 58 semestral turns (1998-S1 .. 2026-S2)
via linear interpolation between annual data points.

## Series included (7 with real-ish data)

| Filename                          | Metric                                | Block | Confidence | Source                      |
|-----------------------------------|---------------------------------------|-------|------------|-----------------------------|
| co2_emissions_global.csv          | energy_climate.co2_gt_year            | global| 0.8        | OWID / Global Carbon Project|
| life_expectancy_global.csv        | health.life_expectancy                | global| 0.8        | UN World Population Prospects|
| top1pct_share.csv                 | inequality.top1pct_share              | global| 0.6        | World Inequality Database    |
| active_conflicts_total.csv        | geopolitics.active_conflicts          | total | 0.7        | UCDP/PRIO                   |
| renewable_share_global.csv        | energy_climate.renewable_share        | global| 0.7        | IEA / OWID                  |
| employment_rate_global.csv        | labor_market.employment_rate          | global| 0.7        | ILOSTAT                     |
| financial_markets_global.csv      | financial_markets.global_index        | global| 0.6        | MSCI ACWI / S&P 500 proxy   |

**Important caveat**: values are approximate, derived from publicly summarized
statistics rather than from primary CSV downloads. Confidence column is the
loader's signal of "trust this number how much" — a future re-fetch from the
primary source will improve all of these.

## PLACEHOLDER files (need direct download)

| Filename                                | Metric                          | Why missing                                                    |
|-----------------------------------------|---------------------------------|----------------------------------------------------------------|
| gini_intra_block_US_PLACEHOLDER.csv     | inequality.gini_intra_block / US| Per-block Gini requires downloading WID country-level CSVs and aggregating to bloc level. |
| gini_intra_block_EU_PLACEHOLDER.csv     | … / EU                          | Same.                                                          |
| mean_years_schooling_US_PLACEHOLDER.csv | education.mean_years_schooling / US | UNDP HDR Excel download per country.                       |
| mean_years_schooling_CN_PLACEHOLDER.csv | … / CN                          | Same.                                                          |
| democracy_v_dem_US_PLACEHOLDER.csv      | governance.democracy_index / US | V-Dem CSV needs DOI download + filtering.                      |
| democracy_v_dem_CN_PLACEHOLDER.csv      | … / CN                          | Same.                                                          |
| gdp_global_PLACEHOLDER.csv              | (used as weight override)       | Could be useful for weighted_mean overrides — World Bank WDI. |

The loader skips any file whose name contains `PLACEHOLDER` and logs a warning.
Calibration runs against the 7 real-ish series only — sufficient to demonstrate
the methodology.

See `docs/calibration/data_sources.md` for the full source/processing audit
and `docs/calibration/limitations.md` for what's missing and why it matters.

## Open data tasks (issue [etapa-5][data-needed])

When direct downloads from primary sources are feasible, replace the
PLACEHOLDER files with real semestral CSVs and re-run calibration. The
loader and pipeline are designed to pick them up automatically — no code
change required.
