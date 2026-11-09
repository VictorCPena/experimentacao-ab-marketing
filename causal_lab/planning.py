"""Two-sided independent-proportion planning for equal allocation."""

import math

from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize


def required_per_arm(baseline: float, mde: float, *, alpha: float = 0.05, power: float = 0.8) -> int:
    """Return the ceiling of the normal-approximation sample size per arm.

    MDE is an absolute increase in probability, not a relative percentage.
    This prospective approximation assumes independent Bernoulli outcomes,
    1:1 allocation and a single two-sided comparison.
    """
    if not all(math.isfinite(x) for x in (baseline, mde, alpha, power)):
        raise ValueError("Planning inputs must be finite")
    if not (0 < baseline < baseline + mde < 1 and 0 < alpha < power < 1):
        raise ValueError("Require 0 < baseline < baseline + MDE < 1 and 0 < alpha < power < 1")
    size = NormalIndPower().solve_power(
        effect_size=proportion_effectsize(baseline + mde, baseline),
        alpha=alpha,
        power=power,
        ratio=1,
        alternative="two-sided",
    )
    return math.ceil(size)
