-- ============================================================
-- SWIGGY / ZOMATO FOOD DELIVERY ANALYTICS PROJECT
-- File: Database_setup.sql
-- Purpose: Create database, staging + final tables, load & clean data
-- Source CSVs (Kaggle):
--   users.csv, restaurant.csv, orders.csv, food.csv, menu.csv
--   Zomato_Dataset.csv
-- ============================================================
CREATE DATABASE swiggy_zomato_analytics;
USE swiggy_zomato_analytics;

-- ============================================================
-- STAGING TABLES
-- ============================================================

CREATE TABLE staging_users (
    row_idx        INT,
    user_id        INT,
    name           VARCHAR(100),
    email          VARCHAR(150),
    password       VARCHAR(50),
    age            INT,
    gender         VARCHAR(10),
    marital_status VARCHAR(20),
    occupation     VARCHAR(50),
    monthly_income VARCHAR(30),
    educational_qualifications VARCHAR(50),
    family_size    INT
);

CREATE TABLE staging_restaurant (
    row_idx      INT,
    id           BIGINT,
    name         VARCHAR(200),
    city         VARCHAR(100),
    rating       VARCHAR(10),     -- '--' for missing, keep as text
    rating_count VARCHAR(30),     -- 'Too Few Ratings' / '50+ ratings'
    cost         VARCHAR(20),     -- '₹ 200' style text
    cuisine      VARCHAR(300),    -- comma separated, multi-valued
    lic_no       VARCHAR(50),
    link         VARCHAR(500),
    address      VARCHAR(500),
    menu_json    VARCHAR(100)
);

CREATE TABLE staging_food (
    row_idx        INT,
    f_id           VARCHAR(20),
    item           VARCHAR(200),
    veg_or_non_veg VARCHAR(20)
);

CREATE TABLE staging_menu (
    row_idx  INT,
    menu_id  VARCHAR(20),
    r_id     BIGINT,
    f_id     VARCHAR(20),
    cuisine  VARCHAR(300),
    price    DECIMAL(10,2)
);

CREATE TABLE staging_orders (
    row_idx     INT,
    order_date  VARCHAR(20),
    sales_qty   INT,
    sales_amount DECIMAL(12,2),
    currency    VARCHAR(10),
    user_id     INT,
    r_id        VARCHAR(20)   -- text, because some rows carry '567335.0'
);
DROP TABLE staging_delivery;
CREATE TABLE staging_delivery (
    id                          VARCHAR(20),
    delivery_person_id          VARCHAR(30),
    delivery_person_age         INT,
    delivery_person_ratings     DECIMAL(2,1),
    restaurant_latitude         DECIMAL(10,6),
    restaurant_longitude        DECIMAL(10,6),
    delivery_location_latitude  DECIMAL(10,6),
    delivery_location_longitude DECIMAL(10,6),
    order_date                  VARCHAR(20),
    time_orderd                 VARCHAR(20),
    time_order_picked           VARCHAR(20),
    weather_conditions          VARCHAR(30),
    road_traffic_density        VARCHAR(20),
    vehicle_condition           INT,
    type_of_order                VARCHAR(30),
    type_of_vehicle             VARCHAR(30),
    multiple_deliveries         INT,
    festival                    VARCHAR(10),
    city                        VARCHAR(30),
    time_taken_min              INT
);

-- ============================================================
-- FINAL NORMALIZED TABLES
-- ============================================================

CREATE TABLE customers (
    customer_id    INT PRIMARY KEY,
    name           VARCHAR(100),
    email          VARCHAR(150),
    age            INT,
    gender         VARCHAR(10),
    marital_status VARCHAR(20),
    occupation     VARCHAR(50),
    monthly_income VARCHAR(30),
    educational_qualifications VARCHAR(50),
    family_size    INT
);
-- password column dropped intentionally -- PII, not needed for analytics
CREATE TABLE restaurants (
    restaurant_id  BIGINT PRIMARY KEY,
    name           VARCHAR(200),
    city           VARCHAR(100),
    rating         DECIMAL(2,1) NULL,      -- '--' -> NULL
    rating_count_bucket VARCHAR(30),       -- kept as text bucket
    cost_for_two   DECIMAL(10,2),          -- '₹ 200' -> 200.00
    lic_no         VARCHAR(50),
    address        VARCHAR(500)
);

CREATE TABLE cuisines (
    cuisine_id   INT AUTO_INCREMENT PRIMARY KEY,
    cuisine_name VARCHAR(100) UNIQUE
);

CREATE TABLE restaurant_cuisines (
    restaurant_id BIGINT,
    cuisine_id    INT,
    PRIMARY KEY (restaurant_id, cuisine_id),
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id),
    FOREIGN KEY (cuisine_id) REFERENCES cuisines(cuisine_id)
);

CREATE TABLE food (
    food_id        VARCHAR(20) PRIMARY KEY,
    item_name      VARCHAR(200),
    veg_or_non_veg VARCHAR(20)
);

CREATE TABLE menu (
    menu_id       VARCHAR(20),
    restaurant_id BIGINT,
    food_id       VARCHAR(20),
    price         DECIMAL(10,2),
    PRIMARY KEY (menu_id, food_id),
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id),
    FOREIGN KEY (food_id) REFERENCES food(food_id)
);

CREATE TABLE orders (
    order_id        INT AUTO_INCREMENT PRIMARY KEY,
    order_date      DATE,
    sales_qty       INT,
    sales_amount    DECIMAL(12,2),
    currency        VARCHAR(10),
    is_valid_amount TINYINT(1),     -- 0 = negative/refund-like amount (flagged, not deleted)
    customer_id     INT,
    restaurant_id   BIGINT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE delivery (
    delivery_id             INT AUTO_INCREMENT PRIMARY KEY,
    order_id                INT,            -- synthetic link, filled in Database_analysis.sql
    delivery_person_id      VARCHAR(30),
    delivery_person_age     INT,
    delivery_person_ratings DECIMAL(2,1),
    order_date              DATE,
    time_ordered            TIME,
    time_order_picked       TIME,
    weather_conditions      VARCHAR(30),
    road_traffic_density    VARCHAR(20),
    vehicle_condition       INT,
    type_of_order           VARCHAR(30),
    type_of_vehicle         VARCHAR(30),
    multiple_deliveries     INT,
    festival                VARCHAR(10),
    city                    VARCHAR(30),
    time_taken_min          INT,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- ============================================================
-- LOAD RAW CSVs INTO STAGING
-- ============================================================

LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/users.csv'
INTO TABLE staging_users
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(row_idx, user_id, name, email, password, age, gender, marital_status,
 occupation, monthly_income, educational_qualifications, family_size);

TRUNCATE TABLE staging_restaurant;

LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/restaurant.csv'
INTO TABLE staging_restaurant
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(row_idx, id, name, city, rating, rating_count, cost, cuisine, lic_no, link, address, menu_json);

LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/food.csv'
INTO TABLE staging_food
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY '\\'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(row_idx, f_id, item, veg_or_non_veg);


LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/menu.csv'
INTO TABLE staging_menu
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(row_idx, menu_id, r_id, f_id, cuisine, price);

LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/orders.csv'
INTO TABLE staging_orders
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(row_idx, order_date, sales_qty, sales_amount, currency, user_id, r_id);

LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/Zomato Dataset.csv'
INTO TABLE staging_delivery
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY '\\'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(id, delivery_person_id, delivery_person_age, delivery_person_ratings,
 restaurant_latitude, restaurant_longitude, delivery_location_latitude,
 delivery_location_longitude, order_date, time_orderd, time_order_picked,
 weather_conditions, road_traffic_density, vehicle_condition, type_of_order,
 type_of_vehicle, multiple_deliveries, festival, city, time_taken_min);

SELECT 'staging_users' AS table_name, COUNT(*) AS row_count FROM staging_users
UNION ALL SELECT 'staging_restaurant', COUNT(*) FROM staging_restaurant
UNION ALL SELECT 'staging_food', COUNT(*) FROM staging_food
UNION ALL SELECT 'staging_menu', COUNT(*) FROM staging_menu
UNION ALL SELECT 'staging_orders', COUNT(*) FROM staging_orders
UNION ALL SELECT 'staging_delivery', COUNT(*) FROM staging_delivery;

-- ============================================================
-- 1. customers
-- ============================================================
INSERT IGNORE INTO customers
SELECT user_id, name, email, age, gender, marital_status, occupation,
       monthly_income, educational_qualifications, family_size
FROM staging_users
WHERE user_id IS NOT NULL;

-- ============================================================
-- 2. restaurants
-- ============================================================
INSERT INTO restaurants
SELECT DISTINCT
    id,
    name,
    city,
    CASE
        WHEN rating='--' OR rating='' OR rating IS NULL THEN NULL
        ELSE CAST(rating AS DECIMAL(2,1))
    END,
    rating_count,
    CASE
        WHEN cost='' OR cost IS NULL OR cost='₹' THEN NULL
        ELSE CAST(REPLACE(REPLACE(cost,'₹',''),' ','') AS DECIMAL(10,2))
    END,
    lic_no,
    address
FROM staging_restaurant;

-- ============================================================
-- 3. cuisines + restaurant_cuisines
-- ============================================================
CREATE TEMPORARY TABLE staging_cuisine_split AS
WITH RECURSIVE split_cuisine AS (
    SELECT
        id AS restaurant_id,
        TRIM(SUBSTRING_INDEX(cuisine, ',', 1)) AS cuisine_name,
        CASE WHEN LOCATE(',', cuisine) > 0
             THEN SUBSTRING(cuisine, LOCATE(',', cuisine) + 1)
             ELSE NULL END AS remaining
    FROM staging_restaurant
    WHERE cuisine IS NOT NULL AND cuisine <> ''
    UNION ALL
    SELECT
        restaurant_id,
        TRIM(SUBSTRING_INDEX(remaining, ',', 1)),
        CASE WHEN LOCATE(',', remaining) > 0
             THEN SUBSTRING(remaining, LOCATE(',', remaining) + 1)
             ELSE NULL END
    FROM split_cuisine
    WHERE remaining IS NOT NULL
)
SELECT DISTINCT restaurant_id, cuisine_name FROM split_cuisine WHERE cuisine_name <> '';

INSERT IGNORE INTO cuisines (cuisine_name)
SELECT DISTINCT cuisine_name FROM staging_cuisine_split;

INSERT IGNORE INTO restaurant_cuisines (restaurant_id, cuisine_id)
SELECT scs.restaurant_id, c.cuisine_id
FROM staging_cuisine_split scs
JOIN cuisines c ON c.cuisine_name = scs.cuisine_name
JOIN restaurants r ON r.restaurant_id = scs.restaurant_id;  -- drops orphan restaurant_ids

DROP TEMPORARY TABLE staging_cuisine_split;

-- ============================================================
-- 4. food 
-- ============================================================
INSERT IGNORE INTO food
SELECT DISTINCT f_id, item, veg_or_non_veg
FROM staging_food
WHERE f_id IS NOT NULL;

-- ============================================================
-- 5. menu
-- ============================================================
INSERT IGNORE INTO menu (menu_id, restaurant_id, food_id, price)
SELECT DISTINCT
    sm.menu_id, sm.r_id, sm.f_id,
    CASE WHEN sm.price REGEXP '^[0-9]+(\\.[0-9]+)?$' THEN CAST(sm.price AS DECIMAL(10,2)) ELSE NULL END
FROM staging_menu sm
JOIN restaurants r ON r.restaurant_id = sm.r_id
JOIN food f ON f.food_id = sm.f_id;

SELECT COUNT(*)
FROM staging_menu sm
LEFT JOIN restaurants r
    ON sm.r_id = r.restaurant_id
LEFT JOIN food f
    ON sm.f_id = f.food_id
WHERE r.restaurant_id IS NULL
   OR f.food_id IS NULL;

-- ============================================================
-- 6. orders
-- ============================================================
INSERT INTO orders (order_date, sales_qty, sales_amount, currency,
                     is_valid_amount, customer_id, restaurant_id)
SELECT
    STR_TO_DATE(so.order_date, '%Y-%m-%d'),
    so.sales_qty,
    so.sales_amount,
    so.currency,
    CASE WHEN so.sales_amount > 0 THEN 1 ELSE 0 END,
    so.user_id,
    CASE WHEN so.r_id REGEXP '^[0-9]+$' THEN CAST(so.r_id AS DECIMAL(20,0)) ELSE NULL END
FROM staging_orders so
JOIN customers c ON c.customer_id = so.user_id
WHERE so.r_id IS NOT NULL AND so.r_id <> ''
ORDER BY so.row_idx;


-- ============================================================
-- 7. delivery
-- ============================================================
INSERT INTO delivery (delivery_person_id, delivery_person_age, delivery_person_ratings,
                       order_date, time_ordered, time_order_picked, weather_conditions,
                       road_traffic_density, vehicle_condition, type_of_order,
                       type_of_vehicle, multiple_deliveries, festival, city, time_taken_min)
SELECT
    delivery_person_id,
    delivery_person_age,
    delivery_person_ratings,
    STR_TO_DATE(order_date, '%d-%m-%Y'),
    CASE
        WHEN time_orderd REGEXP '^[0-9]{1,2}:[0-9]{2}$' THEN STR_TO_DATE(time_orderd, '%H:%i')
        WHEN time_orderd REGEXP '^[0-9]*\\.[0-9]+$' THEN SEC_TO_TIME(ROUND(time_orderd * 86400))
        ELSE NULL
    END,
    CASE
        WHEN time_order_picked REGEXP '^[0-9]{1,2}:[0-9]{2}$' THEN STR_TO_DATE(time_order_picked, '%H:%i')
        WHEN time_order_picked REGEXP '^[0-9]*\\.[0-9]+$' THEN SEC_TO_TIME(ROUND(time_order_picked * 86400))
        ELSE NULL
    END,
    weather_conditions,
    road_traffic_density,
    vehicle_condition,
    type_of_order,
    type_of_vehicle,
    multiple_deliveries,
    festival,
    city,
    time_taken_min
FROM staging_delivery;

-- ============================================================
-- FINAL VERIFICATION: run this to confirm everything loaded
-- ============================================================
SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM customers
UNION ALL SELECT 'restaurants', COUNT(*) FROM restaurants
UNION ALL SELECT 'cuisines', COUNT(*) FROM cuisines
UNION ALL SELECT 'restaurant_cuisines', COUNT(*) FROM restaurant_cuisines
UNION ALL SELECT 'food', COUNT(*) FROM food
UNION ALL SELECT 'menu', COUNT(*) FROM menu
UNION ALL SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'delivery', COUNT(*) FROM delivery;
