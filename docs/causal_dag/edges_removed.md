# Edges removidas em revisão

Este documento registra edges que foram removidas do DAG durante revisão crítica, com justificativa por edge. Mantido para rastreabilidade — se uma edge for re-adicionada no futuro, é importante entender por que foi removida antes.

---

## Etapa 1.5 — Rodada 2 (7 edges removidas)

### e_005: tech_industry.tech_employment_share → financial_markets.global_index

- **Direção original**: positiva | **Magnitude**: weak | **Lag**: 0 | **Scope**: global

**Por que foi removida**: atribuição causal errada. A correlação entre tech employment share e índice de mercado existe, mas a causalidade é predominantemente inversa (mercado em alta puxa contratação em tech, não o contrário). Tratá-la como tech → markets cria fluxo causal espúrio.

**Substituto natural na Rodada 3**: `e_088_07_bigtech_to_media_trust` e `e_089_08_employment_to_global_index` capturam aspectos relacionados, com direção correta.

---

### e_015: financial_markets.systemic_risk → education.cost_index

- **Direção original**: positiva | **Magnitude**: weak | **Lag**: 6 | **Scope**: global

**Por que foi removida**: transmissão tripla com incerteza alta em cada elo (systemic_risk → cortes orçamentários → custo da educação). Cada elo da cadeia tem efeito difuso e contestável. Modelar como uma única edge esconde mecanismos heterogêneos. Se quiser capturar este efeito no futuro, faz mais sentido ir via `cuts_in_public_spending` como composite intermediário (não modelado).

---

### e_041: governance.democracy_index → ai_capability.frontier_capability

- **Direção original**: negativa | **Magnitude**: weak | **Lag**: 6 | **Scope**: within_block

**Por que foi removida**: direção genuinamente contestada na literatura, já flagada como `direction_contested: true` no PR #1. Argumentos:
- A favor (negativa): democracias regulam mais cedo e mais cuidadosamente, atrasando fronteira.
- A favor (positiva): democracias atraem talento internacional, têm mercados de capital de risco mais profundos, e infraestrutura digital mais distribuída — todos puxam fronteira pra cima.
- China é o caso paradigmático contra a edge: regime autoritário que avança rapidamente em IA. Mas China também acumula limites estruturais (talent flight, sanctions impact).

**Decisão**: remover por enquanto e re-introduzir só se Etapa 5 mostrar evidência empírica clara.

---

### e_042: governance.democracy_index → ai_capability.population_penetration

- **Direção original**: positiva | **Magnitude**: weak | **Lag**: 6 | **Scope**: within_block

**Por que foi removida**: similar a e_041 — direção ambígua. Democracias podem aumentar penetração via maior infraestrutura digital E reduzir penetração via mais privacy laws, idade mínima, restrições. China contradiz com penetração alta sob regime autoritário.

---

### e_054: ai_capability.frontier_capability.EU → ai_capability.frontier_capability.US

- **Direção original**: positiva | **Magnitude**: weak | **Lag**: 4 | **Scope**: spillover

**Por que foi removida**: a transferência real EU→US em capacidade de IA acontece principalmente via M&A (DeepMind comprada pela Google em 2014, Mistral angariando capital em SF) e migração de talento — não via difusão técnica difusa. Modelar como spillover suave subestima o mecanismo (concentração de fluxo) e superestima a magnitude no agregado.

---

### e_083: health.life_expectancy → labor_market.employment_rate

- **Direção original**: positiva | **Magnitude**: weak | **Lag**: 12 | **Scope**: global

**Por que foi removida**: mecanismo fraco para o lag de 12 turnos (6 anos), com direção ambígua. Pessoas vivendo mais tempo trabalham mais (positiva) OU saem mais cedo do mercado por aposentadoria precoce (negativa, em economias com sistemas previdenciários generosos). Net effect difuso.

**Substituto na Rodada 3**: `e_088_37_employment_to_life` captura a direção oposta (mais robusta na literatura — Case & Deaton "deaths of despair").

---

### e_087: information_ecosystem.media_trust → geopolitics.active_conflicts

- **Direção original**: negativa | **Magnitude**: weak | **Lag**: 4 | **Scope**: matrix_targeted

**Por que foi removida**: transmissão confusa, mecanismo tortuoso. "Confiança em mídia ↑ → menos manipulação → menos guerra" passa por muitos nós intermediários (público informado, accountability democrática, foreign policy mais cautelosa). Cada elo tem incerteza própria. Modelar como edge direta esconde a complexidade.

**Substituto melhor**: `disinformation → conflicts` direto (a ser adicionado em Rodada 3 como e_088_28).

---

## Princípio de remoção

Uma edge é removida quando:

1. **Direção contestada empiricamente** sem consenso teórico claro (e_041, e_042).
2. **Mecanismo de transmissão envolve 3+ elos não-modelados**, gerando incerteza composta inaceitável (e_015, e_087).
3. **Causalidade real é inversa** ou bidirecional sem net effect claro (e_005, e_083).
4. **Mecanismo concentrado mal-modelado por edge difusa** (e_054).

Edges fortemente contestadas mas com base teórica mantém-se com `direction_contested: true` em vez de remoção (e.g., e_008, e_014, e_082).
