# Data sources

Each historical series in `data/historical/` is documented here. Confidence
column is the loader's signal of "trust this number how much" (0–1).

## Series with usable data

### `co2_emissions_global.csv`
- **Metric**: `energy_climate.co2_gt_year`
- **Source**: Our World in Data / Global Carbon Project (https://ourworldindata.org/co2-emissions)
- **Date collected**: 2026-04 (from public summaries)
- **Confidence**: 0.8
- **Processing**: Annual data points (1998 ≈ 24.4 GtCO2; 2024 ≈ 37.4 GtCO2) interpolated linearly to 58 semestral turns. Includes the 2020 COVID dip (~34.8).
- **Limitations**: numbers are approximated from public-summary statistics, not pulled from primary CSV downloads. Re-fetching from OWID's API would tighten confidence to 0.95+.

### `life_expectancy_global.csv`
- **Metric**: `health.life_expectancy`
- **Source**: UN World Population Prospects (https://population.un.org/wpp/)
- **Confidence**: 0.8
- **Processing**: annual UN estimates → semestral linear interp. Captures the 2020–2022 COVID dip.
- **Limitations**: same approximation caveat.

### `top1pct_share.csv`
- **Metric**: `inequality.top1pct_share`
- **Source**: World Inequality Database (https://wid.world/)
- **Confidence**: 0.6
- **Processing**: annual global top-1% wealth share → semestral interp. Trajectory: 19% (1998) → ~28% (2024 estimated).
- **Limitations**: WID has multiple definitions (income vs wealth, pre-tax vs post-tax). Numbers here are an aggregate consistent with public summaries; a direct WID download would clarify which series is being matched.

### `active_conflicts_total.csv`
- **Metric**: `geopolitics.active_conflicts`
- **Source**: UCDP/PRIO Armed Conflict Dataset (https://ucdp.uu.se/)
- **Confidence**: 0.7
- **Processing**: annual count of armed conflicts (>1000 battle deaths/year) → semestral interp. Notable: 2014–2015 step up after Syrian war and Donbas; 2022 spike with Ukraine.
- **Limitations**: UCDP definitions changed in 2014 — values pre/post may not be directly comparable.

### `renewable_share_global.csv`
- **Metric**: `energy_climate.renewable_share`
- **Source**: IEA / Our World in Data
- **Confidence**: 0.7
- **Processing**: annual renewable share of total final energy consumption → semestral interp.
- **Limitations**: which renewables are included (hydro? biomass?) varies by source. Approximation here assumes the broad IEA definition.

### `employment_rate_global.csv`
- **Metric**: `labor_market.employment_rate`
- **Source**: ILOSTAT (https://ilostat.ilo.org/)
- **Confidence**: 0.7
- **Processing**: annual employment-to-population ratio (15+) → semestral interp. Includes 2020 COVID dip.
- **Limitations**: ILO has multiple working-age definitions; numbers here use the 15+ population standard.

### `financial_markets_global.csv`
- **Metric**: `financial_markets.global_index`
- **Source**: MSCI ACWI / S&P 500 (rebased to 100 in 1998-S1)
- **Confidence**: 0.6
- **Processing**: annual index values, rebased to 1998-S1 = 100.
- **Limitations**: which index is "the" global index is debated. The proxy here tracks a US-heavy global benchmark. A weighted blend of MSCI ACWI + emerging-markets index would be more representative of the full ~30/27/7/36 GDP-weighted blocks.

## PLACEHOLDER series (not yet fetched)

These files exist in `data/historical/` with the suffix `_PLACEHOLDER` so
the structure is visible, but they're skipped by the loader and don't
participate in calibration:

| File                                          | Metric                                | What's needed                                            |
|-----------------------------------------------|---------------------------------------|----------------------------------------------------------|
| `gini_intra_block_US_PLACEHOLDER.csv`         | `inequality.gini_intra_block`         | WID country-level Gini, aggregated to bloc.              |
| `gini_intra_block_EU_PLACEHOLDER.csv`         | … / EU                                | Same.                                                    |
| `mean_years_schooling_US_PLACEHOLDER.csv`     | `education.mean_years_schooling`      | UNDP HDR per country.                                    |
| `mean_years_schooling_CN_PLACEHOLDER.csv`     | … / CN                                | Same.                                                    |
| `democracy_v_dem_US_PLACEHOLDER.csv`          | `governance.democracy_index`          | V-Dem CSV download via DOI.                              |
| `democracy_v_dem_CN_PLACEHOLDER.csv`          | … / CN                                | Same.                                                    |
| `gdp_global_PLACEHOLDER.csv`                  | (used as weight overrides)            | World Bank WDI.                                          |

When a primary-source CSV becomes available, drop it in `data/historical/`
without the PLACEHOLDER suffix and re-run `scripts/calibrate.py`. The
loader picks it up automatically; no code change required.

## Issue tracker

Open data tasks: search for `[etapa-5][data-needed]` on the GitHub issues page.
