"""
streamlit_app.py
----------------
Web UI for the AI Resume Analyzer.

Run with:
    streamlit run streamlit_app.py

Features:
- Resume upload (PDF / DOCX / TXT)
- Job description paste
- Missing skills detection
- ATS match score
- Improvement suggestions
"""

import tempfile
import os
import streamlit as st

from resume_analyzer.parser import extract_text, clean_text, split_into_lines, extract_hyperlinks
from resume_analyzer.skill_extractor import analyze_resume_structure
from resume_analyzer.matcher import compute_match_score
from resume_analyzer.suggestions import generate_suggestions
from resume_analyzer.nlp_utils import nlp_status, extract_noun_phrases

st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="wide")

st.title("📄 AI Resume Analyzer")
st.caption("Upload a resume, paste a job description, and get an ATS score, "
           "missing-skill detection, and improvement suggestions.")

# ---- Sidebar: NLP backend status ----
status = nlp_status()
with st.sidebar:
    st.subheader("⚙️ NLP Engine Status")
    st.write("✅ scikit-learn (TF-IDF + ATS scoring): active")
    st.write(f"{'✅' if status['nltk_active'] else '⚠️'} nltk (lemmatization): "
             f"{'active' if status['nltk_active'] else 'not set up - see README'}")
    st.write(f"{'✅' if status['spacy_active'] else '⚠️'} spaCy (bonus skill/org detection): "
             f"{'active' if status['spacy_active'] else 'not set up - see README'}")
    st.caption("The app works fully with just scikit-learn. nltk and spaCy "
               "add extra polish when installed and downloaded.")

# ---- Inputs ----
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Upload Resume")
    uploaded_file = st.file_uploader(
        "Upload your resume (PDF, DOCX, or TXT)",
        type=["pdf", "docx", "txt"],
    )

with col2:
    st.subheader("2. Paste Job Description")
    jd_text_input = st.text_area(
        "Paste the job description here",
        height=250,
        placeholder="Paste the full job description text...",
    )

analyze_clicked = st.button("🔍 Analyze Resume", type="primary", use_container_width=True)

# ---- Analysis ----
if analyze_clicked:
    if uploaded_file is None:
        st.error("Please upload a resume file first.")
    elif not jd_text_input.strip():
        st.error("Please paste a job description first.")
    else:
        with st.spinner("Analyzing resume..."):
            # Save uploaded file to a temp path so our existing parser can read it
            suffix = os.path.splitext(uploaded_file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            try:
                raw_text = extract_text(tmp_path)
                text = clean_text(raw_text)
                lines = split_into_lines(text)
                hyperlinks = extract_hyperlinks(tmp_path)

                profile = analyze_resume_structure(text, lines, hyperlinks)
                findings = generate_suggestions(text, lines, profile)

                jd_text = clean_text(jd_text_input)
                match = compute_match_score(text, jd_text, profile["skills"])
            finally:
                os.unlink(tmp_path)

        st.success("Analysis complete!")

        # ---- ATS Score ----
        st.subheader("🎯 ATS Match Score")
        score_col, tfidf_col, overlap_col = st.columns(3)
        score_col.metric("Overall ATS Score", f"{match['final_score']} / 100")
        tfidf_col.metric("Text Similarity", f"{match['tfidf_similarity']}")
        overlap_col.metric("Required-Skill Overlap", f"{match['skill_overlap_score']}%")
        st.progress(min(int(match["final_score"]), 100) / 100)

        # ---- Skills ----
        st.subheader("🧩 Skills")
        skill_col1, skill_col2 = st.columns(2)
        with skill_col1:
            st.markdown("**✅ Matched Skills** (present in resume & required by JD)")
            if match["matched_skills"]:
                st.write(", ".join(match["matched_skills"]))
            else:
                st.write("None detected.")
        with skill_col2:
            st.markdown("**❌ Missing Skills** (required by JD, not found in resume)")
            if match["missing_skills"]:
                st.write(", ".join(match["missing_skills"]))
            else:
                st.write("None - great coverage!")

        with st.expander("All skills detected in resume (by category)"):
            if profile["skills"]:
                for category, skills in profile["skills"].items():
                    st.write(f"**{category.replace('_', ' ').title()}:** {', '.join(skills)}")
            else:
                st.write("No known skills detected.")

        if status["spacy_active"]:
            with st.expander("Bonus: additional candidate phrases (spaCy, unverified)"):
                phrases = extract_noun_phrases(text)
                st.caption("These are noun phrases spaCy picked up that may indicate "
                           "skills/tools not in our fixed skills list - review manually.")
                st.write(", ".join(phrases) if phrases else "None found.")

        # ---- Profile summary ----
        st.subheader("👤 Resume Profile")
        p_col1, p_col2, p_col3 = st.columns(3)
        p_col1.write(f"**Email:** {profile['contact']['email'] or 'Not found'}")
        p_col1.write(f"**Phone:** {profile['contact']['phone'] or 'Not found'}")
        p_col2.write(f"**LinkedIn:** {profile['contact']['linkedin'] or 'Not found'}")
        p_col2.write(f"**GitHub:** {profile['contact']['github'] or 'Not found'}")
        p_col3.write(f"**Years of experience:** {profile['years_experience']}")
        p_col3.write(f"**Education:** {', '.join(profile['education']) or 'Not detected'}")

        if profile.get("organizations_detected"):
            st.write(f"**Organizations detected (spaCy):** "
                     f"{', '.join(profile['organizations_detected'])}")

        # ---- Suggestions ----
        st.subheader("💡 Improvement Suggestions")
        icon_map = {"good": "✅", "warning": "⚠️", "info": "ℹ️"}
        for f in findings:
            st.write(f"{icon_map.get(f['status'], '•')} **{f['check']}**: {f['detail']}")

st.divider()
st.caption("Built with pdfplumber, python-docx, scikit-learn, nltk & spaCy "
           "(nltk/spaCy enhance results when set up, but aren't required to run the app).")
