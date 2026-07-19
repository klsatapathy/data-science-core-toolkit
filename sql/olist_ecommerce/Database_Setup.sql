-- ============================================================
-- OLIST E-COMMERCE ANALYTICS PROJECT
-- File: 01_schema.sql
-- Purpose: Create database and all tables
-- ============================================================

CREATE DATABASE IF NOT EXISTS olist_ecommerce;
USE olist_ecommerce;

-- Drop tables if re-running (order matters due to FK constraints)
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS order_reviews;
DROP TABLE IF EXISTS order_payments;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS geolocation;
DROP TABLE IF EXISTS product_category_translation;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS sellers;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS staging_reviews;
SET FOREIGN_KEY_CHECKS = 1;

-- ------------------------------------------------------------
-- customers
-- ------------------------------------------------------------
CREATE TABLE customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_unique_id VARCHAR(50),
    customer_zip_code_prefix VARCHAR(10),
    customer_city VARCHAR(100),
    customer_state VARCHAR(5)
);

-- ------------------------------------------------------------
-- sellers
-- ------------------------------------------------------------
CREATE TABLE sellers (
    seller_id VARCHAR(50) PRIMARY KEY,
    seller_zip_code_prefix VARCHAR(10),
    seller_city VARCHAR(100),
    seller_state VARCHAR(5)
);

-- ------------------------------------------------------------
-- products
-- ------------------------------------------------------------
CREATE TABLE products (
    product_id VARCHAR(50) PRIMARY KEY,
    product_category_name VARCHAR(100),
    product_name_lenght INT,
    product_description_lenght INT,
    product_photos_qty INT,
    product_weight_g INT,
    product_length_cm INT,
    product_height_cm INT,
    product_width_cm INT
);

-- ------------------------------------------------------------
-- product_category_translation (Portuguese -> English category names)
-- ------------------------------------------------------------
CREATE TABLE product_category_translation (
    product_category_name VARCHAR(100) PRIMARY KEY,
    product_category_name_english VARCHAR(100)
);

-- ------------------------------------------------------------
-- geolocation (zip code -> lat/lng mapping, ~1M rows)
-- ------------------------------------------------------------
CREATE TABLE geolocation (
    geolocation_zip_code_prefix VARCHAR(10),
    geolocation_lat DECIMAL(10,8),
    geolocation_lng DECIMAL(11,8),
    geolocation_city VARCHAR(100),
    geolocation_state VARCHAR(5)
);

-- ------------------------------------------------------------
-- orders
-- ------------------------------------------------------------
CREATE TABLE orders (
    order_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    order_status VARCHAR(20),
    order_purchase_timestamp DATETIME,
    order_approved_at DATETIME,
    order_delivered_carrier_date DATETIME,
    order_delivered_customer_date DATETIME,
    order_estimated_delivery_date DATETIME,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- ------------------------------------------------------------
-- order_items (line items per order)
-- ------------------------------------------------------------
CREATE TABLE order_items (
    order_id VARCHAR(50),
    order_item_id INT,
    product_id VARCHAR(50),
    seller_id VARCHAR(50),
    shipping_limit_date DATETIME,
    price DECIMAL(10,2),
    freight_value DECIMAL(10,2),
    PRIMARY KEY (order_id, order_item_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (seller_id) REFERENCES sellers(seller_id)
);

-- ------------------------------------------------------------
-- order_payments
-- ------------------------------------------------------------
CREATE TABLE order_payments (
    order_id VARCHAR(50),
    payment_sequential INT,
    payment_type VARCHAR(20),
    payment_installments INT,
    payment_value DECIMAL(10,2),
    PRIMARY KEY (order_id, payment_sequential),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- ------------------------------------------------------------
-- order_reviews (7 columns - includes creation/answer timestamps)
-- ------------------------------------------------------------
CREATE TABLE order_reviews (
    review_id VARCHAR(50),
    order_id VARCHAR(50),
    review_score INT,
    review_comment_title VARCHAR(255),
    review_comment_message TEXT,
    review_creation_date DATETIME,
    review_answer_timestamp DATETIME,
    PRIMARY KEY (review_id, order_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- ------------------------------------------------------------
-- staging_reviews (temporary text-only table used to safely
-- load the reviews CSV, which contains embedded newlines and
-- backslashes inside comment text that break simple CSV parsing)
-- ------------------------------------------------------------
CREATE TABLE staging_reviews (
    review_id TEXT,
    order_id TEXT,
    review_score TEXT,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TEXT,
    review_answer_timestamp TEXT
);


-- ============================================================
-- OLIST E-COMMERCE ANALYTICS PROJECT
-- File: 02_import_data.sql
-- Purpose: Load all CSV files into the tables created in 01_schema.sql
--
-- BEFORE RUNNING:
-- 1. Find your MySQL secure upload folder:
--       SHOW VARIABLES LIKE 'secure_file_priv';
-- 2. Copy ALL CSV files into that folder (including the
--    olist_order_reviews_cleaned.csv file - see README for why
--    the reviews file needs special handling).
-- 3. Replace the folder path below if yours is different.
-- 4. If large imports (geolocation, reviews) time out in
--    Workbench, that is usually just a CLIENT display timeout -
--    check row counts with SELECT COUNT(*) before re-running.
-- ============================================================

USE olist_ecommerce;

SET @upload_path = 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/';

-- ------------------------------------------------------------
-- 1. customers
-- ------------------------------------------------------------
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/olist_customers_dataset.csv'
INTO TABLE customers
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 ROWS;
-- Expect: 99,441 rows

-- ------------------------------------------------------------
-- 2. sellers
-- ------------------------------------------------------------
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/olist_sellers_dataset.csv'
INTO TABLE sellers
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 ROWS;
-- Expect: 3,095 rows

-- ------------------------------------------------------------
-- 3. products
-- Some numeric columns (name/description length, weight, dims)
-- are blank for a handful of products -> convert '' to NULL.
-- ------------------------------------------------------------
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/olist_products_dataset.csv'
INTO TABLE products
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(product_id, product_category_name, @name_len, @desc_len, @photos_qty, @weight, @length, @height, @width)
SET
 product_name_lenght        = NULLIF(@name_len, ''),
 product_description_lenght = NULLIF(@desc_len, ''),
 product_photos_qty         = NULLIF(@photos_qty, ''),
 product_weight_g           = NULLIF(@weight, ''),
 product_length_cm          = NULLIF(@length, ''),
 product_height_cm          = NULLIF(@height, ''),
 product_width_cm           = NULLIF(@width, '');
-- Expect: 32,951 rows

-- ------------------------------------------------------------
-- 4. product_category_translation
-- ------------------------------------------------------------
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/product_category_name_translation.csv'
INTO TABLE product_category_translation
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 ROWS;
-- Expect: 71 rows

-- ------------------------------------------------------------
-- 5. geolocation (~1M rows - largest file, may take 30-60s)
-- ------------------------------------------------------------
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/olist_geolocation_dataset.csv'
INTO TABLE geolocation
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 ROWS;
-- Expect: 1,000,163 rows

SELECT COUNT(*) AS geolocation_count FROM geolocation;

-- ------------------------------------------------------------
-- 6. orders
-- Dates in this dataset are ISO format: YYYY-MM-DD HH:MM:SS
-- Some date columns are blank (e.g. cancelled orders never
-- delivered) -> NULLIF converts '' to NULL before STR_TO_DATE.
-- ------------------------------------------------------------
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/olist_orders_dataset.csv'
INTO TABLE orders
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(order_id, customer_id, order_status,
 @purchase_ts, @approved_ts, @carrier_ts, @customer_ts, @estimated_ts)
SET
 order_purchase_timestamp      = STR_TO_DATE(NULLIF(@purchase_ts, ''), '%Y-%m-%d %H:%i:%s'),
 order_approved_at             = STR_TO_DATE(NULLIF(@approved_ts, ''), '%Y-%m-%d %H:%i:%s'),
 order_delivered_carrier_date  = STR_TO_DATE(NULLIF(@carrier_ts, ''), '%Y-%m-%d %H:%i:%s'),
 order_delivered_customer_date = STR_TO_DATE(NULLIF(@customer_ts, ''), '%Y-%m-%d %H:%i:%s'),
 order_estimated_delivery_date = STR_TO_DATE(NULLIF(@estimated_ts, ''), '%Y-%m-%d %H:%i:%s');
-- Expect: 99,441 rows

SELECT COUNT(*) AS orders_count FROM orders;

-- ------------------------------------------------------------
-- 7. order_items
-- ------------------------------------------------------------
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/olist_order_items_dataset.csv'
INTO TABLE order_items
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(order_id, order_item_id, product_id, seller_id, @ship_date, price, freight_value)
SET shipping_limit_date = STR_TO_DATE(NULLIF(@ship_date, ''), '%Y-%m-%d %H:%i:%s');
-- Expect: 112,650 rows

SELECT COUNT(*) AS order_items_count FROM order_items;

-- ------------------------------------------------------------
-- 8. order_payments
-- ------------------------------------------------------------
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/olist_order_payments_dataset.csv'
INTO TABLE order_payments
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 ROWS;
-- Expect: 103,886 rows

SELECT COUNT(*) AS order_payments_count FROM order_payments;

-- ------------------------------------------------------------
-- 9. order_reviews  (needs the CLEANED csv - see README)
--
-- WHY: the raw olist_order_reviews_dataset.csv has review
-- comments that contain embedded newlines and stray backslash
-- characters right before a closing quote. MySQL's LOAD DATA
-- parser (unlike a real CSV parser) treats '\"' as an escaped
-- quote and literal newlines as row breaks, which shifts columns
-- and throws "Row X doesn't contain data for all columns".
--
-- FIX: use olist_order_reviews_cleaned.csv (provided in this
-- repo / generated via clean_reviews.py) which has embedded
-- newlines replaced with spaces and all backslashes stripped.
-- ------------------------------------------------------------

-- Step 1: load raw cleaned CSV into a text-only staging table
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/olist_order_reviews_cleaned.csv'
INTO TABLE staging_reviews
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 ROWS;
-- Expect: 99,224 rows

SELECT COUNT(*) AS staging_reviews_count FROM staging_reviews;

-- Step 2: cast/convert into the real order_reviews table
TRUNCATE TABLE order_reviews;

INSERT INTO order_reviews
(review_id, order_id, review_score, review_comment_title, review_comment_message,
 review_creation_date, review_answer_timestamp)
SELECT
 review_id,
 order_id,
 CAST(review_score AS UNSIGNED),
 NULLIF(review_comment_title, ''),
 NULLIF(review_comment_message, ''),
 STR_TO_DATE(NULLIF(review_creation_date, ''), '%Y-%m-%d %H:%i:%s'),
 STR_TO_DATE(NULLIF(review_answer_timestamp, ''), '%Y-%m-%d %H:%i:%s')
FROM staging_reviews;
-- Expect: 99,224 rows

SELECT COUNT(*) AS order_reviews_count FROM order_reviews;

-- ------------------------------------------------------------
-- Cleanup: staging table no longer needed after this point
-- ------------------------------------------------------------
-- DROP TABLE staging_reviews;

-- ------------------------------------------------------------
-- FINAL VERIFICATION: run this to confirm every table loaded
-- ------------------------------------------------------------
SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM customers
UNION ALL SELECT 'sellers', COUNT(*) FROM sellers
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'product_category_translation', COUNT(*) FROM product_category_translation
UNION ALL SELECT 'geolocation', COUNT(*) FROM geolocation
UNION ALL SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL SELECT 'order_payments', COUNT(*) FROM order_payments
UNION ALL SELECT 'order_reviews', COUNT(*) FROM order_reviews;

