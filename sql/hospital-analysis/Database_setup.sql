-- ============================================================
-- HOSPITAL DATABASE ANALYSIS PROJECT
-- File: 01_schema.sql
-- Purpose: Create database and all tables
-- ============================================================

CREATE DATABASE hospital_db;
USE hospital_db;

-- ------------------------------------------------------------
-- patients
-- ------------------------------------------------------------
CREATE TABLE patients (
    patient_id VARCHAR(10) PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    gender VARCHAR(10),
    date_of_birth DATE,
    contact_number VARCHAR(20),
    address VARCHAR(255),
    registration_date DATE,
    insurance_provider VARCHAR(100),
    insurance_number VARCHAR(50),
    email VARCHAR(100)
);

-- ------------------------------------------------------------
-- doctors
-- ------------------------------------------------------------
CREATE TABLE doctors (
    doctor_id VARCHAR(10) PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    specialization VARCHAR(100),
    phone_number VARCHAR(20),
    years_experience INT,
    hospital_branch VARCHAR(100),
    email VARCHAR(100)
);

-- ------------------------------------------------------------
-- appointments
-- ------------------------------------------------------------
CREATE TABLE appointments (
    appointment_id VARCHAR(10) PRIMARY KEY,
    patient_id VARCHAR(10),
    doctor_id  VARCHAR(10),
    appointment_date DATE,
    appointment_time TIME,
    reason_for_visit VARCHAR(255),
    status VARCHAR(20),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
);

-- ------------------------------------------------------------
-- treatment
-- ------------------------------------------------------------
CREATE TABLE treatment (
    treatment_id VARCHAR(10) PRIMARY KEY,
    appointment_id VARCHAR(10),
    treatment_type VARCHAR(100),
    description VARCHAR(255),
    cost DECIMAL(10,2),
    treatment_date DATE,
    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id)
);

-- ------------------------------------------------------------
-- billing
-- ------------------------------------------------------------
CREATE TABLE billing (
    bill_id VARCHAR(10) PRIMARY KEY,
    patient_id VARCHAR(10),
    treatment_id VARCHAR(10),
    bill_date DATE,
    amount DECIMAL(10,2),
    payment_method VARCHAR(50),
    payment_status VARCHAR(20),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (treatment_id) REFERENCES treatment(treatment_id)
);


-- ============================================================
-- HOSPITAL DATABASE ANALYSIS PROJECT
-- Purpose: Load all CSV files into the tables
-- ============================================================

USE hospital_db;

-- ------------------------------------------------------------
-- 1. patients
-- ------------------------------------------------------------
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/patients.csv'
INTO TABLE patients
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(patient_id, first_name, last_name, gender, @dob, contact_number,
 address, @reg_date, insurance_provider, insurance_number, email)
SET
 date_of_birth     = STR_TO_DATE(NULLIF(@dob, ''), '%Y-%m-%d'),
 registration_date = STR_TO_DATE(NULLIF(@reg_date, ''), '%Y-%m-%d');

SELECT COUNT(*) AS patients_count FROM patients;

-- ------------------------------------------------------------
-- 2. doctors
-- ------------------------------------------------------------
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/doctors.csv'
INTO TABLE doctors
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

SELECT COUNT(*) AS doctors_count FROM doctors;

-- ------------------------------------------------------------
-- 3. appointments
-- ------------------------------------------------------------
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/appointments.csv'
INTO TABLE appointments
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(appointment_id, patient_id, doctor_id, @appt_date, appointment_time,
 reason_for_visit, status)
SET
 appointment_date = STR_TO_DATE(NULLIF(@appt_date, ''), '%Y-%m-%d');

SELECT COUNT(*) AS appointments_count FROM appointments;

-- ------------------------------------------------------------
-- 4. treatment
-- ------------------------------------------------------------
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/treatments.csv'
INTO TABLE treatment
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(treatment_id, appointment_id, treatment_type, description, cost, @treat_date)
SET
 treatment_date = STR_TO_DATE(NULLIF(@treat_date, ''), '%Y-%m-%d');

SELECT COUNT(*) AS treatment_count FROM treatment;

-- ------------------------------------------------------------
-- 5. billing
-- ------------------------------------------------------------
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/billing.csv'
INTO TABLE billing
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(bill_id, patient_id, treatment_id, @bill_date, amount, payment_method, payment_status)
SET
 bill_date = STR_TO_DATE(NULLIF(@bill_date, ''), '%Y-%m-%d');

SELECT COUNT(*) AS billing_count FROM billing;

-- ------------------------------------------------------------
-- FINAL VERIFICATION: run this to confirm every table loaded
-- ------------------------------------------------------------
SELECT 'patients' AS table_name, COUNT(*) AS row_count FROM patients
UNION ALL SELECT 'doctors', COUNT(*) FROM doctors
UNION ALL SELECT 'appointments', COUNT(*) FROM appointments
UNION ALL SELECT 'treatment', COUNT(*) FROM treatment
UNION ALL SELECT 'billing', COUNT(*) FROM billing;
