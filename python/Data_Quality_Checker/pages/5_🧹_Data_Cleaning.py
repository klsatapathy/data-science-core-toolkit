"""
pages/5_🧹_Data_Cleaning.py
=============================
Presents cleaning options and applies them via the existing
`DataCleaner` class (through `streamlit_utils.pipeline.run_cleaning`).
No cleaning logic is implemented in this file.
"""

from __future__ import annotations

import streamlit as st

from data_quality_checker import config
from data_quality_checker.exceptions import InvalidCleaningStrategyError
from streamlit_utils import pipeline
from streamlit_utils.ui import inject_global_css, page_header, render_sidebar_status, require_dataset

st.set_page_config(page_title="Data Cleaning", page_icon="🧹", layout="wide")
inject_global_css()
render_sidebar_status()
page_header("🧹 Data Cleaning", "Apply optional cleaning operations using the existing DataCleaner backend.")

require_dataset()
df = st.session_state.df

with st.form("cleaning_form"):
    st.markdown("#### ⚙️ Choose cleaning operations")

    col1, col2 = st.columns(2)
    with col1:
        remove_duplicates = st.checkbox("Remove duplicate rows", value=True)
        trim_whitespace = st.checkbox("Trim leading/trailing whitespace", value=True)
        text_case = st.selectbox("Standardize text casing", options=["none", "lower", "upper", "title"], index=0)

    with col2:
        fill_strategy = st.selectbox(
            "Fill missing values",
            options=["none"] + list(config.FILL_STRATEGIES),
            index=0,
            help="Numeric-only strategies (mean/median) fall back to mode on text columns.",
        )
        fill_constant = None
        if fill_strategy == "constant":
            fill_constant = st.text_input("Constant value to fill with", value="")

        date_columns = st.multiselect(
            "Convert date columns to a standard format",
            options=list(df.columns),
        )
        date_format = st.text_input("Target date format", value="%Y-%m-%d", disabled=not date_columns)

    submitted = st.form_submit_button("🧹 Apply Cleaning", type="primary", use_container_width=True)

if submitted:
    try:
        with st.spinner("Applying cleaning operations..."):
            cleaner = pipeline.run_cleaning(
                df,
                remove_duplicates=remove_duplicates,
                trim_whitespace=trim_whitespace,
                text_case=text_case,
                date_columns=date_columns,
                date_format=date_format,
                fill_strategy=fill_strategy,
                fill_constant=fill_constant,
            )
            export_path = pipeline.export_cleaned_dataset(cleaner)
        st.session_state.cleaned_df = cleaner.get_cleaned_data()
        st.session_state.cleaning_log = cleaner.get_cleaning_log()
        st.session_state.cleaned_export_path = export_path
        st.success("Cleaning applied successfully!")
    except InvalidCleaningStrategyError as exc:
        st.error(f"Invalid cleaning configuration: {exc}")

st.divider()

if "cleaned_df" not in st.session_state:
    st.info("Configure the options above and click **Apply Cleaning** to see results here.")
    st.stop()

cleaned_df = st.session_state.cleaned_df

st.markdown("#### 📝 Cleaning Log")
if st.session_state.cleaning_log:
    for entry in st.session_state.cleaning_log:
        st.markdown(f"- {entry}")
else:
    st.caption("No operations were selected.")

st.markdown("#### 👀 Cleaned Dataset Preview")
before_col, after_col = st.columns(2)
with before_col:
    st.caption(f"Before: {df.shape[0]:,} rows × {df.shape[1]} columns")
    st.dataframe(df.head(10), use_container_width=True)
with after_col:
    st.caption(f"After: {cleaned_df.shape[0]:,} rows × {cleaned_df.shape[1]} columns")
    st.dataframe(cleaned_df.head(10), use_container_width=True)

st.write("")
with open(st.session_state.cleaned_export_path, "rb") as fh:
    st.download_button(
        "⬇️ Download Cleaned CSV",
        data=fh.read(),
        file_name="cleaned_dataset.csv",
        mime="text/csv",
        type="primary",
    )

st.divider()
st.page_link("pages/6_📈_Visualizations.py", label="➡️ Continue to Visualizations", icon="📈")
