/* ============================================================================
   HOSPITAL DATABASE ANALYSIS — SQL ANALYSIS PORTFOLIO
   ============================================================================
   Author        : Lokanath Satapathy
   Database      : MySQL 8.0 (MySQL Workbench)
   Dataset       : Hospital Management Dataset (Kaggle) — 5 tables
   Objective     : End-to-end operational analysis covering doctor
                   performance, patient segmentation (RFM), appointment
                   efficiency, demand trends, and billing/payment risk.


/* ============================================================================
   SECTION A — DOCTOR PERFORMANCE & REVENUE
   ============================================================================ */

-- ----------------------------------------------------------------------------
-- A1. Revenue & Appointment Volume per Doctor
-- ----------------------------------------------------------------------------
SELECT
    d.doctor_id,
    CONCAT(d.first_name, ' ', d.last_name) AS doctor_name,
    d.specialization,
    d.hospital_branch,
    COUNT(DISTINCT a.appointment_id) AS total_appointments,
    COUNT(DISTINCT t.treatment_id)   AS total_treatments,
    ROUND(SUM(t.cost), 2)            AS total_revenue,
    ROUND(AVG(t.cost), 2)            AS avg_treatment_cost
FROM doctors d
JOIN appointments a ON d.doctor_id = a.doctor_id
LEFT JOIN treatment t ON a.appointment_id = t.appointment_id
GROUP BY d.doctor_id, doctor_name, d.specialization, d.hospital_branch
ORDER BY total_revenue DESC;

/* INSIGHT A1 — Total doctor revenue: ₹5,51,249.85. Top 3 doctors = 39.71% of it (mild concentration, not extreme).
Sarah Taylor is #1 (15% of total revenue) — 2.2x more than lowest performer Sarah Smith (6.79%).
Central Hospital is the top branch — 41.55% revenue share despite only 4/10 doctors.

   INSIGHT A2 — Volume ≠ Value: Linda Brown has 2nd-lowest appointments (16) but ranks 5th in revenue — highest avg cost/treatment (₹3,339). 
   Sarah Smith has decent volume (17) but lowest avg cost (₹2,202) → ranks last.
   Dermatology has the highest avg revenue/doctor (₹67,570) — beats Pediatrics (₹51,788) even though Pediatrics has more total revenue (more doctors). */


-- ----------------------------------------------------------------------------
-- A2. Doctor Ranking Within Specialization (Window Function: RANK)
-- ----------------------------------------------------------------------------
WITH doctor_revenue AS (
    SELECT
        d.doctor_id,
        CONCAT(d.first_name, ' ', d.last_name) AS doctor_name,
        d.specialization,
        ROUND(SUM(t.cost), 2) AS total_revenue
    FROM doctors d
    JOIN appointments a ON d.doctor_id = a.doctor_id
    LEFT JOIN treatment t ON a.appointment_id = t.appointment_id
    GROUP BY d.doctor_id, doctor_name, d.specialization
)
SELECT
    doctor_name,
    specialization,
    total_revenue,
    RANK() OVER (PARTITION BY specialization ORDER BY total_revenue DESC) AS rank_in_specialization
FROM doctor_revenue
ORDER BY specialization, rank_in_specialization;

/* INSIGHT A3 — Pediatrics has the widest gap —
#1 Alex Davis (₹69,586) earns 1.86x more than #5 Sarah Smith (₹37,441). 
Biggest internal performance spread.
Dermatology: Sarah Taylor (#1) leads David Taylor (#2) by 24% (₹82,696 vs ₹66,585) — 
clear top performer.
Oncology (only 2 doctors): Linda Wilson beats Robert Davis by 23% — smallest pool, so less reliable to draw conclusions from.
Sarah Taylor (Dermatology) is #1 in her specialization and #1 overall — consistent top performer across both views.. */


-- ----------------------------------------------------------------------------
-- A3. Experience vs Revenue (Bucketed Aggregation)
-- ----------------------------------------------------------------------------
SELECT
    CASE
        WHEN d.years_experience < 10 THEN '0-9 yrs'
        WHEN d.years_experience BETWEEN 10 AND 19 THEN '10-19 yrs'
        ELSE '20+ yrs'
    END AS experience_bucket,
    COUNT(DISTINCT d.doctor_id) AS doctor_count,
    ROUND(AVG(t.cost), 2) AS avg_treatment_cost,
    ROUND(SUM(t.cost), 2) AS total_revenue
FROM doctors d
JOIN appointments a ON d.doctor_id = a.doctor_id
LEFT JOIN treatment t ON a.appointment_id = t.appointment_id
GROUP BY experience_bucket
ORDER BY experience_bucket;

/* INSIGHT A4 — No clear correlation — junior doctor (0-9 yrs, just 1 doctor = Linda Brown) 
has the highest avg treatment cost (₹3,339), beating both 10-19 yrs (₹2,540) and 20+ yrs (₹2,762) groups.
20+ yrs bucket dominates total revenue (₹3,78,446) simply because it has 7 of 10 doctors
not because senior doctors charge more per treatment.
10-19 yrs group has the lowest avg cost (₹2,540) despite being mid-experience 
no linear "more experience = more revenue" pattern.
Takeaway: doctor revenue depends more on specialization/patient load than years of experience." */


/* ============================================================================
   SECTION B — PATIENT SEGMENTATION (RFM ANALYSIS)
   ============================================================================ */

-- ----------------------------------------------------------------------------
-- B1. Patient RFM Scoring & Segmentation (Window Function: NTILE)
-- ----------------------------------------------------------------------------
WITH patient_rfm AS (
    SELECT
        p.patient_id,
        CONCAT(p.first_name, ' ', p.last_name) AS patient_name,
        DATEDIFF(CURDATE(), MAX(a.appointment_date)) AS recency_days,
        COUNT(DISTINCT a.appointment_id) AS frequency,
        ROUND(SUM(b.amount), 2) AS monetary
    FROM patients p
    JOIN appointments a ON p.patient_id = a.patient_id
    LEFT JOIN treatment t ON a.appointment_id = t.appointment_id
    LEFT JOIN billing b ON t.treatment_id = b.treatment_id
    GROUP BY p.patient_id, patient_name
),
rfm_scores AS (
    SELECT
        *,
        NTILE(4) OVER (ORDER BY recency_days DESC) AS r_score,
        NTILE(4) OVER (ORDER BY frequency ASC)      AS f_score,
        NTILE(4) OVER (ORDER BY monetary ASC)       AS m_score
    FROM patient_rfm
),
rfm_segments AS (
    SELECT
        *,
        CASE
            WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Champions'
            WHEN r_score >= 3 AND f_score >= 2 THEN 'Regular Patients'
            WHEN r_score >= 3 AND f_score = 1 THEN 'New Patients'
            WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk (Lapsing)'
            WHEN r_score = 1 AND f_score = 1 AND m_score >= 3 THEN 'High-Value Lapsed'
            ELSE 'Others'
        END AS patient_segment
    FROM rfm_scores
)
SELECT
    patient_segment,
    COUNT(*) AS num_patients,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_of_total,
    ROUND(AVG(monetary), 2)     AS avg_monetary,
    ROUND(AVG(frequency), 2)    AS avg_frequency,
    ROUND(AVG(recency_days), 0) AS avg_recency_days
FROM rfm_segments
GROUP BY patient_segment
ORDER BY num_patients DESC;

/* INSIGHT B1 — Champions Are a Major Segment, Not a Rounding Error
   Champions = 18 patients (37.5%) — 2nd largest segment overall, 
   right behind "Others." Highest avg spend too (₹16,883).

   INSIGHT B2 — At Risk = Small but High-Value Re-engagement Target
   At Risk = only 5 patients (10.42%) but avg spend ₹11,898 (2nd highest) 
   and avg recency 1072 days (~2.9 yrs since last visit) — small pool, 
   but high-value dormant patients worth a follow-up campaign.

   INSIGHT B3 — No Frequency Ceiling, Champions Visit A Lot
   Champions avg_frequency = 5.83 visits — well above the "2-3 visit" retail-style assumption. 
   Regular Patients (3.50) and At Risk (5.00) also show decent repeat frequency 
   hospital repeat-visit behavior isn't as limited as expected.*/


-- ----------------------------------------------------------------------------
-- B2. Patient Age Group vs Spend (Date Function: TIMESTAMPDIFF)
-- ----------------------------------------------------------------------------
SELECT
    CASE
        WHEN TIMESTAMPDIFF(YEAR, p.date_of_birth, CURDATE()) < 30 THEN 'Under 30'
        WHEN TIMESTAMPDIFF(YEAR, p.date_of_birth, CURDATE()) BETWEEN 30 AND 49 THEN '30-49'
        WHEN TIMESTAMPDIFF(YEAR, p.date_of_birth, CURDATE()) BETWEEN 50 AND 69 THEN '50-69'
        ELSE '70+'
    END AS age_group,
    COUNT(DISTINCT p.patient_id) AS patient_count,
    ROUND(AVG(b.amount), 2)      AS avg_bill_amount,
    ROUND(SUM(b.amount), 2)      AS total_billed
FROM patients p
JOIN billing b ON p.patient_id = b.patient_id
GROUP BY age_group
ORDER BY age_group;

/* INSIGHT B4 — 30-49 is the biggest revenue driver 
20 patients, ₹2,26,268 total (41% of all billing)
largest patient base, not just largest spender.
50-69 has the highest avg bill (₹2,888.98)  
not 70+ as typically expected. 
Older-but-not-oldest patients cost the most per visit.
70+ has lowest avg bill (₹2,682.73) despite being the "senior" group 
fewer of them (6) and cheaper avg treatment than 30-49 or 50-69.
Under 30 — lowest avg spend (₹2,511.48) and 2nd-smallest group (9 patients) 
youngest patients cost least per bill, as expected.
Takeaway: cost peaks in middle-to-late adulthood (50-69), not at the oldest age bracket  
worth flagging since it breaks the "older = costlier" assumption. */


-- ----------------------------------------------------------------------------
-- B3. Insurance Provider Reliance
-- ----------------------------------------------------------------------------
SELECT
    p.insurance_provider,
    COUNT(DISTINCT p.patient_id) AS patient_count,
    ROUND(SUM(b.amount), 2)      AS total_billed,
    ROUND(AVG(b.amount), 2)      AS avg_bill_amount
FROM patients p
JOIN billing b ON p.patient_id = b.patient_id
GROUP BY p.insurance_provider
ORDER BY total_billed DESC;

/* INSIGHT B5 —MedCare Plus dominates 
18 patients, ₹2,41,092 total billed (46% of all revenue)  
hospital's biggest financial dependency.
PulseSecure has fewest patients (10) 
but highest avg bill (₹2,902.03) 
smaller base, costlier claims per patient.
HealthIndia is weakest on all fronts  
fewest total billing (₹53,823) and lowest avg bill (₹2,446.53).
Takeaway: MedCare Plus concentration = cash-flow risk if their claims processing slows down */


/* ============================================================================
   SECTION C — APPOINTMENT OPERATIONS (NO-SHOWS / CANCELLATIONS)
   ============================================================================ */

-- ----------------------------------------------------------------------------
-- C1. Appointment Status Breakdown
-- ----------------------------------------------------------------------------
SELECT
    status,
    COUNT(*) AS appointment_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM appointments), 2) AS pct_of_total
FROM appointments
GROUP BY status
ORDER BY appointment_count DESC;

/* INSIGHT C1 — No-show is the single biggest category (26%)  
beats even Cancelled (25.5%) and Scheduled (25.5%).
Combined No-show + Cancelled = 51.5% of all appointments 
more than half of scheduled slots produced zero revenue. Major operational leakage.
Only 23% (46) appointments actually completed — lowest of all 4 statuses.
Takeaway: this is a serious scheduling/reminder problem, not a minor inefficiency 
over half the hospital's appointment capacity is being wasted.*/


-- ----------------------------------------------------------------------------
-- C2. No-show / Cancellation Rate by Doctor
-- ----------------------------------------------------------------------------
SELECT
    d.doctor_id,
    CONCAT(d.first_name, ' ', d.last_name) AS doctor_name,
    COUNT(*) AS total_appointments,
    SUM(CASE WHEN a.status IN ('No-show', 'Cancelled') THEN 1 ELSE 0 END) AS lost_appointments,
    ROUND(SUM(CASE WHEN a.status IN ('No-show', 'Cancelled') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS lost_pct
FROM doctors d
JOIN appointments a ON d.doctor_id = a.doctor_id
GROUP BY d.doctor_id, doctor_name
HAVING total_appointments >= 5
ORDER BY lost_pct DESC;

/* INSIGHT C2 — Sarah Smith has the worst rate — 58.82% appointments lost (10 of 17). 
Combined with her already being the lowest revenue earner. 
she's the clearest priority for a reminder-call pilot.
David Jones close 2nd worst (57.14%). 
Pattern emerging: low-revenue doctors also have high no-show rates.
Linda Wilson and Jane Davis have the best rates (42.11%, 42.86%) 
still high in absolute terms, but noticeably better than the rest.
Every single doctor has a lost rate above 42% 
this isn't a few problem doctors, it's a hospital-wide scheduling issue.*/


-- ----------------------------------------------------------------------------
-- C3. No-show / Cancellation Rate by Day of Week (Date Function: DAYNAME)
-- ----------------------------------------------------------------------------
SELECT
    DAYNAME(appointment_date) AS day_of_week,
    COUNT(*) AS total_appointments,
    SUM(CASE WHEN status IN ('No-show', 'Cancelled') THEN 1 ELSE 0 END) AS lost_appointments,
    ROUND(SUM(CASE WHEN status IN ('No-show', 'Cancelled') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS lost_pct
FROM appointments
GROUP BY day_of_week
ORDER BY lost_pct DESC;

/* INSIGHT C3 — Sunday is worst — 61.54% lost rate. 
Even though weekend, patients skip most on Sundays.
Wednesday close 2nd (59.46%) and highest volume day too (37 appointments) 
so absolute lost count (22) is huge biggest single-day leakage.
Saturday is the best day (39.13%) lowest lost rate despite being weekend.
Weekday pattern breaks the usual "Monday/Friday worst" assumption 
here it's Sunday & Wednesday, not the week's start/end. 
Reminder push should target these two days specifically. */


-- ----------------------------------------------------------------------------
-- C4. Status Breakdown by Reason for Visit
-- ----------------------------------------------------------------------------
SELECT
    reason_for_visit,
    COUNT(*) AS total_appointments,
    SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed,
    SUM(CASE WHEN status IN ('No-show', 'Cancelled') THEN 1 ELSE 0 END) AS lost,
    ROUND(SUM(CASE WHEN status IN ('No-show', 'Cancelled') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS lost_pct
FROM appointments
GROUP BY reason_for_visit
ORDER BY lost_pct DESC;

/* INSIGHT C4 — Emergency has the highest lost rate (62.07%) 
worst possible category to lose, since these are urgent cases, not routine ones. 
Contradicts the "urgent visits have better follow-through" assumption.
Consultation (60.47%) and Therapy (59.52%) are close behind 
routine and ongoing-care visits both losing more than half their slots.
Checkup (40%) and Follow-up (39.02%) have the best rates 
scheduled routine care patients show up more reliably than emergency/consultation patients.
Takeaway: reminder systems should prioritize Emergency and Consultation visits first 
that's the opposite of where you'd normally focus reminder effort, and it's the biggest risk category. */


/* ============================================================================
   SECTION D — DEMAND & TIME TRENDS
   ============================================================================ */

-- ----------------------------------------------------------------------------
-- D1. Monthly Appointment Volume & Revenue Trend
-- ----------------------------------------------------------------------------
SELECT
    DATE_FORMAT(a.appointment_date, '%Y-%m') AS appointment_month,
    COUNT(DISTINCT a.appointment_id) AS appointment_count,
    ROUND(SUM(t.cost), 2) AS monthly_revenue
FROM appointments a
LEFT JOIN treatment t ON a.appointment_id = t.appointment_id
GROUP BY appointment_month
ORDER BY appointment_month;

/* INSIGHT D1 — April is the clear peak  
both highest volume (25 appointments) and highest revenue (₹64,271.54).
December is the weakest month 
lowest revenue (₹27,569.71) and lowest avg revenue/appointment (₹2,297), 
even though September had fewer appointments (11 vs 12). Year ends on the worst note.
June has the highest avg revenue per appointment (₹3,160) despite mid-range volume (18) 
a high-value-treatment month, not a high-volume one.
No clear growth trend across the year 
revenue fluctuates month to month rather than trending up looks flat/seasonal rather than growing. */


-- ----------------------------------------------------------------------------
-- D2. Month-over-Month Revenue Growth % (Window Function: LAG)
-- ----------------------------------------------------------------------------
WITH monthly_revenue AS (
    SELECT
        DATE_FORMAT(a.appointment_date, '%Y-%m') AS appointment_month,
        ROUND(SUM(t.cost), 2) AS monthly_revenue
    FROM appointments a
    LEFT JOIN treatment t ON a.appointment_id = t.appointment_id
    GROUP BY appointment_month
)
SELECT
    appointment_month,
    monthly_revenue,
    LAG(monthly_revenue) OVER (ORDER BY appointment_month) AS prev_month_revenue,
    ROUND(
        (monthly_revenue - LAG(monthly_revenue) OVER (ORDER BY appointment_month))
        / LAG(monthly_revenue) OVER (ORDER BY appointment_month) * 100,
        2
    ) AS mom_growth_pct
FROM monthly_revenue
ORDER BY appointment_month;

/* INSIGHT D2 — Extreme volatility swings range from -47.46% (Dec) to +35.87% (Apr). 
No stable growth trend, pure up-down noise month to month.
December crash (-47.46%) is the worst single drop of the year 
confirms D1's finding that the year ends on the weakest note.
April (+35.87%) and March (+29.00%) show back-to-back strong recovery months 
Q1 end into Q2 start is the strongest growth window.
7 of 12 months show negative growth 
more down-months than up-months, but big positive swings (Mar, Apr, Oct) prevent an overall declining trend. 
With only ~200 appointments/year, this volatility is expected — small sample size, not a real business signal. */


-- ----------------------------------------------------------------------------
-- D3. Busiest Day of the Week
-- ----------------------------------------------------------------------------
SELECT
    DAYNAME(appointment_date) AS day_of_week,
    COUNT(*) AS appointment_count
FROM appointments
GROUP BY day_of_week
ORDER BY appointment_count DESC;

/* INSIGHT D3 —Wednesday and Tuesday tied for busiest 
37 appointments each, way ahead of everything else.
Combined, Tue+Wed = 74 appointments 
37% of all 200 appointments just on 2 days. 
Rest of the week averages ~25/day.
Friday and Saturday are tied lowest (23 each) 
weekend/pre-weekend slowdown, opposite of what mid-week shows.*/


-- ----------------------------------------------------------------------------
-- D4. Average Days Between Appointment and Billing (Date Function: DATEDIFF)
-- ----------------------------------------------------------------------------
SELECT
    ROUND(AVG(DATEDIFF(b.bill_date, a.appointment_date)), 1) AS avg_days_to_bill
FROM appointments a
JOIN treatment t ON a.appointment_id = t.appointment_id
JOIN billing b ON t.treatment_id = b.treatment_id;

/* INSIGHT D4 — avg_days_to_bill = 0
billing pipeline is instant, same-day invoicing for every treatment. Zero lag between appointment and bill generation.
No collections delay from a process standpoint .*/


/* ============================================================================
   SECTION E — BILLING & PAYMENT RISK
   ============================================================================ */

-- ----------------------------------------------------------------------------
-- E1. Payment Status Breakdown by Amount at Risk
-- ----------------------------------------------------------------------------
SELECT
    payment_status,
    COUNT(*) AS bill_count,
    ROUND(SUM(amount), 2) AS total_amount,
    ROUND(SUM(amount) * 100.0 / (SELECT SUM(amount) FROM billing), 2) AS pct_of_total_amount
FROM billing
GROUP BY payment_status
ORDER BY total_amount DESC;

/* INSIGHT E1 —Failed is the #1 category by amount, not just count 
₹1,93,213 (35.05% of total billed) never collected. Worse than Pending.
Failed + Pending combined = 68.54% of total billed amount (₹3,77,825) 
over two-thirds of hospital revenue is stuck or lost, only 31.46% actually Paid.
Amount % roughly matches count % here (Failed 67 bills/35%, Pending 69 bills/33%) 
no hidden concentration in a few large bills, risk is evenly spread across many mid-size bills. */


-- ----------------------------------------------------------------------------
-- E2. Treatment Type Revenue Ranking (Window Function: RANK)
-- ----------------------------------------------------------------------------
SELECT
    treatment_type,
    COUNT(*) AS treatment_count,
    ROUND(AVG(cost), 2) AS avg_cost,
    ROUND(SUM(cost), 2) AS total_revenue,
    RANK() OVER (ORDER BY SUM(cost) DESC) AS revenue_rank
FROM treatment
GROUP BY treatment_type
ORDER BY revenue_rank;

/* INSIGHT E2 — Chemotherapy is #1 by total revenue (₹1,28,856) but not the priciest per-unit 
its rank comes from volume (49 treatments, most of any type).
MRI has the highest avg cost (₹3,224.95) by far, but ranks #2 overall 
fewer treatments (36) than Chemotherapy holds it back.
X-Ray — high volume (41) but low avg cost (₹2,698.87), still lands #3 purely on count.
ECG is the cheapest per-unit (₹2,532.22) and lowest total revenue (₹96,224) despite decent volume (38) 
confirms it's the low-value treatment type.*/


-- ----------------------------------------------------------------------------
-- E3. Payment Method Behavior by Outcome
-- ----------------------------------------------------------------------------
SELECT
    payment_method,
    COUNT(*) AS bill_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_of_bills,
    ROUND(AVG(amount), 2) AS avg_bill_amount,
    SUM(CASE WHEN payment_status = 'Failed' THEN 1 ELSE 0 END) AS failed_count,
    ROUND(SUM(CASE WHEN payment_status = 'Failed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS failed_pct
FROM billing
GROUP BY payment_method
ORDER BY bill_count DESC;

/* INSIGHT E3 — Cash has the worst failure rate — 37.70%, highest of all 3 methods, 
despite being the smallest share (30.50% of bills). 
Surprising — cash should be simplest, but fails most.
Credit Card is most reliable lowest failure rate (30.67%) and highest bill volume (75, 37.50%).*/


-- ----------------------------------------------------------------------------
-- E4. High-Value Unpaid Bills (Targeted Follow-up List)
-- ----------------------------------------------------------------------------
SELECT
    b.bill_id,
    p.patient_id,
    CONCAT(p.first_name, ' ', p.last_name) AS patient_name,
    b.amount,
    b.payment_status,
    b.bill_date
FROM billing b
JOIN patients p ON b.patient_id = p.patient_id
WHERE b.payment_status IN ('Pending', 'Failed')
ORDER BY b.amount DESC
LIMIT 10;

/* INSIGHT E4 — All top 10 unpaid bills sit tightly between ₹4,687-₹4,966 
a clear cluster of high-ticket cases, not one outlier skewing the list.
Michael Wilson appears 3 times (B156, B036, B042) 
single patient with ₹14,579 across 3 unpaid bills. 
Highest-priority individual follow-up.
Split is 6 Pending vs 4 Failed most recoverable-but-stuck rather than fully failed,
so a payment nudge/reminder could realistically recover a good chunk.*/

/* ============================================================================
   END OF SCRIPT — 20 BUSINESS INSIGHTS ACROSS 5 ANALYTICAL AREAS
   ============================================================================
   A. Doctor Performance   -> Insights A1, A2, A3, A4
   B. Patient RFM          -> Insights B1, B2, B3, B4, B5
   C. Appointment Ops      -> Insights C1, C2, C3, C4
   D. Demand & Time Trends -> Insights D1, D2, D3, D4
   E. Billing & Payments   -> Insights E1, E2, E3, E4 (+ collections list)
   ============================================================================ */
