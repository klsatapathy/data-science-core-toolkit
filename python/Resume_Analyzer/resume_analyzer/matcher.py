"""
matcher.py
----------
Scores how well a resume matches a job description using:
1. TF-IDF cosine similarity (overall semantic/textual overlap)
2. Explicit skill overlap (which required skills are present/missing)

Final score is a weighted blend of both signals - pure TF-IDF similarity
tends to reward verbose resumes, so anchoring it with explicit skill
overlap gives a fairer, more explainable score (closer to how real
ATS systems behave).
"""

import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from resume_analyzer.skill_extractor import ALL_SKILLS
from resume_analyzer.nlp_utils import lemmatize_text


def _extract_skills_from_jd(jd_text: str) -> set:
    """Pull known skills mentioned in the job description."""
    jd_lower = jd_text.lower()
    found = set()
    for skill in ALL_SKILLS:
        pattern = r"(?<![\w])" + re.escape(skill) + r"(?![\w])"
        if re.search(pattern, jd_lower):
            found.add(skill)
    return found


def tfidf_similarity(resume_text: str, jd_text: str) -> float:
    """
    Cosine similarity between resume and JD, using TF-IDF vectors.
    Text is lemmatized via nltk first (if available) so 'developed' and
    'developing' aren't treated as different words - falls back to raw
    text automatically if nltk corpora aren't set up.
    """
    resume_processed = lemmatize_text(resume_text)
    jd_processed = lemmatize_text(jd_text)

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform([resume_processed, jd_processed])
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    return round(float(similarity) * 100, 2)


def skill_overlap(resume_skills_flat: set, jd_text: str) -> dict:
    """Compare resume skills against skills mentioned in the JD."""
    jd_skills = _extract_skills_from_jd(jd_text)

    if not jd_skills:
        return {
            "jd_skills_detected": [],
            "matched_skills": [],
            "missing_skills": [],
            "overlap_score": 0.0,
        }

    matched = sorted(jd_skills & resume_skills_flat)
    missing = sorted(jd_skills - resume_skills_flat)
    overlap_score = round(len(matched) / len(jd_skills) * 100, 2)

    return {
        "jd_skills_detected": sorted(jd_skills),
        "matched_skills": matched,
        "missing_skills": missing,
        "overlap_score": overlap_score,
    }


def compute_match_score(resume_text: str, jd_text: str, resume_skills: dict,
                         tfidf_weight: float = 0.4, skill_weight: float = 0.6) -> dict:
    """
    Blend TF-IDF similarity with explicit skill overlap into one
    final match score (0-100), plus the breakdown for transparency.
    """
    resume_skills_flat = {s for group in resume_skills.values() for s in group}

    tfidf_score = tfidf_similarity(resume_text, jd_text)
    overlap = skill_overlap(resume_skills_flat, jd_text)

    final_score = round(
        tfidf_weight * tfidf_score + skill_weight * overlap["overlap_score"], 2
    )

    return {
        "final_score": final_score,
        "tfidf_similarity": tfidf_score,
        "skill_overlap_score": overlap["overlap_score"],
        "matched_skills": overlap["matched_skills"],
        "missing_skills": overlap["missing_skills"],
        "jd_skills_detected": overlap["jd_skills_detected"],
    }
