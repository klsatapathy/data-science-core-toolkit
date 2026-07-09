"""
skill_extractor.py
-------------------
Extracts structured information from resume text:
- Contact info (email, phone, LinkedIn)
- Skills (technical + soft), matched against a curated skills database
- Education level
- Years of experience
- Detected resume sections
"""

import re

from resume_analyzer.nlp_utils import extract_organizations

# A curated skills database. Extend freely - this is the "knowledge base"
# that stands in for a trained NER model.
SKILLS_DB = {
    "programming_languages": [
        "python", "java", "c++", "c#", "javascript", "typescript", "r", "go",
        "rust", "scala", "sql", "php", "ruby", "kotlin", "swift", "matlab"
    ],
    "data_science": [
        "machine learning", "deep learning", "nlp", "natural language processing",
        "computer vision", "data analysis", "data visualization", "statistics",
        "pandas", "numpy", "scikit-learn", "sklearn", "tensorflow", "pytorch",
        "keras", "opencv", "xgboost", "matplotlib", "seaborn", "power bi",
        "tableau", "etl", "data mining", "feature engineering", "a/b testing",
        "time series", "regression", "classification", "clustering"
    ],
    "web_dev": [
        "react", "angular", "vue", "node.js", "django", "flask", "fastapi",
        "html", "css", "rest api", "graphql", "next.js", "express"
    ],
    "cloud_devops": [
        "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd", "jenkins",
        "terraform", "linux", "git", "github actions", "airflow"
    ],
    "databases": [
        "mysql", "postgresql", "mongodb", "redis", "oracle", "sqlite",
        "cassandra", "elasticsearch", "snowflake", "bigquery"
    ],
    "soft_skills": [
        "leadership", "communication", "teamwork", "problem solving",
        "project management", "time management", "collaboration",
        "critical thinking", "adaptability", "mentoring", "stakeholder management"
    ],
}

# Flatten for quick lookup, longest phrases first so "machine learning" is
# matched before "learning" alone, etc.
ALL_SKILLS = sorted(
    {skill for group in SKILLS_DB.values() for skill in group},
    key=len,
    reverse=True,
)

EDUCATION_KEYWORDS = {
    "phd": ["phd", "ph.d", "doctorate"],
    "masters": ["m.tech", "mtech", "m.sc", "msc", "mba", "master of", "m.s.", "ms "],
    "bachelors": ["b.tech", "btech", "b.sc", "bsc", "bachelor of", "b.e.", "be "],
    "diploma": ["diploma"],
}

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(
    r"(\+\d{1,3}[\s-]?)?(\(?\d{3,5}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4}"
)
LINKEDIN_RE = re.compile(r"(linkedin\.com/in/[\w-]+)", re.IGNORECASE)
GITHUB_RE = re.compile(r"(github\.com/[\w-]+)", re.IGNORECASE)
YEARS_EXP_RE = re.compile(r"(\d+)\+?\s*(?:years|yrs)\s*(?:of)?\s*experience", re.IGNORECASE)

SECTION_HEADERS = [
    "experience", "work experience", "professional experience", "education",
    "skills", "technical skills", "projects", "certifications", "summary",
    "objective", "achievements", "publications", "awards"
]


def extract_contact_info(text: str, hyperlinks: list = None) -> dict:
    """
    Extract email/phone/LinkedIn/GitHub from visible text AND from
    hyperlink URLs (covers icon-only contact links with no visible text -
    very common in modern resume templates).
    """
    hyperlinks = hyperlinks or []
    links_blob = " ".join(hyperlinks)
    # Search visible text first, then hyperlink URLs as a fallback source
    combined_for_email = text + " " + links_blob.replace("mailto:", " ")
    combined_for_links = text + " " + links_blob

    email_match = EMAIL_RE.search(combined_for_email)
    phone_match = PHONE_RE.search(text)  # phones are never hidden behind hyperlinks
    linkedin_match = LINKEDIN_RE.search(combined_for_links)
    github_match = GITHUB_RE.search(combined_for_links)

    return {
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0).strip() if phone_match else None,
        "linkedin": linkedin_match.group(1) if linkedin_match else None,
        "github": github_match.group(1) if github_match else None,
    }


def extract_skills(text: str) -> dict:
    """Return skills found in the text, grouped by category."""
    text_lower = text.lower()
    found = {category: [] for category in SKILLS_DB}

    for category, skills in SKILLS_DB.items():
        for skill in skills:
            # word-boundary-safe search (handles multi-word skills too)
            pattern = r"(?<![\w])" + re.escape(skill) + r"(?![\w])"
            if re.search(pattern, text_lower):
                found[category].append(skill)

    return {k: sorted(set(v)) for k, v in found.items() if v}


def extract_education(text: str) -> list:
    text_lower = text.lower()
    found_levels = []
    for level, keywords in EDUCATION_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            found_levels.append(level)
    # order from highest to lowest
    order = ["phd", "masters", "bachelors", "diploma"]
    return [lvl for lvl in order if lvl in found_levels]


def extract_years_experience(text: str) -> int:
    """Look for explicit 'X years of experience' mentions; fall back to 0."""
    matches = YEARS_EXP_RE.findall(text)
    if matches:
        return max(int(m) for m in matches)
    return 0


def detect_sections(lines: list) -> dict:
    """Map section header -> line index where it was found."""
    found = {}
    for idx, line in enumerate(lines):
        normalized = line.lower().strip(" :-")
        for header in SECTION_HEADERS:
            if normalized == header or normalized.startswith(header):
                found.setdefault(header, idx)
    return found


def analyze_resume_structure(text: str, lines: list, hyperlinks: list = None) -> dict:
    """Bundle all structured extraction into a single profile dict."""
    return {
        "contact": extract_contact_info(text, hyperlinks),
        "skills": extract_skills(text),
        "education": extract_education(text),
        "years_experience": extract_years_experience(text),
        "sections_found": list(detect_sections(lines).keys()),
        "word_count": len(text.split()),
        "organizations_detected": extract_organizations(text),  # spaCy NER, [] if unavailable
    }
