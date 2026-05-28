# Support Triage Tool

Reads a CSV of support tickets and produces two outputs:

1. **Per-ticket CSV**: suggested priority, category/subcategory, recurrence flag, and a human-readable explanation for each ticket
2. **Console dashboard**: volume by category, open/escalated backlog by priority, open tickets missing an agent assignment, top recurring-customer hotspots, and a satisfaction pattern

## Setup

```bash
pip install -r requirements.txt
```

Two dependencies: `rake-nltk` (keyword extraction) and `nltk` (tokenisation). NLTK corpora are downloaded automatically on first run.

## Sample Usage
Run:
```bash
python triage.py <path_to_csv>
```

The tool accepts the CSV file (`support_tickets.csv`) and produces 2 outputs:

## Output 1 — per-ticket CSV (`output/triage_results.csv`)

One row per ticket with these columns:

| Column | Description |
|---|---|
| `suggested_priority` | Critical / High / Medium / Low |
| `priority_source` | `original` (trusted from CSV) or `inferred` |
| `suggested_category` | top-level category |
| `suggested_subcategory` | subcategory within the category |
| `category_source` | `original` or `inferred` |
| `recurrence_flag` | `yes` if the description references an earlier ticket from this customer |
| `linked_tickets` | comma-separated TKT-NNN IDs found in the description |
| `explanation` | one-line summary a manager can act on directly |

<img width="1187" height="643" alt="image" src="https://github.com/user-attachments/assets/3c419a7d-07df-4a91-8588-aad67bcc1a4e" />


## Output 2 — console dashboard

Printed to stdout alongside the CSV write. Chosen over HTML/markdown because it requires no browser and reads well in a terminal or CI log.

<img width="821" height="711" alt="image" src="https://github.com/user-attachments/assets/9736674f-1d1a-495a-9e99-6ceeec1655cf" />


## How each field is produced

**Priority**

Looking at the data, tickets in the same subcategory almost always cluster at similar urgency level: so subcategory is the most reliable starting signal. Resolution time has a loose correlation with priority but too many outliers to trust directly. On top of that base, the text of the description often contains explicit urgency cues ("legal", "going live", "threatening to cancel") that clearly warrant bumping the level. Recurrence is also a signal: a customer raising the same issue for the third time is implicitly higher priority than a first report.

If the CSV already has a valid priority it is kept as-is (`priority_source: original`). When blank, the tool infers it in layers (each layer can only raise, never lower):

1. Base level from the subcategory taxonomy (`taxonomy.py`)
2. Bump one level if the customer has ≥ 2 prior tickets in the file
3. `Escalated` status floors at `High`
4. Critical signals in the description ("legal", "formal complaint", "SLA") → `Critical`
5. High signals ("threatening to cancel", "going live", "completely unusable") → floor at `High`

**Category / subcategory**

Ticket descriptions in this domain contain very obvious keywords: "API", "hallucination", "webhook", "billing", that map directly to a small, stable taxonomy. RAKE extracts multi-word key phrases from the description (better than single words for terms like "content filter" or "overage charges"), scores them against keyword lists for each category/subcategory, and takes the highest-scoring match. If the CSV already has a valid category it is kept and only a missing subcategory is inferred.

Missing category/subcategory will be filled based on the above.

**Recurrence**

Looking at the dataset, customers who are following up on an earlier ticket almost always name it explicitly in the description ("see TKT-017", "follow up to TKT-005"). A regex on the `TKT-NNN` pattern reliably catches these. The same-customer check is essential, a ticket description can mention someone else's ticket number, and that is not a recurrence.

Produced is a recurrence flag and the linked tickets.

**Explanation**

No inference here: the explanation is assembled directly from structured fields: ticket ID, customer, the suggested labels, any linked prior tickets, and current status. The goal is a single line a manager can read without opening the original ticket.

**Dashboard**

All stats are derived from the same enriched ticket list that feeds the CSV. Five views were chosen based on what the data made obvious: category volume (where load concentrates), open/escalated backlog by priority (what needs action today), unassigned open tickets (spotted that agent_assigned is consistently blank on unresolved tickets: a gap worth surfacing), recurring customer hotspots (accounts most likely to churn), and satisfaction by category (which issue types leave customers unhappiest).

Console output was chosen for simplicity: no browser, no server, runs anywhere the script runs. At larger scale a dynamic app (e.g. Streamlit) or combining both outputs into a single HTML file would be more appropriate.

## Project structure

```
triage.py       — entry point, orchestrates everything
priority.py     — priority inference rules
matcher.py      — RAKE-based category/subcategory matching
recurrence.py   — detects explicit cross-ticket references
output.py       — CSV writer, explanation builder, console dashboard
taxonomy.py     — all categories, keywords, and signal patterns
```
