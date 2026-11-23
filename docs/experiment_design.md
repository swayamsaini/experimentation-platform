# Experiment Design: Fast-Ship Programme v1 (Pre-Registered)

1. **Hypothesis:** Enrolling eligible sellers in Fast-Ship increases 6-week GMV via search badge visibility and conversion.
2. **Unit & Hashing:** `seller_key`; `int(sha256(f"fastship_v1:{seller_key}")[:8], 16) % 1000 < 500 -> treatment`.
3. **Health Gates:** Chi-square SRM check at alpha = 0.001 (blocks results on failure); covariate balance target |SMD| < 0.10.
4. **Variance Reduction:** Pooled CUPED with 12-week `pre_gmv` + Lin (2013) HC3 regression adjustment.
5. **Inference:** Exact Welch-Satterthwaite t-CI; Delta Method for ratio metrics; O'Brien-Fleming alpha-spending across 6 weekly looks; cross-fitted T-learner & econml DR-learner for exploratory HTE (BH FDR 10%).
