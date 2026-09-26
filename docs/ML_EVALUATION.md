# CampusCart — Matching & Recommendation Evaluation Plan

Smart Swap, Wanted matching and recommendations should be evaluated as ranking systems, not as decorative scores.

## Offline evaluation

Create a time-split dataset from historical interactions so that training/candidate features are derived only from events available before the evaluation window. Measure:

- Precision@K: fraction of top-K results that became positive interactions.
- Recall@K: fraction of positive interactions recovered in top-K.
- NDCG@K: ranking quality when stronger positives should appear earlier.
- Coverage: fraction of active inventory that can be surfaced.
- Freshness: time from listing creation to first relevant exposure.

Compare the heuristic scorer with at least one simple baseline (recency/popularity) before claiming improvement.

## Online evaluation

For a deployed system, record anonymized recommendation impressions and outcomes. Compare variants using a fixed experiment window and predefined metrics such as save rate, contact rate, offer rate and completed-transaction rate. Do not use post-outcome information as a feature for the decision that produced the outcome.

## Data-quality safeguards

- Prevent the seller from being recommended their own listing.
- Keep campus boundaries explicit.
- Clamp or robustly transform price outliers.
- Handle sparse users with a cold-start path.
- Do not expose private addresses or sensitive user data to the ranking layer unless required.


## Reproducible evaluation workflow

1. Export observed interaction events with `python scripts/export_ml_events.py --output ml_data/interactions.jsonl`.
2. Run `python scripts/evaluate_recommendations.py --input ml_data/interactions.jsonl`.
3. The evaluator reports NDCG@K for an observed-data popularity baseline when sufficient data exists; it does not invent metrics when the dataset is empty.
4. Re-run the same evaluation against time-matched datasets when testing recommendation changes.
