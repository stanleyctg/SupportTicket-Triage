import re


_TKT_REF_PATTERN = re.compile(r"TKT-\d{3}", re.IGNORECASE)


def find_explicit_refs(description: str, current_id: str) -> list:
    """
    Extract TKT-NNN references from description, excluding the ticket itself.
    Returns a list of uppercase ticket IDs, e.g. ['TKT-007', 'TKT-021'].
    """
    if not description:
        return []
    refs = _TKT_REF_PATTERN.findall(description)
    return [r.upper() for r in refs if r.upper() != current_id.upper()]


def detect_recurrence(ticket: dict, prior_tickets: list) -> tuple:
    """
    Returns:
        is_recurrence  : True if explicit refs found in description
        linked_tickets : list of referenced ticket IDs
        prior_count    : total prior tickets from this customer (for priority bumping)
    """
    description = ticket.get("ticket_description") or ""
    ticket_id   = (ticket.get("ticket_id") or "").strip()
    customer_id = ticket.get("customer_id")

    prior_count = sum(1 for t in prior_tickets if t.get("customer_id") == customer_id)

    linked_tickets = find_explicit_refs(description, ticket_id)

    if linked_tickets:
        return True, linked_tickets, prior_count

    return False, [], prior_count