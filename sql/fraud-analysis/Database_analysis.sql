/* ============================================================================
   BANKING FRAUD ANALYTICS — SQL ANALYSIS PORTFOLIO
   ============================================================================
   Author        : Lokanath Satapathy
   Database      : MySQL 8.0 (MySQL Workbench)
   Dataset       : PaySim Synthetic Financial Fraud Detection Dataset (Kaggle)
   Objective     : Advanced fraud-pattern analysis using window functions,
                   anomaly detection, account-risk profiling, time trends,
                   and automation (views/triggers/procedures) — beyond the
                   descriptive-only style of the first 3 SQL projects.
   ============================================================================ */


/* ============================================================================
   SECTION A — FRAUD OVERVIEW & TRANSACTION TYPE PATTERNS
   ============================================================================ */

-- ----------------------------------------------------------------------------
-- A1. Fraud Count & Rate by Transaction Type
-- ----------------------------------------------------------------------------
SELECT
    tt.type_code,
    COUNT(*)                                   AS total_txn,
    SUM(t.isFraud)                              AS fraud_txn,
    ROUND(SUM(t.isFraud) * 100.0 / COUNT(*), 4) AS fraud_rate_pct
FROM transactions t
JOIN transaction_types tt ON t.type_code = tt.type_code
GROUP BY tt.type_code
ORDER BY fraud_rate_pct DESC;

-- INSIGHT A1 — TRANSFER has the highest fraud rate (0.7688%), ~4.2x higher than
-- CASH_OUT (0.1840%). CASH_IN, DEBIT, and PAYMENT never carry fraud (0%) — fraud
-- is exclusively a TRANSFER/CASH_OUT phenomenon.


-- ----------------------------------------------------------------------------
-- A2. Fraud Rate Ranking Across Types (Window Function: RANK)
-- ----------------------------------------------------------------------------
WITH type_fraud AS (
    SELECT
        tt.type_code,
        COUNT(*)             AS total_txn,
        SUM(t.isFraud)        AS fraud_txn,
        SUM(t.isFraud) * 1.0 / COUNT(*) AS fraud_rate
    FROM transactions t
    JOIN transaction_types tt ON t.type_code = tt.type_code
    GROUP BY tt.type_code
)
SELECT
    type_code,
    total_txn,
    fraud_txn,
    ROUND(fraud_rate * 100, 4) AS fraud_rate_pct,
    RANK() OVER (ORDER BY fraud_rate DESC) AS fraud_rank
FROM type_fraud
ORDER BY fraud_rank;

-- INSIGHT A2 — Ranking confirms: TRANSFER (rank 1), CASH_OUT (rank 2), then a
-- 3-way tie at rank 3 for CASH_IN/DEBIT/PAYMENT, all at 0% fraud.


-- ----------------------------------------------------------------------------
-- A3. Transaction Amount Bucketed by Fraud (CASE Bucketing)
-- ----------------------------------------------------------------------------
SELECT
    CASE
        WHEN amount < 10000  THEN '0-10K'
        WHEN amount < 100000 THEN '10K-100K'
        WHEN amount < 1000000 THEN '100K-1M'
        ELSE '1M+'
    END AS amount_bucket,
    COUNT(*)                                    AS total_txn,
    SUM(isFraud)                                 AS fraud_txn,
    ROUND(SUM(isFraud) * 100.0 / COUNT(*), 4)    AS fraud_rate_pct
FROM transactions
GROUP BY amount_bucket
ORDER BY MIN(amount);

-- INSIGHT A3 — Fraud rate rises sharply with amount: 0.0216% (0-10K) ->
-- 0.0638% (10K-100K) -> 0.1404% (100K-1M) -> 2.0716% (1M+). The 1M+ bucket has
-- a ~96x higher fraud rate than the smallest bucket — fraud clearly skews
-- toward high-value transactions.


/* ============================================================================
   SECTION B — BALANCE RECONCILIATION & ANOMALY DETECTION
   ============================================================================ */

-- ----------------------------------------------------------------------------
-- B1. Origin Balance Reconciliation Error (CTE) — Fraud vs Legit
-- ----------------------------------------------------------------------------
WITH balance_check AS (
    SELECT
        transaction_id,
        isFraud,
        (newbalanceOrig + amount - oldbalanceOrg) AS error_balance_orig
    FROM transactions
    WHERE type_code IN ('TRANSFER', 'CASH_OUT')
)
SELECT
    isFraud,
    ROUND(AVG(error_balance_orig), 2) AS avg_error_balance,
    ROUND(STDDEV(error_balance_orig), 2) AS stddev_error_balance
FROM balance_check
GROUP BY isFraud;

-- INSIGHT B1 — Counter-intuitive result: legitimate transactions actually show
-- a HIGHER average balance error (286,803.51) than fraud ones (10,692.33).
-- Fraud transactions reconcile almost perfectly, while legit ones carry more
-- natural noise — likely rounding/partial-payment behavior. Balance error
-- alone is not a reliable standalone fraud flag.


-- ----------------------------------------------------------------------------
-- B2. Full Account Drain Detection (Origin Emptied to Zero)
-- ----------------------------------------------------------------------------
SELECT
    isFraud,
    COUNT(*) AS total_txn,
    SUM(CASE WHEN oldbalanceOrg > 0 AND newbalanceOrig = 0 THEN 1 ELSE 0 END) AS full_drain_txn,
    ROUND(SUM(CASE WHEN oldbalanceOrg > 0 AND newbalanceOrig = 0 THEN 1 ELSE 0 END)
          * 100.0 / COUNT(*), 2) AS full_drain_pct
FROM transactions
WHERE type_code IN ('TRANSFER', 'CASH_OUT')
GROUP BY isFraud;

-- INSIGHT B2 — Full account drain is a strong signal: 97.55% of fraud
-- transactions fully empty the origin account vs only 42.72% of legit ones —
-- more than double the rate.


-- ----------------------------------------------------------------------------
-- B3. Amount Percentile Ranking Within Type (Window Function: PERCENT_RANK)
-- ----------------------------------------------------------------------------
SELECT
    transaction_id,
    type_code,
    amount,
    isFraud,
    ROUND(PERCENT_RANK() OVER (PARTITION BY type_code ORDER BY amount), 4) AS amount_percentile
FROM transactions
WHERE type_code IN ('TRANSFER', 'CASH_OUT')
ORDER BY amount_percentile DESC
LIMIT 20;

-- INSIGHT B3 — Top-percentile transactions are dominated by CASH_OUT at
-- exactly 10,000,000, almost all fraud. But a few very large TRANSFERs
-- (57M, 62M) are legitimate — extreme amount alone isn't a clean fraud
-- signal for the TRANSFER type specifically.


/* ============================================================================
   SECTION C — ACCOUNT-LEVEL RISK PROFILING
   ============================================================================ */

-- ----------------------------------------------------------------------------
-- C1. Top Destination Accounts by Fraudulent Amount Received (Window: RANK)
-- ----------------------------------------------------------------------------
WITH dest_fraud AS (
    SELECT
        nameDest,
        COUNT(*)      AS fraud_txn_count,
        SUM(amount)   AS total_fraud_amount
    FROM transactions
    WHERE isFraud = 1
    GROUP BY nameDest
)
SELECT
    nameDest,
    fraud_txn_count,
    total_fraud_amount,
    RANK() OVER (ORDER BY total_fraud_amount DESC) AS risk_rank
FROM dest_fraud
ORDER BY risk_rank
LIMIT 15;

-- INSIGHT C1 — Fraud amount is spread thin, not concentrated: nearly every
-- top-15 destination account received just 1 fraud transaction of exactly
-- 10,000,000. Only C668046170 stands out with 2 fraud transactions — no
-- single account dominates.


-- ----------------------------------------------------------------------------
-- C2. Origin Account Transaction Velocity (Window Function: LAG)
-- ----------------------------------------------------------------------------
WITH origin_activity AS (
    SELECT
        transaction_id,
        nameOrig,
        step,
        isFraud,
        LAG(step) OVER (PARTITION BY nameOrig ORDER BY step) AS prev_step
    FROM transactions
    WHERE type_code IN ('TRANSFER', 'CASH_OUT')
)
SELECT
    nameOrig,
    transaction_id,
    step,
    prev_step,
    (step - prev_step) AS steps_since_last_txn,
    isFraud
FROM origin_activity
WHERE prev_step IS NOT NULL
ORDER BY steps_since_last_txn ASC
LIMIT 20;

-- INSIGHT C2 — The fastest repeat-transaction accounts (0-1 step gap) show
-- zero fraud in this sample — rapid-fire velocity did NOT surface fraud
-- cases here, so this signal is weaker than expected for this dataset.


-- ----------------------------------------------------------------------------
-- C3. Account Risk Score (Stored Procedure)
-- ----------------------------------------------------------------------------
DELIMITER $$

CREATE PROCEDURE get_account_risk_score(IN acct VARCHAR(30))
BEGIN
    SELECT
        nameOrig,
        COUNT(*) AS total_txn,
        SUM(isFraud) AS fraud_txn,
        ROUND(SUM(isFraud) * 100.0 / COUNT(*), 2) AS fraud_rate_pct,
        ROUND(AVG(amount), 2) AS avg_amount
    FROM transactions
    WHERE nameOrig = acct
    GROUP BY nameOrig;
END$$

DELIMITER ;

-- Usage: CALL get_account_risk_score('C1231006815');

-- INSIGHT C3 — Spot-checked account C1044884182 (from the velocity check):
-- only 2 total transactions, 0 fraud, avg amount 412,254.93 — an ordinary
-- low-activity account, no red flags.


/* ============================================================================
   SECTION D — TIME-BASED FRAUD TRENDS
   ============================================================================ */

-- ----------------------------------------------------------------------------
-- D1. Hourly Transaction Volume vs Fraud Count
-- ----------------------------------------------------------------------------
SELECT
    step,
    COUNT(*)      AS total_txn,
    SUM(isFraud)  AS fraud_txn
FROM transactions
GROUP BY step
ORDER BY step;

-- INSIGHT D1 — Fraud count per hour is fairly steady (mean ~11/hour, min 0,
-- max 40) despite total transaction volume swinging widely (2 to ~51K/hour) —
-- fraud volume doesn't scale with overall traffic.


-- ----------------------------------------------------------------------------
-- D2. Step-over-Step Fraud Growth % (Window Function: LAG)
-- ----------------------------------------------------------------------------
WITH hourly_fraud AS (
    SELECT
        step,
        SUM(isFraud) AS fraud_txn
    FROM transactions
    GROUP BY step
)
SELECT
    step,
    fraud_txn,
    LAG(fraud_txn) OVER (ORDER BY step) AS prev_fraud_txn,
    ROUND(
        (fraud_txn - LAG(fraud_txn) OVER (ORDER BY step)) * 100.0
        / NULLIF(LAG(fraud_txn) OVER (ORDER BY step), 0), 2
    ) AS fraud_growth_pct
FROM hourly_fraud
ORDER BY step;

-- INSIGHT D2 — Biggest fraud growth spikes (500-600%) all come from very
-- small bases (e.g. 2->14, 4->28 transactions) — statistical noise from low
-- absolute counts, not genuine surges.


-- ----------------------------------------------------------------------------
-- D3. Day-Level Fraud Concentration (step -> day bucket)
-- ----------------------------------------------------------------------------
SELECT
    FLOOR(step / 24) + 1 AS day_number,
    COUNT(*)              AS total_txn,
    SUM(isFraud)           AS fraud_txn,
    ROUND(SUM(isFraud) * 100.0 / COUNT(*), 4) AS fraud_rate_pct
FROM transactions
GROUP BY day_number
ORDER BY day_number;

-- INSIGHT D3 — Day 31 shows a 100% fraud rate (282/282 transactions) — a
-- simulation-tail artifact (the 30-day/720-step window overflows into a
-- partial day of leftover fraud-test transactions), not a real business
-- pattern. Excluding that edge day, day 3 (4.53%) and day 19 (2.14%) are the
-- next-highest genuine fraud-rate days.


/* ============================================================================
   SECTION E — SYSTEM FLAG PERFORMANCE & AUTOMATION
   ============================================================================ */

-- ----------------------------------------------------------------------------
-- E1. isFlaggedFraud vs isFraud — System Detection Confusion Matrix
-- ----------------------------------------------------------------------------
SELECT
    isFraud,
    isFlaggedFraud,
    COUNT(*) AS txn_count
FROM transactions
GROUP BY isFraud, isFlaggedFraud
ORDER BY isFraud DESC, isFlaggedFraud DESC;

-- INSIGHT E1 — isFlaggedFraud is almost useless as a detector: it catches
-- only 16 out of 8,213 true fraud cases — a 0.19% recall rate. A system
-- relying on this flag alone would miss over 99.8% of fraud.


-- ----------------------------------------------------------------------------
-- E2. High-Risk Transaction View (Reusable for Reporting/BI)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_high_risk_transactions AS
SELECT
    transaction_id,
    step,
    type_code,
    amount,
    nameOrig,
    nameDest,
    isFraud,
    isFlaggedFraud
FROM transactions
WHERE type_code IN ('TRANSFER', 'CASH_OUT')
  AND oldbalanceOrg > 0
  AND newbalanceOrig = 0
  AND amount > 200000;

-- Usage: SELECT * FROM v_high_risk_transactions ORDER BY amount DESC LIMIT 20;

-- INSIGHT E2 — The simple high-risk rule (TRANSFER/CASH_OUT + full drain +
-- amount > 200000) flags 606,363 transactions, but only 5,297 (0.87%) are
-- actually fraud — high recall potential but very low precision as a
-- standalone rule; needs tightening (e.g. combine with the B3 percentile
-- signal) before real use.


-- ----------------------------------------------------------------------------
-- E3. Auto-Flag Trigger for New High-Risk Transactions
-- ----------------------------------------------------------------------------
DELIMITER $$

CREATE TRIGGER trg_flag_high_risk_txn
BEFORE INSERT ON transactions
FOR EACH ROW
BEGIN
    IF NEW.type_code IN ('TRANSFER', 'CASH_OUT')
       AND NEW.oldbalanceOrg > 0
       AND NEW.newbalanceOrig = 0
       AND NEW.amount > 200000 THEN
        SET NEW.isFlaggedFraud = 1;
    END IF;
END$$

DELIMITER ;

-- INSIGHT E3 — [Note: this trigger only fires on new inserts, not the
-- already-loaded 6.3M rows — mention in README that it's a forward-looking
-- automation layer, not a retroactive fix for E2's view.]


/* ============================================================================
   END OF SCRIPT — ADVANCED SQL FRAUD ANALYTICS
   ============================================================================
   A. Fraud Overview & Type Patterns   -> Insights A1, A2, A3
   B. Balance Reconciliation & Anomaly -> Insights B1, B2, B3
   C. Account-Level Risk Profiling     -> Insights C1, C2, C3
   D. Time-Based Fraud Trends          -> Insights D1, D2, D3
   E. System Flag & Automation         -> Insights E1, E2, E3
   ============================================================================ */
