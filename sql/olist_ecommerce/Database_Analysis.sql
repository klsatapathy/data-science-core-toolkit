/* ============================================================================
   OLIST BRAZILIAN E-COMMERCE — SQL ANALYSIS PORTFOLIO
   ============================================================================
   Author        : [Lokanath Satapathy]
   Database      : MySQL 8.0 (MySQL Workbench)
   Dataset       : Olist Brazilian E-Commerce Public Dataset (9 tables)
   Objective     : End-to-end business analysis covering revenue, product
                   performance, customer segmentation, retention, and
                   operations (delivery + payments).

   STRUCTURE
   ---------
   SECTION A — Revenue & Growth Trends
   SECTION B — Product Performance
   SECTION C — Customer Segmentation (RFM Analysis)
   SECTION D — Customer Retention (Cohort Analysis)
   SECTION E — Operations (Delivery & Payments)
   ============================================================================ */


/* ============================================================================
   SECTION A — REVENUE & GROWTH TRENDS
   ============================================================================ */

-- ----------------------------------------------------------------------------
-- A1. Monthly Revenue & Order Volume Trend
-- ----------------------------------------------------------------------------
SELECT 
    DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS order_month,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(oi.price + oi.freight_value), 2) AS total_revenue
FROM orders o
JOIN order_items oi 
    ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY order_month
ORDER BY order_month;

/* INSIGHT A1 — Platform Growth Trajectory
   Orders grew from ~750/month in Jan 2017 to a stable ~6,000-7,000/month
   range by 2018, indicating a platform that scaled through 2017 and
   matured by 2018. Data before Jan 2017 (Sep/Oct/Dec 2016, <300 orders)
   reflects a pilot/launch phase and is excluded from growth commentary
   to avoid distorted percentage swings. */


-- ----------------------------------------------------------------------------
-- A2. Month-over-Month Revenue Growth % (Window Function: LAG)
-- ----------------------------------------------------------------------------
WITH monthly_revenue AS (
    SELECT 
        DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS order_month,
        COUNT(DISTINCT o.order_id) AS total_orders,
        ROUND(SUM(oi.price + oi.freight_value), 2) AS total_revenue
    FROM orders o
    JOIN order_items oi 
        ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY order_month
)
SELECT 
    order_month,
    total_orders,
    total_revenue,
    LAG(total_revenue) OVER (ORDER BY order_month) AS prev_month_revenue,
    ROUND(
        (total_revenue - LAG(total_revenue) OVER (ORDER BY order_month)) 
        / LAG(total_revenue) OVER (ORDER BY order_month) * 100, 
        2
    ) AS mom_growth_pct
FROM monthly_revenue
ORDER BY order_month;

/* INSIGHT A2 — Seasonal Spike & Post-Peak Cooldown
   November 2017 shows a +53.55% MoM revenue jump — aligning with
   Brazil's Black Friday, one of the country's biggest e-commerce
   events. This is followed by a -26.90% drop in December 2017, a
   classic "demand pull-forward" pattern where post-sale demand
   temporarily contracts. From mid-2018 onward, growth flattens into a
   +/-10% oscillation band, suggesting market maturity (with the caveat
   that the Olist dataset is known to have incomplete records after
   Sep 2018). Recommendation: scale inventory/logistics capacity ahead
   of Q4 seasonal demand. */


/* ============================================================================
   SECTION B — PRODUCT PERFORMANCE
   ============================================================================ */

-- ----------------------------------------------------------------------------
-- B1. Top Product Categories by Revenue (Window Function: RANK)
-- ----------------------------------------------------------------------------
SELECT 
    p.product_category_name,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    SUM(oi.price) AS total_revenue,
    ROUND(AVG(oi.price), 2) AS avg_price_per_item,
    RANK() OVER (ORDER BY SUM(oi.price) DESC) AS revenue_rank
FROM order_items oi
JOIN products p 
    ON oi.product_id = p.product_id
JOIN orders o 
    ON oi.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY p.product_category_name
ORDER BY total_revenue DESC
LIMIT 15;

/* INSIGHT B1 — High-Margin vs High-Volume Categories
   Health & Beauty (beleza_saude) leads in total revenue despite fewer
   orders than Bed/Bath/Table (cama_mesa_banho), because its average
   price (₹130) is significantly higher. Watches & Gifts
   (relogios_presentes) has the highest average price in the top 5
   (₹199) — a classic high-ticket "gifting" category. Bed/Bath/Table
   is the clearest volume-driven, lower-margin category (highest order
   count, rank #3 in revenue). Recommendation: prioritize marketing
   spend on high-margin categories (Health & Beauty, Watches/Gifts) and
   explore bundling strategies for high-volume/low-AOV categories to
   lift average order value. */


/* ============================================================================
   SECTION C — CUSTOMER SEGMENTATION (RFM ANALYSIS)
   ============================================================================ */

-- ----------------------------------------------------------------------------
-- C1. Customer-Level RFM Scoring & Segmentation
-- ----------------------------------------------------------------------------
WITH customer_rfm AS (
    SELECT 
        c.customer_unique_id,
        DATEDIFF(
            (SELECT MAX(order_purchase_timestamp) FROM orders), 
            MAX(o.order_purchase_timestamp)
        ) AS recency_days,
        COUNT(DISTINCT o.order_id) AS frequency,
        ROUND(SUM(oi.price + oi.freight_value), 2) AS monetary
    FROM orders o
    JOIN customers c 
        ON o.customer_id = c.customer_id
    JOIN order_items oi 
        ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),
rfm_scores AS (
    SELECT 
        customer_unique_id,
        recency_days,
        frequency,
        monetary,
        NTILE(4) OVER (ORDER BY recency_days DESC) AS r_score,
        NTILE(4) OVER (ORDER BY frequency ASC) AS f_score,
        NTILE(4) OVER (ORDER BY monetary ASC) AS m_score
    FROM customer_rfm
),
rfm_segments AS (
    SELECT 
        *,
        CASE 
            WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Champions'
            WHEN r_score >= 3 AND f_score >= 2 THEN 'Loyal Customers'
            WHEN r_score >= 3 AND f_score = 1 THEN 'Recent Customers'
            WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
            WHEN r_score = 1 AND f_score = 1 AND m_score >= 3 THEN 'Cant Lose Them'
            ELSE 'Others'
        END AS customer_segment
    FROM rfm_scores
)
SELECT 
    customer_segment,
    COUNT(*) AS num_customers,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_of_total,
    ROUND(AVG(monetary), 2) AS avg_monetary,
    ROUND(AVG(frequency), 2) AS avg_frequency,
    ROUND(AVG(recency_days), 0) AS avg_recency_days
FROM rfm_segments
GROUP BY customer_segment
ORDER BY num_customers DESC;

/* INSIGHT C1 — The Pareto Effect
   Champions make up only 8.45% of customers but have the highest
   average spend (₹268) of any segment — a textbook 80/20 pattern
   where a small base drives disproportionate value.

   INSIGHT C2 — At-Risk Segment = Biggest Revenue Leakage
   "At Risk" is the LARGEST segment at 33.96% of the customer base,
   with an average recency of 365 days (i.e., no purchase in a year).
   With 31,700+ customers averaging ₹166 in past spend, this segment
   represents the single largest win-back opportunity on the platform.

   INSIGHT C3 — Repeat Purchase Behavior Is Weak Platform-Wide
   Average frequency is ~1.0 across almost every segment (even
   Champions average only 1.20) — confirming that most customers,
   regardless of segment, purchase only once.


/* ============================================================================
   SECTION D — CUSTOMER RETENTION (COHORT ANALYSIS)
   ============================================================================ */

-- ----------------------------------------------------------------------------
-- D1. Monthly Cohort Retention (Window Functions: MIN OVER, TIMESTAMPDIFF)
-- ----------------------------------------------------------------------------
WITH customer_orders AS (
    SELECT 
        c.customer_unique_id,
        o.order_id,
        DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m-01') AS order_month
    FROM orders o
    JOIN customers c 
        ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
),
customer_cohort AS (
    SELECT 
        customer_unique_id,
        order_id,
        order_month,
        MIN(order_month) OVER (PARTITION BY customer_unique_id) AS cohort_month
    FROM customer_orders
),
cohort_data AS (
    SELECT 
        cohort_month,
        customer_unique_id,
        TIMESTAMPDIFF(MONTH, cohort_month, order_month) AS month_number
    FROM customer_cohort
),
cohort_size AS (
    SELECT 
        cohort_month,
        COUNT(DISTINCT customer_unique_id) AS total_customers
    FROM cohort_data
    WHERE month_number = 0
    GROUP BY cohort_month
)
SELECT 
    cd.cohort_month,
    cs.total_customers AS cohort_size,
    cd.month_number,
    COUNT(DISTINCT cd.customer_unique_id) AS retained_customers,
    ROUND(
        COUNT(DISTINCT cd.customer_unique_id) * 100.0 / cs.total_customers, 
        2
    ) AS retention_pct
FROM cohort_data cd
JOIN cohort_size cs 
    ON cd.cohort_month = cs.cohort_month
GROUP BY cd.cohort_month, cs.total_customers, cd.month_number
ORDER BY cd.cohort_month, cd.month_number;

/* INSIGHT D1 — Near-Zero Month-1 Retention Across Every Cohort
   Every acquisition cohort from 2017-2018 shows Month-1 retention
   below 1% (e.g., Nov 2017 Black Friday cohort: 0.57%; Jan 2018:
   0.34%) — collapsing from 100% at Month 0 straight to under 1% at
   Month 1, with no gradual decline. This is a cliff, not a curve.

   INSIGHT D2 — The Issue Is Systemic, Not a One-Time Fluke
   Cohort size grew steadily (750 → 7,060 customers/month through
   2017), proving the acquisition engine worked — but retention never
   improved across any cohort, indicating a structural, platform-wide
   retention gap rather than a seasonal or one-off issue.

   INSIGHT D3 — Cross-Validated by RFM
   This finding independently confirms the ~1.0 average frequency seen
   across all RFM segments in Section C — two separate analytical
   methods arriving at the same conclusion strengthens the finding.

   Recommendation: Olist operates largely as a one-time-purchase
   marketplace. A portion of acquisition budget should shift toward
   post-purchase retention mechanisms (email re-engagement, loyalty
   incentives), particularly aimed at the "At Risk" segment (33.96% of
   customers) identified in Section C. */


/* ============================================================================
   SECTION E — OPERATIONS (DELIVERY & PAYMENTS)
   ============================================================================ */

-- ----------------------------------------------------------------------------
-- E1. Delivery Timeliness vs Review Score
-- ----------------------------------------------------------------------------
WITH delivery_analysis AS (
    SELECT 
        o.order_id,
        DATEDIFF(o.order_delivered_customer_date, o.order_purchase_timestamp) AS actual_delivery_days,
        DATEDIFF(o.order_estimated_delivery_date, o.order_delivered_customer_date) AS days_early_or_late,
        r.review_score
    FROM orders o
    JOIN order_reviews r 
        ON o.order_id = r.order_id
    WHERE o.order_status = 'delivered'
        AND o.order_delivered_customer_date IS NOT NULL
),
delivery_buckets AS (
    SELECT 
        *,
        CASE 
            WHEN days_early_or_late < 0 THEN 'Late Delivery'
            WHEN days_early_or_late >= 0 AND days_early_or_late <= 5 THEN 'On-Time (0-5 days early)'
            ELSE 'Very Early (5+ days early)'
        END AS delivery_status
    FROM delivery_analysis
)
SELECT 
    delivery_status,
    COUNT(*) AS total_orders,
    ROUND(AVG(review_score), 2) AS avg_review_score,
    ROUND(AVG(actual_delivery_days), 1) AS avg_delivery_days,
    SUM(CASE WHEN review_score <= 2 THEN 1 ELSE 0 END) AS bad_reviews_count,
    ROUND(SUM(CASE WHEN review_score <= 2 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS bad_review_pct
FROM delivery_buckets
GROUP BY delivery_status
ORDER BY avg_review_score DESC;

/* INSIGHT E1 — Late Delivery Nearly Halves Review Scores
   Average review score drops from 4.31 (very early deliveries) to
   just 2.27 (late deliveries) — a ~47% decline. Late deliveries carry
   a 62.41% negative-review rate (score <=2), roughly 7x higher than
   very-early deliveries (9.02%). Late orders also average 33.8 days
   to deliver vs 10.4 days for very-early orders — nearly 3x longer,
   suggesting these are not minor delays but systemic logistics
   failures affecting a specific subset of orders.
   Recommendation: audit sellers/carriers/routes responsible for
   extreme delays — fixing this tail could meaningfully lift
   platform-wide satisfaction. */


-- ----------------------------------------------------------------------------
-- E2. Delivery Performance by State (Geographic Analysis)
-- ----------------------------------------------------------------------------
WITH delivery_by_state AS (
    SELECT 
        c.customer_state,
        o.order_id,
        DATEDIFF(o.order_delivered_customer_date, o.order_purchase_timestamp) AS actual_delivery_days,
        DATEDIFF(o.order_estimated_delivery_date, o.order_delivered_customer_date) AS days_early_or_late,
        r.review_score
    FROM orders o
    JOIN customers c 
        ON o.customer_id = c.customer_id
    JOIN order_reviews r 
        ON o.order_id = r.order_id
    WHERE o.order_status = 'delivered'
        AND o.order_delivered_customer_date IS NOT NULL
)
SELECT 
    customer_state,
    COUNT(*) AS total_orders,
    ROUND(AVG(actual_delivery_days), 1) AS avg_delivery_days,
    ROUND(AVG(days_early_or_late), 1) AS avg_days_early_or_late,
    ROUND(AVG(review_score), 2) AS avg_review_score,
    SUM(CASE WHEN days_early_or_late < 0 THEN 1 ELSE 0 END) AS late_orders,
    ROUND(SUM(CASE WHEN days_early_or_late < 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS late_pct
FROM delivery_by_state
GROUP BY customer_state
HAVING COUNT(*) >= 100
ORDER BY avg_delivery_days DESC
LIMIT 15;

/* INSIGHT E2 — North/Northeast Brazil Is a Logistics Bottleneck
   The slowest-delivery states are almost entirely North/Northeast
   Brazil: Amazonas (AM, 26.2 days), Alagoas (AL, 24.4), Pará (PA,
   23.6), Sergipe (SE, 21.4), Maranhão (MA, 21.3) — 2-3x longer than
   the national logistics benchmark dominated by Southeast states.
   This reflects Brazil's well-documented Southeast/North-Northeast
   infrastructure gap. Notably, Amazonas has a very low late-delivery
   rate (2.76%) despite the longest average delivery time, indicating
   estimated delivery dates are pre-adjusted to avoid "late" flags —
   masking a genuinely slow customer experience.
   Recommendation: explore regional fulfillment partnerships in
   North/Northeast states, or set clearer delivery-time expectations
   at checkout for these regions. */


-- ----------------------------------------------------------------------------
-- E3. Payment Method Behavior & Satisfaction
-- ----------------------------------------------------------------------------
WITH payment_analysis AS (
    SELECT 
        op.payment_type,
        op.payment_installments,
        op.payment_value,
        o.order_id,
        r.review_score
    FROM order_payments op
    JOIN orders o 
        ON op.order_id = o.order_id
    JOIN order_reviews r 
        ON o.order_id = r.order_id
    WHERE o.order_status = 'delivered'
)
SELECT 
    payment_type,
    COUNT(*) AS total_orders,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_of_orders,
    ROUND(AVG(payment_value), 2) AS avg_order_value,
    ROUND(AVG(payment_installments), 1) AS avg_installments,
    ROUND(AVG(review_score), 2) AS avg_review_score
FROM payment_analysis
GROUP BY payment_type
ORDER BY total_orders DESC;

-- Bonus: Installments vs Average Order Value (credit card only)
SELECT 
    payment_installments,
    COUNT(*) AS total_orders,
    ROUND(AVG(payment_value), 2) AS avg_order_value
FROM order_payments
WHERE payment_type = 'credit_card'
GROUP BY payment_installments
ORDER BY payment_installments;

/* INSIGHT E3 — Credit Card Dominates; Installments Scale With Order Value
   Credit card accounts for 74% of all orders, followed by boleto
   (bank slip, 19%) — a notable share for an offline/manual payment
   method, likely reflecting Brazil's unbanked/underbanked population.
   Review scores are nearly identical across all payment types
   (4.11-4.24), confirming payment method has no meaningful effect on
   satisfaction.

   INSIGHT E4 — Installments Are a Purchasing Enabler for High-Ticket Items
   Average order value rises consistently with installment count:
   ₹95.87 at 1 installment vs ₹183.47 at 5 installments — nearly
   double. This confirms installments function as an affordability
   mechanism for bigger purchases, directly relevant to the
   high-average-price categories identified in Section B (Watches &
   Gifts, Office Furniture).
   Recommendation: promote installment options prominently (e.g.,
   "no-interest up to 6x") for high-ticket categories to maximize
   conversion. */


/* ============================================================================
   END OF SCRIPT — 15 BUSINESS INSIGHTS ACROSS 5 ANALYTICAL AREAS
   ============================================================================
   A. Revenue & Growth        -> Insights A1, A2 (+ seasonal spike)
   B. Product Performance     -> Insight B1
   C. RFM Segmentation        -> Insights C1, C2, C3
   D. Cohort Retention        -> Insights D1, D2, D3
   E. Operations              -> Insights E1, E2, E3, E4
   ============================================================================ */