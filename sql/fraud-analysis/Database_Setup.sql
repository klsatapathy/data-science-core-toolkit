-- ============================================================
-- BANKING FRAUD ANALYTICS PROJECT (PaySim Dataset)
-- File: 01_schema.sql
-- Purpose: Create database and all tables
-- ============================================================

CREATE DATABASE IF NOT EXISTS banking_fraud_analytics;
USE banking_fraud_analytics;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS staging_transactions;
DROP TABLE IF EXISTS transaction_types;
SET FOREIGN_KEY_CHECKS = 1;

-- ------------------------------------------------------------
-- transaction_types (lookup for CASH-IN, CASH-OUT, DEBIT, PAYMENT, TRANSFER)
-- ------------------------------------------------------------
CREATE TABLE transaction_types (
    type_code VARCHAR(20) PRIMARY KEY,
    type_description VARCHAR(100)
);

-- ------------------------------------------------------------
-- staging_transactions (temporary text-only table used to safely
-- load the raw CSV before casting numeric/flag columns)
-- ------------------------------------------------------------
CREATE TABLE staging_transactions (
    step TEXT,
    type TEXT,
    amount TEXT,
    nameOrig TEXT,
    oldbalanceOrg TEXT,
    newbalanceOrig TEXT,
    nameDest TEXT,
    oldbalanceDest TEXT,
    newbalanceDest TEXT,
    isFraud TEXT,
    isFlaggedFraud TEXT
);

-- ------------------------------------------------------------
-- transactions (main fact table, ~6.3M rows)
-- ------------------------------------------------------------
CREATE TABLE transactions (
    transaction_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    step INT,
    type_code VARCHAR(20),
    amount DECIMAL(15,2),
    nameOrig VARCHAR(30),
    oldbalanceOrg DECIMAL(15,2),
    newbalanceOrig DECIMAL(15,2),
    nameDest VARCHAR(30),
    oldbalanceDest DECIMAL(15,2),
    newbalanceDest DECIMAL(15,2),
    isFraud TINYINT,
    isFlaggedFraud TINYINT,
    FOREIGN KEY (type_code) REFERENCES transaction_types(type_code)
);


-- ============================================================
-- BANKING FRAUD ANALYTICS PROJECT (PaySim Dataset)
-- File: 02_import_data.sql
-- Purpose: Load the CSV into staging, then cast into transactions
--
-- BEFORE RUNNING:
-- 1. Find your MySQL secure upload folder:
--       SHOW VARIABLES LIKE 'secure_file_priv';
-- 2. Copy the PaySim CSV into that folder.
-- 3. Replace the file name below with your actual downloaded
--    file name (Kaggle sometimes names it differently, e.g.
--    Synthetic_Financial_datasets_log.csv).
-- ------------------------------------------------------------

USE banking_fraud_analytics;

-- ------------------------------------------------------------
-- 1. transaction_types (static lookup, 5 rows)
-- ------------------------------------------------------------
INSERT INTO transaction_types (type_code, type_description) VALUES
('CASH_IN', 'Cash deposited into account'),
('CASH_OUT', 'Cash withdrawn from account'),
('DEBIT', 'Debit transaction'),
('PAYMENT', 'Payment made from account'),
('TRANSFER', 'Transfer to another account');

-- ------------------------------------------------------------
-- 2. staging_transactions (raw CSV load, ~6.3M rows)
-- ------------------------------------------------------------
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/Synthetic_Financial_datasets_log.csv'
INTO TABLE staging_transactions
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 ROWS;
-- Expect: ~6,362,620 rows

SELECT COUNT(*) AS staging_transactions_count FROM staging_transactions;

-- ------------------------------------------------------------
-- 3. cast/convert into the real transactions table
-- ------------------------------------------------------------
INSERT INTO transactions
(step, type_code, amount, nameOrig, oldbalanceOrg, newbalanceOrig,
 nameDest, oldbalanceDest, newbalanceDest, isFraud, isFlaggedFraud)
SELECT
 CAST(step AS UNSIGNED),
 REPLACE(type, '-', '_'),
 CAST(amount AS DECIMAL(15,2)),
 nameOrig,
 CAST(oldbalanceOrg AS DECIMAL(15,2)),
 CAST(newbalanceOrig AS DECIMAL(15,2)),
 nameDest,
 CAST(oldbalanceDest AS DECIMAL(15,2)),
 CAST(newbalanceDest AS DECIMAL(15,2)),
 CAST(isFraud AS UNSIGNED),
 CAST(isFlaggedFraud AS UNSIGNED)
FROM staging_transactions;
-- Expect: ~6,362,620 rows

SELECT COUNT(*) AS transactions_count FROM transactions;

-- ------------------------------------------------------------
-- Cleanup: staging table no longer needed after this point
-- ------------------------------------------------------------
-- DROP TABLE staging_transactions;

-- ------------------------------------------------------------
-- FINAL VERIFICATION
-- ------------------------------------------------------------
SELECT 'transaction_types' AS table_name, COUNT(*) AS row_count FROM transaction_types
UNION ALL SELECT 'transactions', COUNT(*) FROM transactions;
