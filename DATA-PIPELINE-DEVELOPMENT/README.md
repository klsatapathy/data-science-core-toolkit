# DATA-PIPELINE-DEVELOPMENT

**COMPANY:-** CODTECH IT SOLUTIONS

**NAME:-** LOKANATH SATAPATHY

**INTERN ID:-** CT12WTOK

**DOMAIN:-** DATA SCIENCE

**DURATION:-** 12 NEEEKS

**MENTOR:-** NEELA SANTOSH


# 🔄 ETL Pipeline for Data Preprocessing, Transformation, and Loading

An end-to-end ETL (Extract, Transform, Load) pipeline built with **Python**, **Pandas**, and **scikit-learn** to streamline data preparation for machine learning tasks. This pipeline automates essential preprocessing steps like missing value handling, categorical encoding, and feature scaling.

---

## 📌 Overview

This project provides a robust, modular ETL pipeline that:

- Loads datasets from CSV or Excel formats
- Handles missing values
- Encodes categorical variables
- Scales numerical features
- Outputs a clean dataset ready for machine learning models

---

## 🔧 Key Features

### 1. Data Loading Flexibility
- Supports **CSV** and **Excel** files
- Error handling for unsupported formats and file path issues

### 2. Comprehensive Preprocessing
- **Missing Values**:
  - Detection and imputation using column-wise **mean** (for numerical columns)
- **Categorical Encoding**:
  - Automatic **one-hot encoding** for non-numeric columns
- **Target Column**:
  - Separates the target column for supervised learning

### 3. Feature Scaling
- Uses `StandardScaler` from **scikit-learn**
- Retains original column names post-scaling

### 4. User-Friendly Interface
- Interactive prompts for:
  - File path input
  - Target column selection
- Displays:
  - Column overview
  - Missing value statistics

### 5. Output
- Saves preprocessed dataset to: `cleaned_dataset.csv`
- Maintains relationship between features and target

---

## ⚙️ Technical Stack

- **Language**: Python
- **Libraries**: 
  - `pandas`
  - `scikit-learn`
- **Design**: Modular functions for:
  - File loading
  - Data cleaning
  - Feature transformation

- **Error Handling**:
  - `try-except` blocks
  - Input validation to ensure robustness

---

## 📈 Use Cases

Ideal for:
- **Machine Learning Preprocessing**: Prepares raw data for training/testing models
- **Data Science Education**: Demonstrates ETL principles in practice
- **Rapid Prototyping**: Standard pipeline for early model experimentation
- **Workflow Standardization**: Reusable across projects for consistency

---

## 🧪 Example Workflow

1. Load the raw dataset (e.g., a **diabetes dataset**)
2. Identify and fill missing values
3. Encode categorical columns
4. Scale features to standard distribution
5. Save cleaned data for downstream ML tasks

---


## 💬 Feedback

Suggestions and contributions are welcome! Feel free to fork, modify, and raise issues or pull requests.


**Start preprocessing smarter, not harder! 💡**
