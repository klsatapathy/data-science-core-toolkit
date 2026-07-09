"""
pages/2_👀_Dataset_Preview.py
==============================
Shows head/tail rows, the full dataframe, and column dtypes for the
dataset currently loaded in session_state (no backend logic here --
purely display of the already-loaded pandas DataFrame).
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from streamlit_utils.ui import inject_global_css, metric_row, page_header, render_sidebar_status, require_dataset

st.set_page_config(page_title="Dataset Preview", page_icon="👀", layout="wide")
inject_global_css()
render_sidebar_status()
page_header("👀 Dataset Preview", "Inspect the structure of your dataset before running validation.")

require_dataset()
df = st.session_state.df

metric_row([
    ("Total Rows", f"{len(df):,}", "ok"),
    ("Total Columns", df.shape[1], "ok"),
    ("Duplicate Rows (raw)", int(df.duplicated().sum()), "ok" if df.duplicated().sum() == 0 else "warn"),
    ("Missing Cells", int(df.isna().sum().sum()), "ok" if df.isna().sum().sum() == 0 else "warn"),
])

st.write("")
tab_head, tab_tail, tab_full, tab_dtypes = st.tabs(
    ["🔝 First Rows", "🔚 Last Rows", "📋 Full Dataset", "🔤 Column Types"]
)

with tab_head:
    n_head = st.slider("Rows to show", 5, min(50, len(df)) or 5, min(10, len(df)) or 1, key="n_head")
    st.dataframe(df.head(n_head), use_container_width=True)

with tab_tail:
    n_tail = st.slider("Rows to show", 5, min(50, len(df)) or 5, min(10, len(df)) or 1, key="n_tail")
    st.dataframe(df.tail(n_tail), use_container_width=True)

with tab_full:
    st.dataframe(df, use_container_width=True, height=500)

with tab_dtypes:
    dtype_df = pd.DataFrame({
        "Column": df.columns,
        "Data Type": [str(dt) for dt in df.dtypes],
        "Non-Null Count": [int(df[c].notna().sum()) for c in df.columns],
        "Null Count": [int(df[c].isna().sum()) for c in df.columns],
    })
    st.dataframe(dtype_df, use_container_width=True, height=450)

st.divider()
st.page_link("pages/3_✅_Data_Validation.py", label="➡️ Continue to Data Validation", icon="✅")
