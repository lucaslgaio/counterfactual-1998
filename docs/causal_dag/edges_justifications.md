# Justificativa por edge

Cada uma das 87 edges em `spec/causal_dag.json` tem uma seção curta abaixo. **Todas marcadas DRAFT** — revisão humana em pares (humano + Claude Chat) é parte da Etapa 2.

> **Etapa 1.5 — Rodada 1**: edges que referenciavam `inequality.global_gini` foram migradas:
> - e_009, e_011, e_016, e_017, e_020 → agora usam `inequality.gini_intra_block` (mecanismos atuam intra-bloco).
> - e_022 → usa `inequality.gini_between_blocks` (Collier-style argumento sobre desigualdade entre nações).
>
> Edges que ficaram com ambos endpoints vectorizados (após `publications_index` e `mean_years_schooling` virarem vectorized) mudaram scope de `global` para `within_block`: e_009, e_011, e_014, e_016, e_033, e_038, e_078, e_084, e_085.
>
> Edges com target em métrica matricial (`bilateral_tensions`, `active_conflicts`) ganharam scope `matrix_targeted`: e_022, e_023, e_067, e_068, e_072, e_086, e_087.
>
> Edges vector→global ganharam campo `aggregation`: e_004 (`leader`), e_005, e_006, e_010, e_013, e_026, e_028, e_032, e_035, e_036, e_046, e_047, e_050, e_080 (todos `weighted_mean`).
>
> Edges e_024, e_063, e_064 mudaram forma estrutural para `sigmoid_temporal` (dose-resposta de disinformação mudou pós-2016).

> **Etapa 1.5 — Rodada 2**:
> - 7 edges foram removidas (e_005, e_015, e_041, e_042, e_054, e_083, e_087). Justificativas em `edges_removed.md`.
> - e_006 foi dividida em e_006a (trading risk, lag 1) e e_006b (infrastructure dependency, lag 8).
> - ~26 edges tiveram magnitude/lag/contested ajustados. Notas inline em cada edge alterada (`etapa_1_5_note`).
> - Total de edges: 87 → 81 (-7 removidas, +1 split).

Convenção: magnitude qualitativa, lag em turnos (1 turno = 1 semestre), scope = within_block / spillover / global.

Onde indico referências, sugiro papers que tenho confiança razoável que existem; onde houver dúvida, marquei `[verificar referência]`.

---

## Cluster: Tecnologia & IA → Economia

### e_001: ai_capability.frontier_capability → labor_market.automation_exposure
- **Direção**: positiva | **Magnitude**: forte | **Lag**: 2 turnos | **Scope**: within_block

A capacidade de fronteira da IA expande o conjunto de tarefas economicamente automatizáveis. Acemoglu & Restrepo (2020) estimam elasticidade significativa entre capacidade computacional e exposição à automação, com lag de ~1-2 anos para implantação efetiva em workflows.

**Referências sugeridas**: Acemoglu & Restrepo "Robots and Jobs" 2020; Frey & Osborne "Future of Employment" 2017.

**A validar**: magnitude "strong" vs. possível "medium" se considerarmos fricção de adoção institucional; lag de 2 turnos (1 ano) pode subestimar.

### e_002: ai_capability.population_penetration → labor_market.employment_rate
- **Direção**: negativa | **Magnitude**: medium | **Lag**: 4 turnos | **Scope**: within_block

Uma vez que IA está distribuída na população (não apenas em laboratórios), substituição de trabalho começa a reduzir taxa de emprego. Lag de 2 anos reflete tempo de adaptação institucional, treinamento e redirecionamento.

**A validar**: efeito pode ser zero ou positivo se a IA cria mais trabalho do que destrói (Aghion et al. argumento). A literatura está dividida.

### e_003: ai_capability.frontier_capability → tech_industry.bigtech_concentration
- **Direção**: positiva | **Magnitude**: forte | **Lag**: 2 turnos | **Scope**: within_block

Capacidade de fronteira gera retornos crescentes de escala (mais dados → modelos melhores → mais usuários → mais dados). Khan (2017) "Amazon's Antitrust Paradox" articula essa dinâmica para plataformas; aplicada a IA é ainda mais aguda.

### e_004: ai_capability.frontier_capability → financial_markets.global_index
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 1 turno | **Scope**: global

Mercados precificam capacidade futura de IA com algum lag. Forma `exponential_decay` reflete que efeito é maior na primeira surpresa (1998 big_bang) e decai à medida que IA vira "esperada".

### e_005: tech_industry.tech_employment_share → financial_markets.global_index
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 0 turnos | **Scope**: global

Crescimento do setor tech é correlato (não causal direto) com índice global, mas tem componente causal via geração de produtividade e earnings. Lag-0 porque mercados antecipam.

### e_006: ai_capability.frontier_capability → financial_markets.systemic_risk
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 4 turnos | **Scope**: global

IA introduz novos vetores de risco: concentração de infraestrutura computacional, falhas em cascata via dependência operacional, opacidade algorítmica em decisões financeiras. Effeito leva tempo a se materializar.

### e_007: ai_capability.frontier_capability → ai_capability.population_penetration
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 2 turnos | **Scope**: within_block

Maior capacidade torna a IA útil para tarefas mais cotidianas → adoção. Forma sigmoid reflete saturação à medida que penetração aproxima de 100%.

### e_008: ai_capability.population_penetration → tech_industry.tech_employment_share
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 4 turnos | **Scope**: within_block

Penetração maior cria demanda por trabalhadores que treinam, mantêm, customizam e auditam IA — alguns dos quais entram na conta de "tech employment".

**Referências validadas (Etapa 2)**:
- BIS Working Paper 1325 2025, "AI productivity gains without displacement"
- Johnston & Makridis 2025, SSRN, "AI complementarity in tech labor markets"
- Brynjolfsson, Chandar & Chen 2025, NBER 33867, "Generative AI and the Decline of Junior Hiring"

**Confidence**: medium

**Validation note**: Literatura 2024-26: complementaridade dominante curto prazo (BIS 2025 +4% produtividade sem displacement) mas substitui juniors (-13% hiring, Brynjolfsson 2025). Net negligible no agregado. Refs: BIS WP 1325 2025; Johnston Makridis 2025 SSRN; Brynjolfsson Chandar Chen 2025 NBER 33867.

---

## Cluster: Economia → Sociedade

### e_009: labor_market.automation_exposure → inequality.global_gini
- **Direção**: positiva | **Magnitude**: forte | **Lag**: 4 turnos | **Scope**: global

Automação de tarefas rotineiras intermediárias polariza mercado de trabalho (alta-skilled e low-skilled crescem; middle encolhe), aumentando Gini. Autor (2014) "Skill Mismatch" e Autor & Dorn (2013) documentam.

### e_010: labor_market.automation_exposure → inequality.top1pct_share
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 4 turnos | **Scope**: global

Donos de capital de IA capturam parte significativa dos ganhos. Brynjolfsson & McAfee "Race Against the Machine" 2011 [verificar referência exata] argumenta isso explicitamente.

### e_011: labor_market.employment_rate → inequality.global_gini
- **Direção**: negativa | **Magnitude**: medium | **Lag**: 2 turnos | **Scope**: global

Pleno emprego aprieta o mercado de trabalho de baixa qualificação, reduzindo desigualdade. Compositional effect bem documentado em literatura macro.

### e_012: financial_markets.global_index → inequality.top1pct_share
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 1 turno | **Scope**: global

Bull markets concentram ganhos em quem detém ativos financeiros, que é desproporcionalmente o top 1%. Saez & Zucman (2016) documentam.

### e_013: tech_industry.bigtech_concentration → inequality.top1pct_share
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 2 turnos | **Scope**: global

Concentração de mercado em poucos players → fundadores e early investors capturam fortunas. A lista Forbes mostra pico de fortunas em fundadores de tech (Bezos, Zuckerberg, etc) coincide com aumento da concentração.

### e_014: labor_market.employment_rate → education.mean_years_schooling
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 8 turnos | **Scope**: global

Mercado de trabalho aquecido aumenta retorno à educação, motivando mais escolaridade. Lag longo (4 anos) reflete tempo de decisão familiar + ensino formal.

**Referências validadas (Etapa 2)**:
- Kahn 2010, Labour Economics 17(2):303-316, "The long-term labor market consequences of graduating from college in a bad economy"
- Schudde & Bernell 2019, SAGE Open, "Educational Attainment and Unemployment: A Cross-State Analysis"
- Boushey 2021, Washington Center for Equitable Growth, "Recessions and education in the United States"

**Confidence**: medium

**Validation note**: Direcao genuinamente ambigua: recessao->mais escolaridade (Kahn 2010 Great Recession) vs economia quente->opportunity cost de estudar sobe. Magnitude negligible no agregado global por cancelamento. Refs: Kahn 2010 Labor Economics; Schudde Bernell 2019 SAGE; Boushey 2021 Equitable Growth.

### e_015: financial_markets.systemic_risk → education.cost_index
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 6 turnos | **Scope**: global

Crises financeiras ↑ resultam em cortes de orçamento público para educação e mais endividamento estudantil → custo sobe para o aluno final. Goldin & Katz "Race Between Education and Technology" capítulo sobre custo.

### e_016: inequality.global_gini → labor_market.employment_rate
- **Direção**: negativa | **Magnitude**: weak | **Lag**: 6 turnos | **Scope**: global

Alta desigualdade reduz demanda agregada (renda concentrada → menor consumo) → menos emprego. Stiglitz "The Price of Inequality" 2012 argumenta isso. Magnitude pequena porque outros canais compensam.

---

## Cluster: Sociedade → Política

### e_017: inequality.global_gini → governance.democracy_index
- **Direção**: negativa | **Magnitude**: forte | **Lag**: 6 turnos | **Scope**: within_block

Alta desigualdade erosiona instituições democráticas: captura regulatória pelos ricos, polarização, populismo. Acemoglu & Robinson "Why Nations Fail" 2012; "Economic Origins of Dictatorship and Democracy" 2006.

### e_018: inequality.top1pct_share → governance.democracy_index
- **Direção**: negativa | **Magnitude**: medium | **Lag**: 4 turnos | **Scope**: within_block

Concentração de riqueza extrema permite captura de processo político (financiamento de campanha, mídia, lobby). Gilens & Page (2014) "Testing Theories of American Politics" mostram preferências do top 1% têm muito mais peso em políticas públicas que mediana.

### e_019: education.mean_years_schooling → governance.democracy_index
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 8 turnos | **Scope**: within_block

Mais escolaridade → cidadania mais ativa, instituições democráticas mais resilientes. Lipset 1959 "Some Social Requisites of Democracy" articulou isso. Forma `log_linear` porque retornos diminuem após educação básica universal.

### e_020: inequality.global_gini → governance.ai_regulation_maturity
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 6 turnos | **Scope**: within_block

Aumento de desigualdade gera demanda política por intervenção regulatória sobre tech (vista como amplificadora). Backlash que produz AI Acts.

### e_021: education.mean_years_schooling → governance.ai_regulation_maturity
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 6 turnos | **Scope**: within_block

População mais educada → debate público mais informado → regulação mais sofisticada. Não é causalidade direta forte.

### e_022: inequality.global_gini → geopolitics.active_conflicts
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 8 turnos | **Scope**: global

Desigualdade extrema dentro de países correlaciona com instabilidade política e conflito armado. Cederman et al. (2011) "Horizontal Inequalities and Ethnonationalist Civil War" para evidência empírica.

### e_023: education.mean_years_schooling → geopolitics.active_conflicts
- **Direção**: negativa | **Magnitude**: weak | **Lag**: 10 turnos | **Scope**: global

Mais escolaridade reduz risco de conflito armado. Collier & Hoeffler "Greed and Grievance in Civil War" 2004. Lag muito longo reflete que efeito é geracional.

---

## Cluster: Informação & Política

### e_024: information_ecosystem.disinformation_level → governance.democracy_index
- **Direção**: negativa | **Magnitude**: forte | **Lag**: 4 turnos | **Scope**: within_block

Desinformação massiva erode instituições democráticas. Manifesto pós-2016 da literatura de "post-truth politics". Persily (2017) "Can Democracy Survive the Internet?" Journal of Democracy.

### e_025: information_ecosystem.media_trust → governance.democracy_index
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 4 turnos | **Scope**: global

Mídia tradicional é instituição-canal: confiança nela suporta accountability democrática. Ladd "Why Americans Hate the Media" 2012.

### e_026: governance.democracy_index → information_ecosystem.media_trust
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 4 turnos | **Scope**: global

Democracias funcionais protegem liberdade de imprensa, sustentando trust. Loop de feedback positivo com e_025.

### e_027: governance.ai_regulation_maturity → information_ecosystem.disinformation_level
- **Direção**: negativa | **Magnitude**: medium | **Lag**: 4 turnos | **Scope**: within_block

Regulação efetiva de plataformas + obrigatoriedade de disclosure de IA reduz desinformação. EU AI Act como exemplo concreto.

### e_028: information_ecosystem.disinformation_level → information_ecosystem.media_trust
- **Direção**: negativa | **Magnitude**: forte | **Lag**: 1 turno | **Scope**: global

Imediato: mais desinfo no ecossistema → confusão sobre o que é confiável → trust em mídia tradicional cai (junto com tudo). Forma sigmoid porque trust tem floor.

### e_029: ai_capability.population_penetration → information_ecosystem.disinformation_level
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 4 turnos | **Scope**: within_block

Maior penetração de IA na população democratiza ferramentas de geração de conteúdo sintético → mais deepfakes, mais conteúdo manipulado.

### e_030: ai_capability.frontier_capability → information_ecosystem.disinformation_level
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 2 turnos | **Scope**: within_block

Capacidade de fronteira eleva qualidade dos deepfakes (mais convincentes). Magnitude weak porque distribuição (penetração) importa mais que capacidade pura.

---

## Cluster: Conhecimento & Saúde

### e_031: science_rd.breakthroughs_per_year → ai_capability.frontier_capability
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 2 turnos | **Scope**: within_block

Avanços científicos (otimização, neural arch, etc) feedback para a fronteira de IA. Loop reforço com e_037.

### e_032: science_rd.breakthroughs_per_year → health.life_expectancy
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 8 turnos | **Scope**: global

Descobertas em medicina e biologia se traduzem em terapias e expectativa de vida. Forma `log_linear` porque ganhos marginais diminuem em países que já têm life_expectancy alta.

### e_033: science_rd.publications_index → science_rd.breakthroughs_per_year
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 4 turnos | **Scope**: global

Maior volume de pesquisa → maior chance de breakthrough. Diminishing returns claros: dobrar publicações não dobra breakthroughs.

### e_034: health.diagnostic_accuracy → health.life_expectancy
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 4 turnos | **Scope**: global

Diagnóstico mais preciso → tratamento certo, mais cedo → melhor outcome. Magnitude weak porque diagnóstico é só um pedaço da cadeia de saúde.

### e_035: ai_capability.population_penetration → health.diagnostic_accuracy
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 4 turnos | **Scope**: global

IA distribuída em sistemas de saúde → mais diagnósticos AI-augmented. Mas precisa adoção institucional, regulamentação, treinamento — daí lag de 2 anos.

### e_036: ai_capability.population_penetration → education.cost_index
- **Direção**: negativa | **Magnitude**: medium | **Lag**: 6 turnos | **Scope**: global

IA tutor democratiza acesso → custo cai para o aluno. Khan Academy + IA personalizada como exemplo.

### e_037: ai_capability.frontier_capability → science_rd.breakthroughs_per_year
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 2 turnos | **Scope**: within_block

IA aplicada à pesquisa científica acelera descoberta (AlphaFold como caso). Loop reforço com e_031.

**Referências validadas (Etapa 2)**:
- Jumper et al 2021, Nature 596:583-589, "Highly accurate protein structure prediction with AlphaFold"
- Bianchini, Muller & Pelletier 2022, Research Policy 51(10):104604, "Artificial intelligence in science: An emerging general method of invention"
- Cockburn, Henderson & Stern 2018, NBER, "The Impact of Artificial Intelligence on Innovation"

**Confidence**: high

**Validation note**: AlphaFold e exemplo canonico de magnitude strong. Heterogeneidade alta entre dominios — forte em structural biology/quimica, mais fraca em ciencias sociais. Refs: Jumper et al 2021 Nature; Bianchini Muller Pelletier 2022 Research Policy; Cockburn Henderson Stern 2018 NBER. NOTA Etapa 5: calibracao deve considerar variancia alta entre disciplinas.

**Nota Etapa 5 (calibração)**: Calibracao deve considerar variancia alta entre disciplinas (structural biology/quimica vs ciencias sociais). AlphaFold-style breakthroughs concentrados em dominios computaveis.

### e_038: ai_capability.frontier_capability → science_rd.publications_index
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 4 turnos | **Scope**: global

IA assistindo escrita, revisão, geração de hipóteses → mais publicações. Risco de "publication mill" mas efeito quantitativo é positivo.

---

## Cluster: Política → Tecnologia & IA (regulação)

### e_039: governance.ai_regulation_maturity → ai_capability.frontier_capability
- **Direção**: negativa | **Magnitude**: weak | **Lag**: 4 turnos | **Scope**: within_block

Regulação restritiva pode desacelerar fronteira (compliance overhead, restrições de dados). Mas magnitude é fraca porque labs adaptam — efeito mais forte na velocidade que no nível final.

### e_040: governance.ai_regulation_maturity → ai_capability.population_penetration
- **Direção**: negativa | **Magnitude**: weak | **Lag**: 2 turnos | **Scope**: within_block

Regulação afeta acesso ao usuário final (KYC, idade, restrições). Mas a tendência é difícil reverter — magnitude weak.

### e_041: governance.democracy_index → ai_capability.frontier_capability
- **Direção**: negativa | **Magnitude**: weak | **Lag**: 6 turnos | **Scope**: within_block

Democracias tendem a regular mais cedo e mais cuidadosamente, o que pode atrasar fronteira. China não-democrática consegue investir mais agressivamente em alguns subdomínios.

**A validar**: relação ambígua na literatura. Pode ser oposta (democracias atraem talento internacional → fronteira ↑).

### e_042: governance.democracy_index → ai_capability.population_penetration
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 6 turnos | **Scope**: within_block

Democracias têm infraestrutura digital mais distribuída e menos restrições de acesso → maior penetração.

### e_043: governance.ai_regulation_maturity → tech_industry.bigtech_concentration
- **Direção**: negativa | **Magnitude**: weak | **Lag**: 4 turnos | **Scope**: within_block

Antitrust + restrições de aquisições → menos concentração. Microsoft case 2001 e EU vs Google são exemplos diretos.

### e_044: tech_industry.bigtech_concentration → governance.ai_regulation_maturity
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 4 turnos | **Scope**: within_block

Concentração extrema gera pressão política por regulação. Loop de feedback negativo com e_043.

---

## Cluster: Energia & Clima

### e_045: energy_climate.co2_gt_year → energy_climate.renewable_share
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 8 turnos | **Scope**: global

Aumento de CO2 induz pressão social e política por mudança da matriz. Lag muito longo (4 anos) porque transição energética é lenta.

### e_046: ai_capability.frontier_capability → energy_climate.co2_gt_year
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 4 turnos | **Scope**: global

Treinamento e inferência de IA consomem energia significativa. Magnitude global é weak no agregado mas crescente.

### e_047: ai_capability.population_penetration → energy_climate.co2_gt_year
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 4 turnos | **Scope**: global

Inferência distribuída em massa adiciona footprint energético. Pode virar negativa se computação ficar muito mais eficiente — calibração depende do periodo.

### e_048: energy_climate.renewable_share → financial_markets.global_index
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 4 turnos | **Scope**: global

Setor renováveis cresce, capital flui pra ele, mercados refletem. Magnitude weak porque efeito é diluído no agregado global.

### e_049: energy_climate.co2_gt_year → financial_markets.systemic_risk
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 12 turnos | **Scope**: global

Climate risk como fator de systemic risk financeiro (stranded assets, eventos extremos). Lag de 6 anos reflete reconhecimento institucional lento. Carney "Tragedy of the Horizon" 2015.

### e_050: science_rd.breakthroughs_per_year → energy_climate.renewable_share
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 4 turnos | **Scope**: global

Avanços em armazenamento, perovskites, fusão → maior share renovável.

---

## Cluster: Spillovers entre blocos

### e_051: ai_capability.frontier_capability.US → .EU
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 4 turnos | **Scope**: spillover

EU absorve avanços via colaboração científica, hire reverso, papers públicos. Friction US→EU = 0.7 (alta).

### e_052: ai_capability.frontier_capability.US → .CN
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 6 turnos | **Scope**: spillover

CN absorve via papers + reverse engineering, mas friction = 0.4 com modulação por bilateral_tensions e export_controls.

### e_053: ai_capability.frontier_capability.US → .RoW
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 8 turnos | **Scope**: spillover

RoW absorve via difusão geral. Lag mais longo reflete capacidade de absorção heterogênea.

### e_054: ai_capability.frontier_capability.EU → .US
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 4 turnos | **Scope**: spillover

EU também produz e exporta capacidade (DeepMind, Mistral). Magnitude menor que e_051 (assimetria 1998).

### e_055: ai_capability.frontier_capability.CN → .US
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 4 turnos | **Scope**: spillover

DeepSeek-like dinâmica: open weights da China adotados nos EUA. Magnitude weak em 1998 mas pode crescer ao longo da run.

### e_056-058: ai_capability.population_penetration.US → .EU/.CN/.RoW
- **Direção**: positiva | **Magnitude**: medium/weak/weak | **Lag**: 2/4/4 turnos | **Scope**: spillover

Bass diffusion clássica: produtos lançados nos US se difundem por outras regiões. Sigmoid reflete saturação. Bass (1969) "A New Product Growth Model".

### e_059-060: science_rd.breakthroughs_per_year.US → .EU/.CN
- **Direção**: positiva | **Magnitude**: medium/weak | **Lag**: 4/6 turnos | **Scope**: spillover

Ciência se difunde via publicações. Speed depende de língua/política (CN tradicionalmente mais lento por barreira linguística + propriedade intelectual).

### e_061: governance.ai_regulation_maturity.EU → .US
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 4 turnos | **Scope**: spillover

"Brussels effect" (Bradford 2020): regulação europeia influencia mercados globais. Empresas multinacionais adotam padrão mais alto.

### e_062: governance.ai_regulation_maturity.EU → .RoW
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 4 turnos | **Scope**: spillover

RoW (especialmente Brasil, Coreia, Índia) tende a copiar templates regulatórios europeus. Mais forte que e_061 porque RoW tem menos stack regulatório próprio.

### e_063-064: information_ecosystem.disinformation_level.US → .EU/.RoW
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 1 turno | **Scope**: spillover

Conteúdo de desinformação em inglês se espalha rápido para outras regiões. Lag 1 (semestre) reflete quase-instantaneidade.

---

## Cluster: Geopolítica

### e_065-066: geopolitics.bilateral_tensions.US_CN → .ai_regulation_maturity.US/.CN
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 2 turnos | **Scope**: within_block

Tensões geopolíticas legitimam regulação nacional sob argumento de "soberania algorítmica" e "segurança nacional". Chips Act, EO de Biden sobre IA são exemplos diretos.

### e_067-068: ai_capability.frontier_capability.US/.CN → bilateral_tensions.US_CN
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 2 turnos | **Scope**: global

Avanços de IA em qualquer dos blocos elevam tensão (security dilemma). Allison "Destined for War" 2017 sobre Thucydides Trap.

### e_069: bilateral_tensions.US_CN → financial_markets.systemic_risk
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 2 turnos | **Scope**: global

Tensões US-CN diretamente elevam systemic risk via supply chain disruption, sanções, volatilidade.

### e_070: geopolitics.active_conflicts → financial_markets.systemic_risk
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 0 turnos | **Scope**: global

Conflitos ativos imediatamente elevam risk premia. Lag-0.

### e_071: geopolitics.active_conflicts → financial_markets.global_index
- **Direção**: negativa | **Magnitude**: weak | **Lag**: 0 turnos | **Scope**: global

Conflitos derrubam mercados, mas magnitude é fraca no agregado global (frequentemente é sub-regional). Lag-0.

### e_072: bilateral_tensions.US_CN → geopolitics.active_conflicts
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 4 turnos | **Scope**: global

Tensões geram conflitos por proxy (Ucrânia, Mar do Sul da China). Lag de 2 anos reflete escalação progressiva.

### e_073: geopolitics.active_conflicts → energy_climate.co2_gt_year
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 2 turnos | **Scope**: global

Guerras emitem CO2 (combustíveis fósseis para máquinas militares, destruição). Magnitude weak porque é fração pequena do total global.

---

## Cluster: Feedback loops

### e_074: ai_capability.population_penetration → ai_capability.population_penetration (self)
- **Direção**: negativa | **Magnitude**: weak | **Lag**: 2 turnos | **Scope**: within_block | **Self loop**

Auto-saturação: à medida que penetration aproxima do teto, taxa de crescimento diminui. Forma sigmoid com beta=95 (teto). Bass diffusion clássico.

### e_075: financial_markets.systemic_risk → financial_markets.global_index
- **Direção**: negativa | **Magnitude**: forte | **Lag**: 0 turnos | **Scope**: global

Risk ↑ → markets ↓ imediatamente. Lag-0.

### e_076: financial_markets.global_index → financial_markets.systemic_risk
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 6 turnos | **Scope**: global

Bull markets longos acumulam risco (alavancagem, complacência). Minsky "Financial Instability Hypothesis". Lag de 3 anos.

### e_077: tech_industry.bigtech_concentration → ai_capability.frontier_capability
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 4 turnos | **Scope**: within_block

Concentração permite escala de investimento que estica a fronteira. Mas trade-off com competição.

### e_078: governance.democracy_index → education.mean_years_schooling
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 8 turnos | **Scope**: global

Democracias investem mais em educação universal. Loop com e_019.

### e_079: education.cost_index → education.mean_years_schooling
- **Direção**: negativa | **Magnitude**: medium | **Lag**: 8 turnos | **Scope**: global

Custo alto exclui populações de baixa renda → escolaridade média global cai. Loop com e_036 (penetration ↑ → cost ↓ → schooling ↑).

### e_080: tech_industry.bigtech_concentration → financial_markets.systemic_risk
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 6 turnos | **Scope**: global

Concentração de mercado (incluindo nuvem, infraestrutura) cria pontos únicos de falha sistêmica.

### e_081: labor_market.automation_exposure → labor_market.employment_rate
- **Direção**: negativa | **Magnitude**: medium | **Lag**: 4 turnos | **Scope**: within_block

Exposição se realiza em desemprego com lag. Adicional a e_002 (que vai via penetração).

**Referências validadas (Etapa 2)**:
- Acemoglu & Restrepo 2020, Journal of Political Economy 128(6):2188-2244, "Robots and Jobs: Evidence from US Labor Markets"
- Autor 2015, Journal of Economic Perspectives 29(3):3-30, "Why Are There Still So Many Jobs? The History and Future of Workplace Automation"
- IMF Staff Discussion Note 2024, "Gen AI extension to labor displacement model"

**Confidence**: high

**Validation note**: Magnitude strong empiricamente solida. Cada robo/1000 trabalhadores reduz EPOP em ~0.2pp (Acemoglu Restrepo 2020). Lag 4 turnos consistente com janela de implantacao tipica. Refs: Acemoglu Restrepo 2020 AER; Autor 2015 JEP; IMF SDN 2024 Gen AI extension.

### e_082: labor_market.automation_exposure → tech_industry.tech_employment_share
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 6 turnos | **Scope**: within_block

Exposição cria demanda por trabalhadores tech (treinadores, auditores, integradores).

**Referências validadas (Etapa 2)**:
- Bessen 2019, NBER Working Paper, "Automation and Jobs: When Technology Boosts Employment"
- Acemoglu & Restrepo 2018, NBER WP 24196, "The Race between Man and Machine: Implications of Technology for Growth, Factor Shares, and Employment"
- Goldfarb, Taska & Teodoridis 2023, Journal of Political Economy, "Could machine learning be a general-purpose technology? Evidence from online job postings"

**Confidence**: medium

**Validation note**: Direcao contestada confirmada empiricamente: substitui workers tech rotineiros (juniors, data analysts) e aumenta workers tech especializados (ML engineers, MLOps). Net effect negligible. Refs: Bessen 2019 NBER; Acemoglu Restrepo 2018 NBER WP 24196; Goldfarb Taska Teodoridis 2023 J Pol Economy.

### e_083: health.life_expectancy → labor_market.employment_rate
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 12 turnos | **Scope**: global

Pessoas mais saudáveis trabalham mais tempo. Magnitude weak no curto prazo, lag muito longo.

### e_084: education.mean_years_schooling → science_rd.publications_index
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 10 turnos | **Scope**: global

Mais escolaridade → mais pesquisadores → mais publicações. Lag de 5 anos = ensino superior + pós.

### e_085: education.mean_years_schooling → labor_market.automation_exposure
- **Direção**: negativa | **Magnitude**: weak | **Lag**: 10 turnos | **Scope**: global

Mais escolaridade → maior parte da força de trabalho em ocupações menos-rotineiras → menos exposta a automação. Magnitude weak porque alguns empregos high-skill também são automatizáveis.

### e_086: governance.democracy_index → bilateral_tensions.US_CN
- **Direção**: negativa | **Magnitude**: weak | **Lag**: 6 turnos | **Scope**: global

Democracias funcionais reduzem misperception e escalada (institutional channels). Effeito ambíguo na literatura.

### e_087: information_ecosystem.media_trust → geopolitics.active_conflicts
- **Direção**: negativa | **Magnitude**: weak | **Lag**: 4 turnos | **Scope**: global

Mídia funcional reduz manipulação que leva à guerra. Magnitude weak — é canal indireto.

---

## Pontos transversais a validar

1. **Lags**: todos os lags são chutes plausíveis. Estimar via VAR/IRF nos dados históricos é parte da Etapa 5.
2. **Magnitudes qualitativas**: a divisão weak/medium/strong é arbitrária. Calibrar via dados.
3. **Edges ausentes**: quase certamente há edges que omiti. Revisão por cluster com Claude Chat na Etapa 2 deve identificar.
4. **Edges em excesso**: algumas podem ser redundantes (e.g., automation_exposure → gini E → top1pct_share juntas). Cuidado pra não dupla-contar.
5. **Direções ambíguas**: e_041 (democracy → frontier_capability) tem direção contestada na literatura — testar empiricamente.
6. **Composite vs. independent**: várias edges podem fazer mais sentido como composições (ex: "labor disruption" combinando exposure + employment_rate). Considerar refatorar.
