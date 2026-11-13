# Explanation

These pages explain how flex-signal works and why it is designed the way it is.

```{toctree}
:maxdepth: 1

signal_frame_and_flags
spec_schema
steps_and_backends
time_and_units
conditions
calibration
imputation_tiers
```

Each future page arrives with the milestone that builds the feature it describes:

| Page | What it covers | Milestone |
|---|---|---|
| flex-pse integration | Aligning to a `TimeBlock` and handing data to flexparameterize | M3 |
| Forecasting and backtesting | Forecast issue times, exogenous inputs, blocked backtests | M4 |
| The orchestrator contract | The API rules flex-orchestrator's wrapper relies on | M6 |
| Acquirium integration | Reading streams, writing results, `PipelineApp` | M7 |
