# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- **Hand-off to models (M3).** `flexsignal.handoff` turns cleaned data into what a model needs, with no model
  library imported:
  - `to_grid(data, grid, options)` gives one value per model time step: UTC to the facility's `timezone`,
    `offset` and `data_years` to read other windows, forward or backward interval resampling with an `agg`, summed
    amounts split over finer steps, gap rules (`interpolate`, `ffill`, `zero`, `error`, with a `limit`), or
    `reduce` to one number. The result (`GridValues`) carries units, filled counts, steps resting on filled or
    corrected samples, the window read, `to_overrides()` and `data_hash()`. `data_window` says which UTC data
    that reads.
  - `fit_data(X, y, prep)` joins input and output frames, resamples, applies a gap rule (`error`, `drop`,
    `interpolate`, `longest_segment`), logs each step and hashes the result; `split_holdout` keeps the end for
    testing. flex-signal stops at `X, y`: call a flex-pse regressor yourself, with `fit.input_units` and
    `fit.output_units`.
  - `grids_of`, `scope_of`, `targets`: which time block a model path belongs to, for models with several.
  - `GridOptions` and `FitPrep` keep flex-orchestrator's field names, defaults and validation.

  These functions, and their tests, come from flex-orchestrator, which will call them instead of its own copies
  (PLAN.md D22, `FLEX_ORCHESTRATOR_OVERLAP.md`).
- **flex-pse integration (M3).** `flexsignal.integrations.flexpse`: `time_grid` (a flowsheet spec's or built
  model's time points, one axis per time block), `time_scopes`, and `apply_values`, which takes a spec or a
  built model with the same result: on a spec, a copy with `fix` elements (and costing fields such as a flat price);
  on a built model, its variables fixed in place (and mutable Params, such as a price built as a Param, set). flex-pse is
  imported only inside these functions; `import flexsignal` still loads no flex-pse, pyomo or idaes.
- **`flexsignal.eval.metrics`** (RMSE, MAE, MAPE), and `fs.eval` / `fs.handoff` reachable from `import flexsignal`.
- **Docs and tutorial (M3).** An explanation page on handing data to flex-pse models; how-to guides to apply data to
  a flex-pse model and to prepare fit data; tutorial 07, from raw data to a solved flex-pse model and a fitted
  surrogate.
- **CI.** The integration job installs the latest flex-pse release (0.3.1, by git tag, with HiGHS); a weekly job
  runs it against flex-pse `main`. `environment.yml` installs the same pin.
- **`Pipeline.add_step`.** Build a pipeline one step at a time: `pipe = fs.Pipeline(name="x")`, then
  `pipe.add_step(step)` for each step, in the order they should run. Each step is checked as it is added, and the
  call returns the pipeline so it can be chained. Passing a list still works and builds the same spec.
- **Calibration against a reference (M2).** `correct.Calibrate` fits a mapping from a stream to a trusted,
  intermittent reference on the rows where `fit_when` holds, and applies it wherever `apply_when` holds. It
  prefers the reference's own value where it is trusted (`prefer_reference`), flags predictions `CORRECTED`, and
  can refit on a rolling window to follow drift (`refit={"rolling": "1D"}`). Models: `sklearn:LinearRegression`,
  `Ridge`, `HuberRegressor`, `TheilSenRegressor`, `statsmodels:OLS`, `RLM`, and `scipy:curve_fit` with a
  formula. `mode="residual"` models the error instead of the value. Fit metrics (rows, RMSE, R²) appear in the
  fitted state and in `report()`.
- **Model imputers (M2).** `impute.Kalman` (statsmodels structural model and Kalman smoother, with optional daily
  or weekly cycles), `impute.Regression` (linear model of other streams, their lags, and Fourier terms),
  `impute.KNN` and `impute.Iterative` (scikit-learn), and `impute.Tiered`, which routes each gap to a method by
  its length. Every imputer takes `max_gap`, never fills `EXCLUDED` or `NO_SAMPLE` values, and flags what it
  fills `IMPUTED_MODEL`.
- **Signal steps (M2).** `clean.Filter` (Savitzky-Golay, zero-phase Butterworth, moving median) and
  `clean.Detotalize` (running total to rate, with rollover and reset handling). New flag `FILTERED`.
- **Condition helpers (M2).** `held(C == 0, "30min")`, `valid(B)`, `is_raw(B)` and `flagged(A, "OUTLIER")`, plus
  `minimum`/`maximum`. Conditions are type-checked when a spec is loaded ("needs True/False", "gives numbers").
  Formulas (numeric expressions with fitted parameters) for `scipy:curve_fit`.
- **Imputer benchmark (M2).** `flexsignal.eval.benchmark_imputers` hides known values as gaps of given lengths,
  lets each imputer fill them, and scores RMSE, MAE, bias and coverage; `hide_values` and `summarize` help.
- **`synthetic.abcd`**: the A/B/C/D calibration problem with known truth, optional drift, and a reference that is
  biased or reads 0 under known conditions.
- **Docs (M2).** "flex-signal in ten minutes"; explanation pages on conditions, calibration and imputation tiers;
  how-to guides to calibrate against a reference, impute gaps and evaluate imputers. Getting-started pages now
  run in CI too.
- **Tutorials (M2).** 05 calibrates A against B under conditions, with drift; 06 compares imputers by gap length
  and builds a tiered imputer from the result.

### Changed

- Conditions no longer go through `pandas.eval`. flex-signal parses them and evaluates the tree itself with numpy.
  Two semantics are now explicit: `&` and `|` bind like `and` and `or` (as in `pandas.eval`), and every
  comparison with a missing value is False, `!=` included.
- Model keys in specs (`calibrate`, `regression`) must be registered linear-model keys; arbitrary
  `"package.module:Class"` paths are refused, so loading a spec never imports code.
- Synthetic faults that only shift values (calibration, drift, step) no longer block later faults from being
  injected on top of them.

- **Core data model (M1).**
  - `SignalFrame`: values, a per-sample `uint16` quality-flag bitmask, per-stream `StreamMeta` (units, quantity
    kind, source) and provenance `history`. The time index is always tz-aware UTC, nanosecond resolution, sorted
    and unique, and frames are immutable.
  - Timestamps without a time zone are taken as this machine's local time (`local_timezone()`, overridable with
    the `TZ` environment variable) and raise a `NaiveTimestampWarning`. Passing `timezone=` silences it. This
    applies to `SignalFrame`, `from_frame`, `read_csv`, `read_parquet` and spec file inputs; timestamps written
    in a spec still mean UTC. New core dependency: `tzlocal`.
  - `Flag` bits: `MISSING`, `OUT_OF_RANGE`, `RATE_OF_CHANGE`, `OUTLIER`, `STUCK`, `MANUAL`, `EXCLUDED`,
    `CORRECTED`, `IMPUTED_SHORT`, `IMPUTED_MODEL`, `FORECAST`, `DERIVED`, `RESAMPLED`, `NO_SAMPLE`. Cleaning sets a
    value to NaN and sets a flag; it never deletes data.
  - `NO_SAMPLE` marks the rows a stream gets only because another input has a sample at that time, when several
    inputs are joined. `align`, `resample` and `interpolate` skip those rows. Before this, an off-grid source
    joined with an on-grid one aligned to the join's padding and came out all NaN.
  - The `SignalError` hierarchy (`SignalConfigError`, `SignalDataError`, `SignalBackendError`). Errors carry a
    dotted `field` path and survive pickling.
  - The step registry with the `flexsignal.steps` entry-point group, and the backend registry
    (`get_backend("scipy:PchipInterpolator")`, lazy imports, "install the extra" errors) with the
    `flexsignal.backends` group.
- **`SignalSpec` (schema `0.1.0`).**
  - Strict, frozen pydantic models with `kind`-discriminated steps, named input slots (`frame`, `parquet`, `csv`)
    and outputs (`parquet`, `csv`).
  - `load_spec` / `dump_spec`, `MIGRATIONS`, `$source` file references, and `spec_hash` over canonical JSON.
  - Conditions (`keep_when`, `invalid_when`) can't run code. `check_condition` parses each one and accepts only
    stream names, numbers, arithmetic, comparisons, `and`/`or`/`not`/`&`/`|`/`~` and the math functions in
    `CONDITION_FUNCTIONS`. It runs when a spec is loaded and before evaluation, and refuses attribute access,
    indexing, strings and other calls with an error naming the field.
  - Errors name the exact field once, e.g. `steps.2.window: '1 hour' is not a duration ...`. A spec with several
    problems lists them all.
  - The JSON Schema is committed at `src/flexsignal/spec/schemas/signal_spec.schema.json`, and a test keeps it
    current.
  - A step *is* its spec: the object built in Python is what JSON loads into. Fitted state is a separate JSON dict
    returned by `fit()`.
- **Steps.**
  - select: `align`, `resample`, `window`, `mask`, `rename`, `combine`, `shift`.
  - clean: `range`, `rate_of_change`, `stuck`, `hampel` (with a `min_scale` noise floor), `tukey` (fences learned
    in `fit`), `expression`.
  - impute: `interpolate` (linear, nearest, previous, PCHIP, Akima via numpy/scipy), limited to gaps no longer
    than `max_gap` and never filling `EXCLUDED` values.
- **Pipelines and entry points.**
  - `Pipeline` / `FittedPipeline` with `fit`, `transform`, `report`, `to_payload` / `from_payload`, and `save` /
    `load` (plain JSON files, no pickle).
  - Every step's effect is recorded in the output's history by comparing its input and output.
  - `flexsignal.run` / `flexsignal.fit` follow the orchestrator contract: spec in, JSON-able `RunResult` out, no
    I/O when data is passed in, and progress callbacks.
- **File I/O.** Parquet that keeps flags, units and provenance in the Arrow metadata, and CSV with exact float
  round-trips.
- **`flexsignal.testing.synthetic`.** A seeded generator of plant-like data (flow, pressure, temperature, pump
  status, an intermittent reference meter). It injects spikes, stuck runs, gaps, out-of-range values, drift and
  steps, with exact ground-truth masks.
- **Tests.**
  - Each cleaner flags exactly the injected faults.
  - Python- and JSON-built pipelines give bit-identical output.
  - Every step kind round-trips through JSON.
  - Orchestrator contract tests: params-model embedding, JSON results and payloads, pickling, no I/O.
  - Every code block in the explanation and how-to docs runs in CI.
- **Docs.**
  - Explanation pages: SignalFrame and flags, the pipeline spec, steps and backends, time and units.
  - How-to guides: clean a stream, save and load a fitted pipeline.
  - An example script.
  - A full API reference, with step, field, flag and backend tables generated from the registries.
- **Tutorials.** Four marimo notebooks in `tutorials/`, from a first look at the data to multi-stream rules:
  a first look, cleaning one stream, pipelines and specs, and several streams. Each scores its steps against
  the injected faults and asserts its own results. CI runs them as scripts, and the docs site publishes them as
  static pages. Install with the new `[tutorials]` extra.

- **Project scaffold (M0).**
  - `flex-signal` distribution with the `flexsignal` import package: a src layout, Python ≥3.11, and the core
    dependencies from `PLAN.md` §5.1.
  - Subpackage skeleton (`core`, `spec`, `io`, `backends`, `steps`, `pipeline`, `eval`, `api`,
    `integrations.flexpse`, `integrations.acquirium`), with each module's purpose and target milestone in its
    docstring.
  - import-linter contracts for the layering, the independence of the integrations, and the rules that only
    `integrations.flexpse` may import flex-pse, pyomo or idaes and only `integrations.acquirium` may import
    acquirium or polars.
  - Tooling: ruff (flex-pse's rules plus `D`, Google style), black, pre-commit with a pre-push suite, and pytest
    tier markers (`unit`, `component`, `integration`). A root `conftest.py` fails collection when a test has
    anything other than exactly one tier marker.
  - CI mirroring flex-pse v0.3.0:
    - uv installs;
    - tests on Python 3.11–3.14 (Linux), plus 3.13 on macOS and Windows;
    - a single coverage run uploaded to Codecov (`codecov.yml`);
    - an integration job;
    - a standard-install check against the built wheel.
  - Sphinx docs (furo, MyST) deployed to GitHub Pages, and a PyPI publish workflow.
  - `CONTRIBUTING.md`, plus issue and PR templates mirroring flex-pse.
- **Test:** `import flexsignal` loads no flex-pse, pyomo, idaes, torch, polars or acquirium (`PLAN.md` D1).
