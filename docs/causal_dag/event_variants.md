# Variantes de eventos âncora

Cada um dos 16 eventos históricos âncora de `data/historical_events.json` é representado em `spec/event_variants.json` como uma distribuição de 3-4 variantes. Em vez de "ocorre / não ocorre" binário, o sampler decide qual variante se manifesta em cada run, com probabilidades base moduladas pelo estado do mundo naquele momento.

**Todas as variantes e probabilidades são DRAFT**. Validação histórica + literatura acadêmica é trabalho da Etapa 2.

---

## 1998-S2 · Crise financeira russa

**Variantes**:
- `real` (P=0.6): default russo + contágio LTCM como histórico.
- `mitigado` (P=0.3): default ocorre mas alertas preditivos via IA reduzem contágio em ~50%.
- `evitado` (P=0.1): FMI age preventivamente, default contornado via negociação.

**Modulator principal**: `ai_intelligence_composite_US` — capacidade de IA aplicada à inteligência financeira. Quanto maior, mais probabilidade das variantes mitigadas.

**A validar**: a literatura sugere que default russo era estruturalmente provável dado a crise asiática de 97; a margem de manobra de IA pode ser menor que 0.3+0.1=40%.

---

## 1999-S2 · Y2K

**Variantes**:
- `real` (P=0.5): passa sem grandes incidentes (linha real).
- `neutralizado_ia` (P=0.4): IA audita sistemas globais; transição é triunfo público.
- `incidente_localizado` (P=0.1): falha em sistema mal-auditado, contida pela IA.

**Modulator**: `ai_intelligence_composite_US`.

**Cascata**: `neutralizado_ia` impulsiona adoção de IA em órgãos governamentais nos turnos seguintes (delta_package incluí +2pp em `ai_capability.population_penetration`).

---

## 2000-S1 · Pico Nasdaq

**Variantes**:
- `real` (P=0.5): Nasdaq atinge ~5000 e começa correção.
- `pico_amplificado` (P=0.3): IA-hype leva acima de 7000.
- `pico_atenuado` (P=0.2): modelos de risco com IA já indicam sobrevalorização; pico mais baixo (~3500).

**Modulators**: `ai_economic_dependency` (positivo, infla bolha), `ai_intelligence_composite_US` (positivo, atenua).

**A validar**: assunção que IA-hype amplifica bolha vs IA-risk-models a contém depende de qual ator (mainstream investors vs quants/hedge funds) tem mais peso na época.

---

## 2001-S1 · Estouro da bolha .com

**Variantes**:
- `real` (P=0.5): crash similar ao histórico, perda ~70% no Nasdaq em 2 anos.
- `amplificado` (P=0.25): se a bolha foi amplificada antes, crash mais profundo (-85%).
- `atenuado` (P=0.25): IA-driven hedging reduz queda; correção em -40%.

**Modulators**: `financial_fragility` (positivo, amplifica), `ai_intelligence_composite_US` (positivo, atenua).

**Cross-event modulator a considerar (Etapa 2)**: o outcome de `pico_nasdaq` deve modular as probabilidades aqui (se foi `pico_amplificado`, `amplificado` aqui deveria ter prob > 0.25).

---

## 2001-S2 · 11 de Setembro

**Variantes**:
- `real` (P=0.55): Torres + Pentágono + Pensilvânia.
- `frustrado` (P=0.30): inteligência preditiva detecta a célula horas antes.
- `alvo_alterado` (P=0.10): apenas Pentágono atingido.
- `anulado` (P=0.05): rede da Al-Qaeda desmantelada antes da execução.

**Modulator principal**: `ai_intelligence_composite_US` (negativo, reduz P_real; positivo, amplifica `frustrado` e `anulado`).

**Cascatas a considerar**:
- Se `frustrado` ou `anulado`, probabilidade da invasão do Iraque (2003) cai significativamente — capturar via cross-event modulator.
- `frustrado` legitima vigilância maciça via IA, acelerando regulation_maturity_US e disinformation_level (deltas no package).

---

## 2003-S1 · Invasão do Iraque

**Variantes**:
- `real` (P=0.5): invasão como histórica, baseada em alegações WMD.
- `evitado` (P=0.3): análise contrafactual via IA expõe fragilidade das alegações.
- `limitado` (P=0.15): operação cirúrgica com targets selecionados por IA.
- `expandido` (P=0.05): conflito se alastra para Síria/Irã ainda em 2003.

**Modulator**: `ai_intelligence_composite_US`.

**Cascata**: outcome aqui afeta `geopolitics.bilateral_tensions.US_RoW` por décadas. Se `evitado`, dinâmica do Oriente Médio diverge significativamente da linha real.

---

## 2007-S2 · Início da crise subprime

**Variantes**:
- `real` (P=0.5): crise se desenvolve historicamente.
- `antecipado` (P=0.3): modelos de IA detectam sobreexposição em 2006; ajustes regulatórios suavizam.
- `amplificado` (P=0.2): modelos preditivos via IA aceleram pânico; flash crash mais profundo.

**A validar**: a aplicação de IA a modelos de risco em 2006-2007 era plausível dado capacidade `frontier=92` desde 1998? Ou a capacidade institucional de incorporar não acompanhava a capacidade da IA?

---

## 2008-S2 · Lehman Brothers

**Variantes**:
- `real` (P=0.5): Lehman colapsa, contágio massivo.
- `salvo` (P=0.3): Lehman é resgatado por consórcio orquestrado por modelos de IA do Treasury.
- `amplificado` (P=0.2): múltiplos bancos colapsam simultaneamente.

**Modulators**: `ai_intelligence_composite_US`, `financial_fragility`.

**Cross-event**: outcome do subprime modula este — se `antecipado`, P_salvo aumenta.

---

## 2010-S2 · Início da Primavera Árabe

**Variantes**:
- `real` (P=0.5): movimentos populares derrubam regimes em Tunísia/Egito/Líbia.
- `intensificada` (P=0.25): mobilização viral por IA acelera revoluções, mais regimes caem.
- `contida` (P=0.25): vigilância e contra-mobilização por IA dos regimes contém os movimentos.

**Modulators**: `ai_disinfo_capacity` (positivo amplifica `intensificada`), `ai_intelligence_composite_global` (negativo amplifica `contida`).

**A validar**: tensão entre IA mobilizadora vs IA repressora — em 2010 ambas existiam? capacidade de Estados autoritários de aplicar IA repressivamente era nascente.

---

## 2011-S1 · Fukushima

**Variantes**:
- `real` (P=0.65): tsunami atinge Fukushima Daiichi; fusão parcial.
- `atenuado` (P=0.25): sistema preditivo via IA dá margem extra; danos reduzidos.
- `amplificado` (P=0.10): falha em cascata em vários reatores japoneses.

**Modulator**: `ai_intelligence_composite_global`.

**A validar**: o tsunami é evento natural. Mitigação via IA assume que sistema antecipou em horas/dias (factível) e que evacuação foi executada melhor (questionável dado a magnitude do desastre).

---

## 2014-S1 · Anexação da Crimeia

**Variantes**:
- `real` (P=0.5): anexação ocorre, sanções ocidentais leves.
- `deterrência` (P=0.25): inteligência via IA dá tempo a OTAN; Rússia recua na fase pré-anexação.
- `escalada` (P=0.15): operação russa se expande para Donbas em 2014.
- `ciber_apenas` (P=0.10): Rússia opta por intervenção ciber massiva sem invasão física.

**Modulators**: `ai_intelligence_composite_global` (positivo amplifica `deterrência`), `ai_disinfo_capacity` (positivo amplifica `ciber_apenas`).

---

## 2016-S1 · Brexit

**Variantes**:
- `real` (P=0.5): Leave vence por margem estreita.
- `remain_apertado` (P=0.3): Remain vence 51-49.
- `leave_amplificado` (P=0.2): disinfo coordenada via IA leva Leave a vencer por margem maior.

**Modulator principal**: `ai_disinfo_capacity` em UK (parte do bloco EU).

---

## 2016-S2 · Eleição Trump

**Variantes**:
- `real` (P=0.45): Trump vence Hillary no Colégio Eleitoral.
- `clinton_vence` (P=0.30): Hillary vence apertado; deepfakes detectados a tempo.
- `trump_amplificado` (P=0.15): vitória maior por desinfo industrial.
- `outro_candidato` (P=0.10): crise interna do Republicano leva a candidato alternativo.

**Modulators**: `ai_disinfo_capacity`, `governance.ai_regulation_maturity.US` (positivo, amplifica `clinton_vence` por deteção).

---

## 2020-S1 · COVID-19

**Variantes**:
- `real` (P=0.45): pandemia se espalha como historicamente.
- `controlado_cedo` (P=0.20): vigilância epidemiológica via IA detecta surto antes de espalhar.
- `vacinas_express` (P=0.25): pandemia ocorre mas IA acelera vacinas em 4 meses (não 11).
- `amplificado` (P=0.10): pandemia mais letal por mutações cedo + falha de coordenação.

**Modulators**: `ai_intelligence_composite_global`, `science_rd.breakthroughs_per_year.US`.

**Cascata**: outcome aqui muda dramaticamente o ritmo de adoção de IA pós-pandemia (delta_package de `controlado_cedo` injeta +3pp em `population_penetration` em US/EU/CN).

---

## 2022-S1 · Invasão russa da Ucrânia

**Variantes**:
- `real` (P=0.4): Rússia invade em fevereiro/22.
- `deterrência` (P=0.25): inteligência precisa via IA + contramobilização pré-emptiva da OTAN dissuade.
- `limitada` (P=0.20): operação russa fica restrita a Donbas/Kherson.
- `escalada_nuclear` (P=0.15): conflito escala para uso de armamento tático.

**Modulator**: `ai_intelligence_composite_global`.

**Cross-event**: outcome da Crimeia (2014) modula este — `deterrência` em 2014 reduz P_real aqui.

---

## 2022-S2 · ChatGPT (linha real)

**Variantes**:
- `irrelevante` (P=0.5): como Athena já existe desde 1998, lançamento similar é incremental.
- `concorrente_open` (P=0.3): concorrente open-source emerge nesse trimestre.
- `agi_announce` (P=0.2): anúncio de AGI por um dos labs.

**Modulator**: `ai_capability.population_penetration.US`, `ai_intelligence_composite_global`.

---

## Pontos transversais a validar

1. **Probabilidades base**: todos somam 1.0 (validação automática), mas valores específicos são chutes informados. Literatura sobre cada evento pode ajustar.
2. **Magnitude dos modulators**: assumi coeficientes na faixa 0.3-0.7. Etapa 2/5 calibra contra dados históricos.
3. **Cross-event modulators**: implementação atual considera apenas o estado quantitativo. Cross-event (outcome do evento X afeta probabilidade do evento Y) é estrutural — fica para Etapa 4 implementar como tabela `event_event_modulators` adicional.
4. **Composite factors**: 5 propostos (`ai_intelligence_composite_US`, `_global`, `financial_fragility`, `ai_economic_dependency`, `ai_disinfo_capacity`). Coeficientes da fórmula são DRAFT — derivar de PCA empírico nos dados históricos.
