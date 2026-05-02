# Visibility Cockpit Reference

This folder preserves screenshots from the previous unified, simplified project
view. It is a reference for future visibility tooling in this dissertation repo,
not an active evidence notebook and not a dashboard implementation to port
wholesale.

The previous view worked well because it made the project discussable at a high
level: a supervisor could see the current claim, how the system worked, why the
project had moved through particular harnesses, what artefacts existed, and
which decisions shaped the next step. The new project needs the same visibility
quality, but the research direction is different.

## What To Preserve

- A single generated supervisor-facing surface for the current research state.
- Navigation by research meaning, not by repository structure.
- Current claim, uncertainty, next action, and decision history in one place.
- Clear links between visible claims and their source records.
- Example artefacts that can be inspected and discussed safely.
- A visual account of the architecture/evaluation evolution over time.
- Minimal manual maintenance: the cockpit should be regenerated from durable
  source records wherever possible.

## What Must Change For This Project

This dissertation is not repeating the previous harness-reliability study. The
new visibility cockpit should be rebuilt around the current research question:

- comparison against real benchmarks and benchmark-derived contracts;
- wider field coverage beyond a single seizure-frequency anchor;
- direct, retrieval, modular, and evidence-contract architectures;
- correctness, evidence support, status/temporality, normalization, auditability,
  cost, latency, token use, and harness complexity;
- model registry snapshots and benchmark comparability;
- synthetic-only results labelled as bounded development evidence, not clinical
  deployment evidence;
- canonical/supporting/archive run labels, rather than moving "latest" claims.

## Reference Screenshots

The screenshots are saved in `screenshots/` with stable names:

1. `01-source-letter-extracted-output.png` - side-by-side source letter and
   extracted output.
2. `02-how-it-works-example-row.png` - workflow explanation with row-level
   inspection.
3. `03-harness-tradeoff-surface.png` - budget/performance frontier and selected
   harness details.
4. `04-current-status-claim.png` - current research claim, uncertainty, and next
   action.
5. `05-session-log.png` - chronological session/evaluation log.
6. `06-timeline-milestones.png` - near-term milestones and closed history.
7. `07-linked-decisions.png` - decision turns and linked records.
8. `08-branch-detail.png` - detailed view for a selected branch/harness.
9. `09-architecture-ladder.png` - visual evolution of architecture branches.

## Future Cockpit Shape

The future cockpit should be a compact generated static site, likely under
`site/`, fed by `scripts/build_cockpit_data.py`. It should draw from docs, run
records, result tables, adjudication files, model registry snapshots, and
decision notes. The cockpit should never become a second source of truth.

Useful first views for this repo:

- Current research claim and uncertainty.
- Benchmark and field-family coverage.
- Architecture ladder and ablation map.
- Canonical/supporting/archive run register.
- Budget, latency, token, and complexity comparison.
- Evidence-support and adjudication summaries.
- Model-family and model-tier comparison.
- Example source/prediction/adjudication rows.
- Decision log linking research choices to evidence.

## Boundary

This folder documents design inspiration and project-memory requirements. The
active implementation plan remains in `docs/implementation_plan.md`, especially
Phase 12: Generated Unified Cockpit.
