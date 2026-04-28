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

> **Etapa 1.5 — Rodada 3**: 49 edges adicionadas (e_088 a e_136) cobrindo 6 clusters + 5 edges para health.mental_wellbeing. Loops de feedback centrais explicitamente formados:
> - **AI Funding Cycle**: financial_markets ↔ ai_capability via VC funding (e_004, e_089, e_096) — quando crise atinge mercados, capacidade de IA também desacelera.
> - **Regulação ↔ Concentração**: bigtech ↔ regulation (e_043, e_044, e_099, e_118) — concentração gera pressão regulatória, regulação reduz concentração com lag.
> - **Trust ↔ Disinformação**: media_trust ↔ disinformation (e_028, e_029, e_027, e_107) — confiança alta resiste à adoção de disinfo, mas disinfo erode trust com força. Sem o feedback negativo (e_107), motor produzia só amplificação monotônica.
>
> A função `validate_central_loops()` em `src/spec/validation.py` checa que esses 3 ciclos estão presentes a cada validação.

Convenção: magnitude qualitativa, lag em turnos (1 turno = 1 semestre), scope = within_block / spillover / global.

Onde indico referências, sugiro papers que tenho confiança razoável que existem; onde houver dúvida, marquei `[verificar referência]`.

---

## Cluster: Tecnologia & IA → Economia

### e_001: ai_capability.frontier_capability → labor_market.automation_exposure
- **Direção**: positiva | **Magnitude**: forte | **Lag**: 2 turnos | **Scope**: within_block

A capacidade de fronteira da IA expande o conjunto de tarefas economicamente automatizáveis. Acemoglu & Restrepo (2020) estimam elasticidade significativa entre capacidade computacional e exposição à automação, com lag de ~1-2 anos para implantação efetiva em workflows.

**Referências sugeridas**: Acemoglu & Restrepo "Robots and Jobs" 2020; Frey & Osborne "Future of Employment" 2017.

**A validar**: magnitude "strong" vs. possível "medium" se considerarmos fricção de adoção institucional; lag de 2 turnos (1 ano) pode subestimar.

**Referências validadas (Etapa 2)**:
- Acemoglu & Restrepo 2022, Econometrica 90(5):1973-2016, "Tasks, Automation, and the Rise in U.S. Wage Inequality"
- McKinsey Global Institute 2024, "AI in the Workplace"
- Brynjolfsson, Rock & Syverson 2021, AEJ: Macroeconomics 13(1):333-72, "The Productivity J-Curve: How Intangibles Complement General Purpose Technologies"

**Confidence**: high

**Validation note**: Mecanismo central do framework Acemoglu/Restrepo task displacement. Magnitude strong consistente. Lag 2 (1 ano) e prazo tipico tech-to-deployment. Refs: Acemoglu Restrepo 2022 Econometrica; McKinsey Global Institute 2024; Brynjolfsson Rock Syverson 2021 AEJ Macro.

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

**Referências validadas (Etapa 2)**:
- Acemoglu & Restrepo 2022, Econometrica 90(5):1973-2016, "Tasks, Automation, and the Rise in U.S. Wage Inequality"
- BIS Working Paper 1135 2024, "Automation, labor share and AI"
- IMF Staff Discussion Note 2024, "Gen AI: Artificial Intelligence and the Future of Work"

**Confidence**: high

**Validation note**: Magnitude strong robusta; 50-70% da variancia salarial US 1980-2016 explicada por task displacement. Heterogeneidade entre blocos (forte US/EU, mais fraca CN/RoW pre-2010). Refs: Acemoglu & Restrepo 2022 Econometrica; BIS WP 1135 2024; IMF SDN 2024 Gen AI.

### e_010: labor_market.automation_exposure → inequality.top1pct_share
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 6 turnos | **Scope**: global

Donos de capital de IA capturam parte significativa dos ganhos. Brynjolfsson & McAfee "Race Against the Machine" 2011 argumenta isso explicitamente.

**Referências validadas (Etapa 2)**:
- Piketty, Saez & Zucman 2018, NBER WP 22945 / QJE 133(2):553-609, "Distributional National Accounts: Methods and Estimates for the United States"
- Moll, Rachel & Restrepo 2025, "Uneven Growth: Automation's Impact on Income and Wealth Inequality"
- Alvaredo, Atkinson, Piketty & Saez 2013, Journal of Economic Perspectives 27(3):3-20, "The Top 1 Percent in International and Historical Perspective"

**Confidence**: medium

**Validation note**: Direcao robusta via 3 canais (capital share, entrepreneurial returns, CEO bargaining). Magnitude heterogenea por bloco — forte em US/UK, fraca em Japao/Alemanha/Nordicos. Lag 4->6 pq top share reage mais lento que gini geral. Refs: Piketty Saez Zucman 2018 NBER; Moll Rachel Restrepo 2025; Alvaredo et al 2013 JEP.

<!-- candidate_references:
- Acemoglu & Restrepo 2022. "Tasks, Automation, and the Rise in U.S. Wage Inequality". Econometrica 90(5): 1973-2016. [confidence: high — task-displacement explica 50-70% das mudanças na estrutura salarial dos EUA pós-1980; mecanismo central que conecta automation_exposure a desigualdade no topo via concentração de capital]
- Piketty, Saez & Zucman 2018. "Distributional National Accounts: Methods and Estimates for the United States". Quarterly Journal of Economics 133(2): 553-609. [confidence: high — fato empírico canônico da subida do top1pct desde 1980; documentam que o aumento veio inicialmente de labor income mas é mostly capital income desde 2000, alinhado com mecanismo da edge]
- Brynjolfsson & McAfee 2011. "Race Against the Machine: How the Digital Revolution is Accelerating Innovation, Driving Productivity, and Irreversibly Transforming Employment and the Economy". Digital Frontier Press, Lexington MA. [confidence: high — referência original citada na justificativa, livro confirmado existir]
- Moll, Rachel & Restrepo 2022. "Uneven Growth: Automation's Impact on Income and Wealth Inequality". Bank of England Working Paper 913 / NBER. [confidence: medium — conecta explicitamente aumento de automação a concentração de capital ownership no topo; base potencial para calibração do lag e magnitude]
- Possível dataset: World Inequality Database (wid.world) — séries de top1pct income share por país desde 1900, mantido por Piketty/Saez/Zucman; útil pra calibrar magnitude e lag empiricamente. [confidence: high]
-->

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

**Referências validadas (Etapa 2)**:
- Allcott & Gentzkow 2017, Journal of Economic Perspectives 31(2):211-236, "Social Media and Fake News in the 2016 Election"
- Edelman 2017-2024, longitudinal, "Edelman Trust Barometer"
- Newman et al 2024, Reuters Institute, "Digital News Report 2024"

**Confidence**: high

**Validation note**: Canal estabelecido empiricamente. Edelman Trust Barometer cai monotonicamente em paises com exposicao alta a fake news (US, Brasil, Polonia 2016+). Magnitude strong robusta. Refs: Allcott Gentzkow 2017 J Econ Perspectives; Edelman Trust Barometer 2017-2024 longitudinal; Newman et al 2024 Reuters Digital News Report.

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

**Referências validadas (Etapa 2)**:
- Brunnermeier 2009, Journal of Economic Perspectives 23(1):77-100, "Deciphering the Liquidity and Credit Crunch 2007-2008"
- Adrian & Brunnermeier 2016, American Economic Review 106(7):1705-41, "CoVaR"
- Bernanke 2018, FRBSF Brookings Paper, "The Real Effects of the Financial Crisis"

**Confidence**: high

**Validation note**: Edge mais empiricamente robusta do DAG. Cada crise sistemica documentada (1987, 1998 LTCM, 2000 dotcom, 2008 GFC, 2020 COVID, 2023 SVB) deprime mercados em tempo real. Refs: Brunnermeier 2009 J Econ Perspectives; Adrian Brunnermeier 2016 AER (CoVaR); Bernanke 2018 FRBSF.

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

---

## Apêndice: edges adicionadas na Rodada 3 (justificadas e validadas na Etapa 2)

As edges abaixo foram adicionadas na Etapa 1.5 Rodada 3 sem seção dedicada
no corpo deste documento. Justificativa inicial vive em `etapa_1_5_note`
(spec/causal_dag.json); referências e confidence vêm da revisão Etapa 2.

### e_101: ai_capability.population_penetration → education.mean_years_schooling
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 6 turnos | **Scope**: within_block

**Justificativa Rodada 3**: Rodada 3 - PROVAVELMENTE A EDGE MAIS IMPORTANTE FALTANDO. Direção contestada: tutoria personalizada barata (positiva) vs cognitive offloading (negativa). Debate Caplan vs ed-tech otimistas. Mecanismo de transformação cultural mais consequente no contrafactual.

**Referências validadas (Etapa 2)**:
- Kestin et al 2025, Scientific Reports, "AI tutoring with structured pedagogy improves learning outcomes (RCT)"
- Wecks et al 2025, ScienceDirect, "Unrestricted AI access reduces knowledge retention by 11 percentage points"
- LearnLM/Eedi 2025, UK RCT, "Curated AI tutoring intervention effects in K-12 mathematics"

**Confidence**: medium

**Validation note**: Direcao contestada confirmada por RCTs 2025: AI tutor com pedagogia bem desenhada melhora aprendizado (Kestin 2025), AI raw piora retencao (-11pp, Wecks 2025). Sinal depende da arquitetura do deployment. Refs: Kestin et al 2025 Sci Reports; Wecks et al 2025 ScienceDirect; LearnLM/Eedi RCT 2025 UK.

**Nota Etapa 5 (calibração)**: Dividir em duas edges (AI_with_safeguards -> +schooling, AI_unrestricted -> -schooling) ou usar parametro modulador de design pedagogico.

### e_123: ai_capability.frontier_capability → health.life_expectancy
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 12 turnos | **Scope**: global

**Justificativa Rodada 3**: Rodada 3: personalized medicine, drug discovery, public health surveillance; canal direto além de breakthroughs/diagnostic

**Referências validadas (Etapa 2)**:
- Wong et al 2024, Nature, "Discovery of a structural class of antibiotics with explainable deep learning"
- Reddy 2024, Lancet Digital Health, "AI in clinical medicine: regulatory pathways and deployment timelines"
- OECD 2023, Health at a Glance, "Artificial Intelligence in Health"

**Confidence**: medium

**Validation note**: Mecanismo via personalized medicine, drug discovery, public health. Lag 8->12 pq drug development e public health deployment limitados por aprovacao regulatoria, nao capacidade tecnica. AlphaFold viabilizou drug targets mas FDA approvals demoram 8-12 anos. Refs: Wong et al 2024 Nature antibiotics; Reddy 2024 Lancet Digital Health; OECD 2023 Health at a Glance AI.

### e_126: tech_industry.bigtech_concentration → science_rd.breakthroughs_per_year
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 4 turnos | **Scope**: within_block

**Justificativa Rodada 3**: Rodada 3: BigTech labs (DeepMind, FAIR, MSR) produzem fração crescente de breakthroughs em IA pós-2015

**Referências validadas (Etapa 2)**:
- Birhane et al 2022, Nature Machine Intelligence 4:902-916, "The values encoded in machine learning research"
- Ahmed & Wahed 2020, NeurIPS, "The De-democratization of AI: Deep Learning and the Compute Divide in Artificial Intelligence Research"
- Hartmann et al 2024, SocArXiv, "Industry vs academia in AI breakthroughs since 2015"

**Confidence**: medium

**Validation note**: DeepMind/FAIR/MSR produzem fracao crescente de breakthroughs em IA. Magnitude weak prudente — produzem muito em IA, pouco em outras areas cientificas. Refs: Birhane et al 2022 Nature Machine Intelligence; Ahmed Wahed 2020 NeurIPS de-democratization; Hartmann et al 2024 SocArXiv.

### e_132: ai_capability.population_penetration → health.mental_wellbeing
- **Direção**: positiva | **Magnitude**: medium | **Lag**: 4 turnos | **Scope**: within_block

**Justificativa Rodada 3**: Rodada 3: tutoria/parceria IA pode aliviar OU exacerbar isolamento. Direção contestada.

**Referências validadas (Etapa 2)**:
- Feng et al 2025, JMIR, "Therapeutic chatbots: meta-analysis of 31 RCTs (SMD -0.35 to -0.43)"
- Sharma & Lin 2025, Nature Medicine Health, "AI companions and mental health: orgaanic adoption risks"
- Haidt 2024, "The Anxious Generation", Penguin Press

**Confidence**: medium

**Validation note**: Meta-analise 31 RCTs (Feng 2025 JMIR): chatbots terapeuticos melhoram (SMD -0.35 a -0.43 dep/anx/stress). Mas adocao organica nao-supervisionada (Replika, Character.AI) preocupa (caso Setzer 2024). Direcao depende do design. Refs: Feng et al 2025 JMIR; Sharma Lin 2025 Nature Med Health; Haidt 2024 Anxious Generation.

**Nota Etapa 5 (calibração)**: Modelar como modulador de design pedagogico-terapeutico — chatbots curados positivos vs companions organicos potencialmente negativos.

### e_124: labor_market.employment_rate → health.life_expectancy
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 8 turnos | **Scope**: within_block

**Justificativa Rodada 3**: Rodada 3: stress de desemprego, perda de healthcare nos US, deaths of despair (Case & Deaton); volta corrigida do e_083 removido

**Referências validadas (Etapa 2)**:
- Case & Deaton 2020, Princeton University Press, "Deaths of Despair and the Future of Capitalism"
- Case & Deaton 2021, PNAS 118(11), "Life expectancy in adulthood is falling for those without a BA degree"
- Ruhm 2024, PMC, "Are recessions good or bad for health? A reassessment of the business cycle and mortality literature"

**Confidence**: medium

**Validation note**: Mecanismo deaths of despair forte em US (Case Deaton), quase nulo em economias com welfare states robustos. Scope alterado para within_block dada heterogeneidade radical. Refs: Case Deaton 2020 Princeton; Case Deaton 2021 PNAS; Ruhm 2024 PMC business cycle.

### e_129: financial_markets.global_index → science_rd.publications_index
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 4 turnos | **Scope**: global

**Justificativa Rodada 3**: Rodada 3: mercados em alta → corporate R&D → publicações

**Referências validadas (Etapa 2)**:
- Brown, Fazzari & Petersen 2009, Journal of Finance 64(1):151-185, "Financing Innovation and Growth: Cash Flow, External Equity, and the 1990s R&D Boom"
- National Science Board Indicators (annual), "Science and Engineering Indicators"
- Hall & Lerner 2010, Handbook of the Economics of Innovation, "The Financing of R&D and Innovation"

**Confidence**: medium

**Validation note**: Corporate R&D budgets correlam com market valuations. Magnitude weak honesta — corporate R&D e ~30% do R&D global, balance publico dominante. Refs: Brown Fazzari Petersen 2009 J Finance; National Science Board Indicators (annual); Hall Lerner 2010 Handbook.

### e_104: education.mean_years_schooling → information_ecosystem.media_trust
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 8 turnos | **Scope**: global

**Justificativa Rodada 3**: Rodada 3: educação como capacidade crítica (mais discriminação de fontes confiáveis) vs cinismo (desconfiança de tudo). Direção contestada. Scope global porque target media_trust é global.

**Referências validadas (Etapa 2)**:
- Edelman Trust Barometer 2024, "Annual Global Trust Survey"
- Tsfati & Ariely 2014, Communication Research 41(6):760-782, "Individual and Contextual Correlates of Trust in Media"
- Hopmann, Shehata & Stromback 2015, Journalism Studies 16(5):667-685, "Contagious Media Effects: How Media Use and Exposure to Game-Framed News Influence Media Trust"

**Confidence**: medium

**Validation note**: Direcao genuinamente ambigua: mais educado correlaciona com menos confianca em midia tradicional (cinismo informado) mas mais confianca em midia 'de qualidade' curada. Net global e fraco. Refs: Edelman Trust Barometer 2024; Tsfati Ariely 2014 Communication Research; Hopmann Shehata Stromback 2015 Journalism Studies.

### e_122: inequality.gini_intra_block → health.life_expectancy
- **Direção**: negativa | **Magnitude**: medium | **Lag**: 8 turnos | **Scope**: global

**Justificativa Rodada 3**: Rodada 3: Wilkinson & Pickett 'The Spirit Level' — desigualdade alta encurta vida média mesmo controlando renda absoluta

**Referências validadas (Etapa 2)**:
- Wilkinson & Pickett 2009, Allen Lane, "The Spirit Level: Why More Equal Societies Almost Always Do Better"
- Pickett & Wilkinson 2015, Social Science & Medicine 128:316-326, "Income inequality and health: A causal review"
- Kondo et al 2009, BMJ 339:b4471, "Income inequality, mortality, and self-rated health: meta-analysis of multilevel studies"

**Confidence**: medium

**Validation note**: Wilkinson Pickett 'The Spirit Level' e referencia classica. Criticas metodologicas existem (Saunders 2010, Snowdon 2010) mas direcao robusta em meta-analise. Magnitude debatida. Refs: Wilkinson Pickett 2009 Spirit Level; Pickett Wilkinson 2015 Soc Sci Med; Kondo et al 2009 BMJ meta-analysis.

**Nota Etapa 5 (calibração)**: Usar range conservador para magnitude; criticas metodologicas (Saunders 2010, Snowdon 2010) sugerem uncertainty band larga.

### e_133: inequality.gini_intra_block → health.mental_wellbeing
- **Direção**: negativa | **Magnitude**: medium | **Lag**: 6 turnos | **Scope**: within_block

**Justificativa Rodada 3**: Rodada 3: desigualdade alta correlaciona com pior saúde mental média (Wilkinson)

**Referências validadas (Etapa 2)**:
- Pickett & Wilkinson 2010, Bloomsbury Press, "Equality: A reader" (chapter on inequality and mental illness)
- Ribeiro et al 2017, Lancet Psychiatry 4(7):554-562, "Income inequality and mental illness-related morbidity and resilience: a systematic review and meta-analysis"
- Patel et al 2018, Lancet 392(10157):1553-1598, "The Lancet Commission on global mental health and sustainable development"

**Confidence**: medium

**Validation note**: Pickett Wilkinson 2010 mostra correlacao forte desigualdade-mental illness em paises ricos. Meta-analises confirmam direcao. Magnitude medium defensavel. Refs: Pickett Wilkinson 2010 Equality; Ribeiro et al 2017 Lancet Psychiatry; Patel et al 2018 Lancet.

### e_110: energy_climate.co2_gt_year → health.life_expectancy
- **Direção**: negativa | **Magnitude**: medium | **Lag**: 12 turnos | **Scope**: global

**Justificativa Rodada 3**: Rodada 3: climate change → eventos extremos + poluição → mortalidade (Lancet Countdown); lag longo mas mecanismo robusto

**Referências validadas (Etapa 2)**:
- Romanello et al 2024, The Lancet, "The 2024 report of the Lancet Countdown on health and climate change"
- Burke, Hsiang & Miguel 2015, Nature 527:235-239, "Global non-linear effect of temperature on economic production"
- WHO 2023, World Health Organization, "Climate change and health"

**Confidence**: high

**Validation note**: Lancet Countdown 2024: 489.000 mortes adicionais/ano por heat-related causes em 2022. Magnitude medium e lag 12 (6 anos) honestos dado efeitos cumulativos. Refs: Romanello et al 2024 Lancet Countdown; Burke Hsiang Miguel 2015 Nature; WHO 2023 Climate change and health.

### e_134: information_ecosystem.disinformation_level → health.mental_wellbeing
- **Direção**: negativa | **Magnitude**: weak | **Lag**: 2 turnos | **Scope**: within_block

**Justificativa Rodada 3**: Rodada 3: ecossistema informacional saturado → ansiedade, paranoia, desorientação

**Referências validadas (Etapa 2)**:
- Bago, Rand & Pennycook 2020, Journal of Experimental Psychology: General 149(8):1608-1613, "Fake news, fast and slow: Deliberation reduces belief in false (but not true) news headlines"
- Sharma et al 2024, PLoS One, "Information overload and psychological wellbeing: a systematic review"
- American Psychological Association 2023, "Stress in America Report"

**Confidence**: medium

**Validation note**: Literatura emergente sobre infoxicacao e wellbeing. Magnitude weak honesta — efeito real mas limitado a sub-populacoes altamente expostas. Refs: Bago Rand Pennycook 2020 J Exp Psychol Gen; Sharma et al 2024 PLoS One; APA 2023 Stress in America Report.

### e_128: governance.ai_regulation_maturity → science_rd.breakthroughs_per_year
- **Direção**: negativa | **Magnitude**: weak | **Lag**: 4 turnos | **Scope**: within_block

**Justificativa Rodada 3**: Rodada 3: regulação retarda (gain-of-function) ou acelera (safety standards = trust = funding)? Genuinamente ambígua.

**Referências validadas (Etapa 2)**:
- Korinek & Stiglitz 2021, NBER WP 28453, "Artificial Intelligence, Globalization, and Strategies for Economic Development"
- AI Now Institute 2024, "Annual Report"
- Engler 2023, Brookings, "The EU and U.S. diverge on AI regulation: A transatlantic comparison and steps to alignment"

**Confidence**: medium

**Validation note**: Debate ativo: regulacao acelera adocao via trust (Korinek Stiglitz 2021) vs retarda gain-of-function. Magnitude weak honesta. Refs: Korinek Stiglitz 2021 NBER WP 28453; AI Now Institute 2024 Annual Report; Engler 2023 Brookings AI regulation tradeoffs.

### e_130: geopolitics.active_conflicts → science_rd.breakthroughs_per_year
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 4 turnos | **Scope**: global

**Justificativa Rodada 3**: Rodada 3: wars catalisam invenções (radar, internet, GPS) mas desestabilizam pesquisa civil

**Referências validadas (Etapa 2)**:
- Mowery 2010, Industrial and Corporate Change 19(4):1219-1256, "Military R&D and innovation"
- Ruttan 2006, Oxford University Press, "Is War Necessary for Economic Growth? Military Procurement and Technology Development"
- Gross & Sampat 2023, American Economic Review, "America, Jump-Started: World War II R&D and the Takeoff of the U.S. Innovation System"

**Confidence**: medium

**Validation note**: Wars catalisaram radar/internet/GPS (Mowery 2010) mas correlacao fraca quando se controla por periodos (Ruttan 2006). Net effect ambiguo. Refs: Mowery 2010 Industrial Corporate Change; Ruttan 2006 Is War Necessary?; Gross Sampat 2023 AER WWII innovation.

### e_125: health.diagnostic_accuracy → financial_markets.systemic_risk
- **Direção**: negativa | **Magnitude**: weak | **Lag**: 4 turnos | **Scope**: global

**Justificativa Rodada 3**: Rodada 3: detecção precoce de pandemias reduz risco sistêmico catastrófico (COVID-19 mostrou magnitude potencial)

**Referências validadas (Etapa 2)**:
- McKinsey 2020, "COVID-19: Implications for business and economic impact"
- WHO 2023, "Pandemic Preparedness and Response"
- IMF 2024, "World Economic Outlook: pandemic spillovers and macroeconomic risk"

**Confidence**: medium

**Validation note**: COVID-19 expos custo de deteccao tardia (US$ 16T cumulative GDP loss). Magnitude weak defensavel — prevencao de tail risk raro. Refs: McKinsey 2020 COVID-19 economic impact; WHO 2023 Pandemic Preparedness; IMF 2024 World Economic Outlook pandemic spillovers.

### e_127: science_rd.publications_index → governance.ai_regulation_maturity
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 6 turnos | **Scope**: within_block

**Justificativa Rodada 3**: Rodada 3: mais publicação → mais material pra reguladores entenderem riscos → regulação mais sofisticada (alignment papers viraram base de AI Act)

**Referências validadas (Etapa 2)**:
- Stix 2021, Minds and Machines 31:295-321, "Actionable Principles for Artificial Intelligence Policy: Three Pathways"
- Bareis & Katzenbach 2022, Science, Technology, & Human Values 47(5):855-881, "Talking AI into Being: The Narratives and Imaginaries of National AI Strategies"
- Engler 2023, Brookings, "The EU and U.S. diverge on AI regulation"

**Confidence**: medium

**Validation note**: Alignment papers (Bostrom 2014, Russell 2019, Christiano 2018) viraram base intelectual de AI Act EU. Magnitude weak dado tempo longo entre publicacao e regulacao. Refs: Stix 2021 Minds and Machines; Bareis Katzenbach 2022 Sci Tech Hum Values; Engler 2023 Brookings.

### e_131: science_rd.publications_index → science_rd.publications_index
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 4 turnos | **Scope**: within_block

**Justificativa Rodada 3**: Rodada 3: cumulative knowledge — papers citam papers, snowball; bem documentado em scientometrics

**Referências validadas (Etapa 2)**:
- Price 1965, Science 149(3683):510-515, "Networks of Scientific Papers"
- Bornmann & Mutz 2015, Journal of the Association for Information Science and Technology 66(11):2215-2222, "Growth rates of modern science: A bibliometric analysis based on the number of publications and cited references"
- Frenken et al 2017, Research Policy 46(3):618-632, "The growth of scientific knowledge"

**Confidence**: medium

**Validation note**: Cumulative knowledge bem documentado em scientometrics. Taxa de crescimento ~3-4%/ano sustentada por self-reinforcement. Refs: Price 1965 Science; Bornmann Mutz 2015 JASIST; Frenken et al 2017 Research Policy.

**Nota Etapa 5 (calibração)**: Implementacao SDM precisa incluir saturacao (sigmoid) para evitar explosao exponencial; parametro de saturacao ~5% growth/ano em steady state, mecanismo de attention scarcity (Frenken 2017) limitando crescimento real. NOTA CRITICA — sem isso o motor explode.

### e_135: health.mental_wellbeing → labor_market.employment_rate
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 4 turnos | **Scope**: within_block

**Justificativa Rodada 3**: Rodada 3: bem-estar mental afeta participação no mercado de trabalho

**Referências validadas (Etapa 2)**:
- Bubonya, Cobb-Clark & Wooden 2017, Labour Economics 46:150-165, "Mental health and productivity at work: Does what you do matter?"
- OECD 2021, "Mental Health and Work: Tackling the workplace mental health crisis"
- WHO 2022, "World Mental Health Report: Transforming mental health for all"

**Confidence**: medium

**Validation note**: Depression reduz labor force participation por ~5-10pp (Bubonya 2017). Magnitude weak prudente em escala agregada. Refs: Bubonya Cobb-Clark Wooden 2017 Labour Economics; OECD 2021 Mental Health and Work; WHO 2022 World Mental Health Report (US$ 1T/ano em produtividade global).

### e_136: health.mental_wellbeing → governance.democracy_index
- **Direção**: positiva | **Magnitude**: weak | **Lag**: 8 turnos | **Scope**: within_block

**Justificativa Rodada 3**: Rodada 3: cidadania exige bandwidth psicossocial; depressão/ansiedade massiva debilita instituições

**Referências validadas (Etapa 2)**:
- Foa & Mounk 2016, Journal of Democracy 27(3):5-17, "The Danger of Deconsolidation: The Democratic Disconnect"
- Inglehart & Norris 2017, Perspectives on Politics 15(2):443-454, "Trump and the Populist Authoritarian Parties: The Silent Revolution in Reverse"
- Steffens et al 2021, Political Psychology 42(2):185-204, "Identity leadership and democratic functioning"

**Confidence**: low

**Validation note**: Mecanismo teoricamente defensavel mas literatura empirica direta e fina. Nao ha paper canonico ligando mental health populacional a democratic functioning diretamente. Refs: Foa Mounk 2016 J Democracy; Inglehart Norris 2017 populist authoritarian; Steffens et al 2021 Political Psychology.

**Nota Etapa 5 (calibração)**: Confidence baixa; usar range muito conservador, possivelmente magnitude negligible se evidencia nao aparecer durante calibracao. Ligacao mental_wellbeing -> democracy_index e teorica, sem paper canonico.
