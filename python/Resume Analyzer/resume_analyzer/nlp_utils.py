"""
nlp_utils.py
------------
Wraps nltk and spaCy usage in one place, with graceful fallbacks.

Why guarded like this: spaCy needs a downloaded language model
(`en_core_web_sm`) and nltk needs downloaded corpora (punkt, stopwords,
wordnet) - both require a one-time internet-connected setup step. If either
is missing, the app should still work using the regex-based extraction
already in skill_extractor.py, just without the extra NLP polish.

Run this once after installing requirements:
    python -m spacy download en_core_web_sm
    python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); \
               nltk.download('stopwords'); nltk.download('wordnet'); \
               nltk.download('averaged_perceptron_tagger_eng')"
"""

_spacy_nlp = None
_spacy_load_attempted = False

_nltk_ready = False
_nltk_load_attempted = False


def get_spacy_model():
    """Lazily load spaCy's small English model. Returns None if unavailable."""
    global _spacy_nlp, _spacy_load_attempted
    if _spacy_load_attempted:
        return _spacy_nlp

    _spacy_load_attempted = True
    try:
        import spacy
        _spacy_nlp = spacy.load("en_core_web_sm")
    except Exception:
        # covers: spacy not installed, OR model not downloaded
        _spacy_nlp = None
    return _spacy_nlp


def ensure_nltk_ready() -> bool:
    """Check required nltk corpora are available. Returns True if usable."""
    global _nltk_ready, _nltk_load_attempted
    if _nltk_load_attempted:
        return _nltk_ready

    _nltk_load_attempted = True
    try:
        import nltk
        from nltk.corpus import stopwords, wordnet  # noqa: F401
        from nltk.tokenize import word_tokenize

        # Will raise LookupError if corpora aren't downloaded yet.
        word_tokenize("test sentence")
        stopwords.words("english")
        wordnet.synsets("test")
        _nltk_ready = True
    except Exception:
        _nltk_ready = False
    return _nltk_ready


def lemmatize_text(text: str) -> str:
    """
    Lemmatize + strip stopwords using nltk, to normalize text before TF-IDF
    (so 'developed'/'developing'/'develops' all collapse to 'develop').
    Falls back to the original text untouched if nltk isn't ready.
    """
    if not ensure_nltk_ready():
        return text

    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    from nltk.tokenize import word_tokenize

    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words("english"))

    tokens = word_tokenize(text.lower())
    lemmatized = [
        lemmatizer.lemmatize(tok) for tok in tokens
        if tok.isalpha() and tok not in stop_words
    ]
    return " ".join(lemmatized)


def extract_noun_phrases(text: str, max_phrases: int = 30) -> list:
    """
    Use spaCy to pull candidate skill/tool phrases (noun chunks) that
    might not be in our fixed skills database. Returns [] if spaCy
    isn't available - this is a "bonus" signal, not a required one.
    """
    nlp = get_spacy_model()
    if nlp is None:
        return []

    doc = nlp(text)
    phrases = []
    for chunk in doc.noun_chunks:
        cleaned = chunk.text.strip().lower()
        # keep short, plausible tool/skill-like phrases only
        if 1 < len(cleaned) <= 40 and len(cleaned.split()) <= 4:
            phrases.append(cleaned)
    # de-dup while preserving order
    seen = set()
    unique_phrases = []
    for p in phrases:
        if p not in seen:
            seen.add(p)
            unique_phrases.append(p)
    return unique_phrases[:max_phrases]


def extract_organizations(text: str, max_orgs: int = 10) -> list:
    """Use spaCy NER to pull company/university names. Returns [] if unavailable."""
    nlp = get_spacy_model()
    if nlp is None:
        return []

    doc = nlp(text)
    orgs = []
    seen = set()
    for ent in doc.ents:
        if ent.label_ in ("ORG",) and ent.text.strip().lower() not in seen:
            seen.add(ent.text.strip().lower())
            orgs.append(ent.text.strip())
    return orgs[:max_orgs]


def nlp_status() -> dict:
    """Report which optional NLP backends are actually active - shown in the UI."""
    return {
        "spacy_active": get_spacy_model() is not None,
        "nltk_active": ensure_nltk_ready(),
    }
