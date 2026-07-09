"""
app.py
======
Entry point for the Streamlit web application.

Run with:
    streamlit run app.py

This file is the "Home" page. Streamlit automatically discovers every
script under `pages/` and lists them in the sidebar, so no manual
routing/navigation code is required.

This file, and every file under `pages/` and `streamlit_utils/`, contains
NO data-quality business logic -- all validation, profiling, cleaning,
reporting, and chart generation is delegated to the existing
`data_quality_checker` package (see streamlit_utils/pipeline.py).
"""

from __future__ import annotations

import streamlit as st

from streamlit_utils.ui import feature_card, inject_global_css, page_header, render_sidebar_status

st.set_page_config(
    page_title="Data Quality Checker & CSV Validator",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()
render_sidebar_status()

page_header(
    "🧪 Data Quality Checker & CSV Validator",
    "A professional toolkit for validating, profiling, cleaning, and reporting on CSV data quality — "
    "now available as an interactive web app on top of the existing Python backend.",
)

st.markdown("### What this app does")
st.write(
    "Upload any CSV file and this app will detect missing values, duplicates, invalid emails/phones/dates, "
    "negative values, whitespace issues, and more — then let you clean the data, visualize the results, "
    "and export professional reports, all without writing a line of code."
)

st.markdown("### ✨ Features")
row1 = st.columns(3)
with row1[0]:
    feature_card("📂 Smart CSV Import", "Auto-detects encoding & delimiter, handles large files, and fails gracefully on corrupted input.")
with row1[1]:
    feature_card("✅ Deep Validation", "Missing values, duplicate rows/columns, invalid emails/phones/dates, negatives, whitespace & special characters.")
with row1[2]:
    feature_card("📊 Full Profiling", "Row/column counts, memory usage, unique values, top frequent values, and numeric/categorical summaries.")

row2 = st.columns(3)
with row2[0]:
    feature_card("🧹 One-click Cleaning", "Remove duplicates, trim whitespace, standardize case, convert dates, and fill missing values.")
with row2[1]:
    feature_card("📈 Visual Insights", "Missing-value heatmaps, null % bar charts, duplicate-row summaries, and distribution plots.")
with row2[2]:
    feature_card("📄 Multi-format Reports", "Download your findings as CSV, JSON, or a beautifully styled HTML report.")

st.markdown("### 🔄 Workflow")
steps = [
    ("1. Upload", "Upload a CSV or load the bundled sample dataset."),
    ("2. Preview", "Inspect rows, columns, and data types."),
    ("3. Validate", "Run the full data-quality validation suite."),
    ("4. Profile", "Generate row/column statistics and summaries."),
    ("5. Clean", "Apply optional cleaning operations."),
    ("6. Visualize & Report", "Explore charts and export CSV/JSON/HTML reports."),
]
cols = st.columns(len(steps))
for col, (title, desc) in zip(cols, steps):
    with col:
        feature_card(title, desc)

st.markdown("---")
left, right = st.columns([3, 1])
with left:
    st.info("👈 Use the sidebar to navigate, or click below to get started.")
with right:
    st.page_link("pages/1_📂_Upload_Dataset.py", label="Get Started →", icon="📂")
