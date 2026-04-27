# counterfactual-1998

Simulador histórico contrafactual: como o mundo (1998–2026) teria evoluído se uma IA equivalente ao Claude 4 tivesse surgido no final da bolha .com.

A unidade de simulação é a **sociedade global**, modelada por 12 dimensões e 24 métricas. A cada semestre, o LLM atua como motor causal, narrador e atualizador de estado, devolvendo (1) uma narrativa em prosa e (2) deltas numéricos validados via Pydantic. A simulação é probabilística (Monte Carlo): mesma config + seeds diferentes produzem runs divergentes.

> **Status**: Fase 1 do roadmap (esqueleto funcional). Veja [PROJECT_SPEC.md](./PROJECT_SPEC.md) para o modelo conceitual, dimensões, eventos âncora e fases.

## Setup

```bash
# Pré-requisitos: Python 3.11+
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Configure a API key
cp .env.example .env
# Edite .env e cole sua ANTHROPIC_API_KEY
```

## Smoke test (Fase 1)

Roda 1 turno (S1/1998) e imprime narrativa + deltas:

```bash
python -m src.smoke_test
```

## Estrutura

```
counterfactual-1998/
├── PROJECT_SPEC.md            # modelo conceitual completo
├── data/
│   ├── initial_state.json     # estado S1/1998 ancorado em dados reais
│   └── historical_events.json # 16 eventos âncora 1998–2026 (semestres)
└── src/
    ├── config.py              # SimulationConfig (parâmetros da run)
    ├── models.py              # State, deltas, eventos, choques
    ├── llm.py                 # cliente Anthropic + tool use
    ├── prompts.py             # system prompt + builder de mensagem
    ├── shocks.py              # choques exógenos com seed
    └── smoke_test.py          # teste de 1 turno end-to-end
```

## Princípios

1. Saída do LLM sempre estruturada via tool use, validada por Pydantic.
2. Estado quantitativo (números) e narrativa (texto) são separados desde o turno 1.
3. Cada turno é puro: `(state, event, shock, user_input, narrative_history) → (narrative, deltas)`.
4. Aleatoriedade explícita e reprodutível por seed.
