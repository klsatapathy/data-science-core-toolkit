"""
pages/4_📊_Data_Profiling.py
==============================
Runs `DataProfiler.profile()` (existing backend) and displays the
resulting statistics. No profiling logic is implemented here.
"""

from __future__ import annotations

import streamlit as st

from streamlit_utils import pipeline
from streamlit_utils.ui import inject_global_css, metric_row, page_header, render_sidebar_status, require_dataset

st.set_page_config(page_title="Data Profiling", page_icon="📊", layout="wide")
inject_global_css()
render_sidebar_status()
page_header("📊 Data Profiling", "Generate a full statistical profile of your dataset.")

require_dataset()
df = st.session_state.df

run_col, info_col = st.columns([1, 3])
with run_col:
    run_clicked = st.button("▶️ Generate Profile", type="primary", use_container_width=True)
with info_col:
    st.caption("Row/column counts, memory usage, missing stats, unique values, and numeric/categorical summaries.")

if run_clicked:
    with st.spinner("Profiling dataset..."):
        st.session_state.profile = pipeline.run_profiling(df)
    st.success("Profiling completed successfully.")

st.divider()

if "profile" not in st.session_state:
    st.info("Click **Generate Profile** to analyze this dataset.")
    st.stop()

profile = st.session_state.profile

st.markdown("#### 📌 Overview")
metric_row([
    ("Total Rows", f"{profile.total_rows:,}", "ok"),
    ("Total Columns", profile.total_columns, "ok"),
    ("Memory Usage", profile.memory_usage_human, "ok"),
    ("Columns w/ Missing Data", sum(1 for v in profile.missing_value_totals.values() if v > 0), "ok"),
])

st.write("")
tab_missing, tab_unique, tab_frequent, tab_numeric, tab_categorical = st.tabs(
    ["🕳️ Missing Values", "🔑 Unique Values", "⭐ Top Frequent Values", "🔢 Numeric Summary", "🔤 Categorical Summary"]
)

with tab_missing:
    st.dataframe(pipeline.missing_values_to_dataframe(profile), use_container_width=True, height=400)

with tab_unique:
    unique_df = pipeline.missing_values_to_dataframe(profile)[["Column", "Unique Values"]]
    st.dataframe(unique_df.sort_values("Unique Values", ascending=False), use_container_width=True, height=400)

with tab_frequent:
    selected_col = st.selectbox("Choose a column", options=profile.column_names, key="freq_col")
    items = profile.most_frequent_values.get(selected_col, [])
    if items:
        import pandas as pd
        freq_df = pd.DataFrame(items, columns=["Value", "Frequency"])
        st.bar_chart(freq_df.set_index("Value"))
        st.dataframe(freq_df, use_container_width=True)
    else:
        st.info("No values available for this column.")

with tab_numeric:
    numeric_df = pipeline.numeric_summary_to_dataframe(profile)
    if numeric_df.empty:
        st.info("No numeric columns detected in this dataset.")
    else:
        st.dataframe(numeric_df, use_container_width=True, height=350)

with tab_categorical:
    categorical_df = pipeline.categorical_summary_to_dataframe(profile)
    if categorical_df.empty:
        st.info("No categorical/text columns detected in this dataset.")
    else:
        st.dataframe(categorical_df, use_container_width=True, height=350)

st.divider()
st.page_link("pages/5_🧹_Data_Cleaning.py", label="➡️ Continue to Data Cleaning", icon="🧹")
