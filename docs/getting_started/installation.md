# Installation

flex-signal needs Python 3.11 or newer.

## From source

flex-signal is not on PyPI yet. Install it from a clone:

```bash
git clone https://github.com/flex-pse/flex-signal.git
cd flex-signal
pip install -e .
```

The core install includes pandas, numpy, scipy, scikit-learn, statsmodels, pydantic, pyarrow and pandera. It does
not include torch, flex-pse, polars or Acquirium. `import flexsignal` never loads any of those.

## Development environment

The conda environment installs flex-signal in editable mode with the development and documentation tools:

```bash
conda env create -f environment.yml
conda activate flex-signal
pre-commit install --hook-type pre-commit --hook-type pre-push
```

Without conda, use `pip install -e ".[dev,docs,tutorials]"` instead. The pre-commit hooks expect the `flex-signal` conda
environment.

## Optional extras

Each heavy or specialised library is an optional extra, added in the milestone whose code uses it. Only
`tutorials` exists so far: everything up to M2, including the calibration models, the Kalman, regression, k-NN and
iterative imputers and the imputer benchmark, uses the core dependencies.

| Extra | Contents | Milestone |
|---|---|---|
| `tutorials` | marimo (pinned) and matplotlib, to run the [tutorials](../tutorials/index.md) | M1 |
| flex-pse | The latest flex-pse release (0.3.1 today), for `flexsignal.integrations.flexpse` and tutorial 07. Not on PyPI yet, so install it from its git tag (below); `environment.yml` already does | M3 |
| `ml` | skforecast, lightgbm | M4 |
| `nixtla` | statsforecast, mlforecast | M4 |
| `pypots` | PyPOTS deep imputation and forecasting, with pygrinder missing-data patterns | M5 |
| `deep` | neuralforecast | M5 |
| `foundation` | Chronos-2 zero-shot forecasting | M5 |
| `anomaly` | pyod, ruptures, stumpy | M5 |
| `darts`, `sktime` | Adapters to the darts and sktime model zoos | M5 |
| `units` | pint, pint-pandas | M5 |
| `acquirium` | Acquirium client | M7 |

## flex-pse

`flexsignal.handoff` needs nothing extra. Fixing a flex-pse model's variables (`flexsignal.integrations.flexpse`),
the flex-pse how-to guides and tutorial 07 need flex-pse itself. It isn't on PyPI yet, so install the latest release
from its git tag, with HiGHS to solve:

```bash
pip install "flex-pse[parameterize,solvers] @ git+https://github.com/flex-pse/flex-pse.git@0.3.1"
```

`import flexsignal` never imports flex-pse, pyomo or idaes, so the rest of flex-signal works without it.
