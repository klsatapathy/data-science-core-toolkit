"""
suggestions.py
--------------
Rule-based resume quality checks. No ML here on purpose - these are the
same heuristics human reviewers and ATS-adjacent tools actually use:
length, action verbs, quantified impact, passive voice, missing sections,
contact completeness, and bullet-point consistency.
"""

import re

ACTION_VERBS = {
    "led", "built", "created", "developed", "designed", "implemented",
    "managed", "improved", "increased", "reduced", "launched", "optimized",
    "automated", "delivered", "achieved", "drove", "spearheaded", "architected",
    "analyzed", "streamlined", "mentored", "coordinated", "executed", "deployed"
}

WEAK_PHRASES = [
    "responsible for", "worked on", "helped with", "duties included",
    "in charge of", "tasked with"
]

PASSIVE_HINTS = re.compile(
    r"\b(was|were|is|are|been|being)\s+\w+ed\b", re.IGNORECASE
)

QUANTIFIER_RE = re.compile(r"\d+%|\$\d+|\d+x|\d+\+|\d{2,}")

IDEAL_WORD_COUNT_RANGE = (350, 900)  # roughly 1-2 pages


def check_length(word_count: int) -> dict:
    low, high = IDEAL_WORD_COUNT_RANGE
    if word_count < low:
        return {
            "check": "Resume length",
            "status": "warning",
            "detail": f"Only {word_count} words - likely too short (aim for {low}-{high}). "
                      "Consider adding more detail on projects or achievements."
        }
    if word_count > high:
        return {
            "check": "Resume length",
            "status": "warning",
            "detail": f"{word_count} words - likely too long for most recruiters "
                      f"(aim for {low}-{high}). Trim less relevant older experience."
        }
    return {
        "check": "Resume length",
        "status": "good",
        "detail": f"{word_count} words - within a healthy range."
    }


def check_action_verbs(lines: list) -> dict:
    bullet_lines = [l for l in lines if l.startswith(("-", "•", "*")) or re.match(r"^\d+\.", l)]
    if not bullet_lines:
        bullet_lines = lines  # fall back to all lines if no bullets detected

    strong_count = 0
    weak_count = 0
    for line in bullet_lines:
        first_word = re.sub(r"^[-•*\d.\s]+", "", line).split(" ")[0].lower().strip(",.")
        if first_word in ACTION_VERBS:
            strong_count += 1
        if any(phrase in line.lower() for phrase in WEAK_PHRASES):
            weak_count += 1

    if weak_count > 0:
        return {
            "check": "Action verbs & phrasing",
            "status": "warning",
            "detail": f"Found {weak_count} weak/passive phrase(s) like 'responsible for' or "
                      "'worked on'. Replace with strong action verbs (e.g., 'led', 'built', "
                      "'improved')."
        }
    if strong_count == 0:
        return {
            "check": "Action verbs & phrasing",
            "status": "warning",
            "detail": "Few or no bullet points start with strong action verbs. Start "
                      "achievement bullets with verbs like 'Built', 'Led', 'Reduced'."
        }
    return {
        "check": "Action verbs & phrasing",
        "status": "good",
        "detail": f"{strong_count} bullet(s) start with strong action verbs."
    }


def check_quantified_impact(text: str) -> dict:
    matches = QUANTIFIER_RE.findall(text)
    if len(matches) == 0:
        return {
            "check": "Quantified impact",
            "status": "warning",
            "detail": "No numbers, percentages, or metrics detected. Add measurable impact, "
                      "e.g., 'improved model accuracy by 12%' or 'reduced processing time by 3x'."
        }
    return {
        "check": "Quantified impact",
        "status": "good",
        "detail": f"Found {len(matches)} quantified metric(s) - good use of measurable impact."
    }


def check_contact_info(contact: dict) -> dict:
    missing = [k for k, v in contact.items() if not v]
    if "email" in missing or "phone" in missing:
        return {
            "check": "Contact information",
            "status": "warning",
            "detail": f"Missing key contact info: {', '.join(missing)}."
        }
    if missing:
        return {
            "check": "Contact information",
            "status": "info",
            "detail": f"Consider adding: {', '.join(missing)} (helps recruiters find your profile)."
        }
    return {
        "check": "Contact information",
        "status": "good",
        "detail": "All key contact details present."
    }


def check_sections(sections_found: list) -> dict:
    expected = {"experience", "education", "skills"}
    normalized_found = set()
    for s in sections_found:
        for exp in expected:
            if exp in s:
                normalized_found.add(exp)

    missing = expected - normalized_found
    if missing:
        return {
            "check": "Resume sections",
            "status": "warning",
            "detail": f"Could not clearly detect section(s): {', '.join(sorted(missing))}. "
                      "Use clear headers so both recruiters and ATS parsers find them."
        }
    return {
        "check": "Resume sections",
        "status": "good",
        "detail": "Core sections (experience, education, skills) detected."
    }


def generate_suggestions(text: str, lines: list, profile: dict) -> list:
    """Run every check and return a consolidated list of findings."""
    return [
        check_length(profile["word_count"]),
        check_action_verbs(lines),
        check_quantified_impact(text),
        check_contact_info(profile["contact"]),
        check_sections(profile["sections_found"]),
    ]
