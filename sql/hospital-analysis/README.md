# 🏥 Hospital Database Analysis Project

[![MySQL](https://img.shields.io/badge/Database-MySQL%208.0-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Python](https://img.shields.io/badge/EDA-Python%20%7C%20pandas%20%7C%20seaborn-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Power BI](https://img.shields.io/badge/Dashboard-Power%20BI-F2C811?logo=powerbi&logoColor=black)](https://powerbi.microsoft.com/)

An end-to-end data analytics project on hospital operations — from raw CSVs to a MySQL relational database, SQL-based business insights, a Python exploratory analysis, and an interactive 4-page Power BI dashboard.

**Dataset:** [Hospital Management Dataset (Kaggle)](https://www.kaggle.com/datasets/kanakbaghel/hospital-management-dataset)
**Tables:** `patients` · `doctors` · `appointments` · `treatment` · `billing`

---

## 📁 Repo Structure

```
hospital-database-analysis/
├── sql/
│   ├── Database_setup.sql       # Schema + CSV import (LOAD DATA INFILE)
│   └── Database_analysis.sql    # 20 business-insight queries, 5 sections
├── eda/
│   └── hospital_eda.ipynb       # Python EDA (pandas, seaborn, matplotlib)
├── data/
│   ├── patients.csv
│   ├── doctors.csv
│   ├── appointments.csv
│   ├── treatments.csv
│   └── billing.csv
├── dashboard/
│   ├── hospital_dashboard.pbix  # Power BI file
│   └── screenshots/
│       ├── overview.png
│       ├── doctor_performance.png
│       ├── patients_appointments.png
│       └── billing_risk.png
└── README.md
```

> Folder names above are a suggestion — rename to match your actual repo layout before pushing.

## 🗄️ Database Schema

Five tables linked by foreign keys:

```
patients (patient_id PK)
doctors (doctor_id PK)
appointments (appointment_id PK) -> patient_id, doctor_id
treatment (treatment_id PK) -> appointment_id
billing (bill_id PK) -> patient_id, treatment_id
```

| Table | Key columns |
|---|---|
| **patients** | demographics, contact info, registration date, insurance provider/number |
| **doctors** | specialization, years of experience, hospital branch |
| **appointments** | date/time, reason for visit, status (Completed / No-show / Cancelled / Scheduled) |
| **treatment** | treatment type, description, cost, treatment date |
| **billing** | bill amount, payment method, payment status (Paid / Pending / Failed) |

## ⚙️ Setup

1. Run `Database_setup.sql` in MySQL Workbench (or the MySQL CLI) to create the database and all 5 tables.
2. Update the `LOAD DATA INFILE` paths in the same script to point to where your CSVs live on disk.
3. Run the load statements — each is followed by a `SELECT COUNT(*)` check, and the script ends with a verification query across all tables.
4. Run `Database_analysis.sql` (in full or section by section) to reproduce the SQL insights.
5. Open `hospital_eda.ipynb` in Jupyter, point it at the same CSVs, and run all cells for the Python-side visualizations.
6. Open `hospital_dashboard.pbix` in Power BI Desktop to explore the interactive dashboard, or import the CSVs directly via **Get Data → Text/CSV** if building from scratch.

> **Note:** `LOAD DATA INFILE` requires `secure_file_priv` to allow the source folder, or the file to sit in MySQL's configured secure upload directory. On the CLI you may need `LOAD DATA LOCAL INFILE` instead, depending on your server configuration.

## 📊 SQL Analysis — 20 Insights Across 5 Sections

`Database_analysis.sql` uses joins, CTEs, and window functions (`RANK`, `NTILE`, `LAG`) to answer:

**Section A — Doctor Performance & Revenue**
Revenue/volume per doctor · rank within specialization · experience vs. revenue

**Section B — Patient Segmentation (RFM Analysis)**
RFM scoring & segmentation (Champions, Regular, At Risk, etc.) · age group vs. spend · insurance provider reliance

**Section C — Appointment Operations**
Status breakdown · no-show/cancellation rate by doctor & day of week · status by reason for visit

**Section D — Demand & Time Trends**
Monthly volume & revenue trend · MoM revenue growth % · busiest day · appointment-to-billing lag

**Section E — Billing & Payment Risk**
Payment status by amount at risk · treatment type revenue ranking · payment method failure behavior · high-value unpaid bills

## 🐍 Python EDA

`hospital_eda.ipynb` is a companion notebook covering patient demographics, doctor staffing, appointment outcomes, treatment revenue, and billing risk with seaborn/matplotlib visualizations — see the notebook's own summary section for details.

## 📈 Power BI Dashboard

A 4-page interactive dashboard, styled with a custom theme (`hospital_theme.json`) for consistent branding across pages.

### Page 1 — Overview
KPI cards (Total Revenue, Appointments, Collection Rate %, Lost Rate %, Patients) · monthly revenue trend · appointment status donut · billed amount by payment status · top unpaid bills table · revenue by doctor

![Overview](sql/hospital-analysis/screenshots/overview.PNG)

### Page 2 — Doctor Performance
Revenue by doctor · lost (no-show/cancellation) rate by doctor · avg treatment cost by experience bucket · doctor rank within specialization table

![Doctor Performance](sql/hospital-analysis/screenshots/doctor_performance.PNG)

### Page 3 — Patients & Appointments
RFM segment table & donut · status breakdown by reason for visit (matrix) · revenue by age bucket · lost rate by day of week · revenue by insurance provider

![Patients & Appointments](sql/hospital-analysis/screenshots/patients_appointments.PNG)

### Page 4 — Billing & Revenue Risk
KPIs (Total Billed, Collected Amount, Amount at Risk, At Risk %) · billed amount by payment status · high-value unpaid bills table · revenue by treatment type · failure rate by payment method

![Billing & Revenue Risk]([sql/hospital-analysis/screenshots/billing_risk.PNG](https://github.com/klsatapathy/data-science-core-toolkit/blob/2fa0b6e452c61e365f809b194149b3fb9ecc01f5/sql/hospital-analysis/screenshots/billing_risk.PNG))

> Add your own screenshots to `dashboard/screenshots/` with the filenames above (or update the paths here) for the images to render on GitHub.

## 💡 Key Insights

- **Doctor performance:** Revenue is concentrated but not extreme — the top 3 doctors account for ~40% of doctor revenue. Volume doesn't equal value: some lower-volume doctors have the highest average treatment cost. No clear link between years of experience and revenue — specialization and patient load matter more.
- **Patient segmentation (RFM):** "Champions" are a major segment (~44% of patients, highest average spend), not a small niche. A high-value "Regular" segment carries the highest average spend overall; a smaller "At Risk/New" segment with long average recency is a strong re-engagement target.
- **Appointment operations:** Roughly half of all appointments (51.5%) are lost to no-shows or cancellations — a hospital-wide issue, not isolated to a few doctors or days.
- **Billing & payment risk:** Only ~31% of total billed amount is actually collected (68.5% Pending or Failed). Cash payments have a notably higher failure rate than card or insurance. A cluster of high-value unpaid bills is identified for targeted follow-up.

## 🛠️ Tech Stack

- **Database:** MySQL 8.0
- **Analysis:** SQL (joins, CTEs, window functions — `RANK`, `NTILE`, `LAG`)
- **EDA:** Python (pandas, seaborn, matplotlib)
- **Dashboard:** Power BI Desktop, custom theme (`hospital_theme.json`)

## 📄 License

Add a license (e.g. MIT) here if you intend this repo to be reused by others.
