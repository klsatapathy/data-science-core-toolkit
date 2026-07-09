"""
pages/3_✅_Data_Validation.py
==============================
Runs `DataValidator.run_all()` (from the existing backend) on the loaded
dataset and renders the results as a dashboard: metric cards, a
per-column results table, and status indicators. No validation logic is
implemented in this file.
"""

from __future__ import annotations

import streamlit as st

from streamlit_utils import pipeline
from streamlit_utils.ui import (
    badge,
    inject_global_css,
    metric_row,
    page_header,
    render_sidebar_status,
    require_dataset,
    status_for,
)

st.set_page_config(page_title="Data Validation", page_icon="✅", layout="wide")
inject_global_css()
render_sidebar_status()
page_header("✅ Data Validation", "Run the full data-quality validation suite on your dataset.")

require_dataset()
df = st.session_state.df

run_col, info_col = st.columns([1, 3])
with run_col:
    run_clicked = st.button("▶️ Run Validation", type="primary", use_container_width=True)
with info_col:
    st.caption("Checks missing values, duplicates, invalid emails/phones/dates, negatives, whitespace, and more.")

if run_clicked:
    progress = st.progress(0, text="Running validation checks...")
    with st.spinner("Validating dataset..."):
        report = pipeline.run_validation(df)
        progress.progress(100, text="Validation complete!")
    st.session_state.validation_report = report
    progress.empty()
    st.success("Validation completed successfully.")

st.divider()

if "validation_report" not in st.session_state:
    st.info("Click **Run Validation** to analyze this dataset.")
    st.stop()

report = st.session_state.validation_report

# ---------------------------------------------------------------------
# Top-level metrics
# ---------------------------------------------------------------------
st.markdown("#### 📌 Overview")
metric_row([
    ("Total Rows", f"{report.total_rows:,}", "ok"),
    ("Total Columns", report.total_columns, "ok"),
    ("Duplicate Rows", f"{report.duplicate_row_count} ({report.duplicate_row_percentage:.1f}%)",
     status_for(report.duplicate_row_count, zero_is_ok=True)),
    ("Empty Columns", len(report.empty_columns), status_for(len(report.empty_columns))),
])

st.write("")
col_a, col_b = st.columns(2)
with col_a:
    st.markdown("**Duplicate column pairs**")
    if report.duplicate_column_pairs:
        st.markdown(badge(f"{len(report.duplicate_column_pairs)} pair(s) found", "bad"), unsafe_allow_html=True)
        for a, b in report.duplicate_column_pairs:
            st.write(f"- `{a}` ≡ `{b}`")
    else:
        st.markdown(badge("None found", "ok"), unsafe_allow_html=True)

with col_b:
    st.markdown("**Empty columns**")
    if report.empty_columns:
        st.markdown(badge(f"{len(report.empty_columns)} column(s)", "bad"), unsafe_allow_html=True)
        st.write(", ".join(f"`{c}`" for c in report.empty_columns))
    else:
        st.markdown(badge("None found", "ok"), unsafe_allow_html=True)

st.divider()

# ---------------------------------------------------------------------
# Per-column results table
# ---------------------------------------------------------------------
st.markdown("#### 🔎 Column-Level Quality Report")

results_df = pipeline.validation_report_to_dataframe(report)

issue_columns = [
    "Null %", "Dup. Values", "Whitespace Rows", "Special Char Rows",
    "Negative Values", "Invalid Emails", "Invalid Phones", "Invalid Dates", "Type Mismatches",
]


def _highlight_issues(row):
    styles = [""] * len(row)
    for i, col in enumerate(row.index):
        if col in issue_columns:
            val = row[col]
            if isinstance(val, (int, float)) and val and val > 0:
                styles[i] = "background-color: #fee2e2; color: #991b1b;"
    return styles


st.dataframe(
    results_df.style.apply(_highlight_issues, axis=1),
    use_container_width=True,
    height=420,
)

with st.expander("ℹ️ What do these columns mean?"):
    st.markdown(
        """
        - **Null %** — percentage of missing values in the column.
        - **Dup. Values** — count of values that repeat more than once.
        - **Whitespace Rows** — rows with leading/trailing whitespace.
        - **Special Char Rows** — rows containing unexpected special characters.
        - **Negative Values** — negative numbers found in a numeric column.
        - **Invalid Emails / Phones / Dates** — only computed for columns whose name
          suggests that type (e.g. `email`, `phone`, `date`), or that look date-like.
        - **Type Mismatches** — stray numeric-looking values in an otherwise text column.
        """
    )

st.divider()
st.page_link("pages/4_📊_Data_Profiling.py", label="➡️ Continue to Data Profiling", icon="📊")
