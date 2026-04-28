"""Deterministic System Dynamics engine (Etapa 4).

Consumes spec/* and produces structured turn-by-turn evolution of the
counterfactual world without calling any LLM.

Public API surface:
    from src.engine.simulation import Simulation, SimulationConfig
    from src.engine.state import WorldState
    from src.engine.turn_runner import TurnResult, DeltaPackage
"""
