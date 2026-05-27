# Support Triage Tool

Reads a CSV of support tickets and produces two outputs:

1. **Per-ticket CSV**: suggested priority, category/subcategory, recurrence flag, and a human-readable explanation for each ticket
2. **Console dashboard**: volume by category, open/escalated backlog by priority, open tickets missing an agent assignment, top recurring-customer hotspots, and a full per-ticket summary table

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

## Output 2 — console dashboard

Printed to stdout alongside the CSV write. Chosen over HTML/markdown because it requires no browser and reads well in a terminal or CI log.

```
Loaded 50 tickets from support_tickets.csv

========================================================================
  SUPPORT TRIAGE TOOL
========================================================================

  50 tickets processed
  13 recurrence flags
  15 priorities inferred  |  3 categories inferred

  VOLUME BY CATEGORY
  --------------------------------------------------
  Model Output        20   ████████████████████
  Integration         11   ███████████
  Performance          7   ███████
  Billing              5   █████
  Safety               3   ███
  Onboarding           3   ███
  Account              1   █

  OPEN / ESCALATED BACKLOG
  --------------------------------------------------
  Critical    2   TKT-037, TKT-048
  High       16   TKT-006, TKT-007, TKT-014, TKT-017, TKT-019, TKT-021…

  RECURRING CUSTOMER HOTSPOTS
  --------------------------------------------------
  CUST-1155   4 recurring ticket(s)
  CUST-2234   2 recurring ticket(s)
  CUST-3310   2 recurring ticket(s)
  CUST-8801   2 recurring ticket(s)
  CUST-4421   2 recurring ticket(s)

  OPEN / ESCALATED — NO AGENT ASSIGNED
  --------------------------------------------------
  TKT-006   CUST-5502    High       Integration        Open
  TKT-014   CUST-8801    High       Model Output       Open
  ...

  PER-TICKET TRIAGE
  ----------------------------------------------------------------------
  ID        Customer     Priority   Category           Recur  Status
  ----------------------------------------------------------------------
  TKT-001   CUST-4421    High       Model Output              Resolved
  TKT-002   CUST-2891    High       Integration               Resolved
  TKT-003   CUST-3310    Low        Billing                   Resolved
  ...
  TKT-037   CUST-2234    Critical   Model Output       YES    Escalated
  TKT-048   CUST-1155    Critical   Model Output       YES    Escalated

========================================================================

  Output written to output/triage_results.csv
```

Sample rows from `output/triage_results.csv`:

```
ticket_id,suggested_priority,priority_source,suggested_category,suggested_subcategory,category_source,recurrence_flag,linked_tickets,explanation
TKT-001,High,original,Model Output,Hallucination,original,no,,TKT-001 [2024-01-03] | CUST-4421 | Priority: High | Category: Model Output / Hallucination | Status: Resolved | No prior history from this customer
TKT-002,High,inferred,Integration,API Timeout,original,no,,TKT-002 [2024-01-04] | CUST-2891 | Priority: High | Category: Integration / API Timeout | Status: Resolved | No prior history from this customer
TKT-037,Critical,inferred,Model Output,Inconsistency,original,yes,"TKT-007, TKT-021",TKT-037 [2024-04-18] | CUST-2234 | Priority: Critical | Category: Model Output / Inconsistency | Status: Escalated | Recurrence: 2 prior tickets from this customer (linked: TKT-007, TKT-021)
TKT-048,Critical,inferred,Model Output,Hallucination,original,yes,"TKT-005, TKT-011, TKT-019, TKT-034",TKT-048 [2024-05-09] | CUST-1155 | Priority: Critical | Category: Model Output / Hallucination | Status: Escalated | Recurrence: 4 prior tickets from this customer (linked: TKT-005, TKT-011, TKT-019, TKT-034)
```

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
