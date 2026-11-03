# Model card · models unavailable

**Model Not Trained** for both sovereign credit risk and twelve-month downgrade probability. No artifacts, scores, rankings, distributions, probabilities, or SHAP explanations are served.

Intended use: sovereign credit and loan-repayment risk analysis for development-finance lenders, other financial institutions, and insurers. This is the product focus, not a claim that a repayment/default model has already been trained. A repayment outcome, time horizon, and authorized repayment/default history must be defined before training that model. A rating downgrade is a different event and must not be presented as loan non-repayment.

## Model A · Sovereign credit risk

Target is not yet defined. A future target might be an explicitly scoped sovereign rating category or documented risk outcome. Economic series alone are not a validated rating or supervised target. No weighted-indicator proxy will be presented as an externally validated rating.

## Model B · Twelve-month downgrade probability

Requires authorized rating event history, agency, issuer/instrument scope, currency basis, observation eligibility, censoring rules, event definition, and a precise twelve-month horizon. No labels or licensed rating history are supplied. An absent event record is not automatically a negative label.

## Required before training and serving

1. Confirm target, intended use, coverage, redistribution rights, and label completeness.
2. Establish historically known-at-time feature vintages. Current WDI downloads and response revision dates cannot establish original availability.
3. Define an immutable feature schema, units, missingness/lag policies, scaling, and reproducible snapshot references.
4. Train offline using chronological partitions and walk-forward backtests. Compare logistic regression with boosting; address country effects and imbalance without temporal leakage.
5. Report ROC-AUC, PR-AUC, precision/recall, thresholded confusion matrices, Brier score, calibration curves, baseline comparisons, and coverage/subgroup limitations. Do not fit calibration on the test period.
6. Store target/license definition, dataset snapshots, preprocessing, metrics, dependency versions, schema, artifact integrity, and reviewed limitations. Load only trusted artifacts, never user uploads.
7. Validate lightweight offline-loaded inference, invalid/stale/missing feature rejection, calibrated probabilities, and faithful attributions.

Optional dependencies are in `.[ml]`. Training, preprocessing, calibration, backtesting, SHAP, artifact loading, and model integration are **not implemented in milestones 1–2**. Reserved directories are extension points, not completed pipelines.
