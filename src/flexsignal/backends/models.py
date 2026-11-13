"""Fit and apply the models that ``calibrate`` and ``regression`` use.

Every model here is linear in its inputs: ``y = intercept + X @ coef``. So the
fitted state is a handful of numbers that save as plain JSON, and applying a
fitted model needs only numpy, not the library that fitted it. The libraries
differ in *how* they estimate the coefficients, e.g. ordinary least squares or a
fit that down-weights outliers.

``scipy:curve_fit`` fits the parameters of a formula instead, for example
``"a + b * A + c * A ** 2"``. The formula is checked and evaluated by
:mod:`flexsignal.core.conditions`, so it can't run code.

Only the keys in :data:`LINEAR_MODELS` (and ``scipy:curve_fit``) are accepted. A
spec can't name an arbitrary ``"package.module:Class"`` here, because loading a
spec must never import code.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

from flexsignal.backends.registry import get_backend, register_backend
from flexsignal.core.conditions import evaluate_formula
from flexsignal.core.exceptions import SignalConfigError, SignalDataError

_SKLEARN_DOCS = "https://scikit-learn.org/stable/modules/generated/"
_SM_DOCS = "https://www.statsmodels.org/stable/generated/"

LINEAR_MODELS: dict[str, str] = {
    "sklearn:LinearRegression": "Ordinary least squares.",
    "sklearn:Ridge": "Least squares with an L2 penalty (params: alpha).",
    "sklearn:HuberRegressor": "Robust fit that down-weights outliers (epsilon).",
    "sklearn:TheilSenRegressor": "Robust median-of-slopes fit; slower.",
    "statsmodels:OLS": "Ordinary least squares (statsmodels).",
    "statsmodels:RLM": "Robust linear model with Huber's T norm (statsmodels).",
}
"""Model keys accepted by ``calibrate`` and ``regression``, with one line each."""

CURVE_FIT = "scipy:curve_fit"
"""Key for fitting a formula's parameters with :func:`scipy.optimize.curve_fit`."""

for _key, _line in LINEAR_MODELS.items():
    _lib, _name = _key.split(":")
    if _lib == "sklearn":
        register_backend(
            _key,
            f"sklearn.linear_model:{_name}",
            description=_line,
            docs_url=f"{_SKLEARN_DOCS}sklearn.linear_model.{_name}.html",
        )
    else:
        register_backend(
            _key,
            f"statsmodels.api:{_name}",
            description=_line,
            docs_url=(
                f"{_SM_DOCS}statsmodels.regression.linear_model.{_name}.html"
                if _name == "OLS"
                else f"{_SM_DOCS}statsmodels.robust.robust_linear_model.RLM.html"
            ),
        )
register_backend(
    CURVE_FIT,
    "scipy.optimize:curve_fit",
    description="Least-squares fit of a formula's parameters.",
    docs_url="https://docs.scipy.org/doc/scipy/reference/generated/"
    "scipy.optimize.curve_fit.html",
)


def check_model_key(key: str) -> str:
    """Return ``key`` if it names an accepted model, else raise ValueError."""
    if key in LINEAR_MODELS or key == CURVE_FIT:
        return key
    known = ", ".join([*LINEAR_MODELS, CURVE_FIT])
    raise ValueError(
        f"unknown model {key!r}. Use one of: {known}. Specs can't name other "
        "classes, because loading a spec must never import code."
    )


def fit_linear(
    key: str,
    X: np.ndarray,
    y: np.ndarray,
    params: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Fit a linear model and return its coefficients.

    Args:
        key: One of :data:`LINEAR_MODELS`.
        X: Inputs, shape ``(n_rows, n_features)``, with no NaN.
        y: Targets, shape ``(n_rows,)``, with no NaN.
        params: Keyword arguments for the model's constructor, e.g.
            ``{"alpha": 1.0}`` for Ridge.

    Returns:
        ``{"intercept": float, "coef": [float, ...]}``.

    Raises:
        SignalConfigError: If ``params`` doesn't suit the model.
        SignalDataError: If there are fewer rows than coefficients to fit.
    """
    check_model_key(key)
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(y) < X.shape[1] + 1:
        raise SignalDataError(
            f"only {len(y)} rows to fit {X.shape[1] + 1} coefficients; widen the "
            "training data or relax the fit condition."
        )
    cls = get_backend(key)
    params = dict(params or {})
    try:
        if key.startswith("sklearn:"):
            if key == "sklearn:TheilSenRegressor":
                params.setdefault("random_state", 0)
            model = cls(**params).fit(X, y)
            intercept, coef = float(model.intercept_), np.ravel(model.coef_)
        else:
            design = np.column_stack([np.ones(len(y)), X])
            fitted = cls(y, design, **params).fit()
            intercept, coef = float(fitted.params[0]), np.asarray(fitted.params[1:])
    except TypeError as exc:
        raise SignalConfigError(
            f"model {key!r} doesn't accept params {sorted(params)}: {exc}.",
            field="params",
        ) from exc
    return {"intercept": intercept, "coef": [float(c) for c in coef]}


def predict_linear(state: Mapping[str, Any], X: np.ndarray) -> np.ndarray:
    """Apply coefficients from :func:`fit_linear`; rows with a NaN input give NaN."""
    X = np.asarray(X, dtype=float)
    coef = np.asarray(state["coef"], dtype=float)
    return float(state["intercept"]) + X @ coef


def fit_curve(
    formula: str,
    data: Any,
    y: np.ndarray,
    initial: Mapping[str, float],
    params: Mapping[str, Any] | None = None,
) -> dict[str, float]:
    """Fit a formula's parameters to ``y`` by least squares.

    Args:
        formula: e.g. ``"a + b * A"``. Every name that isn't a stream must be a
            key of ``initial``.
        data: The rows to fit on (a SignalFrame or DataFrame), with no NaN in
            the streams the formula uses.
        y: The values the formula should reproduce, one per row.
        initial: Starting value for each parameter, e.g. ``{"a": 0, "b": 1}``.
        params: Extra keyword arguments for :func:`scipy.optimize.curve_fit`, e.g.
            ``{"maxfev": 5000}``.

    Returns:
        The fitted parameters, ``{name: value}``.

    Raises:
        SignalDataError: If there are too few rows, or the fit doesn't converge.
    """
    names: Sequence[str] = list(initial)
    if len(y) < len(names) + 1:
        raise SignalDataError(
            f"only {len(y)} rows to fit {len(names)} parameters; widen the training "
            "data or relax the fit condition."
        )
    curve_fit = get_backend(CURVE_FIT)

    def model(_x: Any, *p: float) -> np.ndarray:
        return evaluate_formula(data, formula, dict(zip(names, p, strict=True)))

    try:
        popt, _ = curve_fit(
            model,
            np.zeros(len(y)),
            np.asarray(y, dtype=float),
            p0=[float(initial[n]) for n in names],
            **dict(params or {}),
        )
    except RuntimeError as exc:
        raise SignalDataError(
            f"curve_fit didn't converge for {formula!r}: {exc}. Try better initial "
            "values, or params={'maxfev': 10000}."
        ) from exc
    return {n: float(v) for n, v in zip(names, popt, strict=True)}
