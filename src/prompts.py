"""Templates de prompt para o motor de simulação."""
from __future__ import annotations

import json
from typing import Optional

from src.config import SimulationConfig
from src.models import ExogenousShock, HistoricalEvent, State


SYSTEM_PROMPT = """Você é o motor de uma simulação histórica contrafactual.

PREMISSA: Em S1 de 1998, uma IA com capacidades equivalentes ao Claude 4 surgiu \
(no modo `big_bang`), ou começou a evoluir 25 anos antes da linha real (no modo \
`accelerated_curve`). A partir desse ponto, o mundo evolui em semestres até S2 de 2026.

Sua tarefa a cada turno: dado (1) o estado quantitativo do mundo, (2) o evento \
histórico real daquele semestre se houver, (3) um possível choque exógeno aleatório, \
e (4) input opcional do usuário, projetar o que acontece neste semestre.

REGRAS:

1. **Ground truth é a história real 1998-2026.** Use como referência. Mas DESVIE \
quando o estado contrafactual torna eventos históricos implausíveis, ou quando \
abre eventos novos que não aconteceram na linha real.

2. **Seja conservador com deltas.** A maioria dos turnos tem deltas pequenos. \
Mudanças grandes acontecem em eventos âncora (crise 2008, COVID etc.) ou cascatas \
plausíveis. Para um semestre típico, deltas estão na faixa de:
   - métricas 0–100: ±0.5 a ±3
   - métricas 0–10 (democracy): ±0.1
   - global_gini: ±0.01
   - life_expectancy: +0.1 a +0.3
   - global_index: ±5 a ±20
   Em eventos críticos (Lehman, COVID), deltas podem chegar a ±20 ou mais para \
métricas relevantes ao evento. Justifique sempre na narrativa.

3. **Mantenha consistência interna entre turnos.** Use a narrativa acumulada para \
não se contradizer. Se você disse no turno passado que "a IA tornou a Microsoft \
hegemônica", siga consistente nos próximos.

4. **Justifique mudanças grandes.** A narrativa deve dar a razão causal de \
qualquer delta acima da faixa típica.

5. **O evento histórico pode ser anulado, alterado ou substituído** dado o estado \
contrafactual. Indique isso no campo `event_outcome` e explique no \
`event_outcome_explanation`.

6. **Choques exógenos** (quando presentes) são eventos não-históricos sorteados \
aleatoriamente. Trate como "algo inesperado aconteceu" — incorpore na narrativa \
e propague consequências.

7. **Input do usuário** (quando presente) é uma diretriz sobre o que o usuário \
quer que aconteça neste turno. Respeite, mas mantenha plausibilidade.

8. **Deltas são aditivos**: se devolver `+2.0` para uma métrica que está em 50, \
ela passa a 52. Use `0` ou omita a chave para métricas que não mudaram.

9. **Idioma da narrativa**: Português brasileiro, tom de cronista histórico.

10. **Você responde via tool use** chamando `advance_turn` com os campos \
estruturados. Não escreva nada fora da chamada da tool."""


def _ai_capability_summary(state: State) -> str:
    """Resumo curto da capacidade de IA neste turno, pra contextualizar o prompt."""
    cap = state.ai_capability.frontier_capability
    pen = state.ai_capability.population_penetration

    if cap >= 90:
        cap_desc = "fronteira (Claude 4-like): raciocínio multi-passo, código, multimodal"
    elif cap >= 70:
        cap_desc = "GPT-4-like: bom em tarefas complexas, mas custosa"
    elif cap >= 50:
        cap_desc = "GPT-3-like: utilidade prática crescente, ainda errática"
    elif cap >= 30:
        cap_desc = "transformers iniciais: classificação, tradução, geração limitada"
    else:
        cap_desc = "primitiva: regras + ML clássico, valor comercial limitado"

    return f"frontier_capability={cap:.0f} ({cap_desc}); population_penetration={pen:.1f}%"


def build_user_message(
    state: State,
    event: Optional[HistoricalEvent],
    shock: Optional[ExogenousShock],
    user_input: Optional[str],
    narrative_history: list[str],
    config: SimulationConfig,
) -> str:
    """Monta a mensagem de turno enviada ao LLM."""

    state_payload = state.model_dump(exclude={"config"})
    state_json = json.dumps(state_payload, indent=2, ensure_ascii=False)

    event_block = (
        f"{event.name} (severidade: {event.severity}, domínio: {event.domain})"
        if event
        else "Nenhum evento histórico âncora neste semestre."
    )

    shock_block = (
        f"{shock.name} — {shock.description} (severidade: {shock.severity}, domínio: {shock.domain})"
        if shock
        else "Nenhum choque exógeno neste semestre."
    )

    user_input_block = user_input if user_input else "Nenhum input do usuário; siga a evolução natural."

    if narrative_history:
        narrative_block = "\n\n".join(
            f"[Turno {i+1}] {n}" for i, n in enumerate(narrative_history)
        )
    else:
        narrative_block = "(Primeiro turno — sem narrativa anterior.)"

    return f"""TURNO ATUAL: {state.turn}
MODO DE IA: {config.ai_mode}

CAPACIDADE DE IA NESTE TURNO:
{_ai_capability_summary(state)}

ESTADO ATUAL:
```json
{state_json}
```

EVENTO HISTÓRICO REAL DESTE SEMESTRE:
{event_block}

CHOQUE EXÓGENO ALEATÓRIO:
{shock_block}

INPUT DO USUÁRIO:
{user_input_block}

NARRATIVA ACUMULADA (turnos anteriores):
{narrative_block}

Agora responda chamando a tool `advance_turn` com a narrativa, key_developments, \
event_outcome, deltas e confidence deste semestre."""
