import type { MetricMeta, MetricKey, GlobalMetricKey, VectorizedMetricKey, MatrixMetricKey } from "./types";

// 24 metrics: 12 global, 10 vectorized, 2 matrix.
export const METRICS: Record<MetricKey, MetricMeta> = {
  // Global ------------------------------------------------------------------
  "financial_markets.global_index": { key: "financial_markets.global_index", scope: "global", domain: "Financial Markets", label: "Global Index", unit: "idx 1998=100", badWhenUp: false },
  "financial_markets.systemic_risk": { key: "financial_markets.systemic_risk", scope: "global", domain: "Financial Markets", label: "Systemic Risk", unit: "0-100", badWhenUp: true },
  "education.mean_years_schooling": { key: "education.mean_years_schooling", scope: "global", domain: "Education", label: "Mean Years Schooling", unit: "years", badWhenUp: false },
  "education.cost_index": { key: "education.cost_index", scope: "global", domain: "Education", label: "Cost Index", unit: "idx", badWhenUp: true },
  "inequality.global_gini": { key: "inequality.global_gini", scope: "global", domain: "Inequality", label: "Global Gini", unit: "0-1", badWhenUp: true },
  "inequality.top1pct_share": { key: "inequality.top1pct_share", scope: "global", domain: "Inequality", label: "Top 1% Share", unit: "%", badWhenUp: true },
  "health.life_expectancy": { key: "health.life_expectancy", scope: "global", domain: "Health", label: "Life Expectancy", unit: "years", badWhenUp: false },
  "health.diagnostic_accuracy": { key: "health.diagnostic_accuracy", scope: "global", domain: "Health", label: "Diagnostic Accuracy", unit: "0-10", badWhenUp: false },
  "science_rd.publications_index": { key: "science_rd.publications_index", scope: "global", domain: "Science & R&D", label: "Publications Index", unit: "idx", badWhenUp: false },
  "energy_climate.co2_gt_year": { key: "energy_climate.co2_gt_year", scope: "global", domain: "Energy / Climate", label: "CO₂ Emissions", unit: "Gt/yr", badWhenUp: true },
  "energy_climate.renewable_share": { key: "energy_climate.renewable_share", scope: "global", domain: "Energy / Climate", label: "Renewable Share", unit: "%", badWhenUp: false },
  "information_ecosystem.media_trust": { key: "information_ecosystem.media_trust", scope: "global", domain: "Information", label: "Media Trust", unit: "%", badWhenUp: false },

  // Vectorized --------------------------------------------------------------
  "ai_capability.frontier_capability": { key: "ai_capability.frontier_capability", scope: "vectorized", domain: "AI Capability", label: "Frontier Capability", unit: "0-100", badWhenUp: false },
  "ai_capability.population_penetration": { key: "ai_capability.population_penetration", scope: "vectorized", domain: "AI Capability", label: "Population Penetration", unit: "%", badWhenUp: false },
  "tech_industry.bigtech_concentration": { key: "tech_industry.bigtech_concentration", scope: "vectorized", domain: "Tech Industry", label: "BigTech Concentration", unit: "%", badWhenUp: true },
  "tech_industry.tech_employment_share": { key: "tech_industry.tech_employment_share", scope: "vectorized", domain: "Tech Industry", label: "Tech Employment Share", unit: "%", badWhenUp: false },
  "labor_market.automation_exposure": { key: "labor_market.automation_exposure", scope: "vectorized", domain: "Labor Market", label: "Automation Exposure", unit: "%", badWhenUp: true },
  "labor_market.employment_rate": { key: "labor_market.employment_rate", scope: "vectorized", domain: "Labor Market", label: "Employment Rate", unit: "%", badWhenUp: false },
  "governance.democracy_index": { key: "governance.democracy_index", scope: "vectorized", domain: "Governance", label: "Democracy Index", unit: "0-10", badWhenUp: false },
  "governance.ai_regulation_maturity": { key: "governance.ai_regulation_maturity", scope: "vectorized", domain: "Governance", label: "AI Regulation Maturity", unit: "0-10", badWhenUp: false },
  "information_ecosystem.disinformation_level": { key: "information_ecosystem.disinformation_level", scope: "vectorized", domain: "Information", label: "Disinformation Level", unit: "0-100", badWhenUp: true },
  "science_rd.breakthroughs_per_year": { key: "science_rd.breakthroughs_per_year", scope: "vectorized", domain: "Science & R&D", label: "Breakthroughs / yr", unit: "count", badWhenUp: false },

  // Matrix ------------------------------------------------------------------
  "geopolitics.bilateral_tensions": { key: "geopolitics.bilateral_tensions", scope: "matrix", domain: "Geopolitics", label: "Bilateral Tensions", unit: "0-100", badWhenUp: true },
  "geopolitics.active_conflicts": { key: "geopolitics.active_conflicts", scope: "matrix", domain: "Geopolitics", label: "Active Conflicts", unit: "count", badWhenUp: true },
};

export const GLOBAL_KEYS: GlobalMetricKey[] = Object.values(METRICS).filter(m => m.scope === "global").map(m => m.key as GlobalMetricKey);
export const VECTORIZED_KEYS: VectorizedMetricKey[] = Object.values(METRICS).filter(m => m.scope === "vectorized").map(m => m.key as VectorizedMetricKey);
export const MATRIX_KEYS: MatrixMetricKey[] = Object.values(METRICS).filter(m => m.scope === "matrix").map(m => m.key as MatrixMetricKey);

export const GLOBAL_DOMAINS = Array.from(new Set(GLOBAL_KEYS.map(k => METRICS[k].domain)));
export const VECTORIZED_DOMAINS = Array.from(new Set(VECTORIZED_KEYS.map(k => METRICS[k].domain)));

export function metricShortLabel(key: MetricKey): string {
  return METRICS[key].label;
}
