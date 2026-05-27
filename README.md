# Support Triage Tool

Reads a CSV of support tickets and produces two outputs:

1. **Per-ticket CSV**: suggested priority, category/subcategory, recurrence flag, and a human-readable explanation for each ticket
2. **Console dashboard**: volume by category, open/escalated backlog by priority, open tickets missing an agent assignment, top recurring-customer hotspots, and a satisfaction pattern

## Setup

```bash
pip install -r requirements.txt
```

Two dependencies: `rake-nltk` (keyword extraction) and `nltk` (tokenisation). NLTK corpora are downloaded automatically on first run.

## Usage

```bash
python triage.py <path_to_csv>
```

The tool accepts any CSV with these columns (all present in `support_tickets.csv`):

| Column | Notes |
|---|---|
| `ticket_id` | e.g. `TKT-001` |
| `date_submitted` | `YYYY-MM-DD` |
| `customer_id` | e.g. `CUST-4421` |
| `category` | may be blank — inferred from description |
| `subcategory` | may be blank — inferred from description |
| `priority` | may be blank — inferred from category + subcategory + signals |
| `status` | `Open`, `Resolved`, `Escalated` |
| `agent_assigned` | optional; if blank and status is Open/Escalated, ticket appears in the unassigned section |
| `ticket_description` | free-text description used for inference |
| `resolution_notes` | optional; improves category matching |

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


## How priority is inferred

When the `priority` field is blank or unrecognised, the tool applies these rules in order (each layer can only raise priority, never lower it):

1. Base priority from subcategory taxonomy (defined in `taxonomy.py`)
2. Bump one level if the customer has ≥ 2 prior tickets in the file
3. `Escalated` status floors the priority at `High`
4. Critical signals in the description (legal, formal complaint, SLA) → `Critical`
5. High signals (threatening to cancel, going live, completely unusable) → floor at `High`

## Project structure

```
triage.py       — entry point, orchestrates everything
priority.py     — priority inference rules
matcher.py      — RAKE-based category/subcategory matching
recurrence.py   — detects explicit cross-ticket references
output.py       — CSV writer, explanation builder, console dashboard
taxonomy.py     — all categories, keywords, and signal patterns
```
