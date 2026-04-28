# Blocos geográficos

A simulação opera em 4 blocos: **US**, **EU**, **EU**, **RoW**. Esta granularidade é resultado de um trade-off explícito entre fidelidade geográfica e tractabilidade.

## Por que 4 e não outro número

| Opção | Vantagens | Desvantagens |
|---|---|---|
| **2 blocos (Ocidente / Resto)** | Simplicidade máxima | Perde dinâmica intra-Ocidente (EU vs US tem regulação muito diferente); China invisível |
| **4 blocos (atual)** | Captura US/EU/CN como pólos distintos; RoW absorve o resto | Brasil, Coreia, Japão, Índia, Rússia ficam todos em RoW |
| **8-12 blocos** | Mais granularidade (Japão, Coreia, Índia, Brasil separados) | Cada métrica vetorizada cresce em dimensão; difícil revisar 90+ valores iniciais; Bass diffusion tem 8x8=64 spillovers |

A escolha de 4 reflete a posição de 1998 onde os pólos tecnológicos eram efetivamente US/EU/CN/resto, com RoW se diferenciando internamente apenas a partir de meados dos anos 2000 (ascensão Coreia/Taiwan/Índia em tech).

**Quando subir para mais blocos**: se a Etapa 5 mostrar que o backtest histórico falha sistematicamente em RoW por agregar regiões muito diferentes (e.g., Coreia divergir muito de Brasil), a Etapa 6+ pode separar Japão+Coreia+Taiwan como bloco "EastAsia" e deixar RoW residual.

## Definição operacional dos blocos

| Bloco | Inclui | Excludes |
|---|---|---|
| **US** | Apenas Estados Unidos da América | — |
| **EU** | UE-15 (membros 1995) + Reino Unido + Suíça + Noruega | Países pré-acessão UE-leste |
| **CN** | República Popular da China continental | Hong Kong, Macau, Taiwan |
| **RoW** | Todo o resto: América Latina, África, Oriente Médio, Ásia (exceto China continental), Oceania, Canadá, Rússia | — |

Hong Kong e Taiwan ficam em RoW (não em CN) porque em 1998 sua dinâmica econômica e tech era muito mais próxima do bloco anglófono / livre comércio do que da China continental.

## Estado inicial 1998 — racional

Os valores em `spec/geographic_blocks.json` são DRAFT mas baseados em ordens de grandeza razoáveis. A validação contra dados reais (Banco Mundial, Maddison Project) é parte da Etapa 2.

| Bloco | population_share | gdp_share | tech_capacity | internet_pen | rd_share | Justificativa |
|---|---|---|---|---|---|---|
| US | 4.5% | 30% | 1.0 | 36% | 42% | Hegemon tech 1998. PIB nominal ~30% global. Liderança em P&D, infraestrutura digital, capital de risco. |
| EU | 7.8% | 28% | 0.78 | 18% | 27% | Capacidade científica forte mas indústria tech mais fragmentada. Pioneira em política e regulação. |
| CN | 21.1% | 6.9% | 0.30 | 0.2% | 5% | PIB nominal pequeno em USD 1998 (PPP-adjusted seria maior). Tech nascente, infra digital muito limitada. |
| RoW | 66.6% | 35.1% | 0.40 | 5% | 26% | Bloco residual heterogêneo. Tech_capacity é média ponderada — Japão/Coreia/Taiwan elevam, África/Sul-Ásia puxam pra baixo. |

`tech_capacity_1998` é um proxy 0-1 para "capacidade de absorver tecnologia de fronteira" (combina infra digital, capital humano em STEM, mercado financeiro de risco). Não é um dado bruto — é uma estimativa estruturada. Validar contra ICT Development Index do ITU.

## Inicialização das métricas vectorizadas (14 após Etapa 1.5)

> **Etapa 1.5 — Rodada 1**: 4 mudanças de taxonomia foram aplicadas (4 novas métricas vectorizadas):
> - `science_rd.publications_index` migrou de global para vectorized (US: 100 base = 1998; EU: 80; CN: 25; RoW: 30). China em volume ultrapassou US a partir de ~2018, dinâmica regional crítica.
> - `education.mean_years_schooling` migrou de global para vectorized (US: 12.4; EU: 9.2; CN: 6.4; RoW: 5.8). Trajetórias divergiram radicalmente: US estagnou em ~13.5 desde 1990, EU subiu de 9 para 12, CN de 6 para 10.
> - `inequality.global_gini` foi substituída por par: `gini_intra_block` (vectorized, US: 0.42; EU: 0.30; CN: 0.40; RoW: 0.48) + `gini_between_blocks` (global, 0.69). Mecanismos opostos — convergência entre vs divergência intra — agora separados.
> - `health.mental_wellbeing` foi adicionada (vectorized, US: 65; EU: 70; CN: 60; RoW: 55). Captura efeitos psicossociais que o sistema antes ignorava.


A divisão dos valores iniciais 1998 entre os 4 blocos exigiu propor números plausíveis quando dado granular não estava disponível. Convenção:

- **`frontier_capability`**: US=92 (big_bang assume IA emerge no Vale), EU=78 (capacidade científica próxima mas sem labs frontier), CN=35 (pesquisa nascente), RoW=18 (ML clássico em Japão/Coreia, pouco no resto). Soma não tem significado — é a capacidade do bloco mais avançado dentro de cada bloco.
- **`population_penetration`**: ponto de partida do big_bang em US=5%, decai por bloco conforme infraestrutura digital e GDP per capita. EU=2%, CN=0.3%, RoW=0.2%.
- **`bigtech_concentration`**: 1998 tinha Microsoft + IBM + Sun como big tech US (HHI=24); EU mais fragmentado (HHI=18); CN tinha Lenovo nascente + estatais (HHI=30); RoW tinha NEC, Samsung, etc (HHI=22).
- **`tech_employment_share`**: US=4.2% reflete avanço da bolha .com já em curso; EU=3.0% similar; CN=1.8% incipiente; RoW=2.6% média ponderada.
- **`automation_exposure`**: relativamente uniforme em 1998 (8-9%) — antes da onda de automação cognitiva, exposição é principalmente robótica industrial.
- **`employment_rate`**: variação real entre blocos refletindo estruturas demográficas e participação feminina (CN=70% por participação feminina e estrutura de força de trabalho rural+urbana incluída; EU=60.5% reflete aposentadoria precoce e desemprego estrutural).
- **`democracy_index`**: V-Dem/EIU 1998 dão US=8.0, EU=7.8 (Bélgica/Itália puxam pra baixo), CN=2.5 (autoritário com algumas reformas), RoW=5.0 (mistura ampla).
- **`ai_regulation_maturity`**: 0 em todos os blocos em 1998 — não existe ainda.
- **`disinformation_level`**: estável em ~16-22 globalmente. CN levemente mais alto pelo controle estatal de mídia.
- **`breakthroughs_per_year`**: total global=12. Distribuído em US=6, EU=4, CN=1, RoW=1. Refletindo participação em prêmios Nobel + publicações de alto impacto na época.

**Pontos a validar com humano na Etapa 2**:
- `tech_capacity_1998` para RoW (média de regiões muito diferentes)
- `frontier_capability` no big_bang — porque assumir EU=78 (não emerge tão atrás)?
- `breakthroughs_per_year` — é qualitativo demais, talvez precise critério mais explícito

## Mecânica de spillover (Bass diffusion)

A propagação entre blocos segue o modelo Bass de difusão de inovações (Bass 1969), modificado:

```
delta_target_block = friction(source, target) * coefficient * source_value
```

Onde `friction(source, target)` é um valor 0-1 da matriz `spillover_friction_matrix`:
- 1.0 = transferência sem perda
- 0.0 = isolamento total

**Modulators** ajustam a friction conforme o estado contrafactual:
- `geopolitics.bilateral_tensions.US_CN` ↑ → friction US→CN ↓ (sanções, embargos)
- `governance.ai_regulation_maturity` divergente entre US e EU → friction US→EU ↓ (incompatibilidade técnica)
- `education.mean_years_schooling` global ↑ → friction US→RoW ↑ (capacidade de absorção)

Exemplo: `population_penetration.US` cresce de 5% para 25% entre 1998 e 2005. `friction(US→EU)=0.7` significa que `population_penetration.EU` recebe um "puxão" de 0.7 * 0.4 (q_imitation Bass) * (25-5) = 5.6 pontos sobre o que aconteceria sem spillover.

**Pontos a validar**:
- Valores de `base` em cada par de blocos
- Lista de `modulators` por par
- Parâmetros default Bass (`p_innovation=0.005`, `q_imitation=0.4`)

## Limitações conhecidas

1. **Brasil dentro de RoW**: para um simulador feito por brasileiro, RoW é frustrante — a dinâmica brasileira fica invisível. Etapa 6+ pode adicionar bloco "BR" se houver demanda.
2. **Coreia/Japão/Taiwan dentro de RoW**: em 1998 isso era razoável, em 2010+ deixa de ser. Fragmentar no decorrer da simulação não é trivial.
3. **Granularidade temporal igual entre blocos**: um turno = um semestre para todos. Mas em 2020 a velocidade de adoção de IA na China foi diferente da do Vale. Para capturar isso, precisaria de turnos sub-semestrais por bloco — fora do escopo.
4. **Fricção de spillover é estática estruturalmente**: pode mudar via modulators, mas a estrutura de "qual bloco influencia qual" é fixa. Realisticamente, "RoW" deveria ter sub-redes (Japão↔Coreia ≠ África↔Brasil).
