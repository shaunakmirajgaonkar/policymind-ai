"""
Policy impact simulation: Monte Carlo samples a user-defined impact
formula across low/base/high ranges, producing a full distribution — not
a false-precision single number. Reused proven pattern from DecisionMind
AI / ClimateVision AI.
"""
import numpy as np
from app.core.config import MONTE_CARLO_TRIALS, RANDOM_STATE


def run_policy_simulation(impact_fn, variable_ranges: dict, n_trials: int = MONTE_CARLO_TRIALS):
    rng = np.random.default_rng(RANDOM_STATE)
    samples = np.zeros(n_trials)
    var_names = list(variable_ranges.keys())
    sampled = {}
    for name, (low, base, high) in variable_ranges.items():
        low, base, high = float(low), float(base), float(high)
        if low == high:
            sampled[name] = np.full(n_trials, base)
        else:
            base_c = min(max(base, low + 1e-9), high - 1e-9)
            sampled[name] = rng.triangular(low, base_c, high, n_trials)

    for i in range(n_trials):
        trial = {name: sampled[name][i] for name in var_names}
        try:
            samples[i] = impact_fn(**trial)
        except Exception:
            samples[i] = np.nan

    valid = samples[~np.isnan(samples)]
    if len(valid) == 0:
        return {"error": "impact function failed on all trials"}

    mean = float(np.mean(valid))
    std = float(np.std(valid))
    cv = abs(std / mean) if mean != 0 else float("inf")
    return {
        "mean": round(mean, 4),
        "p10": round(float(np.percentile(valid, 10)), 4),
        "p50": round(float(np.percentile(valid, 50)), 4),
        "p90": round(float(np.percentile(valid, 90)), 4),
        "volatility": round(float(min(1.0, cv)), 4),
        "samples": valid.tolist(),
    }
