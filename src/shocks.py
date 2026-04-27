"""Geração de choques exógenos aleatórios.

A cada turno, com probabilidade `random_shock_probability`, sorteia-se um
choque do pool. O RNG é determinístico por (seed + turn_index), então rodar
duas vezes com a mesma seed gera a mesma sequência de choques.
"""
from __future__ import annotations

import random
from typing import Optional

from src.config import SimulationConfig
from src.models import ExogenousShock


SHOCK_POOL: list[ExogenousShock] = [
    # Tecnologia
    ExogenousShock(
        name="Avanço em fusão nuclear comercial",
        description="Um consórcio público-privado anuncia o primeiro reator de fusão net-positive em escala demonstrativa.",
        domain="energy",
        severity="high",
    ),
    ExogenousShock(
        name="Vulnerabilidade crítica em criptografia",
        description="Pesquisadores publicam ataque viável contra um algoritmo de cifragem amplamente usado.",
        domain="tech",
        severity="high",
    ),
    ExogenousShock(
        name="Quebra do paradigma quântico",
        description="Computação quântica útil em escala chega anos antes do esperado, ameaçando criptografia atual.",
        domain="tech",
        severity="high",
    ),
    ExogenousShock(
        name="Falha massiva em cabo submarino",
        description="Múltiplos cabos transoceânicos são danificados, derrubando rotas de internet por semanas.",
        domain="tech",
        severity="medium",
    ),
    ExogenousShock(
        name="Vazamento massivo em big-tech",
        description="Dados de centenas de milhões de usuários vazam de uma plataforma dominante.",
        domain="tech",
        severity="medium",
    ),
    # Saúde
    ExogenousShock(
        name="Breakthrough em terapia gênica para câncer",
        description="Um regime de terapia gênica obtém remissão durável em múltiplos tipos de tumor sólido.",
        domain="health",
        severity="high",
    ),
    ExogenousShock(
        name="Crise de resistência a antibióticos",
        description="Cepas multirresistentes se espalham, com mortalidade hospitalar em alta.",
        domain="health",
        severity="high",
    ),
    ExogenousShock(
        name="IA descobre nova classe de antibióticos",
        description="Um modelo dirigido a alvos identifica compostos eficazes contra cepas resistentes.",
        domain="health",
        severity="high",
    ),
    ExogenousShock(
        name="Surto zoonótico contido rapidamente",
        description="Um patógeno emergente é identificado e contido antes de virar pandemia, com auxílio de modelagem por IA.",
        domain="health",
        severity="low",
    ),
    # Geopolítica
    ExogenousShock(
        name="Tentativa de golpe em país-chave",
        description="Uma potência regional sofre tentativa de tomada do poder; mercados reagem.",
        domain="geopolitics",
        severity="medium",
    ),
    ExogenousShock(
        name="Acordo de paz inesperado",
        description="Um conflito de longa data é encerrado por mediação inesperada.",
        domain="geopolitics",
        severity="medium",
    ),
    ExogenousShock(
        name="Escândalo de espionagem entre potências",
        description="Documentos vazados expõem operações encobertas, esfriando relações diplomáticas.",
        domain="geopolitics",
        severity="low",
    ),
    ExogenousShock(
        name="Catástrofe natural em região estratégica",
        description="Um terremoto ou tsunami de grande escala afeta um polo industrial ou logístico crítico.",
        domain="geopolitics",
        severity="medium",
    ),
    # Economia
    ExogenousShock(
        name="Choque em commodity-chave",
        description="Disrupção em petróleo, lítio ou semicondutores faz preços dispararem globalmente.",
        domain="financial",
        severity="medium",
    ),
    ExogenousShock(
        name="Inovação financeira disruptiva",
        description="Um novo instrumento financeiro habilitado por IA muda o funcionamento dos mercados.",
        domain="financial",
        severity="medium",
    ),
    ExogenousShock(
        name="Crise cambial em economia emergente",
        description="Uma economia emergente sofre fuga de capitais com efeito de contágio regional.",
        domain="financial",
        severity="medium",
    ),
    # Informação
    ExogenousShock(
        name="Vazamento de documentos governamentais",
        description="Uma fonte interna divulga arquivos sensíveis de inteligência (estilo Snowden).",
        domain="information",
        severity="high",
    ),
    ExogenousShock(
        name="Onda massiva de deepfakes",
        description="Conteúdo sintético em escala industrial inunda o ecossistema de informação.",
        domain="information",
        severity="medium",
    ),
    ExogenousShock(
        name="Plataforma social dominante colapsa",
        description="Uma rede social de bilhões de usuários sofre falência ou fragmentação.",
        domain="information",
        severity="medium",
    ),
    # Energia/clima
    ExogenousShock(
        name="Acidente nuclear severo",
        description="Um reator sofre falha catastrófica, forçando reavaliação global da política nuclear.",
        domain="energy",
        severity="high",
    ),
    ExogenousShock(
        name="Avanço em armazenamento de energia",
        description="Uma química de bateria reduz custo em ordem de grandeza, viabilizando renováveis em escala.",
        domain="energy",
        severity="high",
    ),
    ExogenousShock(
        name="Evento climático extremo destrói infraestrutura",
        description="Furacão ou onda de calor sem precedentes destrói infraestrutura crítica em economia desenvolvida.",
        domain="energy",
        severity="medium",
    ),
    ExogenousShock(
        name="Acordo climático global ambicioso",
        description="Potências chegam a um acordo vinculante de redução de emissões mais agressivo que o esperado.",
        domain="energy",
        severity="medium",
    ),
    # Ciência
    ExogenousShock(
        name="Descoberta em supercondutores",
        description="Um material com supercondutividade em temperatura próxima da ambiente é replicado por terceiros.",
        domain="science",
        severity="high",
    ),
    ExogenousShock(
        name="Avanço em interfaces cérebro-computador",
        description="Implantes BCIs mostram resultados clínicos consistentes em comunicação para pacientes paralisados.",
        domain="science",
        severity="medium",
    ),
]


def _turn_to_index(turn: str) -> int:
    """Converte 'YYYY-S1'/'YYYY-S2' em índice 0-based para o RNG."""
    year_str, sem_str = turn.split("-")
    year = int(year_str)
    sem = 0 if sem_str == "S1" else 1
    return (year - 1998) * 2 + sem


def maybe_generate_shock(turn: str, config: SimulationConfig) -> Optional[ExogenousShock]:
    """Sorteia um choque exógeno para o turno, determinístico por (seed, turn).

    Retorna None se não houver choque neste semestre.
    """
    rng = random.Random(config.seed + _turn_to_index(turn))
    if rng.random() < config.random_shock_probability:
        return rng.choice(SHOCK_POOL)
    return None
