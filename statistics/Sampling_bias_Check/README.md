# 🛒 Amazon Review Sampling Bias Checker

[![Python](https://img.shields.io/badge/EDA-Python%20%7C%20pandas%20%7C%20seaborn-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Stats](https://img.shields.io/badge/Analysis-Sampling%20Theory%20%7C%20Hypothesis%20Testing-orange)]()
[![Kaggle](https://img.shields.io/badge/Notebook-Kaggle-20BEFF?logo=kaggle&logoColor=white)](https://www.kaggle.com/code/lokanathsatapathy/sampling-bias-checker)

An end-to-end statistical investigation into whether Amazon's "Most Helpful" review sort shows shoppers a fair picture of customer opinion — using real sampling theory (random sampling, sampling distributions, the Central Limit Theorem) and formal hypothesis testing, not just a visual eyeball check.

**Dataset:** [Datafiniti Amazon Consumer Reviews (Kaggle)](https://www.kaggle.com/datasets/datafiniti/consumer-reviews-of-amazon-products)
**Size:** 34,660 reviews across 48 Amazon products (Fire tablets, Kindles, Echo devices)

---

## 📁 Repo Structure

```
sampling_bias_checker/
├── eda/
│   └── Sampling_Bias_Checker.ipynb   # Python EDA (pandas, seaborn, matplotlib, scipy)
├── data/
│   └── 1429_1.csv
└── README.md
```

> Folder names above are a suggestion — rename to match your actual repo layout before pushing.

## ⚙️ Setup

1. Open `Sampling_Bias_Checker.ipynb` in Jupyter, point it at `data/1429_1.csv`, and run all cells to reproduce the full statistical analysis.
2. No additional setup needed — every chart renders as a static image directly in the notebook.

## 📊 Python EDA — Full Statistical Breakdown

`Sampling_Bias_Checker.ipynb` covers the full sampling-theory pipeline end to end, not just the headline finding:

**1. Data Quality Audit** — missing values across every core column, including flagging `reviews.didPurchase` as 99.997% missing/unusable and `name` as ~19.5% missing

**2. The Population** — descriptive statistics (mean, median, std dev, skewness) for the full 34,627-review population, and a visual confirmation of its heavy left-skew

**3. Random Sampling** — drawing individual random samples at increasing sizes (n=10, 30, 100, 500) to show how sample-mean accuracy improves with n

**4. Sampling Distribution of the Mean** — 1,000 resampled means at each sample size, compared against the theoretical standard error (σ/√n)

**5. Central Limit Theorem** — histogram grids showing the sampling distribution turning from irregular/skewed (n=10) to visibly normal (n=100–500), confirmed formally with **Shapiro-Wilk normality tests**

**6. The Real-World Bias Check** — comparing the true population, a proper random sample, and a "helpful-sorted" sample (what a shopper actually sees) using a **one-sample t-test** against the known population mean, plus **Cohen's d** to separate statistical significance from practical significance

**6b. Sensitivity Check** — repeating the bias check across N = 10–100 visible reviews to confirm the finding isn't an artifact of one arbitrary cutoff

**6c. Confound Check** — isolating a single product to rule out "product mix" as an alternative explanation for the bias

**7. Bonus Check** — testing whether the same bias shows up in "would recommend" rate, not just star rating

**8. Key Findings & Recommendations** — summarized, business-facing conclusions

## 💡 Key Insights

- **True population mean rating: 4.58 / 5**, heavily left-skewed (skew ≈ -1.9) — 93%+ of all reviews are 4★ or 5★.
- **Random sampling works as expected** — a properly random sample of just 30 reviews tracks the true population mean closely, and the sampling distribution becomes approximately normal by n ≈ 100–500, confirming the Central Limit Theorem on real, non-synthetic data.
- **The "helpful-sorted" sample — what a shopper actually reads — is genuinely biased:** it differs from the true population mean by a statistically significant (p < 0.05) *and* practically large (Cohen's d ≈ -1.66) margin, skewing **lower** than the true average.
- **The bias is robust, not a fluke:** it holds directionally across every tested sample size (N=10–100) and stays a large effect from N=20 upward.
- **The bias survives a confound check** — isolating a single product (39% of all reviews) still shows a significant gap, ruling out product mix as the real explanation.
- The same directional bias also shows up in "would recommend" rate, reinforcing that "helpful" sorting systematically surfaces non-representative opinion.

## 🛠️ Tech Stack

- **Analysis:** Python (pandas, numpy, matplotlib, seaborn, scipy — sampling simulation, Shapiro-Wilk normality tests, one-sample t-tests, Cohen's d)

## 🔗 Related

A companion Plotly-based interactive EDA notebook (published on Kaggle) is available at [Sampling Bias Checker](https://www.kaggle.com/code/lokanathsatapathy/sampling-bias-checker).
