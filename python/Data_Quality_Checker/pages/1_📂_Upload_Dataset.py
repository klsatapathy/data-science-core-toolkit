"""
pages/1_📂_Upload_Dataset.py
=============================
Upload a CSV (or load the bundled sample dataset) and hand it to the
existing `CSVLoader` backend class via `streamlit_utils.pipeline`.
"""

from __future__ import annotations

import streamlit as st

from data_quality_checker.exceptions import DataQualityCheckerError
from streamlit_utils import pipeline
from streamlit_utils.ui import inject_global_css, metric_row, page_header, render_sidebar_status

st.set_page_config(page_title="Upload Dataset", page_icon="📂", layout="wide")
inject_global_css()
render_sidebar_status()
page_header("📂 Upload Dataset", "Load a CSV file to begin the data-quality workflow.")

col_upload, col_sample = st.columns([3, 1])

with col_upload:
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=["csv", "tsv", "txt"],
        help="Encoding and delimiter are auto-detected by the backend CSVLoader.",
    )

with col_sample:
    st.write("")
    st.write("")
    use_sample = st.button("📁 Load Sample Dataset", use_container_width=True)

new_file_selected = uploaded_file is not None and (
    "source_key" not in st.session_state
    or st.session_state.source_key != (uploaded_file.name, uploaded_file.size)
)

if use_sample:
    pipeline.reset_session(keep_workdir=False)
    try:
        with st.spinner("Loading sample dataset..."):
            df, metadata = pipeline.load_sample_dataset()
        st.session_state.df = df
        st.session_state.load_metadata = metadata
        st.session_state.source_file_label = "sample_customers.csv (bundled sample)"
        st.session_state.source_key = ("sample_customers.csv", metadata.file_size_bytes)
        st.success("Sample dataset loaded successfully!")
    except DataQualityCheckerError as exc:
        st.error(f"Could not load the sample dataset: {exc}")

elif new_file_selected:
    pipeline.reset_session(keep_workdir=False)
    try:
        with st.spinner(f"Loading '{uploaded_file.name}'..."):
            df, metadata = pipeline.load_uploaded_file(uploaded_file)
        st.session_state.df = df
        st.session_state.load_metadata = metadata
        st.session_state.source_file_label = uploaded_file.name
        st.session_state.source_key = (uploaded_file.name, uploaded_file.size)
        st.success(f"'{uploaded_file.name}' loaded and validated as a readable CSV file!")
    except DataQualityCheckerError as exc:
        st.error(
            f"**{type(exc).__name__}:** {exc}\n\n"
            "Please check the file and try again — common causes are an unsupported "
            "extension, a corrupted/empty file, or an undetectable encoding."
        )
    except Exception as exc:  # pragma: no cover - safety net
        st.error(f"An unexpected error occurred while loading the file: {exc}")

st.divider()

if "df" in st.session_state:
    df = st.session_state.df
    metadata = st.session_state.load_metadata

    st.markdown("#### 📌 File Summary")
    metric_row([
        ("Filename", st.session_state.source_file_label, "ok"),
        ("File Size", pipeline.human_readable_size(metadata.file_size_bytes), "ok"),
        ("Rows", f"{metadata.row_count:,}", "ok"),
        ("Columns", metadata.column_count, "ok"),
    ])

    st.write("")
    with st.expander("🔧 Detected file properties"):
        st.write(f"**Detected encoding:** `{metadata.detected_encoding}`")
        st.write(f"**Detected delimiter:** `{metadata.delimiter!r}`")
        st.write(f"**Loaded via chunked reads (large file):** {metadata.chunked}")
        if metadata.warnings:
            for w in metadata.warnings:
                st.warning(w)

    st.success("Dataset is ready. Continue to **Dataset Preview** in the sidebar.")
    st.page_link("pages/2_👀_Dataset_Preview.py", label="➡️ Go to Dataset Preview", icon="👀")
else:
    st.info("Upload a CSV file above, or click **Load Sample Dataset** to try the app instantly.")
