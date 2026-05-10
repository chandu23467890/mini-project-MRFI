# Viva Notes

## 1. Problem Framing

This project treats diabetes progression as a metabolic trajectory rather than a binary label. The main engineering idea is that metabolic instability appears before the final clinical diagnosis threshold is crossed. The system therefore focuses on:

- stability over time
- early transition-state detection
- individualized interventions
- evidence-backed alerting

## 2. Why the Stability Score Exists

A single glucose reading is noisy and context-dependent. A stability score compresses multiple dimensions into one interpretable indicator while still preserving subcomponents for explanation.

Weights:

- `40%` glucose control because it reflects direct glycemic burden
- `25%` trend stability because a rising slope indicates progression
- `20%` insulin sensitivity because HOMA-IR captures underlying resistance
- `15%` lifestyle because behavior influences future metabolism but is indirect

## 3. Why Linear Regression for Trend

Linear regression gives an interpretable slope in glucose units over time. In viva, the key defense is interpretability:

- easy to explain clinically
- robust on small datasets
- slope maps directly to worsening or improving control

## 4. Why Holt Exponential Smoothing for Trajectory

Holt smoothing was chosen instead of a heavier time-series model because health logs are sparse and irregular.

Why it fits:

- low parameter count
- less overfitting risk
- works reasonably with short history
- trend component is explicit and explainable

## 5. Why HOMA-IR

HOMA-IR is a validated fasting proxy for insulin resistance:

```text
HOMA-IR = (fasting glucose mg/dL x fasting insulin uU/mL) / 405
```

It matters because a patient can still look “not diabetic” by one threshold while insulin resistance is already deteriorating.

## 6. Why Anomaly Detection Uses Multiple Layers

The anomaly system combines:

- hard clinical thresholds
- personalized IQR-based outlier detection
- rate-of-change checks

This reduces false alarms while still catching dangerous events. Clinical thresholds protect safety. IQR protects personalization. Rate-of-change protects acute drift.

## 7. Why Confidence Intervals Matter

Predictions and scores should not be shown as absolute certainty. Confidence intervals make the system more honest and clinically safer. The interval width reflects data quality and measurement sufficiency.

## 8. Data Quality Logic

The system does not only score health state; it also scores the quality of the evidence used to infer that state.

Components:

- recency
- consistency
- completeness

This is useful in viva because it shows the model accounts for uncertainty in the input stream, not just uncertainty in the output.

## 9. Transaction Design

Three main transaction ideas:

- measurement submission
- stability recalculation
- recommendation generation

Why transactions matter:

- prevents half-written medical state
- keeps alerts and audit logs consistent
- avoids score updates without underlying measurement persistence

## 10. Security and Integrity

Security features already in the project:

- JWT authentication
- password hashing with bcrypt
- audit trail for sensitive actions
- restricted upload size
- configurable secrets
- rollback on database errors

If asked what could be added next:

- refresh tokens
- role-based access control
- encrypted storage for highly sensitive fields
- signed device integrations
- rate limiting

## 11. Limitations You Can State Honestly

- image-based meal analysis is heuristic, not clinical-grade computer vision
- SQLite is fine for evaluation but PostgreSQL is better for production concurrency
- websockets are user-ID path based and should be tied to stronger session validation in a larger deployment
- the recommendation engine is rule-based and interpretable, but not yet learned from outcomes

## 12. Good Viva Sound Bites

- “The system predicts instability, not just diagnosis.”
- “I separated signal quality from health state quality.”
- “I chose interpretable models because this is a medical monitoring context.”
- “Every prediction is paired with confidence and evidence, not just a label.”
- “The architecture prioritizes auditability and safe failure over black-box complexity.”
