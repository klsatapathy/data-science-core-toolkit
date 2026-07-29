# 🎮 Cookie Cats — A/B Testing Framework

[![Python](https://img.shields.io/badge/Analysis-Python%20%7C%20pandas%20%7C%20scipy-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Stats](https://img.shields.io/badge/Methods-Power%20Analysis%20%7C%20Bootstrap%20%7C%20Z--Test-orange)]()
[![Plotly](https://img.shields.io/badge/Interactive-Plotly-3F4F75?logo=plotly&logoColor=white)](https://plotly.com/)

A complete A/B testing lifecycle — experiment design, hypothesis testing, bootstrap validation, and a demonstration of the "peeking problem" — built around a reusable `ABTestFramework` class, applied to a real production experiment from the mobile game Cookie Cats.

**Dataset:** [Mobile Games A/B Testing — Cookie Cats (Kaggle)](https://www.kaggle.com/datasets/mursideyarkin/mobile-games-ab-testing-cookie-cats)
**Size:** 90,189 players — `gate_30` (control) vs `gate_40` (test)

---

## 🎯 Business Question

Cookie Cats uses a "gate" — a forced progress-block — originally placed at level 30. The product team tested moving it to level 40. Does delaying the gate help or hurt player retention?

## 📁 Repo Structure

```
AB_Testing_Framework/
├── Cookie_Cats_AB_Framework.ipynb          # GitHub version (matplotlib/seaborn)
├── Cookie_Cats_AB_Framework_Kaggle.ipynb   # Kaggle version (interactive Plotly, self-contained)
├── ab_test_framework.py                     # Standalone reusable ABTestFramework class
├── cookie_cats.csv                           # Source dataset
├── PLAN.md                                    # Original project plan
└── README.md
```

## ⚙️ Setup

1. Open `Cookie_Cats_AB_Framework.ipynb` in Jupyter with `ab_test_framework.py` and `cookie_cats.csv` in the same folder.
2. Run all cells to reproduce the full analysis.
3. The Kaggle notebook has the `ABTestFramework` class inlined directly (no external `.py` import) so it runs standalone on Kaggle without extra utility-script setup.
4. The framework can also be run directly: `python ab_test_framework.py`

## 🧰 Why This Project Is Different From a Standard Hypothesis Test

Most hypothesis-testing projects analyze a completed experiment. This one covers the full lifecycle — including the parts that happen *before* and *around* the final significance check:

| Typical post-hoc analysis | This project adds |
|---|---|
| Test an existing result | Plan the test *before* running it — sample size & power analysis |
| Single p-value decision | Minimum Detectable Effect (MDE) — what's even worth testing for |
| Formula-based confidence intervals | Bootstrap-based confidence intervals (resampling, no distributional assumptions) |
| — | The "peeking problem" — simulating how early/repeated checks inflate false-positive risk |
| One-off analysis script | A reusable `ABTestFramework` class for future experiments |

## 📊 Analysis Workflow

1. **Exploratory Data Analysis** — group balance check, retention rates, game-rounds distribution
2. **Experiment Design** — `calculate_sample_size()` and `minimum_detectable_effect()` confirm the experiment was adequately powered
3. **Hypothesis Testing** — two-proportion z-tests on both 1-day and 7-day retention (`run_test()`)
4. **Bootstrap Confidence Interval** — 10,000-iteration resampling cross-check on the 7-day retention difference (`bootstrap_ci()`)
5. **The Peeking Problem** — simulates the false-positive inflation caused by checking results early and stopping as soon as p < 0.05 (`simulate_peeking_risk()`)
6. **Business Recommendation** — final decision, weighing which retention metric matters more

## 🔧 The `ABTestFramework` Class

A reusable module built alongside this analysis:

```python
from ab_test_framework import ABTestFramework

fw = ABTestFramework(alpha=0.05, power=0.8)
fw.calculate_sample_size(baseline_rate, mde)
fw.minimum_detectable_effect(baseline_rate, n_per_group)
fw.run_test(group_a, group_b)
fw.bootstrap_ci(group_a, group_b, n_iterations=10000)
fw.simulate_peeking_risk(true_rate_a, true_rate_b, n_per_group, checks_per_experiment)
```

Designed to be dataset-agnostic — usable for any future binary-outcome A/B test, not just this one.

## 💡 Key Findings

- **Adequately powered:** the actual sample size (~44,700-45,489 per group) comfortably exceeds what's needed to detect a 1-percentage-point retention change — the achievable MDE is ~0.74pp.
- **1-day retention:** no significant difference between gate_30 and gate_40.
- **7-day retention:** gate_30 significantly outperforms gate_40 (**19.02% vs 18.20%**, p ≈ 0.0016) — confirmed independently by both the z-test and a 10,000-iteration bootstrap CI, which agree the difference is not zero.
- **Peeking problem:** simulating repeated early checks (10 checkpoints) inflates the false-positive rate several times beyond the intended 5% — reinforcing why the pre-planned sample size should be respected rather than stopping early on a promising result.

## 🎯 Business Recommendation

**Keep the gate at level 30.** Moving it to level 40 does not improve short-term engagement and measurably *hurts* 7-day retention — the more meaningful long-term signal for a live-service game. This is a case where a properly designed, adequately powered test pushed back against the intuitive product hypothesis.

## 🛠️ Tech Stack

Python (pandas, numpy, scipy, statsmodels — power analysis & proportions z-test), Plotly (Kaggle version), matplotlib/seaborn (GitHub version)

## 🔗 Related

Part of a 5-project Statistics portfolio series (basic → advanced): EDA Dashboard → Probability & Sampling → Hypothesis Testing → **A/B Testing Framework (this project)** → Statistical Decision Engine.

## 📄 License

Add a license (e.g. MIT) here if you intend this repo to be reused by others.
