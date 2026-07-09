"""
AI Resume Analyzer - CLI entry point
=====================================
Usage examples:

  # Analyze a single resume (parsing + suggestions only)
  python main.py analyze --resume sample_data/resume_1.txt

  # Analyze a single resume AND match it against a job description
  python main.py analyze --resume sample_data/resume_1.txt --jd sample_data/job_description.txt

  # Rank every resume in a folder against a job description (recruiter mode)
  python main.py rank --resume-dir sample_data --jd sample_data/job_description.txt
"""

import argparse
import json
import os

from resume_analyzer.parser import extract_text, clean_text, split_into_lines, extract_hyperlinks
from resume_analyzer.skill_extractor import analyze_resume_structure
from resume_analyzer.matcher import compute_match_score
from resume_analyzer.suggestions import generate_suggestions
from resume_analyzer.ranker import rank_resumes, print_ranking


def analyze_single_resume(resume_path: str, jd_path: str = None, as_json: bool = False):
    raw_text = extract_text(resume_path)
    text = clean_text(raw_text)
    lines = split_into_lines(text)
    hyperlinks = extract_hyperlinks(resume_path)

    profile = analyze_resume_structure(text, lines, hyperlinks)
    findings = generate_suggestions(text, lines, profile)

    result = {
        "file": os.path.basename(resume_path),
        "profile": profile,
        "suggestions": findings,
    }

    if jd_path:
        jd_text = clean_text(extract_text(jd_path))
        match = compute_match_score(text, jd_text, profile["skills"])
        result["job_match"] = match

    if as_json:
        print(json.dumps(result, indent=2))
        return result

    _pretty_print(result)
    return result


def _pretty_print(result: dict):
    profile = result["profile"]
    print("\n" + "=" * 70)
    print(f"RESUME ANALYSIS: {result['file']}")
    print("=" * 70)

    print("\n--- Contact Info ---")
    for k, v in profile["contact"].items():
        print(f"  {k.capitalize():10}: {v or 'Not found'}")

    print(f"\n--- Experience & Education ---")
    print(f"  Years of experience mentioned: {profile['years_experience']}")
    print(f"  Education levels detected: {', '.join(profile['education']) or 'None detected'}")

    print(f"\n--- Skills Detected ---")
    if profile["skills"]:
        for category, skills in profile["skills"].items():
            print(f"  {category}: {', '.join(skills)}")
    else:
        print("  No known skills detected.")

    print(f"\n--- Sections Found ---")
    print(f"  {', '.join(profile['sections_found']) or 'None clearly detected'}")

    print(f"\n--- Improvement Suggestions ---")
    for s in result["suggestions"]:
        icon = {"good": "[OK]", "warning": "[!!]", "info": "[i]"}.get(s["status"], "-")
        print(f"  {icon} {s['check']}: {s['detail']}")

    if "job_match" in result:
        match = result["job_match"]
        print(f"\n--- Job Description Match ---")
        print(f"  Final match score : {match['final_score']}/100")
        print(f"  TF-IDF similarity : {match['tfidf_similarity']}")
        print(f"  Skill overlap     : {match['skill_overlap_score']}%")
        print(f"  Matched skills    : {', '.join(match['matched_skills']) or 'None'}")
        print(f"  Missing skills    : {', '.join(match['missing_skills']) or 'None'}")

    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(description="AI Resume Analyzer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="Analyze a single resume")
    analyze_parser.add_argument("--resume", required=True, help="Path to resume file (pdf/docx/txt)")
    analyze_parser.add_argument("--jd", required=False, help="Path to job description file")
    analyze_parser.add_argument("--json", action="store_true", help="Output raw JSON instead of pretty print")

    rank_parser = subparsers.add_parser("rank", help="Rank multiple resumes against a job description")
    rank_parser.add_argument("--resume-dir", required=True, help="Folder containing resume files")
    rank_parser.add_argument("--jd", required=True, help="Path to job description file")

    args = parser.parse_args()

    if args.command == "analyze":
        analyze_single_resume(args.resume, args.jd, args.json)
    elif args.command == "rank":
        jd_text = clean_text(extract_text(args.jd))
        results = rank_resumes(args.resume_dir, jd_text, jd_filename=os.path.basename(args.jd))
        print_ranking(results)


if __name__ == "__main__":
    main()
