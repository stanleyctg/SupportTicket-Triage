import csv
import os
from collections import defaultdict


def build_explanation(
    ticket_id: str,
    date: str,
    customer_id: str,
    priority: str,
    category: str,
    subcategory: str,
    status: str,
    is_recurrence: bool,
    linked_tickets: list,
) -> str:
    """
    Build a short actionable summary covering the four spec requirements:
    suggested priority, category/subcategory, recurrence flag, and context.

    Format:
        TKT-048 [2024-02-11] | CUST-1155 | Priority: Critical |
        Category: Model Output / Inconsistency | Status: Escalated |
        Recurrence: 4 prior tickets from this customer (TKT-005, TKT-011, TKT-019, TKT-034)
    """
    cat_str    = f"{category} / {subcategory}" if subcategory else category
    status_str = status.strip() or "Unknown"
    count = len(linked_tickets)

    if is_recurrence and linked_tickets:
        linked_str = ", ".join(linked_tickets)
        ticket_word = "ticket" if count == 1 else "tickets"
        recurrence_str = (
            f"Recurrence: {count} prior {ticket_word} "
            f"from this customer (linked: {linked_str})"
        )
    elif is_recurrence:
        recurrence_str = f"Recurrence: {count} prior tickets from this customer"
    else:
        recurrence_str = "No prior history from this customer"

    return (
        f"{ticket_id} [{date}] | {customer_id} | "
        f"Priority: {priority} | Category: {cat_str} | "
        f"Status: {status_str} | {recurrence_str}"
    )


def write_output(tickets: list, out_path: str) -> None:
    """
    Write per-ticket triage to CSV.

    Columns cover all four spec requirements plus source metadata
    so the manager can see what was inferred vs original.
    """
    fieldnames = [
        "ticket_id",
        "date_submitted",
        "customer_id",
        "suggested_priority",
        "priority_source",
        "suggested_category",
        "suggested_subcategory",
        "category_source",
        "recurrence_flag",
        "linked_tickets",
        "explanation",
    ]

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for t in tickets:
            writer.writerow({
                "ticket_id":             (t.get("ticket_id")      or "").strip(),
                "date_submitted":        (t.get("date_submitted") or "").strip(),
                "customer_id":           (t.get("customer_id")    or "").strip(),
                "suggested_priority":    t["_priority"],
                "priority_source":       "original" if not t["_priority_inferred"] else "inferred",
                "suggested_category":    t["_category"],
                "suggested_subcategory": t["_subcategory"],
                "category_source":       "original" if not t["_cat_inferred"] else "inferred",
                "recurrence_flag":       "yes" if t["_recurrence"] else "no",
                "linked_tickets":        ", ".join(t["_linked_tickets"]),
                "explanation":           t["_explanation"],
            })


def print_summary(tickets: list) -> None:
    """Print a readable console summary after processing."""
    total      = len(tickets)
    recurring  = sum(1 for t in tickets if t["_recurrence"])
    inferred_p = sum(1 for t in tickets if t["_priority_inferred"])
    inferred_c = sum(1 for t in tickets if t["_cat_inferred"])

    backlog: dict = defaultdict(list)
    for t in tickets:
        if (t.get("status") or "").strip() in ("Open", "Escalated"):
            backlog[t["_priority"]].append(t.get("ticket_id", ""))

    cust_recur: dict = defaultdict(int)
    for t in tickets:
        if t["_recurrence"]:
            cust_recur[t.get("customer_id", "")] += 1

    print()
    print("=" * 72)
    print("  SUPPORT TRIAGE TOOL")
    print("=" * 72)
    print(f"\n  {total} tickets processed")
    print(f"  {recurring} recurrence flags")
    print(f"  {inferred_p} priorities inferred  |  {inferred_c} categories inferred")

    cat_counts: dict = defaultdict(int)
    for t in tickets:
        cat_counts[t["_category"]] += 1

    print("\n  VOLUME BY CATEGORY")
    print("  " + "-" * 50)
    max_count = max(cat_counts.values()) if cat_counts else 1
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        bar = "█" * max(1, round(count / max_count * 20))
        print(f"  {cat:<18} {count:>3}   {bar}")

    print("\n  OPEN / ESCALATED BACKLOG")
    print("  " + "-" * 50)
    for p in ["Critical", "High", "Medium", "Low"]:
        ids = backlog.get(p, [])
        if ids:
            id_str = ", ".join(ids)
            print(f"  {p:<10} {len(ids):>2}   {id_str}")

    if cust_recur:
        print("\n  RECURRING CUSTOMER HOTSPOTS")
        print("  " + "-" * 50)
        for cust, count in sorted(cust_recur.items(), key=lambda x: -x[1])[:5]:
            print(f"  {cust}   {count} recurring ticket(s)")

    unassigned_open = [
        t for t in tickets
        if (t.get("status") or "").strip() in ("Open", "Escalated")
        and not (t.get("agent_assigned") or "").strip()
    ]
    if unassigned_open:
        print("\n  OPEN / ESCALATED — NO AGENT ASSIGNED")
        print("  " + "-" * 50)
        for t in unassigned_open:
            tid    = (t.get("ticket_id")    or "").strip()
            cust   = (t.get("customer_id")  or "").strip()
            prio   = t["_priority"]
            cat    = t["_category"][:16]
            status = (t.get("status")       or "").strip()
            print(f"  {tid:<9} {cust:<12} {prio:<10} {cat:<18} {status}")

    scores_all: list = []
    cat_scores: dict = defaultdict(list)
    score_dist: dict = defaultdict(int)
    for t in tickets:
        raw = (t.get("satisfaction_score") or "").strip()
        try:
            score = float(raw)
            if 1 <= score <= 5:
                scores_all.append(score)
                cat_scores[t["_category"]].append(score)
                score_dist[int(score)] += 1
        except ValueError:
            pass

    if scores_all:
        overall_avg = sum(scores_all) / len(scores_all)
        print()
        print("  SATISFACTION PATTERNS")
        print("  " + "-" * 50)
        print(f"  Overall avg: {overall_avg:.1f} / 5   ({len(scores_all)} rated tickets)\n")
        print(f"  {'By category (worst first)':<22} {'Avg':>5}")
        for cat, s in sorted(cat_scores.items(), key=lambda x: sum(x[1]) / len(x[1])):
            avg = sum(s) / len(s)
            filled = round(avg * 2)
            bar = "█" * filled + "░" * (10 - filled)
            print(f"  {cat:<22} {avg:>4.1f}   {bar}")
        print()
        print("  Score distribution")
        max_dist = max(score_dist.values()) if score_dist else 1
        for star in range(1, 6):
            count = score_dist.get(star, 0)
            bar = "█" * max(0, round(count / max_dist * 20))
            print(f"  {star} ★   {bar:<20}  {count}")

    print("\n" + "=" * 72 + "\n")
