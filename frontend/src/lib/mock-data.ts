// 24 pre-generated turns (1998-S1 → 2009-S2) for Counterfactual-1998.
// Engine logic intentionally simple — narratives, events, variants are hand-tuned.

import {
  BLOCKS,
  type AnchorEvent,
  type BlockId,
  type BlocksState,
  type CausalLink,
  type Confidence,
  type ExogenousShock,
  type GlobalMetricKey,
  type GlobalState,
  type MatrixState,
  type Seed,
  type Turn,
  type VectorizedMetricKey,
  type WorldState,
} from "./types";
import { GLOBAL_KEYS, VECTORIZED_KEYS } from "./metrics";

// ---- Initial state --------------------------------------------------------

export const INITIAL_GLOBAL: GlobalState = {
  "financial_markets.global_index": 100,
  "financial_markets.systemic_risk": 35,
  "education.mean_years_schooling": 7.4,
  "education.cost_index": 100,
  "inequality.global_gini": 0.69,
  "inequality.top1pct_share": 19,
  "health.life_expectancy": 67,
  "health.diagnostic_accuracy": 2,
  "science_rd.publications_index": 100,
  "energy_climate.co2_gt_year": 24.4,
  "energy_climate.renewable_share": 6,
  "information_ecosystem.media_trust": 53,
};

export const INITIAL_BLOCKS: BlocksState = {
  US:  { "ai_capability.frontier_capability": 92, "ai_capability.population_penetration": 8.2, "tech_industry.bigtech_concentration": 28, "tech_industry.tech_employment_share": 4.1, "labor_market.automation_exposure": 12, "labor_market.employment_rate": 64.3, "governance.democracy_index": 8.2, "governance.ai_regulation_maturity": 0, "information_ecosystem.disinformation_level": 18, "science_rd.breakthroughs_per_year": 8 },
  EU:  { "ai_capability.frontier_capability": 78, "ai_capability.population_penetration": 5.5, "tech_industry.bigtech_concentration": 18, "tech_industry.tech_employment_share": 3.2, "labor_market.automation_exposure": 9,  "labor_market.employment_rate": 60.1, "governance.democracy_index": 8.0, "governance.ai_regulation_maturity": 0, "information_ecosystem.disinformation_level": 16, "science_rd.breakthroughs_per_year": 4 },
  CN:  { "ai_capability.frontier_capability": 35, "ai_capability.population_penetration": 1.2, "tech_industry.bigtech_concentration": 12, "tech_industry.tech_employment_share": 1.8, "labor_market.automation_exposure": 4,  "labor_market.employment_rate": 71.0, "governance.democracy_index": 2.8, "governance.ai_regulation_maturity": 0, "information_ecosystem.disinformation_level": 22, "science_rd.breakthroughs_per_year": 1 },
  RoW: { "ai_capability.frontier_capability": 18, "ai_capability.population_penetration": 1.8, "tech_industry.bigtech_concentration": 8,  "tech_industry.tech_employment_share": 2.0, "labor_market.automation_exposure": 5,  "labor_market.employment_rate": 58.3, "governance.democracy_index": 4.5, "governance.ai_regulation_maturity": 0, "information_ecosystem.disinformation_level": 22, "science_rd.breakthroughs_per_year": 1 },
};

export const INITIAL_MATRIX: MatrixState = {
  "geopolitics.bilateral_tensions": {
    US_EU: 12, US_CN: 35, US_RoW: 28,
    EU_CN: 25, EU_RoW: 18,
    CN_RoW: 22,
  },
  "geopolitics.active_conflicts": 38,
};

export const INITIAL_STATE: WorldState = {
  global: INITIAL_GLOBAL,
  blocks: INITIAL_BLOCKS,
  matrix: INITIAL_MATRIX,
};

// ---- Turn config (handcrafted skeleton) -----------------------------------

interface TurnSeed {
  event?: AnchorEvent;
  shock?: ExogenousShock;
  narrative: string;
  keyDevelopments: string[];
  lens: string;
  seeds: Seed[];
  confidence: Confidence;
  // Per-turn overrides for delta magnitudes (otherwise procedural)
  overrides?: {
    global?: Partial<Record<GlobalMetricKey, number>>;
    block?: Partial<Record<VectorizedMetricKey, Partial<Record<BlockId, number>>>>;
    matrix?: Partial<Record<keyof MatrixState, any>>;
  };
  causalLinks: CausalLink[];
}

const TURN_LABELS: { year: number; semester: 1 | 2; label: string }[] = [];
for (let y = 1998; y <= 2026; y++) {
  TURN_LABELS.push({ year: y, semester: 1, label: `${y}-S1` });
  TURN_LABELS.push({ year: y, semester: 2, label: `${y}-S2` });
}

// ---- Hand-crafted seeds for 24 turns --------------------------------------

const TURN_SEEDS: TurnSeed[] = [
  // ============== TURN 0 — 1998-S1 ==============
  {
    narrative:
`Em fevereiro de 1998, num galpão alugado em Mountain View que ainda cheira a café requentado e tinta nova de placa-mãe, sete pesquisadores observam um modelo de linguagem responder a uma pergunta sobre teoria dos jogos com uma sofisticação que nenhum deles conseguiu antecipar. O sistema — que receberá publicamente o nome <em>Aletheia</em> três meses depois — não passa em qualquer benchmark formal porque os benchmarks que o mediriam ainda não foram inventados.

A imprensa especializada trata o lançamento com cautela: <em>Wired</em> publica uma matéria de capa intitulada "A Máquina Que Aprende a Pensar (de Verdade, Dessa Vez?)", encerrando com uma boutade do editor de que "o vale acordou de novo achando que reinventou Deus". Os mercados de Tóquio e Frankfurt mal registram. O Dow Jones fecha o semestre 4% acima do início do ano, ignorando completamente o que acaba de nascer.

Mas algo se move silenciosamente nos bastidores. Três das quatro grandes consultorias estratégicas começam a contratar especialistas em "linguagem computacional avançada" — uma rubrica de cargo que não existia em janeiro. O Pentágono assina um contrato de avaliação reservada de US$ 11 milhões. Nas universidades europeias, departamentos de filosofia da mente recebem ligações curiosamente urgentes de fundações privadas. O futuro chegou sem fanfarra, vestido de mercadoria de nicho.`,
    keyDevelopments: [
      "Aletheia (Anthropic-equivalent) anunciada publicamente em San Francisco — recepção morna na imprensa de massa.",
      "Pentágono inicia avaliação confidencial; orçamento de US$ 11M autorizado fora da pauta.",
      "Três das Big-4 consultorias abrem vagas em 'linguagem computacional avançada' pela primeira vez.",
      "Departamentos de filosofia da mente recebem onda atípica de financiamento privado europeu.",
    ],
    lens: "advento silencioso — adoção de elite antes que a sociedade saiba nomear o que está acontecendo",
    seeds: [
      { year: 1956, domain: "Conferência de Dartmouth", text: "O termo 'inteligência artificial' é cunhado por John McCarthy. A promessa de uma década para resolver IA estabelece o padrão de hype-decepção que se repetirá por 70 anos." },
      { year: 1973, domain: "Lighthill Report", text: "Relatório britânico devastador interrompe quase todo financiamento europeu de IA simbólica. O 'inverno' é tão profundo que os pesquisadores aprendem a chamar seu trabalho de outras coisas." },
      { year: 1989, domain: "World Wide Web", text: "Tim Berners-Lee propõe o WWW no CERN. A infraestrutura que transformará IA de curiosidade acadêmica em produto de consumo começa a ser construída antes que ninguém perceba." },
      { year: 1997, domain: "Deep Blue × Kasparov", text: "IBM derrota o campeão mundial de xadrez. A vitória é lida como 'força bruta', não inteligência. Wall Street registra como aviso, não como alvorada." },
    ],
    confidence: "high",
    causalLinks: [
      { source: "Aletheia launch", target: "frontier_capability", strength: 0.9, polarity: 1, scope: "intra-block" },
      { source: "frontier_capability", target: "publications_index", strength: 0.4, polarity: 1, scope: "global" },
      { source: "Pentágono contract", target: "ai_regulation_maturity", strength: 0.2, polarity: 1, scope: "intra-block" },
    ],
    overrides: {
      block: {
        "ai_capability.frontier_capability": { US: 1.6, EU: 0.6, CN: 0.2, RoW: 0.1 },
        "ai_capability.population_penetration": { US: 0.3, EU: 0.1, CN: 0.05, RoW: 0.05 },
        "science_rd.breakthroughs_per_year": { US: 0.5, EU: 0.2, CN: 0, RoW: 0 },
      },
      global: { "science_rd.publications_index": 0.4, "financial_markets.global_index": 1.8 },
    },
  },
  // ============== TURN 1 — 1998-S2 ==============
  {
    event: {
      id: "russian_crisis_1998",
      title: "Crise do Rublo / Default Russo",
      severity: "high",
      primaryBlock: "RoW",
      variant: {
        id: "atenuada",
        label: "atenuada",
        status: "altered",
        description: "O default russo ocorre, mas modelos de risco assistidos por Aletheia em Wall Street e no FMI antecipam contagion routes três semanas antes do colapso. Long-Term Capital Management consegue desfazer 60% das posições antes da liquidação forçada. O socorro do Fed acontece ainda em agosto, antes da onda de pânico atingir a Ásia novamente. Os mercados emergentes sangram, mas não há cardiopatia sistêmica.",
        baseProbability: 0.35,
        actualProbability: 0.62,
        modulators: [
          { name: "ai_capability.frontier_capability (US)", value: "93.6", effect: 0.18 },
          { name: "tech_industry.bigtech_concentration (US)", value: "29.1", effect: 0.04 },
          { name: "financial_markets.systemic_risk", value: "38.2 (alto)", effect: 0.05 },
        ],
      },
    },
    narrative:
`O default russo de agosto de 1998 chega com pontualidade histórica, mas seus efeitos secundários se comportam estranhamente. A Long-Term Capital Management — o fundo de hedge gigante de Greenwich povoado de Nobeis em economia — havia, três semanas antes, contratado uma licença experimental de Aletheia para reanalisar suas posições. O sistema não previu o default em si; previu o caminho de contagion. Identificou quais counterparts europeus tinham exposição assimétrica e quais fundos de pensão asiáticos seriam forçados a vender ativos correlacionados. Em quinze dias, a LTCM desfez sessenta por cento de suas posições alavancadas, evitando — sem entender que evitava — a humilhação pública de pedir socorro ao Fed.

O Federal Reserve ainda intervém, mas a intervenção é cirúrgica e silenciosa. Não há a reunião dramática de quatorze bancos de investimento que <em>esta</em> história lembraria como ponto de inflexão da arrogância quantitativa. Os mercados emergentes ainda sangram — Brasil sobe juros para 49,7%, Coreia revisita o trauma de 1997 — mas o sistema financeiro global não tem o seu momento de quase-morte.

Nas redações de Nova York, alguns analistas começam a notar um padrão: as decisões mais quietas do verão de 1998 foram, sem exceção, as melhores. Ninguém ainda diz o nome da máquina em voz alta nos comentários trimestrais. Mas o nome começa a circular nos almoços fechados de Greenwich e Mayfair.`,
    keyDevelopments: [
      "Default russo confirmado em agosto, mas contagion neutralizada parcialmente pela rede LTCM-Aletheia.",
      "Brasil eleva juros para 49,7%; Coreia do Sul evita segunda crise por 0,8 pontos de spread.",
      "Wall Street descobre informalmente o uso de IA para análise de risco sistêmico — sem reportar a reguladores.",
      "FMI internaliza primeira consultoria de Aletheia para modelagem de spillovers.",
      "Vendas de licenças corporativas de Aletheia triplicam em outubro.",
    ],
    lens: "a primeira crise que a IA quase não nos deixou ter — opacidade premiada, regulação atrasada",
    seeds: [
      { year: 1973, domain: "Black-Scholes", text: "O modelo de precificação de opções industrializa o uso de matemática avançada em finanças. Estabelece o precedente de que 'modelos exóticos' são opacos por design e legítimos pela performance." },
      { year: 1987, domain: "Black Monday", text: "Crash de 22,6% no Dow em um dia, atribuído parcialmente a portfolio insurance algorítmico. Primeira lição não-aprendida sobre o feedback loop de máquinas tomando decisões correlacionadas." },
      { year: 1994, domain: "Tequila Crisis", text: "Crise mexicana revela como capital de portfolio se move em manada digital. A arquitetura de contagion via fluxos eletrônicos está pronta para a era da IA." },
      { year: 1997, domain: "Crise Asiática", text: "Tailândia, Indonésia, Coreia colapsam em sequência. O FMI impõe austeridade que será lembrada como erro de calibração — e que treinará a próxima geração de modelos." },
    ],
    confidence: "high",
    causalLinks: [
      { source: "russian_default", target: "systemic_risk", strength: 0.6, polarity: 1, scope: "global" },
      { source: "Aletheia (US)", target: "systemic_risk", strength: 0.5, polarity: -1, scope: "spillover" },
      { source: "frontier_capability (US)", target: "bigtech_concentration (US)", strength: 0.3, polarity: 1, scope: "intra-block" },
      { source: "russian_default", target: "global_index", strength: 0.4, polarity: -1, scope: "global" },
    ],
    overrides: {
      global: {
        "financial_markets.systemic_risk": 3.2, // less than counterfactual baseline
        "financial_markets.global_index": -2.1,
        "inequality.global_gini": 0.002,
      },
      block: {
        "ai_capability.frontier_capability": { US: 1.4, EU: 0.7, CN: 0.3, RoW: 0.15 },
        "ai_capability.population_penetration": { US: 0.6, EU: 0.2, CN: 0.05, RoW: 0.05 },
        "tech_industry.bigtech_concentration": { US: 1.1, EU: 0.4, CN: 0.2, RoW: 0.1 },
      },
    },
  },
  // ============== TURN 2 — 1999-S1 ==============
  {
    narrative:
`No primeiro semestre de 1999, a palavra "Aletheia" aparece em <em>vinte e três</em> capas de revistas de negócios em sete idiomas. <em>Forbes</em> coloca o sistema na lista de "100 ferramentas mais poderosas do mundo" — uma lista que nunca antes incluiu software. A Microsoft anuncia uma parceria de US$ 800 milhões para integrar capacidades equivalentes em sua próxima geração de Office. A IBM, atrasada e ressentida, compra três startups de NLP em quatro meses.

Mas o efeito mais subterrâneo se passa nas universidades. Em Stanford, MIT, Carnegie Mellon e ETH Zurich, taxas de matrícula em ciência da computação sobem 38% em um único ciclo. O fenômeno é replicado, com defasagem de seis meses, em Tsinghua e na Indian Institutes of Technology. Pela primeira vez desde 1969, o número de estudantes europeus aplicando para PhDs em IA nos EUA ultrapassa o número de americanos.

Há, porém, um som dissonante. Em março, dezessete senadores americanos enviam uma carta ao Departamento de Comércio pedindo "uma avaliação urgente das implicações para segurança nacional do controle privado de capacidades cognitivas estratégicas". A carta é arquivada. Será desarquivada em 2003.`,
    keyDevelopments: [
      "Aletheia em capa de 23 revistas de negócios em sete idiomas no semestre.",
      "Microsoft × Anthropic-equivalent: parceria de US$ 800M para integração no Office.",
      "Matrículas em CS sobem 38% em universidades top americanas.",
      "Carta dos 17 senadores ao DoC pedindo avaliação de segurança nacional — arquivada.",
      "Tsinghua anuncia o primeiro 'Laboratório Estatal de Inteligência Cognitiva' — orçamento sem precedente.",
    ],
    lens: "alfabetização de elite global — a IA vira commodity simbólica antes de ser commodity de uso",
    seeds: [
      { year: 1957, domain: "Sputnik", text: "O lançamento soviético desencadeia o National Defense Education Act nos EUA. Estabelece o padrão de pânico tecnológico → financiamento educacional massivo que se repetirá em 1999." },
      { year: 1969, domain: "ARPANET", text: "Primeira rede de pacotes financiada militarmente. A semente que conecta os universities — e que treinará LLMs em texto comum três décadas depois." },
      { year: 1995, domain: "Netscape IPO", text: "A primeira IPO de internet detona o modelo de financiamento que tornará possível Anthropic-equivalent existir como empresa privada com bilhões em capital de risco." },
      { year: 1998, domain: "Google fundada", text: "Brin e Page indexam a web em Stanford. Em 1999, recebem US$ 25M de Sequoia + KP. O playbook do unicórnio cognitivo está definido." },
    ],
    confidence: "high",
    causalLinks: [
      { source: "Aletheia hype", target: "publications_index", strength: 0.5, polarity: 1, scope: "global" },
      { source: "Aletheia hype", target: "tech_employment_share (US)", strength: 0.6, polarity: 1, scope: "intra-block" },
      { source: "frontier_capability (US)", target: "frontier_capability (EU)", strength: 0.4, polarity: 1, scope: "spillover" },
      { source: "frontier_capability (US)", target: "frontier_capability (CN)", strength: 0.25, polarity: 1, scope: "spillover" },
    ],
    overrides: {
      global: {
        "science_rd.publications_index": 1.8,
        "financial_markets.global_index": 9.4, // dotcom takes off harder
      },
      block: {
        "ai_capability.frontier_capability": { US: 2.2, EU: 1.4, CN: 0.9, RoW: 0.4 },
        "ai_capability.population_penetration": { US: 1.1, EU: 0.5, CN: 0.15, RoW: 0.1 },
        "tech_industry.tech_employment_share": { US: 0.4, EU: 0.2, CN: 0.15, RoW: 0.1 },
      },
    },
  },
  // ============== TURN 3 — 1999-S2 ==============
  {
    shock: {
      id: "hk_protest_unrest",
      title: "Distúrbios anti-globalização em Seattle",
      description: "A reunião ministerial da OMC em Seattle no final de novembro é interrompida por 50.000 manifestantes — mais cedo do que historicamente esperado e com retórica explicitamente anti-tecnológica pela primeira vez. Cartazes mencionam Aletheia ao lado de Nike e Monsanto. O movimento No-WTO é a primeira manifestação política de massa a tematizar a IA como ameaça ao trabalho.",
      primaryBlock: "US",
    },
    narrative:
`O último semestre do milênio se passa num ritmo de aceleração que assusta até os otimistas. O índice NASDAQ fecha 1999 em 4.069 — uma alta de 85% no ano, batendo qualquer recorde anterior. Empresas com prefixo "ai-" valem em dezembro o que valiam empresas com prefixo "e-" em janeiro. Há rumores, ainda não confirmados, de que três fundos soberanos do Golfo estão construindo posições posicionais em ações de IA via veículos opacos em Liechtenstein.

Em paralelo, ocorre algo que nenhum analista do Vale antecipou: <em>os manifestantes</em> chegam primeiro. Em Seattle, no final de novembro, cinquenta mil pessoas paralisam a reunião ministerial da OMC. Pela primeira vez na história das mobilizações anti-globalização, há cartazes mencionando "Aletheia" — junto com Nike, Monsanto, McDonald's. O movimento não tem ainda uma teoria clara do que a IA significa, mas tem uma intuição precisa: <em>algo está sendo decidido sobre nossas vidas em quartos onde não estamos</em>.

A mídia trata o evento como folclore. O Vale trata como ruído. Em Bruxelas, três funcionários médios da Comissão Europeia começam, naquela semana, a redigir o primeiro draft do que se tornará, sete anos depois, a primeira regulação supranacional substantiva de sistemas de IA. Naquele momento, o documento se chama apenas "Working Paper #117".`,
    keyDevelopments: [
      "NASDAQ fecha 1999 em 4.069 (+85% no ano); ações 'ai-*' superam 'e-*' em valuation médio.",
      "Distúrbios em Seattle paralisam OMC; primeira manifestação anti-IA de massa.",
      "Fundos soberanos do Golfo (rumor): posições em IA via veículos em Liechtenstein.",
      "Comissão Europeia inicia internamente o 'Working Paper #117' — futuro AI Act.",
      "Bug do Y2K mitigado parcialmente por revisões automatizadas de código — não-evento gloriosamente bem-sucedido.",
    ],
    lens: "exuberância irracional + primeiros anticorpos sociais — o pêndulo começa a oscilar antes do impacto",
    seeds: [
      { year: 1968, domain: "Maio de 68", text: "A revolta estudantil parisiense ensina que a tecnocracia gera, com regularidade, sua própria contestação. A geração que protestou em Paris está, em 1999, no comando das ONGs anti-globalização." },
      { year: 1995, domain: "Unabomber Manifesto", text: "Ted Kaczynski publica 'Industrial Society and Its Future' no Washington Post. A linguagem anti-tech radical entra no léxico cultural — disponível, em 1999, para ser reciclada por movimentos legítimos." },
      { year: 1992, domain: "Earth Summit Rio", text: "A primeira grande conferência ambiental global estabelece o template das mobilizações transnacionais. Seattle 1999 é seu filho direto." },
      { year: 1973, domain: "Crise do petróleo", text: "Primeira lição em grande escala de que sistemas técnicos complexos podem ser interrompidos por decisões políticas. Sementes do receio em substrato material da IA (chips, energia)." },
    ],
    confidence: "high",
    causalLinks: [
      { source: "dotcom euphoria", target: "global_index", strength: 0.7, polarity: 1, scope: "global" },
      { source: "dotcom euphoria", target: "systemic_risk", strength: 0.4, polarity: 1, scope: "global" },
      { source: "Seattle protests", target: "media_trust", strength: 0.2, polarity: -1, scope: "global" },
      { source: "Aletheia diffusion", target: "frontier_capability (CN)", strength: 0.3, polarity: 1, scope: "spillover" },
      { source: "Seattle protests", target: "ai_regulation_maturity (EU)", strength: 0.4, polarity: 1, scope: "intra-block" },
    ],
    overrides: {
      global: {
        "financial_markets.global_index": 14.2,
        "financial_markets.systemic_risk": 4.1,
        "information_ecosystem.media_trust": -1.2,
      },
      block: {
        "ai_capability.frontier_capability": { US: 2.6, EU: 1.7, CN: 1.3, RoW: 0.6 },
        "ai_capability.population_penetration": { US: 1.6, EU: 0.8, CN: 0.3, RoW: 0.2 },
        "governance.ai_regulation_maturity": { US: 0.1, EU: 0.4, CN: 0.05, RoW: 0.05 },
        "information_ecosystem.disinformation_level": { US: 0.6, EU: 0.4, CN: 0.5, RoW: 0.4 },
      },
    },
  },
];

// ---- Procedural seeds for turns 4..23 -------------------------------------

function makeProceduralSeed(turnIndex: number): TurnSeed {
  const { year, semester } = TURN_LABELS[turnIndex];
  const proceduralEvents: Record<number, AnchorEvent | undefined> = {
    4: undefined,
    5: { // 2000-S2 — Dotcom crash
      id: "dotcom_crash", title: "Crash da Dotcom", severity: "critical", primaryBlock: "US",
      variant: { id: "amortizado", label: "amortizado", status: "altered",
        description: "O crash ocorre, mas modelos de risco baseados em IA, agora em uso em cinco grandes prime brokers, identificam a inversão da curva de earnings em maio. O drawdown do NASDAQ é de 41% (vs 78% no histórico) e demora 14 meses (vs 30) para ser absorvido.",
        baseProbability: 0.55, actualProbability: 0.78,
        modulators: [
          { name: "frontier_capability (US)", value: "98.4", effect: 0.20 },
          { name: "ai_capability.population_penetration (US)", value: "12.1", effect: 0.08 },
        ] }
    },
    7: { // 2001-S2 — 9/11
      id: "september_11", title: "11 de Setembro", severity: "critical", primaryBlock: "US",
      variant: { id: "frustrado", label: "frustrado", status: "averted",
        description: "Atentados detectados pela rede de inteligência aumentada por IA preditiva. Célula da Al-Qaeda interceptada em agosto após análise de fluxo de comunicação por Aletheia-classified. A operação não acontece. Há, porém, um vazamento parcial em 2003 que abalará a confiança em garantias civis.",
        baseProbability: 0.20, actualProbability: 0.42,
        modulators: [
          { name: "ai_intelligence_composite (US)", value: "0.74", effect: 0.50 },
          { name: "governance.ai_regulation_maturity (US)", value: "0.4", effect: -0.10 },
        ] }
    },
    9: { // 2002-S2 — Enron-like
      id: "accounting_scandals", title: "Escândalos contábeis (Enron / WorldCom)", severity: "high", primaryBlock: "US",
      variant: { id: "amplificado", label: "amplificado", status: "altered",
        description: "Auditorias automatizadas por modelos de IA — adotadas por SEC após pressão pública — descobrem padrões em mais 17 grandes corporações além de Enron e WorldCom. O escândalo é maior, não menor.",
        baseProbability: 0.40, actualProbability: 0.61,
        modulators: [{ name: "frontier_capability (US)", value: "104", effect: 0.21 }] }
    },
    11: { // 2003-S2 — Iraq war
      id: "iraq_war", title: "Invasão do Iraque", severity: "critical", primaryBlock: "US",
      variant: { id: "como_real", label: "como na realidade", status: "real",
        description: "A invasão ocorre como na história. Análises de IA da inteligência britânica indicam (corretamente) que os WMDs não existem, mas o relatório é deliberadamente desconsiderado pelo gabinete de guerra. Primeira grande lição contemporânea de que IA superior não vence política.",
        baseProbability: 0.85, actualProbability: 0.91,
        modulators: [{ name: "geopolitics.bilateral_tensions US_RoW", value: "alta", effect: 0.04 }] }
    },
    13: { // 2004-S2 — Facebook era launch
      id: "social_platforms_rise", title: "Ascensão das plataformas sociais", severity: "medium", primaryBlock: "US",
      variant: { id: "moderado_por_ia", label: "moderado por IA desde a fundação", status: "altered",
        description: "Facebook, Orkut e similares lançam com sistemas de moderação por IA já incorporados — não como afterthought de 2017. Disinformation cresce mas em ritmo 40% mais lento que o histórico.",
        baseProbability: 0.50, actualProbability: 0.71,
        modulators: [{ name: "Aletheia API maturity", value: "alta", effect: 0.21 }] }
    },
    16: { // 2006-S1
      id: "ai_act_proposal", title: "Proposta do AI Act Europeu", severity: "high", primaryBlock: "EU",
      variant: { id: "mais_cedo", label: "antecipado em 15 anos", status: "redirected",
        description: "A Comissão Europeia formaliza o AI Act como proposta legislativa — quinze anos antes do histórico. O documento herda a linguagem do Working Paper #117 iniciado em 1999. Tensiona relações com EUA.",
        baseProbability: 0.30, actualProbability: 0.58,
        modulators: [
          { name: "governance.ai_regulation_maturity (EU)", value: "3.2", effect: 0.18 },
          { name: "Seattle legacy", value: "ativo", effect: 0.10 },
        ] }
    },
    20: { // 2008-S1 — financial crisis
      id: "gfc_2008", title: "Crise Financeira Global", severity: "critical",
      variant: { id: "antecipado_parcial", label: "antecipado parcialmente", status: "altered",
        description: "Modelos de IA detectam a deterioração dos MBS subprime em 2007. O Fed atua oito meses antes. Lehman Brothers ainda quebra (recusa fundir-se), mas a contagion é 35% menor. Recessão global ainda ocorre, mais curta.",
        baseProbability: 0.55, actualProbability: 0.74,
        modulators: [
          { name: "frontier_capability (US)", value: "118", effect: 0.15 },
          { name: "systemic_risk", value: "55", effect: 0.04 },
        ] }
    },
  };

  const proceduralShocks: Record<number, ExogenousShock | undefined> = {
    6: { id: "asia_pandemic_h5n1", title: "Surto regional de H5N1 (Sudeste Asiático)", description: "Surto contido em 4 meses graças a vigilância epidemiológica por IA. 218 mortes (vs 6.000+ projetadas em modelos pré-IA).", primaryBlock: "RoW" },
    14: { id: "indian_ocean_tsunami", title: "Tsunami do Oceano Índico", description: "Sistema de alerta precoce parcialmente assistido por IA reduz vítimas em 23% versus baseline. Ainda assim, o evento marca uma geração.", primaryBlock: "RoW" },
    18: { id: "energy_price_spike", title: "Choque do petróleo (US$ 147/barril)", description: "Pico histórico do petróleo bate como na realidade. Demanda chinesa amplificada por industrialização IA-assistida agrava.", primaryBlock: "CN" },
  };

  const lenses = [
    "incubação tecno-econômica — capital corre antes que regulação respire",
    "consolidação de ecossistema — vencedores começam a ser visíveis",
    "atrito civilizatório — tecnologia colide com instituições do século XX",
    "estabilização paradoxal — IA evita crise mas cria dependência",
    "fragmentação geopolítica — cada bloco escreve sua própria liturgia",
    "reconfiguração do trabalho — primeira onda real de deslocamento",
    "regulação reativa — instituições correm atrás do que já mudou",
  ];

  const seedPool: Seed[] = [
    { year: 1944, domain: "Bretton Woods", text: "A arquitetura financeira global pós-guerra estabelece o palco onde crises sistêmicas se propagam. Sem ela, a IA financeira não teria substrato para operar." },
    { year: 1962, domain: "Crise dos Mísseis", text: "O quase-acidente nuclear ensina que sistemas de decisão acelerados por máquinas são frágeis. A lição não foi internalizada." },
    { year: 1989, domain: "Queda do Muro", text: "A unificação do mercado global cria o substrato em que produtos de IA podem escalar a 1 bilhão de usuários em meses." },
    { year: 1991, domain: "Guerra do Golfo", text: "Primeira guerra televisionada em tempo real. Ensina o público a aceitar guerra mediada por tela — pré-condição para guerra mediada por IA." },
    { year: 1979, domain: "Three Mile Island", text: "Acidente nuclear gera o primeiro grande pânico tecnológico moderno. O playbook regulatório nasce aqui." },
    { year: 1986, domain: "Chernobyl", text: "Confirma para uma geração que sistemas opacos podem falhar catastroficamente. Aplicável a IA por analogia direta." },
    { year: 1969, domain: "Apollo 11", text: "A última grande demonstração de competência técnica estatal. A privatização da fronteira (Aletheia incluída) é o reverso desse impulso." },
    { year: 2000, domain: "Genoma humano", text: "O primeiro projeto big-science da era pós-guerra fria. Big-data biology + IA fará o que o sequenciamento sozinho não fez." },
  ];

  const event = proceduralEvents[turnIndex];
  const shock = proceduralShocks[turnIndex];
  const lens = lenses[turnIndex % lenses.length];
  const seeds = [seedPool[(turnIndex * 3) % seedPool.length], seedPool[(turnIndex * 3 + 1) % seedPool.length], seedPool[(turnIndex * 3 + 2) % seedPool.length], seedPool[(turnIndex * 3 + 4) % seedPool.length]];

  // Generic narrative
  const narrative = `O semestre ${year}-S${semester} avança sob o signo de ${lens.split(" — ")[0]}. ${
    event ? `O evento ${event.title.toLowerCase()} se materializa em variante ${event.variant.label}, contornando a leitura canônica que a história não-contrafactual nos legou.` : "Não há evento âncora — o que não impede que as forças de fundo continuem se reorganizando, em silêncio."
  } ${
    shock ? `Um choque exógeno — ${shock.title.toLowerCase()} — atravessa a narrativa e força o motor causal a improvisar.` : ""
  } As séries macroeconômicas seguem direções que confirmam, em grande parte, a tese de incubação acelerada. Os blocos divergem mais do que convergem; a aposta de que a difusão Bass uniformizaria capacidade demonstra-se ingênua quando atrito institucional varia tanto.`;

  const keyDevelopments = [
    `Capacidade de fronteira US cruza patamar simbólico (modelo gerador interno).`,
    `Penetração populacional em EU acelera (efeito spillover Bass + tradução de produtos).`,
    `Concentração BigTech segue subindo monotonamente — sinal de fricção regulatória.`,
    event ? `Evento âncora resolvido em variante "${event.variant.label}".` : `Sem evento âncora; deltas dominados por dinâmica endógena.`,
  ];

  const causalLinks: CausalLink[] = [
    { source: "frontier_capability (US)", target: "frontier_capability (EU)", strength: 0.4, polarity: 1, scope: "spillover" },
    { source: "frontier_capability (US)", target: "frontier_capability (CN)", strength: 0.3 + (turnIndex * 0.01), polarity: 1, scope: "spillover" },
    { source: "frontier_capability", target: "automation_exposure", strength: 0.5, polarity: 1, scope: "intra-block" },
    { source: "automation_exposure", target: "employment_rate", strength: 0.3, polarity: -1, scope: "intra-block" },
    { source: "publications_index", target: "breakthroughs_per_year", strength: 0.4, polarity: 1, scope: "global" },
    { source: "ai_regulation_maturity (EU)", target: "bigtech_concentration (EU)", strength: 0.25, polarity: -1, scope: "intra-block" },
  ];

  return {
    event, shock, narrative, keyDevelopments, lens, seeds, confidence: turnIndex < 16 ? "high" : "medium",
    causalLinks,
  };
}

// ---- State evolution ------------------------------------------------------

function evolveState(prev: WorldState, seed: TurnSeed, turnIndex: number): {
  next: WorldState;
  globalDeltas: { key: GlobalMetricKey; delta: number; why: string }[];
  blockDeltas: { key: VectorizedMetricKey; by: Record<BlockId, number>; why: string }[];
  matrixDeltas: any[];
} {
  const next: WorldState = {
    global: { ...prev.global },
    blocks: {
      US:  { ...prev.blocks.US },
      EU:  { ...prev.blocks.EU },
      CN:  { ...prev.blocks.CN },
      RoW: { ...prev.blocks.RoW },
    },
    matrix: {
      "geopolitics.bilateral_tensions": { ...prev.matrix["geopolitics.bilateral_tensions"] },
      "geopolitics.active_conflicts": prev.matrix["geopolitics.active_conflicts"],
    },
  };

  // Default deterministic drifts (per turn)
  const defaultGlobal: Record<GlobalMetricKey, number> = {
    "financial_markets.global_index": 3.2,
    "financial_markets.systemic_risk": 0.4,
    "education.mean_years_schooling": 0.05,
    "education.cost_index": 1.8,
    "inequality.global_gini": 0.001,
    "inequality.top1pct_share": 0.15,
    "health.life_expectancy": 0.12,
    "health.diagnostic_accuracy": 0.18,
    "science_rd.publications_index": 1.4,
    "energy_climate.co2_gt_year": 0.3,
    "energy_climate.renewable_share": 0.25,
    "information_ecosystem.media_trust": -0.4,
  };

  const defaultBlock: Record<VectorizedMetricKey, Record<BlockId, number>> = {
    "ai_capability.frontier_capability": { US: 1.8, EU: 1.2, CN: 1.5, RoW: 0.7 },
    "ai_capability.population_penetration": { US: 1.4, EU: 0.9, CN: 0.6, RoW: 0.3 },
    "tech_industry.bigtech_concentration": { US: 0.6, EU: 0.3, CN: 0.5, RoW: 0.2 },
    "tech_industry.tech_employment_share": { US: 0.15, EU: 0.10, CN: 0.20, RoW: 0.08 },
    "labor_market.automation_exposure": { US: 0.8, EU: 0.5, CN: 0.7, RoW: 0.3 },
    "labor_market.employment_rate": { US: -0.05, EU: -0.04, CN: 0.02, RoW: -0.02 },
    "governance.democracy_index": { US: -0.02, EU: -0.01, CN: -0.05, RoW: 0.02 },
    "governance.ai_regulation_maturity": { US: 0.10, EU: 0.20, CN: 0.05, RoW: 0.03 },
    "information_ecosystem.disinformation_level": { US: 0.5, EU: 0.4, CN: 0.6, RoW: 0.5 },
    "science_rd.breakthroughs_per_year": { US: 0.30, EU: 0.18, CN: 0.25, RoW: 0.08 },
  };

  const overrides = seed.overrides ?? {};
  const globalDeltas: { key: GlobalMetricKey; delta: number; why: string }[] = [];
  const blockDeltas: { key: VectorizedMetricKey; by: Record<BlockId, number>; why: string }[] = [];

  for (const k of GLOBAL_KEYS) {
    const d = overrides.global?.[k] ?? defaultGlobal[k];
    next.global[k] = +(prev.global[k] + d).toFixed(3);
    if (Math.abs(d) > 0.0005) {
      globalDeltas.push({ key: k, delta: +d.toFixed(3), why: `dinâmica endógena (turno ${turnIndex})` });
    }
  }
  for (const k of VECTORIZED_KEYS) {
    const ovr = overrides.block?.[k] as Partial<Record<BlockId, number>> | undefined;
    const by: Record<BlockId, number> = { US: 0, EU: 0, CN: 0, RoW: 0 };
    for (const b of BLOCKS) {
      const d = ovr?.[b] ?? defaultBlock[k][b];
      by[b] = +d.toFixed(3);
      next.blocks[b][k] = +(prev.blocks[b][k] + d).toFixed(3);
    }
    if (BLOCKS.some(b => Math.abs(by[b]) > 0.005)) {
      blockDeltas.push({ key: k, by, why: ovr ? "ajustado pelo evento/narrativa do turno" : "spillover Bass + dinâmica endógena por bloco" });
    }
  }
  // matrix simple drift
  const tens = next.matrix["geopolitics.bilateral_tensions"];
  for (const pair of Object.keys(tens)) {
    const drift = (Math.sin(turnIndex + pair.length) * 1.2);
    tens[pair] = Math.max(0, Math.min(100, +(tens[pair] + drift).toFixed(2)));
  }
  next.matrix["geopolitics.active_conflicts"] = Math.max(0, prev.matrix["geopolitics.active_conflicts"] + (turnIndex % 4 === 0 ? -1 : 0));

  const matrixDeltas = [
    { key: "geopolitics.bilateral_tensions" as const, delta: tens, why: "tensões bilaterais ajustadas por dinâmica de blocos" },
    { key: "geopolitics.active_conflicts" as const, delta: next.matrix["geopolitics.active_conflicts"] - prev.matrix["geopolitics.active_conflicts"], why: "rotação de conflitos ativos" },
  ];

  return { next, globalDeltas, blockDeltas, matrixDeltas };
}

// ---- Build all 24 turns ---------------------------------------------------

export function buildMockTurns(): Turn[] {
  const seeds: TurnSeed[] = [];
  for (let i = 0; i < 24; i++) {
    seeds.push(TURN_SEEDS[i] ?? makeProceduralSeed(i));
  }

  const turns: Turn[] = [];
  let prevState: WorldState = INITIAL_STATE;
  for (let i = 0; i < 24; i++) {
    const seed = seeds[i];
    const { year, semester, label } = TURN_LABELS[i];
    const { next, globalDeltas, blockDeltas, matrixDeltas } = evolveState(prevState, seed, i);
    turns.push({
      index: i,
      label,
      year,
      semester,
      state: next,
      prevState,
      event: seed.event,
      shock: seed.shock,
      narrative: seed.narrative,
      keyDevelopments: seed.keyDevelopments,
      deltas: { global: globalDeltas, block: blockDeltas, matrix: matrixDeltas },
      causalLinks: seed.causalLinks,
      lens: seed.lens,
      seeds: seed.seeds,
      confidence: seed.confidence,
    });
    prevState = next;
  }
  return turns;
}

export const MOCK_TURNS: Turn[] = buildMockTurns();
export const TOTAL_TURNS = 58;
export const MOCK_TURN_LABELS = TURN_LABELS; // 58 labels available

// ---- Mock runs ------------------------------------------------------------

import type { RunConfig } from "./types";

export const MOCK_RUNS: RunConfig[] = [
  { id: "run_alpha", name: "alpha — big bang puro", aiMode: "big_bang", playMode: "manual", temperature: 0.85, randomShockProbability: 0.05, seed: 19980201, model: "gemini-2.5-pro", notes: "Primeira run de calibração. Baseline de comparação para todas as outras.", createdAt: "2026-03-04T09:14:00Z", currentTurn: 23 },
  { id: "run_beta",  name: "beta — curva acelerada",  aiMode: "accelerated_curve", playMode: "auto", temperature: 0.70, randomShockProbability: 0.08, seed: 19981115, model: "gemini-2.5-flash", notes: "Hipótese: difusão mais lenta nos primeiros 5 anos.", createdAt: "2026-03-12T14:22:00Z", currentTurn: 12 },
  { id: "run_gamma", name: "gamma — alta volatilidade", aiMode: "big_bang", playMode: "hybrid", temperature: 1.10, randomShockProbability: 0.18, seed: 20010911, model: "gemini-2.5-pro", notes: "Para estressar a robustez do motor a choques.", createdAt: "2026-04-01T11:00:00Z", currentTurn: 8 },
  { id: "run_delta", name: "delta — regulação precoce", aiMode: "big_bang", playMode: "manual", temperature: 0.65, randomShockProbability: 0.04, seed: 19990601, model: "gemini-2.5-pro", notes: "Variante: AI Act EU em 2003 ao invés de 2024.", createdAt: "2026-04-18T16:45:00Z", currentTurn: 2 },
  { id: "run_epsilon", name: "epsilon — sem chronista (debug)", aiMode: "big_bang", playMode: "auto", temperature: 0.50, randomShockProbability: 0.05, seed: 20240101, model: "gemini-2.5-flash", notes: "Run de testes — narrativas curtas para debugar SDM.", createdAt: "2026-04-25T08:30:00Z", currentTurn: 0 },
];
