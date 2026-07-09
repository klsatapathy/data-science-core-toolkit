"""
ranker.py
---------
Ranks multiple resumes against a single job description - the
"recruiter view": given a folder of resumes, who should I look at first?
"""

import os
from resume_analyzer.parser import extract_text, clean_text, split_into_lines, extract_hyperlinks
from resume_analyzer.skill_extractor import analyze_resume_structure
from resume_analyzer.matcher import compute_match_score


def rank_resumes(resume_dir: str, jd_text: str, jd_filename: str = None) -> list:
    """
    Analyze every resume in a directory against a job description and
    return them sorted best-match first. `jd_filename` (if given) is
    excluded, in case the JD file lives in the same folder as resumes.
    """
    results = []
    supported_ext = (".pdf", ".docx", ".txt")

    for filename in os.listdir(resume_dir):
        if not filename.lower().endswith(supported_ext):
            continue
        if jd_filename and filename == jd_filename:
            continue

        filepath = os.path.join(resume_dir, filename)
        try:
            raw_text = extract_text(filepath)
            text = clean_text(raw_text)
            lines = split_into_lines(text)
            hyperlinks = extract_hyperlinks(filepath)
            profile = analyze_resume_structure(text, lines, hyperlinks)
            match = compute_match_score(text, jd_text, profile["skills"])

            results.append({
                "filename": filename,
                "final_score": match["final_score"],
                "tfidf_similarity": match["tfidf_similarity"],
                "skill_overlap_score": match["skill_overlap_score"],
                "matched_skills": match["matched_skills"],
                "missing_skills": match["missing_skills"],
                "years_experience": profile["years_experience"],
                "education": profile["education"],
            })
        except Exception as e:
            results.append({
                "filename": filename,
                "error": str(e),
                "final_score": -1,
            })

    results.sort(key=lambda r: r["final_score"], reverse=True)
    return results


def print_ranking(results: list) -> None:
    print("\n" + "=" * 70)
    print("RESUME RANKING (best match first)")
    print("=" * 70)
    for i, r in enumerate(results, start=1):
        if r.get("final_score", -1) < 0:
            print(f"{i}. {r['filename']} - ERROR: {r.get('error')}")
            continue
        print(f"\n{i}. {r['filename']}  ->  Score: {r['final_score']}/100")
        print(f"   TF-IDF similarity: {r['tfidf_similarity']} | "
              f"Skill overlap: {r['skill_overlap_score']}%")
        print(f"   Experience: {r['years_experience']} yrs | "
              f"Education: {', '.join(r['education']) or 'N/A'}")
        if r["matched_skills"]:
            print(f"   Matched skills: {', '.join(r['matched_skills'])}")
        if r["missing_skills"]:
            print(f"   Missing skills: {', '.join(r['missing_skills'])}")
    print("\n" + "=" * 70)
