# 📊 Marketing A/B Test — Hypothesis Testing Toolkit

[![Python](https://img.shields.io/badge/Analysis-Python%20%7C%20pandas%20%7C%20scipy-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Stats](https://img.shields.io/badge/Methods-Chi--Square%20%7C%20Z--Test%20%7C%20T--Test-orange)]()
[![Plotly](https://img.shields.io/badge/Interactive-Plotly-3F4F75?logo=plotly&logoColor=white)](https://plotly.com/)

A full hypothesis-testing toolkit applied to a real, large-scale marketing A/B test — determining whether an ad campaign's conversion lift is statistically real and practically significant enough to justify a rollout decision.

**Dataset:** [Marketing A/B Testing (Kaggle)](https://www.kaggle.com/datasets/faviovaz/marketing-ab-testing)
**Size:** 588,101 users — `ad` (test) vs `psa` (control) groups

---

## 📁 Repo Structure

```
Marketing_AB_Hypothesis_Testing/
├── Marketing_AB_Hypothesis_Testing.ipynb          # GitHub version (matplotlib/seaborn)
├── Marketing_AB_Hypothesis_Testing_Kaggle.ipynb   # Kaggle version (interactive Plotly)
├── marketing_AB.csv                                # Source dataset
└── README.md
```

## ⚙️ Setup

1. Open either notebook in Jupyter, pointing it at `marketing_AB.csv` in the same folder.
2. Run all cells to reproduce the full hypothesis-testing workflow.
3. The Kaggle version renders Plotly charts via `renderer='iframe'` — designed for direct upload to Kaggle; charts may not render in GitHub's static notebook viewer.

## 📊 Analysis — Full Hypothesis Testing Workflow

**1. Data Quality Audit** — 588,101 rows, 0 missing values, 0 duplicates; heavily imbalanced group sizes (564,577 `ad` vs 23,524 `psa`), realistic for real ad-platform holdout groups

**2. Exploratory Data Analysis** — conversion rate comparison and ad-exposure distribution by group

**3. Chi-Square Test of Independence** — tests whether conversion outcome is independent of test group assignment

**4. Two-Proportion Z-Test** — quantifies the exact size of the conversion-rate gap between groups, with Wilson 95% confidence intervals

**5. Welch's T-Test** — tests whether ad-exposure volume differs significantly between converted and non-converted users

**6. Bonus Chi-Square Test** — checks whether conversion depends on the day of peak ad exposure (scheduling angle)

**7. Statistical vs. Practical Significance** — an explicit discussion of why significance alone isn't enough to justify a business decision at this sample size, and why this result clears both bars

## 💡 Key Findings

- **Chi-square test:** conversion outcome is significantly associated with test group (p « 0.05) — not independent.
- **Two-proportion z-test:** `ad` group converts at **2.55%** vs. **1.79%** for the `psa` control — a statistically significant **~43% relative lift**, confirmed by non-overlapping 95% confidence intervals.
- **Welch's t-test:** converted users were exposed to significantly more ads on average than non-converters.
- **Day-of-week chi-square:** conversion is statistically associated with peak-exposure day, though the effect is modest compared to the core ad-vs-control lift.
- **The scale caveat:** with 588K users, even trivially small differences would likely register as "statistically significant" — what makes this result decision-worthy is that the lift is significant **and** large in absolute business terms (43% relative improvement), not a sample-size artifact.

## 🎯 Business Recommendation

Roll out the ad campaign — the conversion lift is both statistically robust and practically significant. For future tests: use a more balanced group split (the current 96%/4% split limits precision on the control-group estimate), and track ad-exposure dosage explicitly, since exposure volume is strongly associated with conversion.

## 🛠️ Tech Stack

Python (pandas, numpy, scipy, statsmodels), Plotly (Kaggle version), matplotlib/seaborn (GitHub version)

## 🔗 Related

Part of a 5-project Statistics portfolio series (basic → advanced): EDA Dashboard → Probability & Sampling → **Hypothesis Testing (this project)** → A/B Testing Framework → Statistical Decision Engine.
