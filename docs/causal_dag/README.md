# Nova arquitetura: System Dynamics + LLM cronista

Este documento explica a refatoração da Etapa 1 do `counterfactual-1998`. Antes desta etapa, o LLM (Gemini 2.5 Flash) era o único responsável por (1) decidir como o estado quantitativo evoluía a cada turno, (2) declarar conexões causais, e (3) escrever a narrativa. A nova arquitetura separa esses três papéis.

## O que muda

**Antes** — pipeline monolítico:
```
estado_t + evento + choque → LLM → (deltas, causal_links, narrativa)
```
O LLM faz tudo. Os números são produto da intuição do modelo, e mudar o prompt muda os números. Reproduzir uma run específica depende de seed do LLM (que não é estável).

**Depois** — pipeline em três camadas:
```
estado_t + evento + choque
    │
    ├─→ MOTOR CAUSAL (DAG + funções estruturais) → deltas determinísticos
    │
    ├─→ SAMPLER DE EVENTO → variante condicional escolhida → delta_package
    │
    └─→ LLM → narrativa interpretativa (recebe deltas como input fixo)
```

O LLM deixa de produzir números e passa a interpretar. Os deltas vêm de equações estruturais explícitas, validáveis, calibráveis. A narrativa fica como camada final de "tradução para o humano".

## Por que essa mudança

Três problemas com a versão anterior:

1. **Não-reprodutibilidade científica**: dois pesquisadores rodando a mesma config com mesma seed obtinham distribuições diferentes de deltas, porque a temperatura do LLM e tokenização interna não são determinísticas. Não podíamos rodar Monte Carlo de verdade.

2. **Acoplamento entre prosa e mecânica**: trocar o tom narrativo (mais sociológico, mais econômico) também mudava as magnitudes dos deltas, porque o mesmo prompt regia ambos. Isso impedia controle experimental.

3. **Sem auditabilidade causal**: o LLM declarava `causal_links` por turno mas não havia consistência inter-turnos. Uma cadeia "russian_default → systemic_risk ↑ → media_trust ↓" aparecia num turno e desaparecia no seguinte, sem que nada na simulação justificasse.

Com SDM, o conjunto de relações causais é fixo (revisado e justificado), as magnitudes são parâmetros que se calibram contra a história real (Etapa 5), e o LLM se concentra no que sabe fazer melhor: escrever sobre o que aconteceu de forma rica e contextualizada.

## Como ler os arquivos `spec/`

A pasta `spec/` contém cinco JSONs declarativos:

| Arquivo | O que define |
|---|---|
| `metric_taxonomy.json` | As 24 métricas, classificadas em vectorized (por bloco), global (escalar único), ou matrix (par 4×4 entre blocos). Inclui valores iniciais 1998 e âncoras de referência. |
| `geographic_blocks.json` | Os 4 blocos (US/EU/CN/RoW) com PIB, população, capacidade tech 1998. Matriz de fricção de spillover entre eles. |
| `causal_dag.json` | 87 edges representando relações causais entre métricas. Cada edge tem direção, magnitude qualitativa, lag temporal, scope (within_block / spillover / global) e referência à justificativa documentada. |
| `structural_functions.json` | Para cada edge, a forma funcional (linear, log_linear, sigmoid, exponential_decay) e parâmetros placeholder. Calibração real é Etapa 5. |
| `event_variants.json` | Para os 16 eventos âncora históricos, 3-4 variantes condicionais cada. Probabilidades base moduladas pelo estado contrafactual. Cada variante tem um delta_package. |

Tudo está marcado `draft: true` no nível de cada item. **Nada disto está calibrado** — é uma proposta inicial estruturada para revisão humana edge por edge.

## Roadmap das 7 etapas

A refatoração total está dividida em:

1. **Etapa 1 (esta)**: especificação formal do DAG, blocos, eventos, sem implementar motor.
2. **Etapa 2**: revisão humana das edges, blocos e variantes (com Claude Chat ajudando), até consenso sobre a estrutura.
3. **Etapa 3**: pesquisa e calibração — preencher os parâmetros das funções estruturais com base em literatura empírica.
4. **Etapa 4**: implementação do motor de simulação SDM (`run_simulation`, `apply_deltas` baseado em DAG, sampling de eventos).
5. **Etapa 5**: backtest da história real 1998-2024 — rodar com seed=histórica, ver se reproduz métricas conhecidas dentro de tolerância.
6. **Etapa 6**: integração do LLM cronista — recebe deltas como input fixo, gera narrativa interpretativa.
7. **Etapa 7**: substituição do motor antigo no smoke_test/CLI; manter o velho rodando em paralelo até validar o novo.

Esta etapa entrega só os arquivos da pasta `spec/`, módulos `src/spec/` para validação, scripts de visualização, testes, e este conjunto de docs.

## Como contribuir / revisar edges

O fluxo previsto para a Etapa 2 (próxima):

1. **Abrir uma issue por cluster de edges** (ex: "Revisar edges Tecnologia & IA → Economia"). Listar as 4-8 edges relevantes.
2. **Discutir cada edge com Claude Chat** carregando `docs/causal_dag/edges_justifications.md` no contexto. O foco é: a edge faz sentido teórico-empiricamente? a magnitude qualitativa está plausível? o lag está razoável?
3. **Atualizar `causal_dag.json`** se necessário (mudar magnitude, lag, direção, ou remover/adicionar edges).
4. **Atualizar `edges_justifications.md`** com a justificativa final, com referências.
5. **Marcar como `draft: false`** apenas quando duas leituras independentes (humano + Claude Chat) concordarem.
6. **PR para `main`** com diff legível por edge.

Variantes de eventos seguem o mesmo padrão, mas em `event_variants.md`. Blocos geográficos têm seu próprio doc em `geographic_blocks.md`.

## Validação

Comandos disponíveis na raiz do repo:

```bash
# Roda todos os validadores
python scripts/validate_spec.py

# Estatísticas do DAG
python scripts/dag_stats.py

# Renderiza diagrama (SVG + PNG, gera também .dot)
python scripts/render_dag.py

# Testes
pytest tests/spec/
```

A saída atual: 31 testes passando, 87 edges validadas, 16 eventos com 51 variantes totais, 54 delta_packages, sem ciclos lag-0, todas referências de métrica resolvidas.

## Princípios não-negociáveis (mantidos)

Da arquitetura original:

1. Estado quantitativo separado da narrativa.
2. Cada turno é puro: dado `(estado_t, evento, choque, input)` → `(estado_{t+1}, narrativa)`.
3. Aleatoriedade explícita por seed (Monte Carlo).
4. História real é ground truth; contrafactual desvia só com justificativa.

Princípios novos da Etapa 1:

5. **Toda relação causal é explícita e revisada**. Nada implícito no LLM.
6. **Magnitude qualitativa antes de número**. Calibração é trabalho separado, depois da estrutura estar sólida.
7. **Vetorização geográfica de primeira classe**. O mundo não é uma média global.
8. **Eventos como variáveis aleatórias condicionais**. "Aconteceu" e "não aconteceu" são apenas duas das 3-4 possibilidades.
