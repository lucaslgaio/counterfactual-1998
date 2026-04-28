# Review Targets — Etapa 2

Edges identificadas para revisão metodológica focada na Etapa 2. Geradas automaticamente por `scripts/identify_review_targets.py`.

**Total**: 28 edges (de ~130) em 6 clusters.

## Critérios aplicados

- `direction_contested`: edges com `direction_contested: true` (decisão de direção pendente)
- `strong`: magnitude `strong` (alto impacto se errada)
- `underconnected`: edges adicionadas na Rodada 3 cuja source ou target está em `health.*` ou `science_rd.*` (inclui `health.mental_wellbeing`)
- `unverified_ref`: justificativa em `edges_justifications.md` contém `[verificar referência]`

Cada edge é listada em exatamente um cluster — o cluster da métrica de **source**. O reviewer do cluster destino pode flaggar spillover concerns durante a sessão se quiser.

---

## Cluster: `tecnologia_ia` (7 edges)

### e_001: `ai_capability.frontier_capability` → `labor_market.automation_exposure`

- **Cluster**: tecnologia_ia
- **Critério(s)**: strong
- **Magnitude atual**: strong
- **Direção atual**: positive
- **Lag atual**: 2 turnos
- **Scope**: within_block
- **PR onde mora**: #1 (etapa-1)
- **Status revisão**: pending

### e_008: `ai_capability.population_penetration` → `tech_industry.tech_employment_share`

- **Cluster**: tecnologia_ia
- **Critério(s)**: direction_contested
- **Magnitude atual**: negligible
- **Direção atual**: positive (contested)
- **Lag atual**: 4 turnos
- **Scope**: within_block
- **PR onde mora**: #3 (rodada-2)
- **Nota inline**: Rodada 2: direção contestada (penetração pode aumentar OU diminuir tech_employment); magnitude weak→negligible (efeito quase nulo no agregado)
- **Status revisão**: pending

### e_037: `ai_capability.frontier_capability` → `science_rd.breakthroughs_per_year`

- **Cluster**: tecnologia_ia
- **Critério(s)**: strong
- **Magnitude atual**: strong
- **Direção atual**: positive
- **Lag atual**: 2 turnos
- **Scope**: within_block
- **PR onde mora**: #3 (rodada-2)
- **Nota inline**: Rodada 2: magnitude medium→strong (AlphaFold mostrou que IA de fronteira acelera ciência radicalmente)
- **Status revisão**: pending

### e_101: `ai_capability.population_penetration` → `education.mean_years_schooling`

- **Cluster**: tecnologia_ia
- **Critério(s)**: direction_contested
- **Magnitude atual**: medium
- **Direção atual**: positive (contested)
- **Lag atual**: 6 turnos
- **Scope**: within_block
- **PR onde mora**: #4 (rodada-3)
- **Nota inline**: Rodada 3 - PROVAVELMENTE A EDGE MAIS IMPORTANTE FALTANDO. Direção contestada: tutoria personalizada barata (positiva) vs cognitive offloading (negativa). Debate Caplan vs ed-tech otimistas. Mecanismo de transformação cultural mais conseq...
- **Status revisão**: pending

### e_123: `ai_capability.frontier_capability` → `health.life_expectancy`

- **Cluster**: tecnologia_ia
- **Critério(s)**: underconnected
- **Magnitude atual**: medium
- **Direção atual**: positive
- **Lag atual**: 8 turnos
- **Scope**: global
- **PR onde mora**: #4 (rodada-3)
- **Nota inline**: Rodada 3: personalized medicine, drug discovery, public health surveillance; canal direto além de breakthroughs/diagnostic
- **Status revisão**: pending

### e_126: `tech_industry.bigtech_concentration` → `science_rd.breakthroughs_per_year`

- **Cluster**: tecnologia_ia
- **Critério(s)**: underconnected
- **Magnitude atual**: weak
- **Direção atual**: positive
- **Lag atual**: 4 turnos
- **Scope**: within_block
- **PR onde mora**: #4 (rodada-3)
- **Nota inline**: Rodada 3: BigTech labs (DeepMind, FAIR, MSR) produzem fração crescente de breakthroughs em IA pós-2015
- **Status revisão**: pending

### e_132: `ai_capability.population_penetration` → `health.mental_wellbeing`

- **Cluster**: tecnologia_ia
- **Critério(s)**: direction_contested / underconnected
- **Magnitude atual**: medium
- **Direção atual**: positive (contested)
- **Lag atual**: 4 turnos
- **Scope**: within_block
- **PR onde mora**: #4 (rodada-3)
- **Nota inline**: Rodada 3: tutoria/parceria IA pode aliviar OU exacerbar isolamento. Direção contestada.
- **Status revisão**: pending

## Cluster: `economia` (8 edges)

### e_009: `labor_market.automation_exposure` → `inequality.gini_intra_block`

- **Cluster**: economia
- **Critério(s)**: strong
- **Magnitude atual**: strong
- **Direção atual**: positive
- **Lag atual**: 4 turnos
- **Scope**: within_block
- **PR onde mora**: #1 (etapa-1)
- **Status revisão**: pending

### e_010: `labor_market.automation_exposure` → `inequality.top1pct_share`

- **Cluster**: economia
- **Critério(s)**: unverified_ref
- **Magnitude atual**: medium
- **Direção atual**: positive
- **Lag atual**: 4 turnos
- **Scope**: global
- **PR onde mora**: #1 (etapa-1)
- **Status revisão**: pending

### e_014: `labor_market.employment_rate` → `education.mean_years_schooling`

- **Cluster**: economia
- **Critério(s)**: direction_contested
- **Magnitude atual**: negligible
- **Direção atual**: positive (contested)
- **Lag atual**: 8 turnos
- **Scope**: within_block
- **PR onde mora**: #3 (rodada-2)
- **Nota inline**: Rodada 2: direção contestada (pleno emprego pode reduzir incentivo a estudar OU aumentar via maior renda); magnitude weak→negligible
- **Status revisão**: pending

### e_075: `financial_markets.systemic_risk` → `financial_markets.global_index`

- **Cluster**: economia
- **Critério(s)**: strong
- **Magnitude atual**: strong
- **Direção atual**: negative
- **Lag atual**: 0 turnos
- **Scope**: global
- **PR onde mora**: #1 (etapa-1)
- **Status revisão**: pending

### e_081: `labor_market.automation_exposure` → `labor_market.employment_rate`

- **Cluster**: economia
- **Critério(s)**: strong
- **Magnitude atual**: strong
- **Direção atual**: negative
- **Lag atual**: 4 turnos
- **Scope**: within_block
- **PR onde mora**: #3 (rodada-2)
- **Nota inline**: Rodada 2: magnitude medium→strong (exposição se realiza em desemprego com força considerável; Acemoglu/Restrepo evidência empírica robusta)
- **Status revisão**: pending

### e_082: `labor_market.automation_exposure` → `tech_industry.tech_employment_share`

- **Cluster**: economia
- **Critério(s)**: direction_contested
- **Magnitude atual**: negligible
- **Direção atual**: positive (contested)
- **Lag atual**: 6 turnos
- **Scope**: within_block
- **PR onde mora**: #3 (rodada-2)
- **Nota inline**: Rodada 2: direção contestada; magnitude weak→negligible
- **Status revisão**: pending

### e_124: `labor_market.employment_rate` → `health.life_expectancy`

- **Cluster**: economia
- **Critério(s)**: underconnected
- **Magnitude atual**: weak
- **Direção atual**: positive
- **Lag atual**: 8 turnos
- **Scope**: global
- **PR onde mora**: #4 (rodada-3)
- **Nota inline**: Rodada 3: stress de desemprego, perda de healthcare nos US, deaths of despair (Case & Deaton); volta corrigida do e_083 removido
- **Status revisão**: pending

### e_129: `financial_markets.global_index` → `science_rd.publications_index`

- **Cluster**: economia
- **Critério(s)**: underconnected
- **Magnitude atual**: weak
- **Direção atual**: positive
- **Lag atual**: 4 turnos
- **Scope**: global
- **PR onde mora**: #4 (rodada-3)
- **Nota inline**: Rodada 3: mercados em alta → corporate R&D → publicações
- **Status revisão**: pending

## Cluster: `sociedade` (3 edges)

### e_104: `education.mean_years_schooling` → `information_ecosystem.media_trust`

- **Cluster**: sociedade
- **Critério(s)**: direction_contested
- **Magnitude atual**: weak
- **Direção atual**: positive (contested)
- **Lag atual**: 8 turnos
- **Scope**: global
- **PR onde mora**: #4 (rodada-3)
- **Nota inline**: Rodada 3: educação como capacidade crítica (mais discriminação de fontes confiáveis) vs cinismo (desconfiança de tudo). Direção contestada. Scope global porque target media_trust é global.
- **Status revisão**: pending

### e_122: `inequality.gini_intra_block` → `health.life_expectancy`

- **Cluster**: sociedade
- **Critério(s)**: underconnected
- **Magnitude atual**: medium
- **Direção atual**: negative
- **Lag atual**: 8 turnos
- **Scope**: global
- **PR onde mora**: #4 (rodada-3)
- **Nota inline**: Rodada 3: Wilkinson & Pickett 'The Spirit Level' — desigualdade alta encurta vida média mesmo controlando renda absoluta
- **Status revisão**: pending

### e_133: `inequality.gini_intra_block` → `health.mental_wellbeing`

- **Cluster**: sociedade
- **Critério(s)**: underconnected
- **Magnitude atual**: medium
- **Direção atual**: negative
- **Lag atual**: 6 turnos
- **Scope**: within_block
- **PR onde mora**: #4 (rodada-3)
- **Nota inline**: Rodada 3: desigualdade alta correlaciona com pior saúde mental média (Wilkinson)
- **Status revisão**: pending

## Cluster: `informacao_ambiente` (3 edges)

### e_028: `information_ecosystem.disinformation_level` → `information_ecosystem.media_trust`

- **Cluster**: informacao_ambiente
- **Critério(s)**: strong
- **Magnitude atual**: strong
- **Direção atual**: negative
- **Lag atual**: 1 turnos
- **Scope**: global
- **PR onde mora**: #1 (etapa-1)
- **Status revisão**: pending

### e_110: `energy_climate.co2_gt_year` → `health.life_expectancy`

- **Cluster**: informacao_ambiente
- **Critério(s)**: underconnected
- **Magnitude atual**: medium
- **Direção atual**: negative
- **Lag atual**: 12 turnos
- **Scope**: global
- **PR onde mora**: #4 (rodada-3)
- **Nota inline**: Rodada 3: climate change → eventos extremos + poluição → mortalidade (Lancet Countdown); lag longo mas mecanismo robusto
- **Status revisão**: pending

### e_134: `information_ecosystem.disinformation_level` → `health.mental_wellbeing`

- **Cluster**: informacao_ambiente
- **Critério(s)**: underconnected
- **Magnitude atual**: weak
- **Direção atual**: negative
- **Lag atual**: 2 turnos
- **Scope**: within_block
- **PR onde mora**: #4 (rodada-3)
- **Nota inline**: Rodada 3: ecossistema informacional saturado → ansiedade, paranoia, desorientação
- **Status revisão**: pending

## Cluster: `politica` (2 edges)

### e_128: `governance.ai_regulation_maturity` → `science_rd.breakthroughs_per_year`

- **Cluster**: politica
- **Critério(s)**: direction_contested / underconnected
- **Magnitude atual**: weak
- **Direção atual**: negative (contested)
- **Lag atual**: 4 turnos
- **Scope**: within_block
- **PR onde mora**: #4 (rodada-3)
- **Nota inline**: Rodada 3: regulação retarda (gain-of-function) ou acelera (safety standards = trust = funding)? Genuinamente ambígua.
- **Status revisão**: pending

### e_130: `geopolitics.active_conflicts` → `science_rd.breakthroughs_per_year`

- **Cluster**: politica
- **Critério(s)**: direction_contested / underconnected
- **Magnitude atual**: weak
- **Direção atual**: positive (contested)
- **Lag atual**: 4 turnos
- **Scope**: global
- **PR onde mora**: #4 (rodada-3)
- **Nota inline**: Rodada 3: wars catalisam invenções (radar, internet, GPS) mas desestabilizam pesquisa civil
- **Status revisão**: pending

## Cluster: `conhecimento_saude` (5 edges)

### e_125: `health.diagnostic_accuracy` → `financial_markets.systemic_risk`

- **Cluster**: conhecimento_saude
- **Critério(s)**: underconnected
- **Magnitude atual**: weak
- **Direção atual**: negative
- **Lag atual**: 4 turnos
- **Scope**: global
- **PR onde mora**: #4 (rodada-3)
- **Nota inline**: Rodada 3: detecção precoce de pandemias reduz risco sistêmico catastrófico (COVID-19 mostrou magnitude potencial)
- **Status revisão**: pending

### e_127: `science_rd.publications_index` → `governance.ai_regulation_maturity`

- **Cluster**: conhecimento_saude
- **Critério(s)**: underconnected
- **Magnitude atual**: weak
- **Direção atual**: positive
- **Lag atual**: 6 turnos
- **Scope**: within_block
- **PR onde mora**: #4 (rodada-3)
- **Nota inline**: Rodada 3: mais publicação → mais material pra reguladores entenderem riscos → regulação mais sofisticada (alignment papers viraram base de AI Act)
- **Status revisão**: pending

### e_131: `science_rd.publications_index` → `science_rd.publications_index`

- **Cluster**: conhecimento_saude
- **Critério(s)**: underconnected
- **Magnitude atual**: weak
- **Direção atual**: positive
- **Lag atual**: 4 turnos
- **Scope**: within_block
- **PR onde mora**: #4 (rodada-3)
- **Nota inline**: Rodada 3: cumulative knowledge — papers citam papers, snowball; bem documentado em scientometrics
- **Status revisão**: pending

### e_135: `health.mental_wellbeing` → `labor_market.employment_rate`

- **Cluster**: conhecimento_saude
- **Critério(s)**: underconnected
- **Magnitude atual**: weak
- **Direção atual**: positive
- **Lag atual**: 4 turnos
- **Scope**: within_block
- **PR onde mora**: #4 (rodada-3)
- **Nota inline**: Rodada 3: bem-estar mental afeta participação no mercado de trabalho
- **Status revisão**: pending

### e_136: `health.mental_wellbeing` → `governance.democracy_index`

- **Cluster**: conhecimento_saude
- **Critério(s)**: underconnected
- **Magnitude atual**: weak
- **Direção atual**: positive
- **Lag atual**: 8 turnos
- **Scope**: within_block
- **PR onde mora**: #4 (rodada-3)
- **Nota inline**: Rodada 3: cidadania exige bandwidth psicossocial; depressão/ansiedade massiva debilita instituições
- **Status revisão**: pending

