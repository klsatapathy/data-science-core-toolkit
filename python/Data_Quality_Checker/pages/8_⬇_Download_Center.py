"""
pages/8_⬇_Download_Center.py
==============================
Central hub for downloading every artifact generated so far this
session: cleaned dataset, CSV/JSON/HTML reports, and charts. Purely a
presentation layer over files already written to disk by the backend
classes (DataCleaner.export, ReportGenerator.to_*, Visualizer.generate_all).
"""

from __future__ import annotations

import io
import zipfile

import streamlit as st

from streamlit_utils.ui import inject_global_css, page_header, render_sidebar_status, require_dataset

st.set_page_config(page_title="Download Center", page_icon="⬇️", layout="wide")
inject_global_css()
render_sidebar_status()
page_header("⬇️ Download Center", "Every artifact generated during this session, in one place.")

require_dataset()

available_files: dict[str, bytes] = {}

st.markdown("#### 🧹 Cleaned Dataset")
if "cleaned_export_path" in st.session_state:
    path = st.session_state.cleaned_export_path
    data = path.read_bytes()
    available_files["cleaned_dataset.csv"] = data
    st.download_button("⬇️ Download Cleaned Dataset (CSV)", data=data, file_name="cleaned_dataset.csv", mime="text/csv")
else:
    st.caption("Not generated yet — visit the **Data Cleaning** page.")

st.write("")
st.markdown("#### 📄 Reports")
if "report_paths" in st.session_state:
    report_paths = st.session_state.report_paths
    cols = st.columns(3)
    labels_mimes = {
        "csv": ("data_quality_report.csv", "text/csv"),
        "json": ("data_quality_report.json", "application/json"),
        "html": ("data_quality_report.html", "text/html"),
    }
    for col, (fmt, path) in zip(cols, report_paths.items()):
        filename, mime = labels_mimes[fmt]
        data = path.read_bytes()
        available_files[filename] = data
        with col:
            st.download_button(f"⬇️ {fmt.upper()} Report", data=data, file_name=filename, mime=mime, use_container_width=True)
else:
    st.caption("Not generated yet — visit the **Reports** page.")

st.write("")
st.markdown("#### 📈 Charts")
if "chart_paths" in st.session_state:
    chart_paths = st.session_state.chart_paths
    cols = st.columns(3)
    for i, path in enumerate(chart_paths):
        data = path.read_bytes()
        available_files[f"charts/{path.name}"] = data
        with cols[i % 3]:
            st.image(str(path), caption=path.name, use_container_width=True)
            st.download_button("⬇️ Download", data=data, file_name=path.name, mime="image/png", key=f"chart_dl_{i}")
else:
    st.caption("Not generated yet — visit the **Visualizations** page.")

st.divider()

st.markdown("#### 📦 Download Everything")
if available_files:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, data in available_files.items():
            zf.writestr(filename, data)
    buffer.seek(0)
    st.download_button(
        "⬇️ Download All as ZIP",
        data=buffer,
        file_name="data_quality_checker_results.zip",
        mime="application/zip",
        type="primary",
    )
else:
    st.info("Nothing has been generated yet. Run cleaning, reports, or visualizations first.")
