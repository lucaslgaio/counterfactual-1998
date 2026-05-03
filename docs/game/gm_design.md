# GM-LLM — design e guardrails

O **GM-LLM** (Game Master) é o componente que interpreta ações livres do jogador
no Modo Jogo, transformando prosa em deltas estruturados que o motor SDM
consome. Ele é deliberadamente "burro" em termos narrativos — só decide o que
*acontece estatisticamente*; quem narra é o cronista.

Esta nota documenta os **quatro guardrails** que mantêm o GM previsível mesmo
operando com Gemini 2.5 Flash @ temperature 0.7.

## Por que precisamos de guardrails

Sem restrição, um GM-LLM tende a:

1. **Inflar magnitudes** — interpretar "lobby por regulação" como `democracy +5.0`
   quando o cap razoável é `+1.2`.
2. **Inventar métricas** — chamar de `public_opinion` algo que o motor não tem.
3. **Determinar 100% de sucesso** — não modela falha de execução; toda ação
   funciona.
4. **Ser opaco** — quando algo dá errado, não dá pra reproduzir o que ele decidiu.

Cada guardrail abaixo ataca um destes problemas.

## 1. Rubrica de magnitude conservadora (no prompt)

O system prompt do GM ([gm_prompt_pt_br.txt](../../src/game/prompts/gm_prompt_pt_br.txt))
explicita:

> SEJA CONSERVADOR — defaulte para low/medium impact. High só para ações que
> envolvam investimento substancial implícito (centenas de milhões, parcerias massivas).

E lista as métricas válidas com seus ranges. Isto reduz o ruído de saída antes
mesmo de qualquer pós-processamento.

## 2. CATEGORY_CAPS (clip pós-retorno)

Definido em [src/game/config.py](../../src/game/config.py):

```python
CATEGORY_CAPS = {
    "research":    {"max_metric_delta": 1.5, "max_metrics_affected": 3},
    "deployment":  {"max_metric_delta": 2.0, "max_metrics_affected": 4},
    "lobby":       {"max_metric_delta": 1.2, "max_metrics_affected": 3},
    "partnership": {"max_metric_delta": 1.5, "max_metrics_affected": 3},
    "comms":       {"max_metric_delta": 1.0, "max_metrics_affected": 4},
    "m_and_a":     {"max_metric_delta": 1.5, "max_metrics_affected": 3},
    "rejected":    {"max_metric_delta": 0.0, "max_metrics_affected": 0},
}
```

`clip_interpretation()` ([src/game/gm.py](../../src/game/gm.py)) aplica o cap após
o GM retornar:

- Se `|delta| > max_metric_delta`, satura no cap (não rejeita).
- Se há mais métricas afetadas que `max_metrics_affected`, mantém top-N por
  magnitude e descarta o resto.
- Marca cada campo clipado em `ActionResult.clipped_fields` para o frontend
  exibir badge "magnitude clipada".

Filosofia: **clipar > rejeitar**. Rejeitar quebra a sensação de agência — o
jogador não entende por que sua ação "sumiu". Clipar é silencioso, transparente,
e mantém o jogo fluindo.

## 3. success_p + roll determinístico (com falha parcial)

GM retorna `success_p ∈ [0,1]`. `roll_outcome()` ([src/game/gm.py](../../src/game/gm.py))
sortea de forma determinística:

```python
combined = f"{seed}:{turn}:{action_hash}"
rng_seed = int(sha256(combined.encode()).hexdigest()[:8], 16)
roll = rng.random()
```

Outcomes:

- `roll < success_p` → **success** (efeito integral)
- `roll < success_p + (1-success_p)*0.5` → **partial_failure** (affected × 0.3,
  side_effects integrais)
- caso contrário → **total_failure** (só side_effects + custo simbólico em
  lab_funds)

A divisão 50/50 do espaço pós-success_p garante que mesmo ações com
`success_p=0.7` têm risco real de fracasso (15% de chance de total failure).

**Determinismo crítico**: mesma `(seed, turn, action_hash)` → mesmo roll.
Reproduz uma partida só com a sequência de prompts.

## 4. Logging estruturado

Cada chamada do GeminiGameMaster grava uma linha em
`runs/game_{game_id}/gm_log.jsonl`:

```json
{
  "turn": 3,
  "prompt": "Recrutamos 10 PhDs em alignment...",
  "raw_response": {"classification": "research", "plausible": true, ...},
  "parsed": {"classification": "research", ...},
  "latency_seconds": 2.1,
  "model": "gemini-2.5-flash"
}
```

Auditável depois — útil para:
- Debug ("por que essa ação foi clipada?").
- Calibração ("o GM está classificando 'lobby' demais como 'research'?").
- Geração de dataset ("treinar um GM menor com estas interpretações").

## Stack técnica

Reusa o cliente Gemini do cronista (`src/chronicler/gemini_client.py`):

| Configuração            | Valor                | Motivo                                       |
|-------------------------|----------------------|----------------------------------------------|
| Model                   | `gemini-2.5-flash`   | Custo. GM não precisa de Pro.                |
| Temperature             | 0.7                  | Mais conservador que cronista (0.85).        |
| Thinking budget         | 0                    | Idem cronista — função call estável.         |
| Function calling mode   | `ANY` (forçado)      | Sem prosa solta; só `interpret_action`.       |
| Safety                  | `BLOCK_ONLY_HIGH`    | Conteúdo histórico/político.                 |

## O que **não** é responsabilidade do GM

- **Narrativa em prosa** — fica com o cronista. GM só dá `narrative_seed` (15-30 palavras).
- **Decidir win/lose** — fica com `_evaluate_status` em `game_runner.py`.
- **Aplicar deltas** — só os retorna; quem aplica é o motor SDM.
- **Inventar métricas novas** — schema Pydantic + lista de `available_metrics` no
  prompt. Se o GM tentar, Pydantic ainda aceita (dict[str, float] livre), mas o
  motor ignora silenciosamente keys desconhecidas via `_route_external_delta`.
  Idealmente, validar contra `list_available_metrics()` antes de aplicar — TODO
  para v0.2.

## Determinismo e reprodutibilidade — limites

Dada `(seed, mission, sequence_of_player_prompts)`, a partida é reproduzível
**modulo o GM-LLM**. Como Gemini não garante determinismo absoluto entre
chamadas (mesmo com temperature 0), seria preciso cachear interpretações para
reprodução perfeita.

**MVP aceita**: roll é determinístico (controlado por nós); GM tem ~95% de
estabilidade na prática (validado empiricamente no cronista). v0.2 pode
adicionar cache de interpretação por `(seed, prompt_hash, turn)`.
