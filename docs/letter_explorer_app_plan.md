# Letter Explorer — Standalone App Plan

## Purpose

A dedicated single-page application that makes the dissertation's extraction
pipeline legible to a clinical or technical reviewer. The core experience:
pick a letter, pick two harnesses, see what each extracted side-by-side with
the evidence highlighted in the letter, and step through the pipeline to
understand why they differ.

This replaces the cockpit-embedded widget, which is fundamentally limited by
`innerHTML` injection (no `<script>` tags, no proper component lifecycle, no
stateful interactivity beyond a single `change` listener).

---

## What Currently Exists

- `site/letter-explorer-data.json` — row 11118 (generalised epilepsy, clear cluster pattern)
- `site/letter-explorer-9278.json` — row 9278 (uncertain seizure classification)
- `scripts/build_letter_explorer_data.py` — extraction script; run it for any row
- `scripts/auto_adjudicate.py` — LLM-as-judge adjudication for all field families

Each JSON contains:
- `letter`: full clinic letter text
- `gold_label_sf`: gold seizure-frequency label
- `runs[]`: one entry per (model, harness), each with:
  - `fields[]`: extracted items with `value`, `evidence`, `family`, `score`
  - `pipeline[]`: ordered harness events (type, component, metrics, errors)
  - `budget`: tokens, cost, latency, call count

The pipeline events do **not** currently contain raw prompts or model
completions. That is a planned addition (see Phase 3 below).

---

## Architecture

Single HTML file at `site/explorer/index.html` with vanilla JS — no framework,
no build step. Data loaded from `../letter-explorer-data.json` and siblings
via `fetch`. Styling in the same file or a companion `explorer.css`.

Why no framework: the cockpit is already vanilla JS and the team knows it.
The data is static JSON. React/Vue adds a build pipeline for no gain here.

---

## Phase 1 — Core Shell (build first)

### Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  NAV: [Letter picker]  [Harness A ▼]  vs  [Harness B ▼]        │
│       [model badge A]                      [model badge B]       │
├──────────────────────┬─────────────────────────────────────────┤
│  LETTER PANE         │  FIELD PANE A    │  FIELD PANE B         │
│  (scrollable)        │  (scrollable)    │  (scrollable)          │
│                      │                  │                        │
│  Highlighted spans   │  Fields with     │  Same fields,          │
│  colour-coded by     │  values, scores, │  different extractions │
│  field family.       │  evidence        │  Delta badges where    │
│  Clicking a field    │                  │  harnesses disagree    │
│  card focuses its    │                  │                        │
│  spans in letter.    │                  │                        │
├──────────────────────┴─────────────────────────────────────────┤
│  PIPELINE TRACE (tabbed: Harness A | Harness B | Diff)          │
│  Stage-by-stage swimlane with timing bars                       │
└─────────────────────────────────────────────────────────────────┘
```

### Letter picker
- Dropdown listing available letters by row ID and clinical summary
- Each letter is a separate JSON file; loaded on demand via fetch
- URL reflects state: `?letter=9278&a=retrieval_field_extractors&b=clines_epilepsy_verified&model=gpt-5.5`

### Harness / model picker
- Two independent pickers (A and B) for side-by-side comparison
- Model picker collapses model + harness into one combined selector
- Single-harness mode available (hide the B column)

### Field pane
- Five field family cards in fixed order (SF, Med, Inv, SC, EC)
- Each card: coloured header, extracted items, evidence quotes, score badge
- Delta indicator: if A and B differ for the same field, show `A≠B` badge
- Clicking a card scrolls the letter to that field's first evidence span
  and pulses the highlight

### Letter pane
- Evidence spans highlighted using client-side substring match
- Five colours, one per field family (existing palette)
- Clicking a highlight scrolls the right field pane to that field card
- Bidirectional: field card click ↔ letter span focus

### Navigation
- Keyboard: `←/→` to step through pipeline stages; `Tab` to switch panes
- URL state so the browser back button works
- Shareable links (no server needed — all client-side)

---

## Phase 2 — Pipeline Trace (richer visualisation)

### Swimlane view

Replaces the flat event list with a proper timeline. Each field family gets
a horizontal lane. Stages within a lane are boxes placed at their real
elapsed time position (using `latency_ms` from event metrics).

```
          0ms       500ms     1000ms    1500ms    2000ms
SF        [chunk]──[spans]──────[extract]──────[verify]
Med               [chunk]──[spans]──[extract]──[verify]
Inv                         [chunk]──[spans]──[extract]
SC                                   [spans]──[extract]
EC                                            [extract]
                                                        [aggregate]
```

For direct harnesses (one call), show a single wide bar across all families.

### Expandable stage cards

Clicking any stage box expands it in a drawer below the swimlane:
- Stage type, component, timestamp
- All metrics (tokens, latency, span counts, chunk counts)
- Warnings and errors

### Step-through mode

A "▶ Step through pipeline" button that reveals stages one at a time.
Each advance highlights the relevant spans in the letter pane and
scrolls the field card for that family into view.

---

## Phase 3 — Prompt/Completion Capture (requires harness change)

To show actual model I/O, the harnesses need a lightweight capture mode.

### What to add to the run records

Add an optional `prompt_artifacts` list at the row level:

```json
{
  "event_id": "11118:3:provider_call_finished",
  "field_family": "seizure_frequency",
  "prompt_messages": [
    {"role": "system", "content": "..."},
    {"role": "user",   "content": "..."}
  ],
  "completion": "...",
  "input_tokens": 1139,
  "output_tokens": 328
}
```

This is opt-in (a `--capture-artifacts` flag on the run scripts) so normal
runs stay compact. The letter explorer data builder picks these up when
present and embeds them in the explorer JSON.

### What it enables in the UI

Each expanded stage card shows:
- "What the model saw" — collapsible prompt panel with syntax highlighting
- "What the model said" — raw completion with JSON parse overlay
- Token counts and cost for that single call
- For modular harnesses: the specific candidate spans that were sent as context

This makes the pipeline a proper audit trail, not just a trace.

---

## Phase 4 — Evidence Chain View

A graph view (SVG or Canvas) showing the full provenance chain for one field:

```
Letter text
  └─ paragraph: "Over the last four weeks…"
       └─ candidate span (semantic chunk 3, 1214 chars)
            └─ field extraction call → "2 cluster days per month"
                 └─ deterministic verifier: PASS (quote present)
                      └─ final value: "2 cluster per month, 6 per cluster"
                           └─ gold label: "2 cluster per month, 6 per cluster"  ✓
```

Hovering any node highlights the corresponding span in the letter pane.
The same chain for a different harness can be shown in a second column
to make divergence immediately legible.

---

## File Structure

```
site/
  explorer/
    index.html          # the app (HTML + CSS + JS, self-contained)
    README.md           # how to run and extend
  letter-explorer-data.json   # row 11118 (existing)
  letter-explorer-9278.json   # row 9278 (existing)
  letter-explorer-*.json      # additional rows, generated on demand

scripts/
  build_letter_explorer_data.py   # existing; run for any row_id
```

The explorer fetches `../letter-explorer-*.json` relative to its location.
No server configuration needed — it works from `file://` or any static host.

---

## Build Order

1. **Phase 1 shell** — nav, two-column field pane, letter highlighting,
   URL state, bidirectional field↔letter focus. This is the MVP that a
   clinical reviewer can use today with existing JSON data.

2. **Phase 2 swimlane** — richer pipeline trace with timeline layout and
   expandable stage drawers. Requires no data changes.

3. **Phase 3 capture** — add `--capture-artifacts` to run scripts, rebuild
   one or two letter JSONs with full prompt/completion data, add I/O panels
   to the UI.

4. **Phase 4 evidence chain** — SVG provenance graph. Optional; build if
   the step-through mode in Phase 2 proves insufficient for the dissertation
   examiner audience.

---

## Notes on Data and Methodology

- The explorer is read-only. It never modifies run records or adjudication
  sheets. All scoring visible in the UI comes from the adjudication CSVs.
- Raw letter text is synthetic (not patient data). The app does not need
  PHI controls for this dataset.
- The `auto_adjudicated` status shown on score badges should be labelled
  clearly as LLM-as-judge, not human adjudication, in any examiner-facing
  display.
- If real patient letters are used in future, the prompt/completion capture
  (Phase 3) must be reviewed against the data governance policy before any
  artifacts are stored or displayed.
