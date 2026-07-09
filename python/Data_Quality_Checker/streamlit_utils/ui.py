"""
streamlit_utils/ui.py
=======================
Reusable, presentation-only UI helpers shared by every page: global CSS,
metric/status cards, the sidebar pipeline-progress tracker, and small
guard functions that stop a page early with a friendly message if a
prerequisite step (upload / validate / profile) hasn't run yet.

Nothing in this file touches the data_quality_checker backend directly.
"""

from __future__ import annotations

import streamlit as st

PRIMARY = "#2563eb"
SUCCESS = "#16a34a"
WARNING = "#d97706"
DANGER = "#dc2626"
MUTED = "#6b7280"


def inject_global_css() -> None:
    st.markdown(
        f"""
        <style>
            .block-container {{ padding-top: 2rem; padding-bottom: 3rem; max-width: 1200px; }}

            .dqc-hero {{
                background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
                border-radius: 16px;
                padding: 2.2rem 2.4rem;
                color: #f9fafb;
                margin-bottom: 1.6rem;
            }}
            .dqc-hero h1 {{ margin: 0 0 .4rem 0; font-size: 2rem; }}
            .dqc-hero p {{ color: #d1d5db; font-size: 1.02rem; margin: 0; }}

            .dqc-card {{
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                padding: 1.1rem 1.3rem;
                box-shadow: 0 1px 2px rgba(0,0,0,0.04);
                height: 100%;
            }}
            .dqc-card h4 {{ margin: 0 0 .35rem 0; color: #111827; }}
            .dqc-card p {{ margin: 0; color: {MUTED}; font-size: 0.92rem; }}

            .dqc-metric {{
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-left: 4px solid {PRIMARY};
                border-radius: 10px;
                padding: .85rem 1rem;
                text-align: left;
            }}
            .dqc-metric .label {{ font-size: 0.78rem; color: {MUTED}; text-transform: uppercase; letter-spacing: .03em; }}
            .dqc-metric .value {{ font-size: 1.6rem; font-weight: 700; color: #111827; line-height: 1.3; }}
            .dqc-metric.ok {{ border-left-color: {SUCCESS}; }}
            .dqc-metric.warn {{ border-left-color: {WARNING}; }}
            .dqc-metric.bad {{ border-left-color: {DANGER}; }}

            .dqc-badge {{
                display: inline-block;
                padding: .18rem .6rem;
                border-radius: 999px;
                font-size: .78rem;
                font-weight: 600;
            }}
            .dqc-badge.ok {{ background: #dcfce7; color: {SUCCESS}; }}
            .dqc-badge.warn {{ background: #fef3c7; color: {WARNING}; }}
            .dqc-badge.bad {{ background: #fee2e2; color: {DANGER}; }}

            .dqc-step {{ font-size: 0.86rem; padding: .15rem 0; }}
            .dqc-step .dot {{ display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:8px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="dqc-hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_for(count: int | None, zero_is_ok: bool = True) -> str:
    """Map an issue count to a status keyword: ok / warn / bad."""
    if count is None:
        return "ok"
    if count == 0:
        return "ok" if zero_is_ok else "warn"
    return "bad"


def metric_card(label: str, value, status: str = "ok") -> None:
    st.markdown(
        f"""
        <div class="dqc-metric {status}">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_row(items: list[tuple[str, object, str]]) -> None:
    """items: list of (label, value, status)."""
    cols = st.columns(len(items))
    for col, (label, value, status) in zip(cols, items):
        with col:
            metric_card(label, value, status)


def badge(text: str, status: str = "ok") -> str:
    return f'<span class="dqc-badge {status}">{text}</span>'


def feature_card(title: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="dqc-card">
            <h4>{title}</h4>
            <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------
# Sidebar pipeline tracker
# --------------------------------------------------------------------------
def render_sidebar_status() -> None:
    st.sidebar.markdown("### Pipeline Status")

    steps = [
        ("Dataset uploaded", "df" in st.session_state),
        ("Validation run", "validation_report" in st.session_state),
        ("Profiling run", "profile" in st.session_state),
        ("Cleaning applied", "cleaned_df" in st.session_state),
        ("Charts generated", "chart_paths" in st.session_state),
        ("Reports generated", "report_paths" in st.session_state),
    ]
    done_count = sum(1 for _, done in steps if done)
    st.sidebar.progress(done_count / len(steps))

    for label, done in steps:
        color = SUCCESS if done else "#d1d5db"
        mark = "✓" if done else "○"
        st.sidebar.markdown(
            f'<div class="dqc-step"><span class="dot" style="background:{color}"></span>'
            f"{mark} {label}</div>",
            unsafe_allow_html=True,
        )

    if "source_file_label" in st.session_state:
        st.sidebar.markdown("---")
        st.sidebar.caption(f"📄 Current file: **{st.session_state.source_file_label}**")


# --------------------------------------------------------------------------
# Guards
# --------------------------------------------------------------------------
def require_dataset() -> bool:
    """Stop the page with a friendly prompt if no dataset has been loaded yet."""
    if "df" not in st.session_state:
        st.warning("No dataset loaded yet.")
        st.page_link("pages/1_📂_Upload_Dataset.py", label="➡️ Go to Upload Dataset", icon="📂")
        st.stop()
    return True


def require_validation() -> bool:
    require_dataset()
    if "validation_report" not in st.session_state:
        st.info("Validation hasn't been run yet for this dataset.")
        st.page_link("pages/3_✅_Data_Validation.py", label="➡️ Go to Data Validation", icon="✅")
        st.stop()
    return True


def require_profile() -> bool:
    require_dataset()
    if "profile" not in st.session_state:
        st.info("Profiling hasn't been run yet for this dataset.")
        st.page_link("pages/4_📊_Data_Profiling.py", label="➡️ Go to Data Profiling", icon="📊")
        st.stop()
    return True
