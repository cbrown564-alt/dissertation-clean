# Coding-Agent Harnesses For Structured Clinical Data Extraction

Accessed: 3 May 2026.

## Review Aim

This review connects two literatures that are usually discussed separately:

1. LLM-based structured information extraction from clinical narratives.
2. Coding-agent harnesses such as Claude Code, OpenAI Codex, Pi, Flue,
   Gemini CLI, SWE-agent, OpenHands, Aider, and harness adapters.

The dissertation question in this repo is not simply whether a language model
can extract seizure frequency, medications, investigations, seizure types, and
epilepsy classifications from clinic letters. It is whether the harness around
the model can make extraction more reliable, auditable, reproducible, and
clinically adjudicable.

The central claim of this review is therefore methodological:

> A clinical extraction system should be evaluated as an agent harness, not as
> a prompt. The harness defines context assembly, tool access, chunking,
> retrieval, schema constraints, parse repair, verification, aggregation,
> evidence logging, budget accounting, and human review.

The repo already contains the right beginnings: clinical NLP baselines,
direct-prompt LLM baselines, retrieval-field extractors, CLINES-inspired
modular pipelines, verifier variants, model registry snapshots, run records,
and adjudication tables. The opportunity is to borrow more deliberately from
modern coding-agent harnesses while keeping the clinical system conservative.

## 1. Clinical Structured Extraction: The Current Evidence

Clinical information extraction has moved from rule-based and ontology-driven
systems toward LLM-centered pipelines, but the older lessons still hold.
Clinical text is not only unstructured; it is status-rich, temporal, uncertain,
and full of distractors. A schema-valid JSON object can still be clinically
wrong if it turns a historical medication into a current one, treats "no
tonic-clonic seizures" as global seizure freedom, or normalizes a non-specific
EEG abnormality as a normal EEG.

Several recent studies establish the shape of the problem.

Agrawal et al. showed that large language models can be effective few-shot
clinical information extractors, making LLM prompting a serious alternative to
task-specific clinical NLP for low-resource extraction settings. The paper is
important because it does not treat extraction as summarization; it evaluates
span, label, and relation-style information extraction tasks.

CLINES is the closest architectural precedent for this repo. It describes a
modular clinical LLM pipeline with semantic chunking, LLM extraction,
assertion/experiencer/value/unit attributes, UMLS normalization, date
resolution, and aggregation into an i2b2-style schema. In zero-shot evaluations
on MIMIC-III, 4CE, and CORAL oncology reports, CLINES outperformed rule/lexicon
systems, transformer encoders, and single-prompt LLM baselines, with reported
gains over the strongest single-prompt LLM of 0.21-0.38 F1 across tasks. The
lesson is not "multi-agent is always better"; it is that a modular harness can
help when long notes require different operations for retrieval, extraction,
normalization, temporal reasoning, and aggregation.

Pathology structured-extraction studies are useful because they are closer to
schema extraction than clinical dialogue. Grothey et al. evaluated GPT-4 and
open-source Llama/Qwen models over 579 German and English pathology reports,
requiring structured JSON for eleven parameters. The study found that
open-source models could approach proprietary performance in some settings,
but also emphasized prompt design, quantization, JSON validity, runtime,
hallucination checks on negative reports, and local deployment. This maps
directly onto the repo's evaluation contract: parse validity, not-mentioned
handling, field-specific errors, and cost/latency are part of the result.

Scalable clinical extraction pipelines increasingly combine cheap retrieval or
regex-like screening with LLM interpretation. SPELL-LLMs, for example, uses a
hybrid local workflow over large clinical corpora: regular expressions identify
candidate snippets and locally hosted LLMs interpret them. This supports the
repo's retrieval-field extractor rung: candidate-span retrieval should be
evaluated as a possible efficiency and focus improvement, but also as a source
of recall loss.

Within epilepsy, the existing `docs/literature_review.md` already covers ExECT,
Xie et al., Holgate et al., Fang et al., and Gan et al. The relevant synthesis
for harness design is:

- ExECT shows that epilepsy clinic-letter extraction has strong non-LLM
  baselines, especially for formulaic medication-like fields.
- Seizure frequency remains hard because it is temporal, qualified, and often
  expressed indirectly.
- Direct LLM extraction can be strong; Fang et al. caution that summaries and
  contextualized variants do not automatically improve performance.
- Synthetic, evidence-grounded supervision can be powerful, but it is a
  different intervention from training-free harness design.
- Evidence spans and rationales are valuable for adjudication, but the public
  trust object should be source-grounded evidence, not hidden chain-of-thought.

## 2. Why Coding-Agent Harnesses Matter

OpenAI's Codex engineering write-up defines the agent loop as the core logic
that orchestrates user input, model inference, tool calls, and observations.
It explicitly frames Codex as a harness: the CLI, cloud, and IDE surfaces share
core execution logic. This matters because the model's "answer" may be an edit,
a test run, a patch, a commit, or a final message. In clinical extraction, the
equivalent is not a patch but a validated payload plus artifacts.

Claude Code's documentation describes an agentic coding tool that reads a
codebase, edits files, runs commands, integrates with development tools, uses
project instructions, skills, hooks, MCP, auto-memory, parallel agents, CI, and
custom agents through an SDK. The important design pattern is not that clinical
extraction should let an LLM roam freely. It is that reliable agent systems
externalize capabilities as explicit harness features: instructions, skills,
tools, hooks, memory, roles, permissions, and review surfaces.

SWE-agent is the most academically useful coding-agent precedent. Its core
claim is that interface design affects agent performance. By designing an
Agent-Computer Interface for code navigation, editing, and test execution, it
improved the ability of a language model agent to solve software engineering
tasks. For this repo, the analogue is a Clinical-Document Interface: bounded
tools for section lookup, candidate-span retrieval, evidence quoting, schema
validation, verifier review, and adjudication export.

OpenHands broadens this into an open platform for software agents that operate
through code, shells, and browsers. The lesson is platformization: model choice,
sandboxing, lifecycle management, logs, and task abstractions can be separated
from the task-specific policy. The repo's provider abstraction and model
registry are aligned with this.

Gemini CLI's architecture separates a client-side terminal application from a
local server/core package that manages model requests and tools such as file
operations, shell execution, and web fetching. This is a useful reminder that
agent harnesses often need a small control plane. In this repo, that control
plane is currently spread across harness functions, providers, schemas, and
scripts. A future `orchestration` layer could make this explicit.

Pi is especially relevant because it describes itself as a minimal terminal
coding harness, not a full product. Its default core is small, but it supports
extensions, skills, prompt templates, themes, packages, tree-structured
history, model switching, print/JSON mode, RPC mode, and an SDK. It also
deliberately omits built-in subagents, plan mode, MCP, and permission popups,
expecting users to add those features if their workflow needs them. The lesson
for this repo is to avoid baking every experimental architecture into the core.
Add thin, composable primitives that can express retrieval, extraction,
verification, adjudication, and model-matrix runs.

Flue is a newer and more explicitly harness-centered framework. It summarizes
the stack as model tokens/tools/prompts, harness skills/memory/sessions,
sandbox bash/security/network, and filesystem read/write/grep/glob. It exposes
sessions, skills with typed outputs, deployable agents, sandbox choices, and
fine-grained secret handling. The clinical analogue is a deployable extraction
workflow where the model never sees secrets or gold labels, every skill has a
typed output contract, and each session produces a durable trace.

Harness adapters such as `harness.lol` are a different but important layer:
they run several coding agents behind one unified CLI and event stream. That
pattern suggests a way to evaluate external coding-agent-style clinical
extractors without integrating each product deeply. A normalized event/run
format lets this repo compare outputs from local harnesses, external CLIs, and
future agent frameworks.

## 3. Taxonomy Of Harness Features

Modern coding-agent harnesses can be reduced to a set of design primitives.
Each has a clinical extraction equivalent.

| Coding-agent primitive | Clinical extraction analogue | Repo status |
| --- | --- | --- |
| Project instructions (`CLAUDE.md`, `AGENTS.md`) | Study protocol, schema rules, adjudication rules, field-specific extraction policies | Present as docs/prompts, not yet a single agent-readable protocol bundle |
| Tool registry | Retrieval, section lookup, evidence quote extraction, schema validation, verifier call, adjudication export | Partly present through modules/scripts |
| Agent loop | Multi-step extraction and verification workflow | Present inside harness functions |
| Skills/workflows | Field extractors, verifier, normalizer, aggregator, adjudication sheet builder | Present conceptually, not formalized as skill objects |
| Typed outputs | JSON schema, Pydantic/dataclass validation, parse repair | Present through schema payloads and tests |
| Context compaction | Long-letter chunking and artifact summarization | Partly present through chunking/retrieval |
| Memory/session history | Run records, artifacts, model registry, prompt versions | Present |
| Sandbox/permissions | No gold-label access; no uncontrolled network; secrets outside model context | Partly present by tests and provider abstraction |
| Parallel agents | Field-family extractors or verifier passes run independently | Not yet a first-class orchestration primitive |
| Hooks | Pre/post validation, budget checks, redaction, provenance checks | Not yet explicit |
| Event stream | Tool/call/artifact trace for observability | Run records exist, but event stream is not formalized |
| Human review UI | Adjudication sheet and cockpit | Present |

This taxonomy suggests that the next architecture expansion should not be
"add more agents" in the abstract. It should add the smallest primitives that
make harness behavior inspectable and configurable.

## 4. Architectural Implications For This Repo

The existing architecture ladder is strong:

- `deterministic_baseline`
- `exect_lite_cleanroom_baseline`
- `exect_v2_external_baseline`
- `direct_full_contract`
- `direct_evidence_contract`
- `retrieval_field_extractors`
- `clines_epilepsy_modular`
- `clines_epilepsy_verified`
- anchor and self-consistency variants

The next expansion should preserve this ladder while adding harness
engineering layers around it.

### 4.1 Add A Formal Harness Manifest

Create a versioned manifest for every harness run. It should specify:

- harness ID and architecture family;
- allowed modules/tools;
- prompts and schema versions;
- provider/model registry entry;
- input context policy: full letter, chunks, retrieved spans, or artifacts;
- output contract and repair policy;
- verifier policy;
- aggregation policy;
- budget limits;
- gold-label isolation rules;
- artifact retention policy.

This is the clinical equivalent of project instructions plus a coding-agent
config. It would make architecture comparisons reproducible and prevent hidden
differences between harnesses.

Suggested path:

```text
config/harnesses/
  direct_full_contract.v1.yaml
  direct_evidence_contract.v1.yaml
  retrieval_field_extractors.v1.yaml
  clines_epilepsy_modular.v1.yaml
  clines_epilepsy_verified.v1.yaml
```

### 4.2 Introduce A Harness Event Log

Run records currently capture rows and payloads, but coding-agent harnesses
teach that traces matter. Add a row-level event log with stable event types:

- `context_built`
- `provider_call_started`
- `provider_call_finished`
- `parse_attempted`
- `parse_repaired`
- `candidate_spans_selected`
- `field_extraction_completed`
- `verification_completed`
- `aggregation_completed`
- `budget_limit_hit`
- `warning_emitted`

This event log should not include PHI in a real clinical setting by default;
it can include hashes, offsets, token counts, field family, and artifact IDs.
For synthetic fixtures, quotes can be retained.

### 4.3 Promote Field Extractors To Skill-Like Units

Pi and Flue both make "skills" first-class. This repo can do the same without
importing a new framework. A clinical extraction skill should have:

- name and version;
- input schema;
- output schema;
- prompt/template reference if LLM-backed;
- deterministic pre/post-processing hooks;
- provider call budget;
- parse repair behavior;
- unit tests with replay/mock outputs.

The existing modules already contain the logic; this is a packaging and
metadata improvement. It would make it easier to add new fields, compare
field-family difficulty, and run field extractors in parallel later.

### 4.4 Add A Clinical-Document Interface

Borrowing from SWE-agent's Agent-Computer Interface, define a small set of
document tools rather than passing arbitrary context:

- `get_sections(row_id)`
- `search_spans(row_id, field_family)`
- `get_span(row_id, start, end, window)`
- `quote_evidence(row_id, locator)`
- `validate_payload(payload)`
- `compare_evidence_to_claim(claim, evidence)`

These can be implemented as normal Python functions, not model tools at first.
The point is to define the interface. Direct prompting can bypass it; retrieval
and modular harnesses can use it. That makes the ablation explicit.

### 4.5 Make Verification More Like Code Review

Coding agents often finish by running tests, lint, or review. Clinical
extraction needs an analogous final gate:

- parse validity check;
- schema completeness check;
- evidence support check;
- status/temporality consistency check;
- known epilepsy edge-case check;
- unsupported-overclaim downgrade;
- final artifact summary for adjudication.

The existing `clines_epilepsy_verified` harness is the correct place to expand
this. The verifier should be evaluated separately: how many errors does it
catch, how often does it incorrectly reject correct claims, and what does it
cost?

### 4.6 Add External Harness Adapters

Do not couple the dissertation to one vendor agent, but add a normalized adapter
boundary inspired by `harness.lol`:

```text
ExternalClinicalAgentAdapter
  run(row, manifest) -> ExtractionPayload + EventLog + RawArtifacts
```

This would allow future experiments where Claude Code, Codex, Pi, Flue, or
OpenHands are asked to run a controlled extraction script in a sandbox. The
dissertation's canonical results should still use local deterministic/replay
harnesses, but adapter support would make the architecture future-proof.

### 4.7 Treat Model Switching As An Experimental Variable

Pi and OpenHands emphasize model-agnostic routing and mid-session switching.
For clinical extraction, dynamic switching should be conservative:

- cheap model for candidate retrieval;
- stronger model for ambiguous field extraction;
- verifier model equal or stronger than extractor;
- escalation only when parse validity, low confidence, or verifier disagreement
  triggers it.

This should be evaluated as a costed reliability variant, not silently added to
the main harness.

## 5. Specific Research Hypotheses Enabled By Harness Expansion

The expanded harness architecture would support sharper dissertation claims:

1. Direct prompting may maximize recall and minimize cost, but modular harnesses
   may improve evidence support and failure discoverability.
2. Retrieval-field extraction may reduce cost and context length, but may lose
   recall when seizure frequency or medication status is distributed across
   sections.
3. Verifier variants may improve precision and evidence support while reducing
   recall through over-rejection.
4. Smaller open models may benefit more from harness structure than frontier
   closed models.
5. Typed outputs and parse repair may improve apparent validity but must be
   separated from clinical correctness.
6. Harness event logs may make adjudication faster and more consistent even
   when aggregate correctness does not improve.
7. Escalation policies may achieve a better cost/correctness frontier than
   using a frontier model for every row and every field.

## 6. Risks And Guardrails

The main risk is turning a clinical extraction dissertation into an agent
theatre exercise. More roles, calls, and artifacts do not automatically produce
better clinical extraction.

Guardrails:

- Keep the direct-prompt baseline strong and current.
- Evaluate every added module through ablation.
- Report cost, latency, token use, and implementation complexity.
- Preserve full-letter baselines so retrieval recall loss is visible.
- Do not expose gold labels to any harness path.
- Do not treat citations as sufficient evidence; score whether the cited text
  supports value, status, temporality, and normalization.
- Prefer deterministic post-processing where clinical rules are unambiguous.
- Keep synthetic-fixture claims separate from real-clinical claims.
- Treat chain-of-thought as implementation detail, not evidence.
- Keep external coding-agent adapters out of canonical clinical claims until
  they are reproducibly sandboxed and logged.

## 7. Recommended Implementation Backlog

### Near Term

1. Add `config/harnesses/*.yaml` manifests for existing harnesses.
2. Add a lightweight `HarnessEvent` dataclass and row-level event log.
3. Add manifest IDs and event-log summary counts to run metadata.
4. Package field extractors as skill-like units with name/version/input/output.
5. Extend the verifier artifact to distinguish value support, status support,
   temporality support, and normalization support.

### Medium Term

1. Implement a Clinical-Document Interface over sections, spans, and evidence.
2. Add budget-limited escalation policies as separate harness variants.
3. Add parallel field-family execution only after event logs make ordering and
   artifacts reproducible.
4. Add an external-agent adapter interface that can normalize outputs from
   CLI-based coding agents or Flue/Pi-style harnesses.
5. Add a table that reports harness complexity: number of calls, modules,
   prompts, schemas, repair attempts, and artifacts per row.

### Later

1. Evaluate synthetic-supervised fine-tuned models as a separate comparator.
2. Add local terminology lookup/UMLS-like normalization as an ablation.
3. Add clinician adjudication timing: does the artifact-rich harness reduce
   review time or improve reviewer agreement?
4. Explore a deployable headless workflow, Flue-style, only after the research
   harness has stable manifests, traces, and guardrails.

## 8. Bottom Line

The repo should not copy Claude Code, Codex, Pi, Flue, or OpenHands as products.
It should copy their deeper lesson: agent behavior is largely a property of the
harness. In clinical structured extraction, the harness is the method.

For this dissertation, the most valuable expansion is not a more elaborate
multi-agent story. It is a more explicit clinical extraction harness: manifests,
typed skills, bounded document tools, event traces, verifier gates, budgeted
model routing, and adjudication-ready artifacts. That would make the existing
architecture ladder more publishable because it would let the dissertation ask
not only "which model got the right answer?" but "which harness made the
answer clinically supported, inspectable, reproducible, and worth its cost?"

## Sources

- Agrawal M, Hegselmann S, Lang H, Kim Y, Sontag D. Large Language Models are
  Few-Shot Clinical Information Extractors. EMNLP 2022.
  <https://arxiv.org/abs/2205.12689>
- Anthropic. Claude Code overview.
  <https://code.claude.com/docs>
- Flue. The Agent Harness Framework.
  <https://flueframework.com/>
- Gemini CLI documentation.
  <https://google-gemini.github.io/gemini-cli/docs/>
- Grothey B, Odenkirchen J, Brkic A, et al. Comprehensive testing of large
  language models for extraction of structured data in pathology.
  Communications Medicine 2025.
  <https://www.nature.com/articles/s43856-025-00808-8>
- Harness.lol. What is harness?
  <https://www.harness.lol/docs>
- Holgate B, Fang S, Shek A, et al. Extracting Epilepsy Patient Data with
  Llama 2. BioNLP 2024.
  <https://aclanthology.org/2024.bionlp-1.43/>
- OpenAI. Unrolling the Codex agent loop. 2026.
  <https://openai.com/index/unrolling-the-codex-agent-loop/>
- OpenHands: An Open Platform for AI Software Developers as Generalist Agents.
  arXiv 2024.
  <https://arxiv.org/abs/2407.16741>
- Pi Coding Agent.
  <https://pi.dev/>
- SPELL-LLMs: A Scalable and Privacy-Compliant NLP Pipeline Using Locally
  Hosted Large Language Models for Clinical Information Extraction.
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC12330431/>
- SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering.
  arXiv 2024.
  <https://arxiv.org/abs/2405.15793>
- Yang Z, Yuan H, Sayeed R, et al. CLINES: Clinical LLM-based Information
  Extraction and Structuring Agent. medRxiv 2025.
  <https://www.medrxiv.org/content/10.64898/2025.12.01.25341355v1>
