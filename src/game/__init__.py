"""Modo Jogo — orquestra o motor SDM turn-by-turn como um jogo single-player.

O jogador é CEO de um lab de IA fronteira em 1998. Cada turno (semestre) submete
uma ação: canônica (template predefinido) ou livre (prosa interpretada por GM-LLM).
A ação vira exógeno injetado no DeltaPackage do motor — a lógica core do motor
permanece intocada.

Entry points públicos:
    from src.game.game_runner import start_game, submit_action
    from src.game.missions import MISSION_AGI_ALIGNED
    from src.game.canonical_actions import CANONICAL_ACTIONS
"""
