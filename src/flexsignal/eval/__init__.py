"""Evaluation: a masking benchmark for imputers.

:func:`benchmark_imputers` hides known values, lets each imputer fill them, and
scores the fill by gap length. :func:`metrics` scores any prediction (RMSE, MAE,
MAPE). Forecast backtesting arrives in M4.
"""

from flexsignal.eval.imputation import benchmark_imputers, hide_values, summarize
from flexsignal.eval.scores import metrics

__all__ = ["benchmark_imputers", "hide_values", "metrics", "summarize"]
