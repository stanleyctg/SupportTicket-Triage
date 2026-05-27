import csv
import os
import sys
from datetime import datetime

from matcher import resolve_category
from output import build_explanation, print_summary, write_output
from priority import resolve_priority
from recurrence import detect_recurrence


def process_tickets(rows: list) -> list:
    def parse_date(row: dict) -> datetime:
        try:
            return datetime.strptime(row.get("date_submitted") or "", "%Y-%m-%d")
        except ValueError:
            return datetime.min

    rows = sorted(rows, key=parse_date)
    processed = []

    for row in rows:
        if not (row.get("ticket_description") or "").strip():
            sat = (row.get("satisfaction_score") or "").strip()
            if sat and not sat.replace(".", "").isdigit():
                row["ticket_description"] = sat
                row["satisfaction_score"] = ""

        status = (row.get("status") or "").strip()

        # Category + subcategory
        category, subcategory, cat_inferred = resolve_category(row)

        # Recurrence
        is_recurrence, linked_tickets, prior_count = detect_recurrence(row, processed)

        # Priority
        row["_subcategory"] = subcategory  # ensure priority lookup has subcategory
        suggested_priority, priority_inferred = resolve_priority(row, prior_count)

        # Explanation
        explanation = build_explanation(
            ticket_id      = (row.get("ticket_id")      or "").strip(),
            date           = (row.get("date_submitted") or "").strip(),
            customer_id    = (row.get("customer_id")    or "").strip(),
            priority       = suggested_priority,
            category       = category,
            subcategory    = subcategory,
            status         = status,
            is_recurrence  = is_recurrence,
            linked_tickets = linked_tickets,
        )

        processed.append({
            **row,
            "_category":          category,
            "_subcategory":       subcategory,
            "_cat_inferred":      cat_inferred,
            "_priority":          suggested_priority,
            "_priority_inferred": priority_inferred,
            "_recurrence":        is_recurrence,
            "_linked_tickets":    linked_tickets,
            "_explanation":       explanation,
        })

    return processed


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python triage.py <path_to_csv>")
        print("Example: python triage.py support_tickets.csv")
        sys.exit(1)

    csv_path = sys.argv[1]

    if not os.path.isfile(csv_path):
        print(f"Error: file not found — {csv_path}")
        sys.exit(1)

    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        print("Error: CSV is empty or has no data rows.")
        sys.exit(1)

    print(f"\nLoaded {len(rows)} tickets from {csv_path}")

    tickets = process_tickets(rows)

    out_path = os.path.join("output", "triage_results.csv")
    write_output(tickets, out_path)
    print_summary(tickets)
    print(f"  Output written to {out_path}\n")


if __name__ == "__main__":
    main()
