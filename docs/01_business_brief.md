# Business Brief: Fast-Ship Programme v1

- **Decision:** Roll out the Fast-Ship Programme to all eligible sellers, expand to a targeted test, or stop.
- **Decision Rule (Pre-Registered):** Roll out if the 95% CI lower bound for CUPED GMV/seller > 0 AND zero guardrails breach. Expand if lift is positive/promising in a safe segment but overall CI includes zero. Stop if upper bound < MDE or guardrails breach across all segments.
- **Primary Metric:** 6-week GMV per eligible seller (delivered item price), winsorised at pooled p99.
- **Secondary Metrics:** Delivered orders/seller, AOV (ratio), 4-5 star review share (Holm FWER).
- **Guardrails (One-Sided 95% Non-Inferiority):** Late-delivery rate (<= +1.0pp), Cancellation rate (<= +0.5pp), Mean review score (>= -0.05 pts).
- **Randomisation Unit:** Seller (`seller_key`), deterministic SHA-256 hash 50/50 split.
- **Eligibility:** >= 5 delivered orders in 12-week pre-period (2018-01-01 to 2018-03-25) AND >= 1 order in final 4 pre-period weeks.
- **MDE & Window:** 8% relative GMV lift; 6-week window (2018-04-02 to 2018-05-13, ending before 21 May 2018 strike).
- **Honesty Note:** Treatment effects in the A/B test are semi-synthetic (injected onto real Olist baselines) for methodology validation.
