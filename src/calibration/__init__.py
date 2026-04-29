"""Calibration of structural parameters against historical data (Etapa 5).

Workflow:
    historical_loader.load_all_series(data_dir)
        ──> dict[metric_key, HistoricalSeries] aligned to the 58 turns

    parameter_space.build_parameter_space(spec)
        ──> list of CalibratableParameter (alpha, beta) with confidence-bounded ranges

    objective.objective_function(alpha_vector, ...)
        ──> scalar weighted error against historical series under null treatment

    optimizer.calibrate(...)
        ──> scipy L-BFGS-B + differential evolution wrapper

    runner.run_full_calibration(...)
        ──> end-to-end orchestrator that persists artifacts to runs/calibration/

Public entry point for scripts:
    from src.calibration.runner import run_full_calibration
"""
