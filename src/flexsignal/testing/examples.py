"""Ready-made example steps, for tests and docs.

The spec tests check that :func:`one_of_every_step` covers every registered step
kind, so adding a step kind means adding an example here.
"""

from __future__ import annotations

from flexsignal.spec import Quantity, StepSpec
from flexsignal.steps import clean, correct, impute, select

__all__ = ["one_of_every_step"]


def one_of_every_step() -> list[StepSpec]:
    """Return one configured instance of every built-in step kind.

    The options are chosen to exercise non-default values, so a round trip
    through JSON tests more than the defaults.
    """
    return [
        select.Align(freq="5min", method="linear", how="inner"),
        select.Resample(freq="15min", agg="median", min_count=2, name="to_15min"),
        select.Window(start="2025-01-06", end="2025-01-08T12:00:00Z"),
        select.Mask(keep_when="pump_on == 1", streams=["flow"]),
        select.Rename(mapping={"temperature": "temp"}),
        select.Combine(output="flow_best", streams=["reference_flow", "flow"]),
        select.Shift("pressure", by="-15min"),
        clean.Range("flow", min=0.0, max=Quantity(value=500, units="m^3/hr")),
        clean.RateOfChange("flow", max_rate=200, per="1h"),
        clean.Stuck("flow", min_duration="1h", tolerance=0.0, exclude_values=[0.0]),
        clean.Hampel(["flow", "pressure"], window="1h", n_sigma=6),
        clean.Tukey("pressure", k=3),
        clean.Expression("pressure", invalid_when="pressure < 0", flag="OUT_OF_RANGE"),
        clean.Filter("temperature", method="savgol", window="1h", polyorder=3),
        clean.Detotalize("pressure", per="1min", rollover=1e6, units="bar/min"),
        correct.Calibrate(
            target="flow",
            reference="reference_flow",
            fit_when="pump_on == 1 and held(pump_on == 1, '30min')",
            apply_when="not flagged(flow, 'STUCK')",
            model="sklearn:HuberRegressor",
            params={"epsilon": 1.5},
            mode="residual",
            features=["flow", "temperature"],
            refit={"rolling": "2D", "every": "12h", "min_rows": 20},
            output="flow_cal",
        ),
        impute.Interpolate("flow", max_gap="15min", method="pchip"),
        impute.Kalman("flow", level="local_linear_trend", seasonal=[{"period": "1D"}]),
        impute.Regression(
            "flow",
            features=["pressure"],
            lags=["5min"],
            fourier=[{"period": "1D", "harmonics": 2}],
            model="statsmodels:OLS",
            max_gap="6h",
        ),
        impute.KNN("flow", features=["pressure"], n_neighbors=3, weights="distance"),
        impute.Iterative("flow", features=["pressure"], max_iter=5),
        impute.Tiered(
            "flow",
            tiers=[
                {"max_gap": "15min", "method": "interpolate"},
                {
                    "max_gap": None,
                    "method": "regression",
                    "options": {"features": ["pressure"]},
                },
            ],
        ),
    ]
