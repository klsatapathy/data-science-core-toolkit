/* ============================================================================
   SWIGGY / ZOMATO FOOD DELIVERY ANALYTICS — SQL ANALYSIS PORTFOLIO
   ============================================================================
   Database   : MySQL 8.0 (MySQL Workbench)
   Depends on : Database_setup.sql (customers, restaurants, cuisines,
                restaurant_cuisines, food, menu, orders, delivery)
   Objective  : End-to-end analysis covering restaurant/cuisine ranking,
                revenue, repeat-order behaviour, delivery performance,
                and peak-hour demand patterns.

   IMPORTANT NOTE ON `delivery`:
   `delivery` (Zomato_Dataset.csv) and `orders` (orders.csv) come from two
   unrelated Kaggle sources with no shared key. Section 0 below builds a
   SYNTHETIC one-to-one link (delivery_id -> order_id) using ROW_NUMBER()
   over a random shuffle, purely so delivery-time analysis can be joined
   to order-level context (city, revenue, etc.) for this portfolio project.
   It is NOT a real operational mapping -- call this out if asked in an
   interview.
   ============================================================================ */

USE swiggy_zomato_analytics;

/* ============================================================================
   SECTION 0 — SYNTHETIC ORDER <-> DELIVERY LINK
   ============================================================================
   delivery has ~45.5K rows, orders has ~150K rows (only valid, i.e.
   is_valid_amount = 1, orders are considered so delivery time is only
   ever linked to a real completed order). Each delivery row gets a
   distinct random order_id -- distinct because we rank both sides with
   ROW_NUMBER() over RAND() and match rank-to-rank.
   ============================================================================ */

DROP TEMPORARY TABLE IF EXISTS tmp_order_pool;
CREATE TEMPORARY TABLE tmp_order_pool AS
SELECT order_id,
       ROW_NUMBER() OVER (ORDER BY RAND()) AS rnk
FROM orders
WHERE is_valid_amount = 1
LIMIT 200000;                                   -- comfortably more than delivery rows

DROP TEMPORARY TABLE IF EXISTS tmp_delivery_pool;
CREATE TEMPORARY TABLE tmp_delivery_pool AS
SELECT delivery_id,
       ROW_NUMBER() OVER (ORDER BY RAND()) AS rnk
FROM delivery;

UPDATE delivery d
JOIN tmp_delivery_pool dp ON dp.delivery_id = d.delivery_id
JOIN tmp_order_pool op ON op.rnk = dp.rnk
SET d.order_id = op.order_id;

DROP TEMPORARY TABLE tmp_order_pool;
DROP TEMPORARY TABLE tmp_delivery_pool;

SELECT COUNT(*) AS delivery_rows, COUNT(order_id) AS linked_rows FROM delivery;


/* ============================================================================
   SECTION A — RANKING
   Restaurant ranking by city, cuisine popularity, top items
   ============================================================================ */

-- A1. Top 5 rated restaurants in every city (ties share the same rank)
SELECT city, name, rating, city_rank
FROM (
    SELECT city, name, rating,
           DENSE_RANK() OVER (PARTITION BY city ORDER BY rating DESC) AS city_rank
    FROM restaurants
    WHERE rating IS NOT NULL
) ranked
WHERE city_rank <= 5
ORDER BY city, city_rank;

-- A2. Most popular cuisines overall (by number of restaurants offering them)
SELECT c.cuisine_name,
       COUNT(DISTINCT rc.restaurant_id) AS restaurant_count,
       RANK() OVER (ORDER BY COUNT(DISTINCT rc.restaurant_id) DESC) AS popularity_rank
FROM restaurant_cuisines rc
JOIN cuisines c ON c.cuisine_id = rc.cuisine_id
GROUP BY c.cuisine_name
ORDER BY popularity_rank
LIMIT 20;

-- A3. Top 10 restaurants by total order volume (ranking by demand, not rating)
SELECT r.name, r.city, COUNT(o.order_id) AS total_orders,
       RANK() OVER (ORDER BY COUNT(o.order_id) DESC) AS demand_rank
FROM orders o
JOIN restaurants r ON r.restaurant_id = o.restaurant_id
GROUP BY r.restaurant_id, r.name, r.city
ORDER BY demand_rank
LIMIT 10;

-- A4. Best-selling food items (by how many menu listings + veg/non-veg split)
SELECT f.item_name, f.veg_or_non_veg, COUNT(*) AS listing_count
FROM menu m
JOIN food f ON f.food_id = m.food_id
GROUP BY f.item_name, f.veg_or_non_veg
ORDER BY listing_count DESC
LIMIT 15;


/* ============================================================================
   SECTION B — REVENUE
   Negative/junk amounts (is_valid_amount = 0) are excluded from every
   revenue total below -- they stay in `orders` but never count as revenue.
   ============================================================================ */

-- B1. Total revenue by currency (INR and USD kept separate -- no fixed
-- exchange rate assumed, since actual date-wise rate isn't in the data)
SELECT currency, SUM(sales_amount) AS total_revenue, COUNT(*) AS valid_orders
FROM orders
WHERE is_valid_amount = 1
GROUP BY currency;

-- B2. Revenue by city (INR orders only, since city-level revenue mixing
-- currencies would be misleading without a conversion rate)
SELECT r.city, SUM(o.sales_amount) AS revenue_inr, COUNT(*) AS orders
FROM orders o
JOIN restaurants r ON r.restaurant_id = o.restaurant_id
WHERE o.is_valid_amount = 1 AND o.currency = 'INR'
GROUP BY r.city
ORDER BY revenue_inr DESC
LIMIT 15;

-- B3. Month-over-month revenue trend (INR)
SELECT DATE_FORMAT(order_date, '%Y-%m') AS order_month,
       SUM(sales_amount) AS revenue_inr,
       COUNT(*) AS orders
FROM orders
WHERE is_valid_amount = 1 AND currency = 'INR'
GROUP BY order_month
ORDER BY order_month;

-- B4. Top 10 revenue-generating restaurants (INR)
SELECT r.name, r.city, SUM(o.sales_amount) AS revenue_inr
FROM orders o
JOIN restaurants r ON r.restaurant_id = o.restaurant_id
WHERE o.is_valid_amount = 1 AND o.currency = 'INR'
GROUP BY r.restaurant_id, r.name, r.city
ORDER BY revenue_inr DESC
LIMIT 10;

-- B5. Revenue contribution by cuisine
SELECT c.cuisine_name, SUM(o.sales_amount) AS revenue_inr
FROM orders o
JOIN restaurant_cuisines rc ON rc.restaurant_id = o.restaurant_id
JOIN cuisines c ON c.cuisine_id = rc.cuisine_id
WHERE o.is_valid_amount = 1 AND o.currency = 'INR'
GROUP BY c.cuisine_name
ORDER BY revenue_inr DESC
LIMIT 15;


/* ============================================================================
   SECTION C — REPEAT ORDERS
   ============================================================================ */

-- C1. Orders per customer + new vs repeat classification
SELECT customer_id, COUNT(*) AS order_count,
       CASE WHEN COUNT(*) > 1 THEN 'Repeat' ELSE 'One-time' END AS customer_type
FROM orders
GROUP BY customer_id;

-- C2. Overall repeat-customer rate
SELECT
    SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END) AS repeat_customers,
    SUM(CASE WHEN order_count = 1 THEN 1 ELSE 0 END) AS one_time_customers,
    ROUND(SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS repeat_rate_pct
FROM (
    SELECT customer_id, COUNT(*) AS order_count
    FROM orders
    GROUP BY customer_id
) cust_orders;

-- C3. Revenue share: repeat customers vs one-time customers
SELECT customer_type, SUM(sales_amount) AS revenue_inr, COUNT(*) AS orders
FROM (
    SELECT o.order_id, o.sales_amount,
           CASE WHEN co.order_count > 1 THEN 'Repeat' ELSE 'One-time' END AS customer_type
    FROM orders o
    JOIN (SELECT customer_id, COUNT(*) AS order_count FROM orders GROUP BY customer_id) co
      ON co.customer_id = o.customer_id
    WHERE o.is_valid_amount = 1 AND o.currency = 'INR'
) tagged
GROUP BY customer_type;

-- C4. Which restaurants have the highest repeat-order rate (customer loyalty)
SELECT r.name, r.city,
       COUNT(*) AS total_orders,
       COUNT(DISTINCT o.customer_id) AS unique_customers,
       ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT o.customer_id), 2) AS orders_per_customer
FROM orders o
JOIN restaurants r ON r.restaurant_id = o.restaurant_id
GROUP BY r.restaurant_id, r.name, r.city
HAVING COUNT(*) >= 20
ORDER BY orders_per_customer DESC
LIMIT 10;

-- C5. Time gap between a customer's consecutive orders (LAG window function)
SELECT customer_id, order_id, order_date,
       DATEDIFF(order_date, LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date)) AS days_since_last_order
FROM orders
ORDER BY customer_id, order_date;


/* ============================================================================
   SECTION D — AVERAGE DELIVERY TIME
   Uses the synthetic order<->delivery link built in Section 0.
   ============================================================================ */

-- D1. Overall average delivery time
SELECT ROUND(AVG(time_taken_min), 1) AS avg_delivery_min FROM delivery;

-- D2. Average delivery time by city
SELECT city, ROUND(AVG(time_taken_min), 1) AS avg_delivery_min, COUNT(*) AS deliveries
FROM delivery
GROUP BY city
ORDER BY avg_delivery_min DESC;

-- D3. Average delivery time by weather condition and traffic density
SELECT weather_conditions, road_traffic_density,
       ROUND(AVG(time_taken_min), 1) AS avg_delivery_min,
       COUNT(*) AS deliveries
FROM delivery
GROUP BY weather_conditions, road_traffic_density
ORDER BY avg_delivery_min DESC;

-- D4. Impact of festival days and multiple-deliveries on delivery time
SELECT festival, multiple_deliveries,
       ROUND(AVG(time_taken_min), 1) AS avg_delivery_min,
       COUNT(*) AS deliveries
FROM delivery
GROUP BY festival, multiple_deliveries
ORDER BY festival, multiple_deliveries;

-- D5. Delivery time by vehicle type and vehicle condition
SELECT type_of_vehicle, vehicle_condition,
       ROUND(AVG(time_taken_min), 1) AS avg_delivery_min,
       COUNT(*) AS deliveries
FROM delivery
GROUP BY type_of_vehicle, vehicle_condition
ORDER BY avg_delivery_min DESC;

-- D6. Delivery time vs order revenue, by city (joined via the synthetic link)
SELECT d.city,
       ROUND(AVG(d.time_taken_min), 1) AS avg_delivery_min,
       ROUND(AVG(o.sales_amount), 2) AS avg_order_value
FROM delivery d
JOIN orders o ON o.order_id = d.order_id
WHERE o.is_valid_amount = 1
GROUP BY d.city
ORDER BY avg_delivery_min DESC;


/* ============================================================================
   SECTION E — PEAK HOURS
   ============================================================================ */

-- E1. Order volume by hour of day (from delivery.time_ordered, since
-- orders.order_date has no time component in the source data)
SELECT HOUR(time_ordered) AS order_hour, COUNT(*) AS orders
FROM delivery
WHERE time_ordered IS NOT NULL
GROUP BY order_hour
ORDER BY order_hour;

-- E2. Peak hour ranking (busiest hours first)
SELECT HOUR(time_ordered) AS order_hour, COUNT(*) AS orders,
       RANK() OVER (ORDER BY COUNT(*) DESC) AS busy_rank
FROM delivery
WHERE time_ordered IS NOT NULL
GROUP BY order_hour
ORDER BY busy_rank
LIMIT 5;

-- E3. Peak hours by day of week
SELECT DAYNAME(order_date) AS day_of_week, HOUR(time_ordered) AS order_hour,
       COUNT(*) AS orders
FROM delivery
WHERE time_ordered IS NOT NULL AND order_date IS NOT NULL
GROUP BY day_of_week, order_hour
ORDER BY orders DESC
LIMIT 20;

-- E4. Does peak-hour traffic correlate with slower delivery?
SELECT
    CASE
        WHEN HOUR(time_ordered) BETWEEN 12 AND 14 THEN 'Lunch Peak (12-2pm)'
        WHEN HOUR(time_ordered) BETWEEN 19 AND 22 THEN 'Dinner Peak (7-10pm)'
        ELSE 'Off-Peak'
    END AS time_slot,
    ROUND(AVG(time_taken_min), 1) AS avg_delivery_min,
    COUNT(*) AS deliveries
FROM delivery
WHERE time_ordered IS NOT NULL
GROUP BY time_slot
ORDER BY avg_delivery_min DESC;


/* ============================================================================
   FINAL VERIFICATION
   ============================================================================ */
SELECT 'Section A - restaurants ranked' AS check_name, COUNT(*) AS row_count FROM restaurants WHERE rating IS NOT NULL
UNION ALL SELECT 'Section B - valid INR orders', COUNT(*) FROM orders WHERE is_valid_amount = 1 AND currency = 'INR'
UNION ALL SELECT 'Section C - unique customers with orders', COUNT(DISTINCT customer_id) FROM orders
UNION ALL SELECT 'Section D - deliveries linked to an order', COUNT(*) FROM delivery WHERE order_id IS NOT NULL
UNION ALL SELECT 'Section E - deliveries with order time', COUNT(*) FROM delivery WHERE time_ordered IS NOT NULL;
