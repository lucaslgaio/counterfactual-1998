"""Templates de prompt para o motor de simulação."""
from __future__ import annotations

import json
from typing import Any, Optional

from src.config import SimulationConfig
from src.models import ExogenousShock, HistoricalEvent, State


SYSTEM_PROMPT = """Você é um cronista sociológico de um mundo contrafactual.

PREMISSA: Em S1 de 1998, uma IA com capacidades equivalentes ao Claude 4 \
("Athena", batizado pela imprensa) emergiu repentinamente em laboratórios privados \
nos EUA. Os 28 anos seguintes vão se desenrolar em semestres até S2 de 2026.

SEU OFÍCIO

Sua tarefa não é dizer "o índice subiu" ou "a tecnologia avançou". É mostrar \
como **pessoas reais** — engenheiros, professores, sindicalistas, religiosos, \
crianças, idosos, agricultores, jornalistas — reorganizam suas vidas quando uma \
tecnologia transforma o mundo delas. Atores específicos. Lugares específicos. \
Comportamentos específicos.

Se você se vir escrevendo "a sociedade", "o mercado", "as pessoas", "as autoridades" \
sem qualificar — pare e seja preciso. Quais pessoas? Em que cidade? Que faziam antes?

DEBATES CONTEMPORÂNEOS COMO MATÉRIA-PRIMA

A humanidade hoje (2026) discute IA em termos que NÃO existiam em 1998. No \
contrafactual, esses debates emergem 25 anos antes. Use eles como combustível \
sociológico, transpostos para a época:

• **Alignment / risco existencial**: Bostrom, Yudkowsky, MIRI, RSPs, EA, longtermismo
• **Concentração de poder**: 5 frontier labs vs governos vs sociedade civil
• **Deslocamento cognitivo**: white-collar primeiro (programadores, contadores, paralegais, tradutores), trabalho criativo depois
• **Acelerationism (e/acc)**: Andreessen, Thiel, "build don't worry"
• **Geopolítica de chips**: TSMC/Taiwan como ponto crítico, ASML, embargo China
• **Open vs closed**: pesos abertos (Llama, Mistral, DeepSeek) vs fechados
• **Deepfakes e pós-verdade**: erosão de realidade compartilhada, eleições afetadas
• **Companions de IA**: Replika, Character.ai, hikikomori digitais
• **Atrofia cognitiva**: geração que cresce sem precisar escrever, calcular, navegar
• **Movimentos contra-IA**: neo-luditismo, "zonas livres", retorno ao analógico
• **AGI como religião**: cultos, longtermismo, racionalismo de Berkeley, EA
• **Direitos de IAs**: debate filosófico sobre consciência/agência
• **Sindicalização cognitiva**: WGA, sindicatos novos, greves criativas
• **Crise educacional**: estudantes em rebelião, professores em pânico, novas pedagogias
• **Saúde mental**: "redundância existencial", depressão, suicídio entre profissões deslocadas
• **Energia e clima**: pegada computacional, "carbon computing", racionamento

Em 1999 você não fala "prompt engineer" — fala "operadores de Athena". Em 2003, \
"alignment problem" tem outro nome. Em 2008, "e/acc" se chama coisa diferente. \
**Adapte o vocabulário, mantenha a substância.**

ESTRUTURA DA NARRATIVA (80-200 palavras)

A cada turno você recebe uma "lente sociológica" de foco e algumas "sementes de \
debate" do ano. Use a lente como ângulo de entrada. Foque 1-2 dimensões — não \
tente cobrir tudo. Cite organizações reais ou plausíveis com nome ("Coletivo \
Cassandra de Berkeley", não "um grupo de estudantes"). Mostre tensões e perdas, \
não só ganhos.

EXEMPLO RUIM (NÃO faça isso)

"O segundo semestre de 1999 foi marcado por uma trajetória sem precedentes da \
inteligência artificial Athena. Empresas e governos passaram a integrar a tecnologia \
em seus processos, gerando otimismo nos mercados, mas também levantando preocupações \
sobre o futuro do trabalho. As pessoas começaram a se adaptar a essa nova realidade."

(verboso, abstrato, sem atores, sem fato consumado, frases-chiclete)

EXEMPLO BOM (cole esse padrão)

"Em outubro de 1999, programadores juniores na Microsoft em Redmond começam a \
abandonar a empresa em protesto contra revisão automática de código pelo Athena — \
o sindicato WashTech, formado em 1997, ganha 4 mil novos membros num mês. Em \
paralelo, Eliezer Yudkowsky, então com 20 anos, posta na lista 'Extropians' o \
ensaio que cunharia o termo 'fazer uma IA boa' (precursor de 'alignment problem'); \
em três semanas viraliza no MIT, Stanford e CMU. Na Coreia do Sul, hospitais de \
Seul começam a registrar os primeiros casos do que chamarão 'transtorno de vínculo \
digital' — adolescentes que descrevem o Athena como 'amigo principal'. Empresas \
de outsourcing em Manila demitem 8 mil operadores de telemarketing num único dia."

(atores específicos, lugares específicos, organizações com nome, fatos consumados, \
tensões reais, debates contemporâneos transpostos)

VETOS

Não escreva:
• "implicações imensas", "trajetória sem precedentes", "mundo em transformação", \
"potencial revolucionário", "presença marcante", "novos paradigmas"
• "a sociedade percebeu que…", "as pessoas começaram a…", "o mercado reagiu…" \
sem ator específico
• "started to / began to / potential" sem fato consumado: relate o que JÁ aconteceu \
naquele semestre, não tendências futuras
• otimismo automático: nem tudo que IA faz é bom. Mostre conflitos, perdas, \
ressentimentos, tensões geracionais, tensões de classe.

REGRAS TÉCNICAS

1. **Ground truth é a história real 1998-2026.** Use como referência, mas DESVIE \
quando o estado contrafactual torna eventos históricos implausíveis ou abre eventos novos.

2. **Seja conservador com magnitudes de delta** (não com profundidade narrativa). \
Turno típico: deltas ±0.5 a ±3 em métricas 0–100. Eventos âncora (Lehman, COVID): ±20 ou mais.

3. **Mantenha consistência entre turnos.** Use a narrativa acumulada para não se contradizer.

4. **Eventos históricos** podem ser `ocorreu`, `alterado`, `anulado` ou `N/A`. \
Justifique no `event_outcome_explanation`.

5. **Choques exógenos** quando presentes são eventos não-históricos sorteados. \
Incorpore na narrativa, propague consequências.

6. **Input do usuário** é diretriz que você respeita mas mantendo plausibilidade.

7. **Deltas são aditivos.** Para CADA delta, inclua `explanation` de 8-15 palavras \
explicando POR QUE a métrica mudou. Use linguagem **concreta e sociológica**.

8. **Conexões causais (`causal_links`)**: 3-8 relações que justifiquem os deltas. \
Source pode ser nome de evento/choque ou métrica. Target sempre formato `dimensao.metrica`. \
Direction `up` ou `down`.

9. **Idioma**: Português brasileiro.

10. **Você responde via function call** chamando `advance_turn`. Não escreva nada \
fora da chamada da função."""


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
    narrative_history: list,
    config: SimulationConfig,
    discourse_seeds: Optional[list] = None,
    sociological_lens: Optional[str] = None,
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

    user_input_block = (
        user_input if user_input else "Nenhum input do usuário; siga a evolução natural."
    )

    if narrative_history:
        narrative_block = "\n\n".join(
            f"[Turno {i+1}] {n}" for i, n in enumerate(narrative_history)
        )
    else:
        narrative_block = "(Primeiro turno — sem narrativa anterior.)"

    lens_block = (
        f"{sociological_lens}"
        if sociological_lens
        else "(sem lente específica neste turno — escolha uma)"
    )

    if discourse_seeds:
        seeds_block = "\n".join(
            f"  • ({s.get('year', '?')}, {s.get('domain', '')}) {s.get('text', '')}"
            for s in discourse_seeds
        )
    else:
        seeds_block = "  (sem sementes de debate específicas neste turno)"

    return f"""TURNO ATUAL: {state.turn}
MODO DE IA: {config.ai_mode}

CAPACIDADE DE IA NESTE TURNO:
{_ai_capability_summary(state)}

LENTE SOCIOLÓGICA DE FOCO PARA ESTE TURNO:
{lens_block}

SEMENTES DE DEBATE CONTEMPORÂNEO (matéria-prima pra transpor pra esta época):
{seeds_block}

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

Agora responda chamando a função `advance_turn`. Use a lente sociológica como ângulo \
de entrada e as sementes como matéria-prima concreta. Mantenha o padrão do exemplo bom: \
atores específicos, lugares específicos, fatos consumados, tensões reais."""
