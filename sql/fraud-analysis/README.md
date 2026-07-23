# 🏦 Banking Fraud Analytics — SQL Project

[![MySQL](https://img.shields.io/badge/Database-MySQL%208.0-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![SQL](https://img.shields.io/badge/Analysis-Window%20Functions%20%7C%20CTEs-336791?logo=postgresql&logoColor=white)](https://www.mysql.com/)

An advanced SQL analytics project on synthetic banking transactions — building a MySQL relational schema, loading ~6.3M transactions, and using window functions, anomaly detection, account-risk profiling, time-trend analysis, and database automation (views/triggers/procedures) to uncover how fraud actually behaves in the data.

**Dataset:** [PaySim Synthetic Financial Fraud Detection Dataset (Kaggle)](https://www.kaggle.com/datasets/ealaxi/paysim1)
**Tables:** `transaction_types` · `staging_transactions` · `transactions`

---

## 📁 Repo Structure

```
banking-fraud-analytics/
├── sql/
│   ├── Database_Setup.sql       # Schema + CSV import (LOAD DATA INFILE)
│   └── Database_analysis.sql    # 15 fraud-pattern queries, 5 sections
└── README.md
```

> Folder names above are a suggestion — rename to match your actual repo layout before pushing.

## 🗄️ Database Schema

```
transaction_types (type_code PK)
transactions (transaction_id PK) -> type_code (FK)
staging_transactions            # temporary text-only table, raw CSV load
```

| Table | Key columns |
|---|---|
| **transaction_types** | `type_code`, `type_description` — lookup for CASH_IN / CASH_OUT / DEBIT / PAYMENT / TRANSFER |
| **staging_transactions** | all columns as `TEXT` — safely holds the raw CSV before casting |
| **transactions** | `step`, `type_code` (FK), `amount`, `nameOrig`, `oldbalanceOrg`, `newbalanceOrig`, `nameDest`, `oldbalanceDest`, `newbalanceDest`, `isFraud`, `isFlaggedFraud` — ~6.3M rows |

## ⚙️ Setup

1. Run `Database_Setup.sql` in MySQL Workbench (or the MySQL CLI) to create the database and all 3 tables.
2. Find your MySQL secure upload folder: `SHOW VARIABLES LIKE 'secure_file_priv';`
3. Copy the PaySim CSV into that folder, and update the `LOAD DATA INFILE` path in the script to match your actual file name (Kaggle sometimes names it `Synthetic_Financial_datasets_log.csv`).
4. Run the load statements — the CSV loads into `staging_transactions` first, then gets cast into `transactions`. Each step is followed by a `SELECT COUNT(*)` check (~6,362,620 rows expected).
5. Run `Database_analysis.sql` (in full or section by section) to reproduce the fraud-pattern insights.

> **Note:** `LOAD DATA INFILE` requires `secure_file_priv` to allow the source folder, or the file to sit in MySQL's configured secure upload directory. On the CLI you may need `LOAD DATA LOCAL INFILE` instead, depending on your server configuration.

## 📊 SQL Analysis — 15 Insights Across 5 Sections

`Database_analysis.sql` uses joins, CTEs, and window functions (`RANK`, `PERCENT_RANK`, `LAG`), plus a view, a trigger, and a stored procedure to answer:

**Section A — Fraud Overview & Transaction Type Patterns**
Fraud rate by transaction type · fraud-rate ranking across types · fraud rate by transaction amount bucket

**Section B — Balance Reconciliation & Anomaly Detection**
Origin balance reconciliation error (fraud vs. legit) · full account drain detection · amount percentile ranking within type

**Section C — Account-Level Risk Profiling**
Top destination accounts by fraudulent amount received · origin account transaction velocity · on-demand account risk score (stored procedure)

**Section D — Time-Based Fraud Trends**
Hourly transaction volume vs. fraud count · step-over-step fraud growth % · day-level fraud concentration

**Section E — System Flag Performance & Automation**
`isFlaggedFraud` vs. `isFraud` confusion matrix · reusable high-risk transaction view · auto-flag trigger for new inserts

## 💡 Key Insights

- **Fraud is type-specific:** Fraud occurs exclusively in TRANSFER and CASH_OUT transactions — CASH_IN, DEBIT, and PAYMENT show 0% fraud. TRANSFER's fraud rate (0.77%) is ~4.2x higher than CASH_OUT's.
- **Amount matters a lot:** Fraud rate rises sharply with transaction amount — the 1M+ bucket has a ~96x higher fraud rate than the smallest bucket.
- **Full account drain is the strongest signal found:** 97.55% of fraud transactions fully empty the origin account vs. only 42.72% of legit ones — more than double the rate. Balance reconciliation error, by contrast, is *not* reliable (legit transactions actually show higher average error than fraud ones).
- **The dataset's own fraud flag is nearly useless:** `isFlaggedFraud` catches only 16 of 8,213 true fraud cases — a 0.19% recall rate.
- **Simple rules trade recall for precision:** A high-risk rule (TRANSFER/CASH_OUT + full drain + amount > 200,000) flags 606,363 transactions but only 5,297 (0.87%) are actually fraud — good for casting a wide net, not for standalone use.
- **Time and velocity are weak signals here:** Fraud volume doesn't scale with hourly traffic, and the fastest repeat-transaction accounts showed zero fraud in this sample.

## 🛠️ Tech Stack

- **Database:** MySQL 8.0
- **Analysis:** SQL (CTEs, window functions — `RANK`, `PERCENT_RANK`, `LAG`, CASE bucketing)
- **Automation:** Views, Triggers, Stored Procedures

## 📄 License

Add a license (e.g. MIT) here if you intend this repo to be reused by others.
