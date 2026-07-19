# Olist Brazilian E-Commerce — SQL Analysis & Power BI Dashboard

An end-to-end business analytics project on the [Olist Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) — from raw MySQL schema design to an interactive Power BI dashboard, covering revenue, product performance, customer segmentation, retention, and operations.

A companion Python/EDA notebook on the same dataset is available in my [EDA_Projects](https://github.com/klsatapathy/EDA_Projects/tree/main/olist-ecommerce-eda) repo.

## 🛠️ Tech Stack

- **MySQL / MySQL Workbench** — schema design, data import/cleaning, analysis queries
- **SQL** — CTEs, window functions (`LAG`, `RANK`, `NTILE`, `MIN() OVER`), aggregations
- **Power BI Desktop** — interactive dashboard, DAX measures, custom SQL data connections

## 📁 Folder Structure

```
olist_ecommerce/
├── README.md
├── database_setup.sql
├── olist_ecommerce_analysis.sql
├── Olist_Ecommerce_Dashboard.pbix
├── Dataset/
│   └── (raw CSVs)
└── screenshots/
    ├── overview.png
    ├── products.png
    ├── customers.png
    └── operations.png
```

## 🗄️ SQL

**`database_setup.sql`** — schema creation for the 9-table Olist database (orders, customers, order_items, products, order_reviews, order_payments, sellers, geolocation, product_category_name_translation) and data import setup.

**`olist_ecommerce_analysis.sql`** — 8 analysis queries across 5 sections, each with a business-facing insight comment:

1. **Revenue & Growth** — monthly revenue trend, MoM growth % (window function: `LAG`)
2. **Product Performance** — top categories by revenue (window function: `RANK`)
3. **RFM Segmentation** — customer scoring via `NTILE`, segmented into Champions / Loyal / At Risk / etc.
4. **Cohort Retention** — monthly cohort retention using `MIN() OVER (PARTITION BY ...)` and `TIMESTAMPDIFF`
5. **Operations** — delivery timeliness vs. review score, delivery time by state, payment method & installment behavior

15 total business insights are documented inline as SQL comments.

## 📊 Power BI Dashboard

An interactive 4-page dashboard (`Olist_Ecommerce_Dashboard.pbix`) connecting directly to the MySQL database via custom SQL queries.

### Overview
KPI cards, monthly revenue trend, MoM growth, order volume, RFM segment breakdown, and payment method mix.

![Overview](sql/olist_ecommerce/screenshots/overview.PNG)

### Products
Category performance summary, volume-vs-price trade-off (bubble chart), and top categories by revenue/order volume.

![Products](sql/olist_ecommerce/screenshots/products.PNG)

### Customers
Cohort retention heatmap, RFM segment table and donut chart.

![Customers](sql/olist_ecommerce/screenshots/customers.PNG)

### Operations
Delivery timeliness vs. review score, delivery time by state, payment installments vs. order value.

![Operations](sql/olist_ecommerce/screenshots/operations.PNG)

> **Note:** The `.pbix` file requires Power BI Desktop to open (free download). A live published version isn't available since Power BI Service publishing requires a work/school account — screenshots above cover the full dashboard.

## 🔑 Key Insights

- **Growth:** Orders scaled from ~750/month (Jan 2017) to a stable ~6–7K/month by 2018, with a clear Black Friday spike in Nov 2017 (+53.5% MoM).
- **Products:** Health & Beauty and Watches/Gifts are high-margin categories; Bed/Bath/Table drives volume at lower margins.
- **RFM:** Champions are only ~8% of customers but the highest spenders (Pareto pattern); "At Risk" is the largest segment (~34%) — the biggest win-back opportunity.
- **Retention:** Month-1 retention is below 1% across every cohort — the platform behaves as a largely one-time-purchase marketplace.
- **Delivery:** Late deliveries nearly halve average review scores (4.31 → 2.27) and carry a ~62% negative-review rate.
- **Geography:** North/Northeast Brazil states (Amazonas, Alagoas, Pará) face delivery times 2–3x longer than the national benchmark.
- **Payments:** Credit card accounts for 74% of orders; average order value roughly doubles from 1 to 5 installments.

## ▶️ Running Locally

1. Run `database_setup.sql` in MySQL Workbench to create the schema.
2. Import the CSVs from `Dataset/` into the corresponding tables.
3. Run `olist_ecommerce_analysis.sql` for the full analysis with inline insights.
4. Open `Olist_Ecommerce_Dashboard.pbix` in Power BI Desktop (update the MySQL connection details if needed).

## 👤 Author

**Lokanath Satapathy**
[GitHub](https://github.com/klsatapathy) · [LinkedIn](https://www.linkedin.com/in/lokanath-satapathy-9271732a2)
