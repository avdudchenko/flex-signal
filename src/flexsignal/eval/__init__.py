"""Evaluation: a masking benchmark for imputers.

:func:`benchmark_imputers` hides known values, lets each imputer fill them, and
scores the fill by gap length. Forecast backtesting arrives in M4.
"""

from flexsignal.eval.imputation import benchmark_imputers, hide_values, summarize

__all__ = ["benchmark_imputers", "hide_values", "summarize"]
