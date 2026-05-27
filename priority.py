import re

from taxonomy import (
    CRITICAL_SIGNALS,
    HIGH_SIGNALS,
    PRIORITY_ORDER,
    RECURRENCE_BUMP_THRESHOLD,
    TAXONOMY,
)


def bump_priority(current: str, levels: int = 1) -> str:
    """Move a priority up by `levels` steps, capped at Critical."""
    idx = PRIORITY_ORDER.index(current) if current in PRIORITY_ORDER else 1
    return PRIORITY_ORDER[min(idx + levels, len(PRIORITY_ORDER) - 1)]


def _base_priority_for_subcategory(subcategory: str) -> str:
    """
    Look up the base priority for a subcategory from the taxonomy.
    Returns 'Medium' as a safe default when subcategory is not found.
    """
    for _cat, subcategories in TAXONOMY.items():
        if subcategory in subcategories:
            return subcategories[subcategory]["base_priority"]
    return "Medium"


def infer_priority(
    subcategory: str,
    description: str,
    prior_count: int,
    status: str,
) -> str:
    """
    Derive a suggested priority using layered rules applied in order:

        1. Base priority from subcategory taxonomy
        2. Bump one level if prior ticket count >= recurrence threshold
        3. Escalated status -> floor of High
        4. Critical signals -> Critical (legal, formal complaint, SLA)
        5. High signals -> floor of High (won't downgrade from Critical)

    Each layer can only raise priority, never lower it.
    """
    priority = _base_priority_for_subcategory(subcategory)
    text = re.sub(r"\s+", " ", (description or "").lower().strip())

    if prior_count >= RECURRENCE_BUMP_THRESHOLD:
        priority = bump_priority(priority)

    if status.strip().lower() == "escalated":
        if PRIORITY_ORDER.index(priority) < PRIORITY_ORDER.index("High"):
            priority = "High"

    if any(re.search(p, text) for p in CRITICAL_SIGNALS):
        priority = "Critical"
    elif any(re.search(p, text) for p in HIGH_SIGNALS):
        if PRIORITY_ORDER.index(priority) < PRIORITY_ORDER.index("High"):
            priority = "High"

    return priority


def resolve_priority(row: dict, prior_count: int) -> tuple:
    """
    Determine the final suggested priority for a ticket row.

    Trusts the original CSV value when present and valid.
    Infers when the field is blank or unrecognised.

    Returns:
        (suggested_priority: str, inferred: bool)
    """
    original = (row.get("priority") or "").strip()

    if original in PRIORITY_ORDER:
        return original, False

    suggested = infer_priority(
        subcategory  = row.get("_subcategory", ""),
        description  = row.get("ticket_description", ""),
        prior_count  = prior_count,
        status       = row.get("status", ""),
    )
    return suggested, True
