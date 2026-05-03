# counterfactual-1998

Simulador histórico contrafactual: como o mundo (1998–2026) teria evoluído se uma IA equivalente ao Claude 4 tivesse surgido no final da bolha .com.

A unidade de simulação é a **sociedade global**, modelada por 12 dimensões e ~26 métricas em 4 blocos geográficos (US/EU/CN/RoW). O motor é determinístico (System Dynamics Model em Python), com calibração contra dados históricos 1998–2024 e um cronista LLM que interpreta narrativamente o que o motor calcula.

> **Status**: monorepo com backend Python + frontend React. Veja [PROJECT_SPEC.md](./PROJECT_SPEC.md) para o modelo conceitual, dimensões, eventos âncora e fases.

## Estrutura do repositório

```
counterfactual-1998/
├── src/                    # Backend Python (motor SDM, especificação, calibração, cronista LLM)
│   ├── spec/               # loaders + validadores da especificação formal
│   ├── engine/             # motor System Dynamics determinístico (Etapa 4)
│   ├── calibration/        # calibração de alphas contra dados históricos (Etapa 5)
│   └── chronicler/         # cronista LLM que interpreta os outputs do motor (Etapa 6)
├── tests/                  # testes do backend (cross-package)
├── spec/                   # especificação formal do DAG causal (JSON)
├── data/
│   ├── historical/         # séries históricas 1998–2024 (calibração)
│   ├── initial_state.json  # estado-mundo S1/1998
│   └── historical_events.json
├── docs/
│   ├── causal_dag/         # documentação do DAG (justificativas, diagrama, edges)
│   ├── engine/             # arquitetura do motor SDM
│   ├── calibration/        # metodologia, fontes, limites
│   └── chronicler/         # design do prompt e schema de output
├── scripts/                # CLIs Python (run_simulation, calibrate, validate, etc.)
├── runs/                   # JSONs de simulações geradas
└── frontend/               # Frontend React + TypeScript (interface visual)
```

## Backend (Python)

### Setup

```bash
# Pré-requisitos: Python 3.9+
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Para rodar o cronista LLM (Etapa 6), configure:
cp .env.example .env
# e edite .env com GEMINI_API_KEY (ou GOOGLE_API_KEY como fallback legado)
```

### Smoke tests

Roda o motor SDM por 58 turnos (1998-S1 → 2026-S2) sem chamar nenhum LLM:

```bash
python scripts/run_simulation.py --seed 42 --turns 58 --output runs/run_001.json
```

Compara variância entre seeds:

```bash
python scripts/compare_runs.py --n-runs 5 --turns 30
```

Gera narrativa via LLM cronista (precisa GEMINI_API_KEY):

```bash
python scripts/run_simulation_with_chronicler.py \
    --seed 42 --turns 58 --output runs/run_with_narrative.json
```

Calibra alphas contra dados históricos:

```bash
python scripts/calibrate.py --output-dir runs/calibration/
python scripts/validate_calibration.py --alphas runs/calibration/alphas_calibrated.json
```

### Testes

```bash
pytest tests/ -v
```

Espera-se 237 testes passando quando todas as etapas estiverem mergeadas:
- 58 spec
- 82 engine
- 39 calibration
- 58 chronicler

### Princípios

1. **Determinismo**: motor produz sempre o mesmo JSON dado `(seed, config, spec)`.
2. **Imutabilidade**: WorldState é frozen dataclass; cada turno deriva um novo.
3. **Provenance em todo lugar**: todo delta numérico é rastreável a edge + função + valor de input.
4. **Divisão clara LLM/motor**: motor decide *o que* aconteceu; cronista LLM decide *como narrar*.
5. **Reproducibilidade**: parâmetros calibrados, seeds fixas, output completo persistido.

### Etapas

- **Etapa 1**: especificação formal do DAG causal — `spec/*.json` + `src/spec/`
- **Etapa 1.5**: 3 rodadas de cleanup/expansão do DAG (87→130 edges)
- **Etapa 2**: revisão metodológica de 28 edges contestáveis
- **Etapa 4**: motor SDM determinístico — `src/engine/`
- **Etapa 5**: calibração de alphas contra 1998–2024 — `src/calibration/`
- **Etapa 6**: cronista LLM (Gemini Flash) — `src/chronicler/`
- **Etapa 7**: frontend React (este PR migra do repo Lovable para `frontend/`)
- **Etapa 8 / Modo Jogo**: jogador como CEO de lab de IA em 1998 — `src/game/` + `src/api/`

## Modo Jogo

Transforma o simulador em jogo single-player: você é CEO de um lab de IA fronteira em 1998 e tem 10 turnos (5 anos) para cumprir uma missão sem causar colapso institucional.

Arquitetura em duas camadas:

- **`src/game/`** — orquestra turn-by-turn. Resolve ações canônicas (templates) ou livres (interpretadas pelo GM-LLM), faz roll determinístico, injeta deltas como exógenos no motor SDM (que permanece intocado em sua lógica core).
- **`src/api/`** — FastAPI HTTP que expõe o jogo ao frontend. Storage in-memory (single-process).
- **`frontend/src/pages/Play.tsx`** — UI rodando em `/play`. Dashboard de métricas + crônica + textarea de ação livre + 5 chips de sugestão canônica.

Quatro guardrails do GM-LLM documentados em [docs/game/gm_design.md](docs/game/gm_design.md): rubrica conservadora no prompt, CATEGORY_CAPS pós-retorno, success_p + roll determinístico, logging estruturado em `runs/game_{id}/gm_log.jsonl`.

### Como rodar (dev)

Terminal 1 — backend (porta 8000):

```bash
source .venv/bin/activate
pip install -e .  # ou apenas: pip install fastapi 'uvicorn[standard]'
uvicorn src.api.main:app --reload --port 8000
```

Para usar ações livres é preciso `GEMINI_API_KEY` (ou `GOOGLE_API_KEY`) no ambiente. Sem chave, ações canônicas continuam funcionando — o servidor responde 503 só para ações livres.

Terminal 2 — frontend (porta 5173):

```bash
cd frontend
npm install
npm run dev
```

Abre em `http://localhost:5173/play`. CORS já configurado para `localhost:5173` em `src/api/main.py` (envvar `CORS_ORIGINS` para origens extras).

### Endpoints da API

- `GET  /game/missions` — catálogo de missões
- `GET  /game/canonical_actions` — catálogo das 5 ações canônicas
- `POST /game` — cria partida `{seed, mission_id}` → `{game_id, state}`
- `GET  /game/{id}/state` — snapshot completo
- `GET  /game/{id}/history` — lista de TurnRecord
- `POST /game/{id}/action` — submete `{type: canonical|free, action_id?, prompt?}`
- `DELETE /game/{id}` — descarta partida

Docs interativas: `http://localhost:8000/docs`.

## Frontend

Aplicação React + TypeScript + Vite localizada em `frontend/`.

### Rodando localmente

```bash
cd frontend
npm install
npm run dev
```

Abre em `http://localhost:5173`.

### Build de produção

```bash
cd frontend
npm run build
```

### Fonte de dados

O frontend tenta carregar simulações reais de `../runs/*.json` (gerados pelo motor Python). Se nenhum JSON existir, faz fallback para mock data em `frontend/src/lib/mock-data.ts`.

A cópia de `../runs/*.json` para `frontend/public/runs/` é feita automaticamente pelo script `scripts/sync-runs.js`, registrado como hook `predev` / `prebuild` no `package.json`. O loader (`frontend/src/lib/real-data-loader.ts`) descobre os arquivos via `import.meta.glob('/public/runs/*.json')`.

Um chip discreto no canto inferior esquerdo da `TurnView` indica a fonte ativa (`data: mock` ou `data: real (run_id)`).

### Tecnologias

- React 18 + TypeScript + Vite
- Tailwind CSS
- Framer Motion (animações)
- Recharts (sparklines)
- ReactFlow (grafo causal)
- Zustand (estado global)
- React Simple Maps (mapa por bloco)

### Identidade visual

"Future-retro / cronista de mundos paralelos". Paleta cyan/amber/magenta sobre fundo bg-deep #0a0e1a. Contraste tipográfico fundamental: serif Cormorant na narrativa, mono JetBrains no resto da UI.
