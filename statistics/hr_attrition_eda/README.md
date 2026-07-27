# HR Employee Attrition — Exploratory Data Analysis & Power BI Dashboard

Statistical analysis of employee attrition patterns using the IBM HR Analytics dataset, covering descriptive statistics, distribution analysis, and attrition-driver identification across every feature — paired with a 5-page interactive Power BI dashboard.

## Overview

This project investigates why employees leave the organization by analyzing 1,470 employee records across 35 features. The analysis combines statistical rigor (mean, median, mode, variance, standard deviation, skewness, hypothesis testing) with business-facing insights suitable for HR decision-making.

## Dataset

**Source:** [IBM HR Analytics Employee Attrition & Performance](https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset) (Kaggle)
**Size:** 1,470 employees × 35 features
**Quality:** No missing values, no duplicate records; 3 zero-variance columns (`EmployeeCount`, `Over18`, `StandardHours`) removed prior to analysis

## Contents

| File | Description |
|---|---|
| `HR_Attrition_EDA_GitHub.ipynb` | Full exploratory analysis — descriptive statistics for all continuous/ordinal features, distribution grids, IQR-based outlier audit, attrition-rate breakdown for every categorical/ordinal feature, Welch's t-tests for statistical significance, correlation analysis, and multivariate deep dives |
| `HR_Attrition_Dashboard.pbix` | 5-page interactive Power BI dashboard (see below) |

## Dashboard Structure

1. **Executive Summary** — KPI overview, attrition by department/gender/overtime/marital status
2. **Attrition Drivers** — job role risk ranking, satisfaction-score analysis, OverTime × JobSatisfaction heatmap, tenure-bucket breakdown
3. **Compensation Analysis** — income by job level/department, income comparison (stayed vs. left), age-vs-income scatter, gender pay-gap check
4. **Demographics & Workforce Profile** — age distribution, education field, business travel, department/gender composition
5. **Employee Explorer** — filterable employee-level table with synced slicers (Department, Job Role, OverTime, Attrition) and live KPI cards

## Key Findings

- **Overall attrition rate: 16.12%** (237 of 1,470 employees)
- **OverTime is the strongest single driver** — employees working overtime leave at roughly 3x the rate of those who don't
- **Sales Representative (~39.8%)** and **Laboratory Technician (~23.9%)** are the highest-risk job roles
- **Tenure under 2 years** carries nearly double the baseline attrition risk; risk drops sharply after year 3
- Welch's t-tests confirm `TotalWorkingYears`, `Age`, `MonthlyIncome`, `YearsAtCompany`, `YearsInCurrentRole`, and `YearsWithCurrManager` differ significantly (p < 0.05) between employees who left and those who stayed
- No meaningful gender pay gap detected when controlling for job level

## Tools Used

Python (pandas, numpy, matplotlib, seaborn, scipy), Power BI Desktop (DAX measures, calculated columns, matrix conditional formatting, synced slicers)

## Related

A companion Plotly-based exploratory notebook (Kaggle-published, interactive charts) is available in the [EDA_Projects](https://github.com/klsatapathy/EDA_Projects) repository under `hr-attrition-eda/`.

## Author

**Lokanath Satapathy** ([@klsatapathy](https://github.com/klsatapathy)) — Part of the [data-science-core-toolkit](https://github.com/klsatapathy/data-science-core-toolkit) portfolio.
