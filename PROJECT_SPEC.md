# Counterfactual-1998 — Simulador Histórico Contrafactual

> **Projeto de pesquisa pessoal sem fim comercial.** Objetivo: explorar, via simulação em turnos com LLM, como a história mundial (1998–2026) poderia ter divergido se uma IA com capacidades comparáveis às atuais tivesse surgido no final da bolha .com.

---

## 1. Visão geral

Inspirado em duas referências:
- **BrassFoot**: jogo brasileiro de gestão de futebol em turnos, onde o jogador define táticas/inputs e o jogo resolve a partida com base em estado interno.
- **Backtest financeiro**: simulação contrafactual aplicada a uma série temporal real, para ver "o que teria acontecido se".

A unidade de simulação é a **sociedade global**, modelada por dimensões setoriais. O LLM (Claude API) atua simultaneamente como:
1. **Motor causal** — raciocina sobre como o estado alterado interage com eventos históricos reais.
2. **Narrador** — produz log textual ("no S2 de 2001, ...").
3. **Atualizador de estado** — devolve deltas numéricos que evoluem o estado quantitativo.

Saída híbrida: **narrativa + dashboards**.

A simulação é **probabilística** (estilo Monte Carlo): mesma config + seeds diferentes produzem runs divergentes. Fontes de aleatoriedade: temperature do LLM, choques exógenos sorteados a cada turno, e variabilidade nos eventos âncora.

---

## 2. Decisões de modelagem

### 2.1 Capacidade da IA (toggle no início da simulação)

- **`big_bang`** (default): em S1 1998, a IA já é equivalente ao Claude 4 atual. Choque máximo desde o turno 1.
- **`accelerated_curve`**: IA começa primitiva em 1998 e evolui ano a ano, mas partindo 25 anos antes da linha real. Mais honesto cientificamente, mas mais complexo de modelar.

### 2.2 Granularidade

- **MVP**: semestre. Período: S1 1998 → S2 2026 = 58 turnos.
- **Versões futuras**: toggle entre dia / mês / trimestre / semestre / ano / década.

### 2.3 Modo de jogo

- **Manual**: usuário decide a cada turno (estilo BrassFoot). Input é opcional — sem input, o turno segue "natural".
- **Auto**: roda do início ao fim sem intervenção (estilo backtest puro).
- **Híbrido**: auto, com pausas em "eventos âncora" para o usuário escolher como o mundo alterado responde.

### 2.4 Fidelidade histórica

A linha do tempo real é o **ground truth**. Eventos históricos âncora (crise 2008, COVID-19, etc.) entram no prompt como contexto, mas o LLM tem licença para alterar/anular eventos quando o estado contrafactual tornaria o evento real implausível.

### 2.5 Aleatoriedade (Monte Carlo)

- **Temperature do LLM**: 0.7 default (configurável).
- **Choques exógenos**: a cada turno, com probabilidade configurável (default 5%), sorteia-se um evento não-histórico (descoberta, catástrofe, escândalo) que entra no prompt.
- **Seed**: cada run tem uma seed salva, permitindo (na medida do possível) reproduzir runs.

---

## 3. Dimensões do estado (12 dimensões, 24 métricas)

Organizadas em 6 clusters, 2 dimensões cada, 2 métricas por dimensão.

| Cluster | Dimensão | Métricas |
|---|---|---|
| **Tecnologia & IA** | AI capability | `frontier_capability` (0–100), `population_penetration` (% pop) |
|  | Tech industry | `bigtech_concentration` (HHI 0–100), `tech_employment_share` (% workforce) |
| **Economia** | Financial markets | `global_index` (base 100 em 1998), `systemic_risk` (0–100) |
|  | Labor market | `employment_rate` (%), `automation_exposure` (% jobs at risk) |
| **Sociedade** | Education | `mean_years_schooling` (anos), `cost_index` (base 100) |
|  | Inequality | `global_gini` (0–1), `top1pct_share` (%) |
| **Conhecimento & Saúde** | Health | `life_expectancy` (anos), `diagnostic_accuracy` (% AI-augmented) |
|  | Science & R&D | `publications_index` (base 100), `breakthroughs_per_year` (count) |
| **Política** | Geopolitics | `us_china_balance` (-100 a +100), `active_conflicts` (count) |
|  | Governance | `democracy_index` (0–10), `ai_regulation_maturity` (0–100) |
| **Informação & Ambiente** | Information ecosystem | `media_trust` (0–100), `disinformation_level` (0–100) |
|  | Energy & climate | `co2_gt_year` (GtCO2/ano), `renewable_share` (%) |

---

## 4. Configuração inicial da simulação

Antes de iniciar uma run, o usuário escolhe:

| Parâmetro | Default | Descrição |
|---|---|---|
| `ai_mode` | `big_bang` | `big_bang` ou `accelerated_curve` |
| `play_mode` | `manual` | `manual`, `auto` ou `hybrid` |
| `initial_population_penetration` | `5.0` | % da população usando IA em S1/1998 |
| `temperature` | `0.7` | Aleatoriedade do LLM |
| `random_shock_probability` | `0.05` | Probabilidade de choque exógeno por turno |
| `seed` | (aleatório) | Reprodutibilidade |
| `model` | `claude-sonnet-4-6` | Modelo da Anthropic |

---

## 5. Estado inicial S1 1998 (valores ancorados em dados reais)

Ver `data/initial_state.json`. Notas:
- `frontier_capability=92` no modo big bang assume que a IA "nasce pronta". No modo accelerated_curve, começaria em ~15.
- `population_penetration` é sobrescrita pela config (default 5%).
- `global_index=100` é um índice base — todos os retornos serão relativos a este ponto.
- `co2_gt_year=24.4` reflete emissões globais de 1998 (Global Carbon Budget).
- `life_expectancy=67` é a média global de 1998 (Banco Mundial).
- `mean_years_schooling=7.4` é a estimativa global Barro-Lee/UNESCO para 1998.
- `global_gini=0.69` reflete desigualdade global (renda) no fim dos anos 90.

---

## 6. Eventos âncora históricos (1998–2026, em semestres)

Curados como JSON em `data/historical_events.json`. Cada turno consulta se há evento naquele semestre e injeta no prompt como contexto.

> **Importante**: no contrafactual, eventos podem ser **anulados, antecipados ou substituídos**. O LLM avalia plausibilidade dada a presença da IA desde 98.

---

## 7. Arquitetura técnica — Fase 1 (MVP)

### 7.1 Stack

- **Linguagem**: Python 3.11+
- **Dependências**: `anthropic`, `pydantic`, `rich`, `python-dotenv`
- **Persistência**: arquivos JSON no diretório `runs/` (uma pasta por simulação)
- **Sem banco de dados, sem servidor, sem frontend.** CLI puro.
- **Saída estruturada**: tool use da API Anthropic, com schema validado por Pydantic.

### 7.2 Estrutura de diretórios

```
counterfactual-1998/
├── README.md
├── PROJECT_SPEC.md
├── pyproject.toml
├── .env.example
├── data/
│   ├── initial_state.json
│   └── historical_events.json
├── src/
│   ├── __init__.py
│   ├── config.py              # SimulationConfig (parâmetros da run)
│   ├── models.py              # State, Event, TurnResponse (Pydantic)
│   ├── llm.py                 # Cliente Anthropic + tool use
│   ├── prompts.py             # Templates de prompt
│   ├── shocks.py              # Choques exógenos com seed
│   └── smoke_test.py          # Teste de 1 turno end-to-end
└── runs/                      # Simulações salvas (gitignored)
```

### 7.3 Loop principal (Fase 2 — pseudocódigo)

```python
def run_simulation(config: SimulationConfig):
    state = load_initial_state(config)
    events = load_historical_events()
    rng = Random(config.seed)
    narrative_history = []

    while state.turn <= "2026-S2":
        event = events.get(state.turn)
        shock = maybe_generate_shock(state.turn, config, rng)
        user_input = prompt_user() if config.play_mode == "manual" else None

        response = simulate_turn(state, event, shock, user_input, narrative_history, config)
        state = apply_deltas(state, response.deltas)
        narrative_history.append(response.narrative)
        save_run(state, response, narrative_history)
        render_dashboard(state)

        state = advance_turn(state)
```

---

## 8. Schema do prompt de turno

### 8.1 Estrutura

- **System prompt**: regras gerais, princípios de simulação, formato de saída.
- **User message**: estado atual JSON, evento histórico (se houver), choque exógeno (se houver), input do usuário (opcional), narrativa acumulada.
- **Tool**: `advance_turn` com schema JSON formal, forçando o LLM a retornar exatamente o formato esperado.

### 8.2 Por que tool use é não-negociável

Separar **narrativa (texto)** de **estado (números)** desde o turno 1 é o que permite trocar o frontend depois (CLI → web → multi-agente) sem reescrever a lógica. Tool use garante que o LLM sempre devolve o schema correto, eliminando retries por JSON malformado.

### 8.3 Modelagem da capacidade de IA por turno

No modo `big_bang`, `frontier_capability` começa em 92 e evolui pouco. No modo `accelerated_curve`, segue uma sigmóide:

```
capability(t) = 100 / (1 + exp(-k * (t - t0)))
# k = 0.15, t0 = 2008 (inflexão 10 anos antes da linha real)
```

---

## 9. Roadmap de implementação

### Fase 1 — Esqueleto funcional + aleatoriedade ✅ (em curso)
- [x] Setup do projeto (pyproject.toml, .env.example, .gitignore)
- [ ] data/initial_state.json e data/historical_events.json
- [ ] config.py: SimulationConfig
- [ ] models.py: State, TurnResponse, apply_deltas
- [ ] prompts.py: templates
- [ ] shocks.py: choques exógenos
- [ ] llm.py: cliente + tool use
- [ ] smoke_test.py: 1 turno end-to-end

### Fase 2 — Loop completo
- [ ] engine.py: loop de turnos com aplicação de deltas
- [ ] persistence.py: save/load de runs em JSON
- [ ] cli.py: interface Rich com dashboard
- [ ] Modo manual + modo auto + híbrido

### Fase 3 — Polimento
- [ ] Sparklines de séries temporais no terminal
- [ ] Comando `compare runs/run_A.json runs/run_B.json`
- [ ] Prompt caching pra reduzir custos
- [ ] README de uso real, gravação de demo

### Fase 4 — Análise
- [ ] Exportar runs pra CSV
- [ ] Monte Carlo de N runs (Anthropic Batch API)
- [ ] Análise de distribuições

---

## 10. Princípios não-negociáveis

1. Saída do LLM SEMPRE em JSON estruturado validado por Pydantic (via tool use).
2. Separação total entre estado quantitativo (números) e narrativa (texto).
3. Cada turno é puro: dado `(state, event, shock, user_input, narrative_history)`, retorna `(narrative, deltas)`.
4. Save de cada turno em disco, pra permitir retomar / ramificar runs.
5. Aleatoriedade explícita e reprodutível via seed.

---

## 11. Riscos e armadilhas conhecidas

- **LLM dá deltas exagerados**: solução = exemplos no prompt mostrando "delta típico" vs "delta de evento âncora", + clamps nos ranges aceitáveis.
- **Inconsistência narrativa entre turnos**: solução = passar narrativa acumulada como contexto. Custo: tokens crescem linearmente. Mitigação futura: prompt caching.
- **Custo da API**: 58 turnos × ~3k tokens médios × Sonnet ≈ pequeno por run. Monte Carlo de 100 runs ainda é barato. Use Batch API quando escalar.
- **Plausibilidade contrafactual**: o LLM vai querer ser "interessante" e exagerar. Calibrar via prompt + temperature.
- **Validação científica**: isso NÃO é previsão. É exploração estruturada de hipóteses.
