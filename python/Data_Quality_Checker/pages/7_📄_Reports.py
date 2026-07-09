"""
pages/7_📄_Reports.py
=======================
Generates CSV / JSON / HTML reports using the existing
`ReportGenerator` backend class and displays/download them.
No report-formatting logic is implemented in this file.
"""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from streamlit_utils import pipeline
from streamlit_utils.ui import inject_global_css, page_header, render_sidebar_status, require_profile, require_validation

st.set_page_config(page_title="Reports", page_icon="📄", layout="wide")
inject_global_css()
render_sidebar_status()
page_header("📄 Reports", "Generate and download reports produced by the existing ReportGenerator backend.")

require_validation()
require_profile()

df = st.session_state.df
validation_report = st.session_state.validation_report
profile = st.session_state.profile
cleaning_log = st.session_state.get("cleaning_log", [])
source_label = st.session_state.get("source_file_label", "uploaded_file.csv")

if st.button("📑 Generate Reports", type="primary"):
    with st.spinner("Generating CSV, JSON, and HTML reports..."):
        st.session_state.report_paths = pipeline.generate_reports(
            validation_report=validation_report,
            profile=profile,
            source_file=source_label,
            cleaning_log=cleaning_log,
        )
    st.success("Reports generated successfully!")

st.divider()

if "report_paths" not in st.session_state:
    st.info("Click **Generate Reports** to create downloadable CSV, JSON, and HTML reports.")
    st.stop()

paths = st.session_state.report_paths

tab_html, tab_json, tab_csv = st.tabs(["🌐 HTML Report", "🧾 JSON Report", "📊 CSV Report"])

with tab_html:
    html_content = paths["html"].read_text(encoding="utf-8")
    components.html(html_content, height=800, scrolling=True)
    st.download_button(
        "⬇️ Download HTML Report",
        data=html_content,
        file_name="data_quality_report.html",
        mime="text/html",
    )

with tab_json:
    json_content = paths["json"].read_text(encoding="utf-8")
    st.json(json.loads(json_content))
    st.download_button(
        "⬇️ Download JSON Report",
        data=json_content,
        file_name="data_quality_report.json",
        mime="application/json",
    )

with tab_csv:
    csv_df = pd.read_csv(paths["csv"])
    st.dataframe(csv_df, use_container_width=True, height=420)
    st.download_button(
        "⬇️ Download CSV Report",
        data=paths["csv"].read_bytes(),
        file_name="data_quality_report.csv",
        mime="text/csv",
    )

st.divider()
st.page_link("pages/8_⬇_Download_Center.py", label="➡️ Go to Download Center", icon="⬇️")
