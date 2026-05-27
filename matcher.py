import re

import nltk
from rake_nltk import Rake

from taxonomy import SUBCATEGORY_CORRECTIONS, TAXONOMY

# NLTK data
for _corpus in ("stopwords", "punkt", "punkt_tab"):
    _path = f"tokenizers/{_corpus}" if _corpus.startswith("punkt") else f"corpora/{_corpus}"
    try:
        nltk.data.find(_path)
    except LookupError:
        nltk.download(_corpus, quiet=True)


def normalise_text(text: str) -> str:
    """Lowercase and collapse whitespace."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.lower().strip())


def normalise_subcategory(raw: str) -> str:
    return SUBCATEGORY_CORRECTIONS.get(raw.strip().lower(), raw.strip())


def extract_keywords(text: str) -> list:
    """
    Extract ranked key phrases from text using RAKE.

    Returns a deduplicated list of lowercase phrases or empty list on failure.
    """
    if not text or not text.strip():
        return []
    try:
        rake = Rake()
        rake.extract_keywords_from_text(text)
        phrases = rake.get_ranked_phrases()
        return list(dict.fromkeys(p.lower() for p in phrases))
    except Exception:
        return []


def match_category(description: str, resolution: str = "") -> tuple:
    """
    Match description text to the best-fit category and subcategory.

    Scoring per keyword:
        +2  if a RAKE-extracted phrase contains the keyword
        +1  if the keyword appears directly in normalised text (fallback)

    The subcategory with the highest total score wins. On a tie the first
    match in taxonomy order is returned, acceptable given the keyword lists
    are designed to be mutually exclusive on common cases.

    Returns:
        (category: str, subcategory: str, inferred: bool)
        inferred=False only when score is 0 (nothing matched).
    """
    combined = f"{description} {resolution}".strip()
    phrases = extract_keywords(combined)
    normalised = normalise_text(combined)

    best_category = "Uncategorised"
    best_subcategory = ""
    best_score = 0

    for category, subcategories in TAXONOMY.items():
        for subcategory, config in subcategories.items():
            score = 0
            for kw in config["keywords"]:
                kw_norm = kw.lower()
                if any(kw_norm in phrase for phrase in phrases):
                    score += 2
                elif kw_norm in normalised:
                    score += 1
            if score > best_score:
                best_score = score
                best_category = category
                best_subcategory = subcategory

    return best_category, best_subcategory, best_score > 0


def resolve_category(row: dict) -> tuple:
    """
    Determine final category and subcategory for a ticket row.

    Three cases:
        1. Both present in CSV -> trust as it is
        2. Category present, subcat missing -> infer subcat within that category
        3. Both missing -> infer both from scratch

    Returns:
        (category: str, subcategory: str, inferred: bool)
        inferred=True means at least one field was blank in the source.
    """
    description = (row.get("ticket_description") or "").strip()
    resolution  = (row.get("resolution_notes") or "").strip()

    original_cat    = (row.get("category") or "").strip()
    original_subcat = normalise_subcategory((row.get("subcategory") or "").strip())

    if original_cat and original_subcat:
        return original_cat, original_subcat, False

    if original_cat and not original_subcat:
        _, inferred_subcat, _ = match_category(description, resolution)
        valid_subcats = TAXONOMY.get(original_cat, {})
        # Only use the inferred subcat if it belongs to the known category
        subcategory = inferred_subcat if inferred_subcat in valid_subcats else ""
        return original_cat, subcategory, True

    # Both missing
    category, subcategory, _ = match_category(description, resolution)
    return category, subcategory, True
