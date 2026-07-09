# 📄 AI Resume Analyzer

An ATS-style resume analyzer with a web UI — upload a resume, paste a job
description, and instantly get an ATS match score, missing-skill detection,
and improvement suggestions.

Built with **Streamlit**, **scikit-learn** (TF-IDF + cosine similarity),
**nltk**, and **spaCy** — no paid APIs, runs fully locally.

## ✨ Features

- 📤 **Resume upload** — PDF, DOCX, or TXT
- 📋 **Job description paste** — plain text box, no file needed
- ❌ **Missing skills detection** — see exactly what the JD wants that your resume doesn't show
- 🎯 **ATS score** — blended TF-IDF similarity + required-skill overlap (0–100)
- 💡 **Improvement suggestions** — resume length, action verbs vs. passive phrasing, quantified impact, missing sections, missing contact info
- 🧠 **Bonus NLP** (when nltk/spaCy are set up) — lemmatized matching for more accurate scoring, spaCy-detected organizations and candidate skill phrases

## 🖥️ Demo

Run locally with:
```bash
streamlit run streamlit_app.py
```

## 🧩 How it works

The engine works fully with just `scikit-learn` + regex — no internet or
GPU required. `nltk` and `spaCy` are wired in as **optional enhancers**: if
installed and their data/models are downloaded, results get sharper. If
not, the app still works completely, just without that extra polish. The
sidebar in the app shows which engines are active.

**ATS score formula:**
```
final_score = 0.4 × TF-IDF_similarity + 0.6 × skill_overlap
```
Pure TF-IDF similarity rewards verbose resumes that just share a lot of
words with the JD, even if actual required skills are missing. Anchoring
the score with explicit skill overlap makes it fairer and explainable — you
can see exactly *why* a resume scored the way it did.

## 📁 Project structure

```
resume_analyzer/
├── streamlit_app.py                 # Web UI (upload + paste + analyze)
├── main.py                          # CLI entry point (analyze / rank)
├── requirements.txt
├── resume_analyzer/
│   ├── parser.py                    # PDF/DOCX/TXT text extraction
│   ├── skill_extractor.py           # skills DB + contact/education/experience extraction
│   ├── nlp_utils.py                 # optional nltk/spaCy wrappers with graceful fallback
│   ├── matcher.py                   # TF-IDF + skill-overlap ATS scoring
│   ├── suggestions.py               # rule-based resume quality checks
│   └── ranker.py                    # batch ranking across many resumes (CLI only)
└── sample_data/
    ├── job_description.txt
    ├── resume_1.txt                 # strong-fit example
    └── resume_2.txt                 # weak-fit example
```

## 🚀 Setup

```bash
git clone https://github.com/YOUR_USERNAME/resume-analyzer.git
cd resume-analyzer
pip install -r requirements.txt
```

**Optional but recommended** — unlocks the nltk/spaCy bonus features:

```bash
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('stopwords'); nltk.download('wordnet')"
```

If you skip this step, the app still runs fine — the sidebar just shows those two engines as "not set up."

## ▶️ Usage

### Web app (recommended)
```bash
streamlit run streamlit_app.py
```
Opens at `http://localhost:8501`. Upload a resume, paste a job description, click **Analyze Resume**.

### CLI
```bash
# Analyze a single resume
python main.py analyze --resume sample_data/resume_1.txt --jd sample_data/job_description.txt

# Rank every resume in a folder against a job description (recruiter mode)
python main.py rank --resume-dir sample_data --jd sample_data/job_description.txt
```

## 🌐 Live Demo

Deployed at: _add your Streamlit Community Cloud link here after deploying_

## 🛠️ Tech Stack

- Python
- Streamlit (web UI)
- scikit-learn (TF-IDF vectorization + cosine similarity)
- nltk (lemmatization)
- spaCy (NER, noun-phrase extraction)
- pdfplumber / python-docx (file parsing)

## 🔮 Future improvements

- Swap the curated skills database for a larger public taxonomy (e.g. ESCO or O*NET)
- Add a grammar checker (`language_tool_python`) for real grammar suggestions
- Let users review/approve spaCy's bonus noun-phrase skill suggestions in the UI
- Add resume-to-resume similarity to flag near-duplicate/templated resumes in a batch

## 📄 License

MIT — free to use, modify, and share.
