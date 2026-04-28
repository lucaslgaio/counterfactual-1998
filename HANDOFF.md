# Counterfactual-1998 — Handoff para frontend Lovable

Documento de transferência de um projeto de simulação histórica contrafactual para uma sessão Claude Chat construir o frontend web. O backend Python/CLI está em produção em `https://github.com/lucaslgaio/counterfactual-1998` e funciona end-to-end.

---

## 1. O que é o projeto

**Counterfactual-1998** é um simulador histórico contrafactual em turnos: explora, semestre a semestre, como o mundo (1998–2026) teria evoluído **se uma IA equivalente ao Claude 4 atual tivesse surgido em S1 de 1998** — fim da bolha .com. A simulação cobre 58 turnos (29 anos × 2 semestres).

A unidade de simulação é **a sociedade global**, modelada por dimensões setoriais. O LLM é simultaneamente:
1. **Motor causal** — raciocina sobre como o estado contrafactual interage com eventos históricos reais
2. **Cronista sociológico** — produz narrativa em prosa por turno
3. **Atualizador de estado** — devolve deltas numéricos validados

Saída híbrida: **prosa narrativa + dashboards quantitativos**. A run é probabilística (Monte Carlo): mesma config + seeds diferentes = runs divergentes.

**Inspirações declaradas:**
- **BrassFoot** (futebol em turnos brasileiro): UX game-like, usuário injeta inputs/diretrizes
- **Backtest financeiro**: simulação contrafactual aplicada a série temporal real

---

## 2. Stack e status

- **Repo**: https://github.com/lucaslgaio/counterfactual-1998 (público)
- **Linguagem**: Python 3.9+
- **Dependências**: `google-genai` (Gemini SDK), `pydantic>=2.0`, `rich` (UI terminal), `python-dotenv`
- **Modelo LLM**: `gemini-2.5-flash` via Google AI Studio (free tier: 1500 req/dia, 15 RPM)
- **Persistência**: arquivos JSON estáticos em `data/`, runs **só em memória** (não salva ainda)
- **Status**: Fase 1 do roadmap completa + Fase 2 e 3 parcialmente. Funciona end-to-end no terminal com 4-58 turnos.

---

## 3. Modelo conceitual da simulação

### 3.1 As 12 dimensões / 24 métricas do estado

Organizadas em 6 clusters, 2 dimensões por cluster, 2 métricas por dimensão.

| Cluster | Dimensão | Métrica | Faixa | Valor inicial 1998 |
|---|---|---|---|---|
| **Tecnologia & IA** | ai_capability | frontier_capability | 0–100 | 92 (big_bang) |
| | | population_penetration | 0–100% | 5.0 (default config) |
| | tech_industry | bigtech_concentration | 0–100 (HHI) | 22 |
| | | tech_employment_share | 0–100% | 3.1 |
| **Economia** | financial_markets | global_index | base 100 | 100 |
| | | systemic_risk | 0–100 | 35 |
| | labor_market | employment_rate | 0–100% | 62.8 |
| | | automation_exposure | 0–100% | 8 |
| **Sociedade** | education | mean_years_schooling | 0–25 anos | 7.4 |
| | | cost_index | base 100 | 100 |
| | inequality | global_gini | 0–1 | 0.69 |
| | | top1pct_share | 0–100% | 19 |
| **Conhecimento & Saúde** | health | life_expectancy | 0–120 anos | 67 |
| | | diagnostic_accuracy | 0–100% | 2 |
| | science_rd | publications_index | base 100 | 100 |
| | | breakthroughs_per_year | 0–1000 | 12 |
| **Política** | geopolitics | us_china_balance | -100 a +100 | 75 (EUA dominantes) |
| | | active_conflicts | 0–200 | 38 |
| | governance | democracy_index | 0–10 | 5.5 |
| | | ai_regulation_maturity | 0–100 | 0 |
| **Informação & Ambiente** | information_ecosystem | media_trust | 0–100 | 53 |
| | | disinformation_level | 0–100 | 18 |
| | energy_climate | co2_gt_year | 0–100 GtCO₂/ano | 24.4 |
| | | renewable_share | 0–100% | 6 |

Cada métrica tem ficha completa em `src/glossary.py` com:
- `description` (o que é)
- `unit` (% pp, anos, GtCO₂/ano, base 100, etc.)
- `range_label`
- `anchors`: 3-4 pontos de referência (ex: `(15, "ML clássico")`, `(60, "GPT-3-like")`, `(92, "Claude 4-like")`)
- `template` de interpretação (f-string com `{before}`, `{after}`, `{delta}`)

### 3.2 Polaridade contextual

Subset `BAD_WHEN_UP` (9 métricas onde aumentar = piorar do ponto de vista humano):

```
systemic_risk, automation_exposure, global_gini, top1pct_share,
active_conflicts, disinformation_level, co2_gt_year, cost_index,
bigtech_concentration
```

Usado para colorir deltas: verde quando vai na direção "boa pra humanos", vermelho quando vai na direção "ruim". Importante pra UX.

### 3.3 Configuração inicial da run

Cada simulação começa com uma `SimulationConfig`:

```python
ai_mode: "big_bang" | "accelerated_curve"   # default: big_bang
play_mode: "manual" | "auto" | "hybrid"     # default: manual
initial_population_penetration: float       # default: 5.0 (sobrescreve o estado)
temperature: float                           # default: 0.85
random_shock_probability: float              # default: 0.05 (5% por turno)
seed: int                                    # default: aleatória
model: str                                   # default: "gemini-2.5-flash"
max_tokens: int                              # default: 8192
```

### 3.4 Eventos âncora históricos

16 eventos curados em `data/historical_events.json`, mapeados em semestres:

```
1998-S2: Crise financeira russa / default                         (high, financial)
1999-S2: Y2K bug + transição milênio                              (low, tech)
2000-S1: Pico Nasdaq (5048)                                        (high, financial)
2001-S1: Estouro da bolha .com                                    (critical, financial)
2001-S2: Atentados de 11 de Setembro                              (critical, geopolitics)
2003-S1: Invasão do Iraque                                        (high, geopolitics)
2007-S2: Início da crise subprime                                 (high, financial)
2008-S2: Falência Lehman Brothers                                 (critical, financial)
2010-S2: Início da Primavera Árabe                                (high, geopolitics)
2011-S1: Fukushima / tsunami Japão                                (high, energy)
2014-S1: Anexação da Crimeia pela Rússia                          (high, geopolitics)
2016-S1: Referendo Brexit                                         (high, governance)
2016-S2: Eleição de Donald Trump                                  (high, governance)
2020-S1: Pandemia COVID-19                                        (critical, health)
2022-S1: Invasão russa da Ucrânia                                 (critical, geopolitics)
2022-S2: Lançamento do ChatGPT (linha real)                       (high, tech)
```

A cada turno, se há evento, o LLM avalia: `ocorreu | alterado | anulado | N/A`.

### 3.5 Choques exógenos aleatórios

Pool de 25 cenários em `src/shocks.py`. A cada turno, sorteia-se 1 com probabilidade `random_shock_probability` (default 5%). RNG **determinístico** por `(seed + turn_index)` — mesmo seed = mesmos choques. Domínios: tech, health, geopolitics, financial, information, energy, science.

Exemplos:
- "Avanço em fusão nuclear comercial" (high, energy)
- "Quebra do paradigma quântico" (high, tech)
- "IA descobre nova classe de antibióticos" (high, health)
- "Vazamento de documentos governamentais" (high, information)
- "Acidente nuclear severo" (high, energy)

---

## 4. Mecânica do turno

### 4.1 Loop principal

```python
state = load_initial_state(config)  # com population_penetration override
narrative_history = []
metric_history = {}  # pra sparklines

for i in range(num_turns):
    event = events.get(state.turn)              # evento âncora se houver
    shock = maybe_generate_shock(state.turn, config)  # determinístico por seed
    seeds = seeds_for_turn(state.turn, config.seed)   # 4 sementes de debate
    lens = lens_for_turn(state.turn, config.seed)     # 1 das 10 lentes

    response = simulate_turn(state, event, shock,
                             user_input, narrative_history,
                             config, seeds, lens)

    state = apply_deltas(state, response.deltas)  # aditivo com clamp
    state = state.model_copy(update={"turn": advance_turn(state.turn)})
    narrative_history.append(response.narrative)
    update_metric_history(metric_history, state)

    # painel de progresso cumulativo + prompt opcional
    show_progress(...)
    user_input = prompt_or_skip(batch_remaining)
```

### 4.2 Aplicação de deltas

Deltas são **aditivos** com **clamp** automático aos limites de cada métrica:

```python
new_value = clamp(current_value + delta, lo, hi)
```

Onde `(lo, hi)` vem das constraints Pydantic (`Field(ge=..., le=...)`). Chaves desconhecidas são silenciosamente ignoradas — o motor é tolerante a hallucinations leves.

### 4.3 Avanço de turno

```python
"1998-S1" → "1998-S2"
"1998-S2" → "1999-S1"
...
"2026-S2" → fim da simulação
```

Total: 58 turnos.

### 4.4 Modos de jogo

- **manual** (default): a cada turno, prompt aceita: Enter (1 turno), número N (rodar N turnos sem pausa), texto livre (diretriz pro próximo turno)
- **auto**: roda do início ao fim sem pausa
- **hybrid**: planejado mas não implementado — auto com pausas em eventos âncora critical

---

## 5. Integração com LLM

### 5.1 Padrão: function calling forçado

Usamos `tool_choice={mode: "ANY", allowed_function_names: ["advance_turn"]}` pra forçar o LLM a sempre chamar nossa função estruturada. Sem isso, ele pode responder em texto livre e a parsing falha.

### 5.2 Schema da função `advance_turn` (em formato Gemini)

```json
{
  "name": "advance_turn",
  "parameters": {
    "type": "OBJECT",
    "properties": {
      "narrative": {"type": "STRING", "description": "PT-BR, 80-200 palavras"},
      "key_developments": {"type": "ARRAY", "items": {"type": "STRING"}},
      "event_outcome": {"type": "STRING", "enum": ["ocorreu", "alterado", "anulado", "N/A"]},
      "event_outcome_explanation": {"type": "STRING", "nullable": true},
      "deltas": {
        "type": "ARRAY",
        "items": {
          "type": "OBJECT",
          "properties": {
            "metric": {"type": "STRING"},        // ex: "ai_capability.frontier_capability"
            "value": {"type": "NUMBER"},          // delta aditivo
            "explanation": {"type": "STRING"}     // 8-15 palavras explicando o porquê
          },
          "required": ["metric", "value", "explanation"]
        }
      },
      "causal_links": {
        "type": "ARRAY",
        "items": {
          "type": "OBJECT",
          "properties": {
            "source": {"type": "STRING"},  // ex: "crise_russa" ou "ai_capability.frontier_capability"
            "target": {"type": "STRING"},  // sempre "dimensao.metrica"
            "direction": {"type": "STRING", "enum": ["up", "down"]}
          }
        }
      },
      "confidence": {"type": "STRING", "enum": ["low", "medium", "high"]}
    },
    "required": ["narrative", "key_developments", "event_outcome", "deltas", "causal_links", "confidence"]
  }
}
```

### 5.3 Configurações importantes do Gemini

```python
config = GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,        # ~1500 tokens, sociologicamente carregado
    temperature=0.85,                         # variação criativa
    max_output_tokens=8192,                   # generoso pra comportar narrativa + deltas + causal_links
    thinking_config=ThinkingConfig(thinking_budget=0),  # CRÍTICO: desliga thinking do 2.5 Flash
    safety_settings=[                         # liberado pra cenários históricos pesados
      {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
      {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
      {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
      {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
    ],
    tools=[Tool(function_declarations=[advance_turn_schema])],
    tool_config=ToolConfig(
      function_calling_config=FunctionCallingConfig(
        mode="ANY",
        allowed_function_names=["advance_turn"]
      )
    ),
)
```

**Pegadinhas conhecidas resolvidas durante o desenvolvimento:**

1. **MALFORMED_FUNCTION_CALL com property names com pontos**: Gemini não tolera `properties: {"ai_capability.frontier_capability": ...}` em schemas com 24+ chaves. Solução: deltas como **array de `{metric, value, explanation}`** em vez de objeto com chaves nomeadas. O Pydantic faz a coerção `list → dict` no `model_validator(mode="before")`.

2. **Thinking de Gemini 2.5 consome max_output_tokens**: na primeira run, com `max_tokens=2048` o thinking esgotava antes do output → MALFORMED. Sempre `thinking_budget=0` pra geração estruturada.

3. **`gemini-2.0-flash` saiu do free tier pra contas novas em alguma data de 2026**: `gemini-2.5-flash` é o substituto correto.

4. **Conteúdo histórico (guerras, 11/9, COVID) trigger safety filters**: precisa baixar pra `BLOCK_ONLY_HIGH`.

### 5.4 Modelo de prompt

**System prompt** (~1500 tokens) está em `src/prompts.py`. Tem 6 seções:
1. Premissa e ofício do cronista sociológico
2. Lista de 16 debates contemporâneos sobre IA como matéria-prima
3. Estrutura da narrativa (lente + sementes + 80-200 palavras)
4. Par de exemplo concreto **bom vs ruim** (crítico — o LLM pattern-matcha esse exemplo)
5. Vetos explícitos (frases-chiclete proibidas)
6. Regras técnicas (deltas aditivos, causal_links, idioma, function call)

**User message por turno** inclui:
- TURNO ATUAL (ex: "1998-S2") + AI MODE
- Resumo qualitativo da capacidade da IA
- LENTE SOCIOLÓGICA do turno (1 das 10)
- 4 SEMENTES DE DEBATE injetadas (filtradas por ano ≤ ano do turno, ponderadas por recência)
- Estado quantitativo em JSON
- Evento histórico do semestre (se houver)
- Choque exógeno (se houver)
- Input do usuário (se houver)
- Narrativa acumulada de todos os turnos anteriores (cresce ao longo da run)

---

## 6. Sistema sociológico (parte mais original do projeto)

### 6.1 Sementes de debate contemporâneo

`data/discourse_seeds.json` tem 45 sementes. Cada uma:

```json
{
  "year": 2004,
  "domain": "alignment",
  "text": "Nick Bostrom (Oxford) publica 'Catástrofes Computacionais', primeira articulação acadêmica de risco existencial; comunidade EA se forma em torno dele."
}
```

Domínios incluem: `labor`, `alignment`, `concentration`, `geopolitics`, `intimate`, `religion`, `post_truth`, `education`, `health`, `counter_movement`, `open_closed`, `regulation`, `infrastructure`, `rights`, `ideology`, `energy`, `trust`.

A cada turno, `seeds_for_turn(turn, seed)` em `src/discourse.py`:
1. Filtra sementes onde `year <= ano_do_turno`
2. Pondera por recência: idade ≤1 ano peso 5, ≤3 anos peso 3, ≤7 anos peso 2, mais antigas peso 1
3. Amostra 4 sem reposição usando RNG determinístico por `(seed, turn)`

Resultado: turno em 2008 tira mais sementes de 2005-2008 do que de 1999. Material relevante pra época.

### 6.2 Lentes sociológicas

10 lentes em `src/discourse.py` que rotacionam por turno (RNG por `seed + hash(turn)`):

```
1. trabalho e classe — quem ganha/perde, sindicalização, novas/velhas profissões
2. vida íntima — relacionamentos com IA, parentalidade, amizade, sexualidade, solidão
3. conhecimento e educação — escolas, atrofia cognitiva, novos saberes, geração-IA
4. política e identidade — ideologias, movimentos sociais, polarização, autoritarismo
5. religião e sentido — AGI como divindade, niilismo, neo-monasticismo, longtermismo
6. cultura e arte — o que se cria/consome, gírias, ritualidade, memes
7. resistência e contraculturas — neo-luditismo, retorno ao analógico, zonas livres
8. geografia — cidades epicentros, êxodo, infraestrutura crítica
9. corpo e saúde — medicina, dependência cognitiva, ansiedade, suicídio
10. cidadania e direito — novos direitos, novos crimes, soberania, vigilância
```

A cada turno, **uma lente** é injetada como ângulo de entrada. Em 58 turnos, cada lente cai ~5-6 vezes — distribuição razoável para cobrir múltiplas dimensões sociais.

### 6.3 Por que essa estrutura existe

O LLM, sem essa scaffolding, recai em ficção científica genérica anos 90: "primeiros pilotos de diagnóstico médico", "preocupações sobre o futuro do trabalho". Plausível, vazio.

Com sementes + lentes + system prompt sociologicamente carregado, ele transpõe debates reais (alignment problem, e/acc, atrofia cognitiva, deepfakes em eleições, hikikomori coreanos com companion bots, WGA contra IA generativa) para as datas plausíveis de emergência no contrafactual.

Foi o pivô final do desenvolvimento. Antes disso a narrativa era plana, depois ganhou densidade de cronista.

---

## 7. UX que funciona no terminal (referência pro frontend)

A UX foi desenhada com `rich` no terminal, mas as decisões de design valem pra web.

### 7.1 Sequência da experiência

**Tela 1: Manual das 24 métricas** (opcional, com flag `--manual`)
- 6 painéis (um por cluster)
- Cada métrica: nome, descrição, faixa, 3-4 âncoras de referência

**Tela 2: Intro / splash**
- Título centralizado: `COUNTERFACTUAL // 1998`
- Subtítulo: "um simulador de mundos que não foram"
- Painel ciano com a premissa
- Painel "configuração da run" mostrando ai_mode, seed, modelo, etc
- Pause "Pressione Enter para iniciar..."

**Tela por turno** (sequência):
1. **Turn header**: `TURNO N/M · YYYY-Sx` em régua ciano
2. **Painel de evento histórico** (se houver): cor por severidade (vermelho=critical, laranja=high, amarelo=medium)
3. **Painel de choque exógeno** (se houver): magenta
4. **Painel "matéria-prima sociológica"**: lente do turno + 4 sementes injetadas
5. **Spinner**: "o motor causal está raciocinando sobre 1998-S2..."
6. **Painel narrativo (crônica)**: ciano, prosa em 80-200 palavras
7. **Lista de desenvolvimentos**: bullets `▸`
8. **Outcome do evento**: status colorido + explicação
9. **Tabela de deltas**: colunas (label_curto, Δ_com_unidade, magnitude_em_setas, "por quê") com cores contextuais (verde/vermelho)
10. **Árvore causal**: agrupada por origem, mostra `source → [target ↑/↓, target ↑/↓, ...]`
11. **Confidence**: low/medium/high
12. **Painel cumulativo "estado do mundo até X"**: top 6 mudanças desde início (em prosa) + sparklines por cluster
13. **Prompt**: Enter (1 turno), número (rodar N turnos), ou texto (diretriz)

**Tela final**:
- Régua "FIM DA SIMULAÇÃO · N turnos rodados"
- Mesmo painel cumulativo, top 10
- Turno final exibido

### 7.2 Componentes visuais reutilizáveis

**Sparklines ASCII** (`src/viz.py`):
```
▁▂▃▄▅▆▇█  (8 níveis Unicode)
```
Função `sparkline(values: list[float]) -> str` normaliza min/max e mapeia.

**Setas de magnitude**:
```
| delta < 0.5 | ↑ ou ↓     |
| delta < 2   | ↑↑ ou ↓↓   |
| delta < 6   | ↑↑↑ ou ↓↓↓ |
| delta ≥ 6   | ↑↑↑↑ ou ↓↓↓↓ |
```

**Árvore causal** (Rich `Tree`): agrupa links por `source`, mostra targets como folhas com seta colorida pela polaridade humana (red/green).

**Cluster panels**: cada um dos 6 clusters em painel ciano com tabela de métricas.

### 7.3 Polaridade visual

Em qualquer delta na UI:
- Métrica `BAD_WHEN_UP` subindo → vermelho
- Métrica `BAD_WHEN_UP` descendo → verde
- Outras métricas subindo → verde
- Outras métricas descendo → vermelho

Crítico pra que o usuário "leia" o gráfico instintivamente.

---

## 8. Recomendações para o frontend Lovable

### 8.1 Decisão de arquitetura

Lovable produz **React + Tailwind + Vite + Supabase**. O Python atual não roda lá. Três caminhos:

**A. Reimplementar a lógica em TypeScript (recomendado pra Lovable)**
- Estado do mundo + glossário + sementes + lentes: traduzir os JSON diretamente
- LLM call: usar Vercel AI SDK ou chamar Gemini direto via edge function (Supabase Edge Functions ou Lovable functions)
- Persistência: Supabase Postgres (cada run vira uma row + array de turn snapshots)

**B. Manter Python como backend e expor API**
- FastAPI servindo `POST /turns`, `GET /runs/:id`
- Frontend React consome
- Mais complexo de hospedar (Lovable não roda Python)

**C. Híbrido**
- Frontend chama Gemini direto (com a key dele) e replica a lógica em TS
- Mais simples mas a key do Gemini fica exposta no client (ruim)

**Recomendação: A.** Reimplementação em TypeScript com edge function pro LLM call. O servidor (Supabase Edge Function ou similar) só serve pra esconder a API key e fazer rate limiting.

### 8.2 Schema de banco (Supabase Postgres)

```sql
-- Uma run completa
create table runs (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz default now(),
  user_id uuid references auth.users,
  config jsonb not null,        -- SimulationConfig serializado
  current_turn text,             -- "YYYY-S1" ou "YYYY-S2"
  status text,                   -- "running" | "paused" | "completed"
  initial_state jsonb not null,
  current_state jsonb not null
);

-- Cada turno individual da run (snapshot completo)
create table turns (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references runs on delete cascade,
  turn_number int not null,
  turn_label text not null,      -- "1998-S1"
  state_before jsonb not null,
  state_after jsonb not null,
  event jsonb,                   -- HistoricalEvent ou null
  shock jsonb,                   -- ExogenousShock ou null
  user_input text,
  lens text,
  seeds_used jsonb,              -- array de discourse seeds injetadas
  response jsonb not null,       -- TurnResponse completa: narrative, deltas, causal_links etc
  metric_snapshot jsonb not null,-- valores das 24 métricas após o turno
  created_at timestamptz default now()
);

create index turns_run_id_turn_number on turns(run_id, turn_number);
```

Vantagens: cada turno é independente, pode-se branchar uma run a partir de qualquer turno (Phase 4 do roadmap).

### 8.3 Componentes React sugeridos

```
<App>
  <Splash />
  <ConfigForm />              # ai_mode, temperature, seed, etc
  <Manual />                  # opcional, glossário
  <SimulationView>
    <TurnHeader turn={...} event={...} shock={...} />
    <DiscoursePanel lens={...} seeds={...} />
    <NarrativePanel narrative={...} />
    <KeyDevelopments items={...} />
    <EventOutcome outcome={...} explanation={...} />
    <DeltasTable deltas={...} explanations={...} />
    <CausalGraph links={...} />          # versão web da árvore: D3, vis.js, ReactFlow
    <ProgressDashboard
      initialState={...}
      currentState={...}
      metricHistory={...}
    />
    <NextTurnInput onAdvance={...} />    # Enter | N | diretriz
  </SimulationView>
  <Outro />
</App>
```

### 8.4 Oportunidades visuais que NÃO consegui fazer no terminal

1. **Diagrama de dinâmicas de sistemas** real (estilo Bass diffusion model que o usuário mencionou): nodes + arrows com largura proporcional à força do efeito, agrupando por feedback loop. Use ReactFlow ou D3.
2. **Linha do tempo interativa**: scroll horizontal com 58 turnos, cada um clicável pra ver narrativa + deltas + causal links daquele momento.
3. **Cluster de métricas como cards**: cada cluster como card animado com sparkline animando enquanto a run roda.
4. **Side-by-side de runs**: comparar duas run com configs diferentes (era Fase 3 do plano original).
5. **Replay**: dar play/pause/scrub na simulação, voltar 5 turnos.
6. **"Branchar" uma run** a partir de um turno específico com input diferente.

### 8.5 Identidade visual

A paleta atual no terminal:
- Ciano (#22d3ee) pra elementos principais (títulos, narrativa)
- Amarelo (#facc15) pra turn labels
- Magenta pra choques
- Vermelho/laranja pra eventos críticos/high
- Verde/vermelho contextual pra deltas (polaridade humana)

Vibe geral: "future-retro" / cronista de mundos paralelos. Mantém legibilidade alta, dá sensação de "log de simulação" com peso histórico.

---

## 9. Estrutura completa do repo

```
counterfactual-1998/
├── README.md                    # uso e setup
├── PROJECT_SPEC.md              # spec original do projeto
├── HANDOFF.md                   # ESTE DOCUMENTO
├── pyproject.toml               # deps: google-genai, pydantic, rich, python-dotenv
├── .env.example                 # GOOGLE_API_KEY=
├── .gitignore
├── data/
│   ├── initial_state.json       # estado S1/1998 ancorado
│   ├── historical_events.json   # 16 eventos âncora em semestres
│   └── discourse_seeds.json     # 45 sementes de debate
└── src/
    ├── __init__.py
    ├── config.py                # SimulationConfig (Pydantic)
    ├── models.py                # State, dimensões, TurnResponse, CausalLink, apply_deltas, advance_turn
    ├── glossary.py              # 24 MetricInfo (descrição, unidade, âncoras, template, BAD_WHEN_UP)
    ├── discourse.py             # SOCIOLOGICAL_LENSES, seeds_for_turn, lens_for_turn
    ├── shocks.py                # SHOCK_POOL (25), maybe_generate_shock
    ├── prompts.py               # SYSTEM_PROMPT (1500 tokens), build_user_message
    ├── llm.py                   # cliente Gemini, schema, simulate_turn
    ├── smoke_test.py            # entry point: intro, manual, loop, render, outro
    └── debug_api.py             # diagnóstico de conexão Gemini
```

### 9.1 Arquivos críticos pra portar

Em ordem de prioridade pra reimplementação:

1. **`data/initial_state.json`** — copiar tal qual
2. **`data/historical_events.json`** — copiar tal qual
3. **`data/discourse_seeds.json`** — copiar tal qual
4. **`src/glossary.py`** — traduzir pra TS, é a fonte da metadata visual
5. **`src/prompts.py`** — o `SYSTEM_PROMPT` é o coração do projeto, traduzir literalmente
6. **`src/models.py`** — schema Pydantic vira tipos TS + validação Zod
7. **`src/llm.py`** — chamada pra Gemini com function calling, traduzir pra `@google/generative-ai` ou `ai-sdk`
8. **`src/shocks.py`** — pool + RNG determinístico
9. **`src/discourse.py`** — sampling logic
10. **`src/smoke_test.py`** — UX de referência, NÃO portar literalmente, repensar pra web

---

## 10. Decisões de design importantes (com razões)

### 10.1 Granularidade semestral em vez de trimestral

Original era trimestral (116 turnos). Mudou pra semestral (58 turnos) pra reduzir custo por run e iteração no MVP. Arquitetura permite voltar pra trimestral se quiser (ajustar `advance_turn`, remapear eventos).

### 10.2 Modo big_bang (default) em vez de accelerated_curve

O `accelerated_curve` (IA evolui ao longo dos 28 anos via sigmoide) é mais cientificamente honesto, mas mais difícil de modelar. Big_bang (IA já madura em 1998) é mais limpo experimentalmente — choque máximo desde o turno 1, vê a sociedade respondendo a uma constante.

### 10.3 Deltas aditivos (não absolutos)

LLM tem mais facilidade em pensar "subiu pouco / muito" que em calcular novo valor exato. Aditivo + clamp resolve drift acumulado.

### 10.4 Tool use / function calling forçado (não JSON mode)

Function calling é estritamente validado pelo provider. JSON mode é mais permissivo e quebra mais. Em 58 turnos × N runs Monte Carlo, mesmo 1% de falha vira retry expensive.

### 10.5 Deltas como array, não dict

Foi forçado por bug do Gemini com property names com pontos. Veja seção 5.3.

### 10.6 Sociological lens rotation forçada

O LLM, deixado livre, tende a ficar nas mesmas 2-3 dimensões. Forçar rotação garante cobertura ao longo da run. Tradeoff: alguns turnos podem cair numa lente que não combina perfeitamente com o evento. Mas isso força o LLM a procurar ângulos sociológicos não-óbvios — que é o ponto.

### 10.7 Narrativa acumulada no contexto, sem resumir

Em 58 turnos × ~150 tokens cada = 9k tokens de history no fim. Cabe tranquilo no Gemini. Resumir periodicamente seria otimização prematura. Se o frontend quiser cortar custo, prompt caching da Anthropic ou Gemini context caching é o jeito.

### 10.8 Temperature 0.85 (alto)

Pra Monte Carlo precisamos variação real entre runs. 0.7 era ainda muito determinístico. 0.85 dá variação criativa boa sem perder coerência.

---

## 11. O que ficou em aberto

### 11.1 Não implementado mas planejado

- **Persistência em `runs/` JSON**: hoje run só existe em memória; quando termina, perde
- **Comando `compare runs/run_A.json runs/run_B.json`**: comparar duas runs lado a lado
- **Modo `hybrid`**: auto com pausas em eventos âncora critical
- **Export CSV** das séries temporais pra análise externa
- **Monte Carlo**: rodar N runs paralelos com mesma config, comparar distribuições (Gemini Batch API quando disponível)
- **HTML interativo de saída**: diagrama systems dynamics real estilo Bass diffusion model

### 11.2 Calibrações que podem ainda ser melhoradas

- **Sementes do contrafactual**: 45 hoje, dá pra dobrar pra 90+ com mais cobertura de domínios e datas
- **Lentes sociológicas**: 10 hoje, talvez expandir pra 15 com mais granularidade
- **Sistema prompt em inglês vs português**: hoje é tudo em PT-BR, isso pode estar empobrecendo o vocabulário disponível pro Gemini (modelos são treinados majoritariamente em inglês). Vale testar versão bilíngue.
- **Quando o LLM "amarra" demais**: às vezes ele continua usando "Athena" como nome 5 turnos depois mesmo que o usuário queira que cenários alternativos emerjam. Talvez precise de mecanismo pra "esquecer" ou "ramificar" a narrativa.

### 11.3 Pegadinhas de produção

- **Free tier do Gemini**: 1500 req/dia, 15 RPM. Run de 58 turnos = 58 reqs. Limita a ~25 runs/dia por API key, ou 1 run a cada 4 segundos.
- **Modelos rotativos**: a Google tira modelos do free tier sem aviso. `gemini-2.5-flash` foi o substituto de `gemini-2.0-flash` em meados de 2026. Mantenha um fallback testado.
- **Safety filters acionados**: cenários históricos (11/9, COVID, guerras) podem disparar. Sempre `BLOCK_ONLY_HIGH` pra HARM_CATEGORY_*.
- **Conteúdo gerado**: nem tudo que o LLM escreve é factualmente verdadeiro — é uma simulação alternativa. Disclamer importante na UI.

### 11.4 Sobre custos

Free tier do Google AI Studio cobre uso pessoal/research tranquilamente:
- 1 run de 58 turnos × ~5k tokens médios = pequeno
- Monte Carlo de 10 runs/dia: ainda dentro do free
- Pra escalar (centenas de runs simultâneas), Vertex AI ou Gemini paid tier (~$0.075 / 1M input tokens, $0.30 / 1M output)

---

## 12. Referências externas úteis

- **Anthropic Claude 4 docs**: pra eventualmente plugar como alternative LLM (function calling similar)
- **Google AI Studio**: https://aistudio.google.com (criar API key, ver modelos)
- **Gemini function calling**: https://ai.google.dev/gemini-api/docs/function-calling
- **Lovable**: https://lovable.dev (pra construir o frontend)
- **ReactFlow**: https://reactflow.dev (pra diagramas de causal links)
- **D3 sparklines**: várias libs (ex: `react-sparklines`)
- **Supabase Postgres**: pra persistência de runs
- **Vercel AI SDK**: alternativa pra integrar LLM em React/Next

---

## 13. Como continuar de onde paramos

Um próximo desenvolvedor (ou Claude Chat) pode:

1. **Clonar o repo**: `git clone https://github.com/lucaslgaio/counterfactual-1998`
2. **Ler `PROJECT_SPEC.md` + este `HANDOFF.md`** (~30min de contexto)
3. **Rodar smoke test** localmente pra ver a UX que estamos replicando: `python -m src.smoke_test --turns 4 --seed 42 --manual`
4. **Decidir arquitetura web**: TS reimplementation vs Python API
5. **Começar pelo essencial**: Config form → Single turn run → Multi turn loop → Persistence → Análises

A ordem que valeria seguir pra ter MVP web em ~1 semana:
1. Setup Lovable + Supabase, schema das tabelas
2. Port `data/*.json` direto (são portáveis)
3. Port `glossary.py` pra TS (~150 linhas)
4. Port `prompts.py` pra TS (literal, é só string)
5. Edge function chamando Gemini com function calling
6. Tela de config + 1 turno end-to-end
7. Persistência + retomar run
8. Loop multi-turno + UI de progresso (sparklines, deltas table, causal graph)
9. Polish visual

---

**Autor:** Lucas Leal (`lucaslgaio` no GitHub)
**Período de desenvolvimento:** Abril 2026
**Modelo LLM usado durante o build do backend:** Claude Opus 4.7 (1M context)
**Modelo LLM rodando a simulação:** Google Gemini 2.5 Flash
