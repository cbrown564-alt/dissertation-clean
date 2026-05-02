# Literature Review

## Review Strategy

This chapter is a narrative, decision-oriented literature review. It is not a
formal systematic review, but it follows several principles from the review
methods literature: define the purpose of the review, make the search logic
visible, synthesize rather than list papers, appraise the quality and limits of
evidence, and end with implications for the present study. These principles map
closely onto SANRA, the Scale for the Assessment of Narrative Review Articles,
which emphasizes justification of a review's importance, a clear aim, adequate
literature coverage, referencing, scientific reasoning, and appropriate
presentation of data (Baethge et al., 2019). PRISMA 2020 is designed for
systematic reviews rather than narrative reviews, but its insistence on
transparent eligibility, source selection, and synthesis is still useful as a
discipline (Page et al., 2021).

The review therefore has a thread rather than a topic list. It begins with a
clinical problem: epilepsy clinic letters contain information that is decisive
for care and research but difficult to structure. It then moves through the
technical history of clinical information extraction, from rule-based systems
to transformer models and LLMs. It narrows into epilepsy, where there is now a
recognizable literature on extracting seizure frequency, epilepsy type, seizure
type, medications, and investigations from clinic letters. It then broadens
again to ask what recent LLM extraction systems and coding-agent harnesses teach
about the dissertation's central design choice: whether a training-free,
role-separated, evidence-grounded pipeline can be evaluated as a serious
alternative to a strong single-prompt baseline.

The emphasis is deliberately methodological. The question is not only which
model performs best, but what should count as a good extraction system. Recent
work suggests that performance depends on the whole harness: prompt, schema,
chunking, retrieval, validation, decoding constraints, evidence grounding,
human adjudication, budget accounting, and the tool interface around the model.
That is the bridge between clinical NLP systems such as ExECT and CLINES, and
software-agent harnesses such as SWE-agent, Pi, Flue, OpenHands, and
Terminal-Bench. In both worlds, the model is no longer the whole method.

## 1. The Clinical Problem: Epilepsy Letters Are Rich, Temporal, And Hard To Share

Epilepsy care is unusually dependent on narrative. Seizure frequency, seizure
freedom, last seizure, seizure type, semiology, anti-seizure medication,
investigation results, diagnostic certainty, and risk counselling are often
stored in clinic letters rather than coded fields. In UK outpatient neurology,
the same document may function as a clinical note, a letter to the patient, a
letter to the GP, a longitudinal handover, and a medicolegal record. That makes
it rich, but it also makes it messy.

The problem is not simply that important facts are "unstructured." It is that
they are temporally and clinically qualified. "No tonic-clonic seizures" does
not mean globally seizure-free if absences continue. "Previously on
carbamazepine" does not mean current carbamazepine. "No epileptiform
discharges" does not necessarily mean a normal EEG. "A few clusters since last
review" may be clinically meaningful without supporting a precise monthly rate.
These examples matter because they define what clinical extraction has to
preserve: value, status, temporality, specificity, uncertainty, and evidence.

The epilepsy literature makes seizure frequency a natural anchor. Xie et al.
(2022) frame seizure frequency and seizure freedom as central outcome measures
for epilepsy care and retrospective research, and develop a machine-reading
pipeline to identify seizure-free status, seizure frequency text, and date of
last seizure from clinical notes. Their work highlights that seizure frequency
is not a simple entity. It is a question-answering and temporal interpretation
problem: "How often does the patient have seizures?" and "When was the last
seizure?" may require selecting the right sentence, ignoring historical
distractors, and preserving the current clinical frame.

King's College London and collaborators have pushed this point further in a
series of epilepsy clinic-letter studies. Holgate et al. (2024) used Llama 2 to
extract seizure frequency from NHS epilepsy letters, observing that the model
could identify unknown or ambiguous cases relatively well but struggled with
fine-grained low-frequency categories. Fang et al. (2025) extended LLM
extraction to epilepsy type, seizure type, current anti-seizure medications, and
associated symptoms. Gan et al. (2026) then proposed a synthetic-letter
framework for seizure-frequency extraction, showing that task-faithful
synthetic NHS-style letters with structured labels, rationales, and evidence
spans can train open-weight models that generalize to real clinic letters.

The clinical problem therefore points to three requirements for this
dissertation. First, seizure frequency is a valid anchor because it is
clinically important and technically difficult. Second, seizure frequency alone
is too narrow: medications, investigations, seizure classification, and epilepsy
classification have different language patterns and error modes. Third, the
right target is not free-text summarization. It is clinically adjudicable
structured extraction.

## 2. The Seminal Clinical NLP Lineage: Rules, Shared Tasks, And Ontologies

Clinical information extraction did not begin with LLMs. The field has a long
history of rule-based systems, ontology mapping, shared tasks, and hybrid
pipelines. That history matters because it explains why modern LLM extraction
systems still need schemas, evidence, assertion status, temporal attributes,
and human review.

MedLEE is one of the seminal clinical language processing systems associated
with Carol Friedman and colleagues. It reflects an early tradition of
domain-specific linguistic processing: parse clinical sublanguage, map phrases
to structured concepts, and attach modifiers such as certainty and status.
MetaMap (Aronson, 2001) brought a different but equally influential approach:
mapping biomedical text to UMLS Metathesaurus concepts. cTAKES (Savova et al.,
2010) made clinical text analysis more modular and open-source, combining
sentence detection, tokenization, part-of-speech tagging, chunking, named entity
recognition, concept mapping, negation, and status attributes. The original
cTAKES evaluation already shows a lesson that remains relevant: overlapping
span scores can look substantially better than exact span scores, and concept
mapping/status attributes have their own failure modes.

The i2b2/n2c2 shared tasks created another methodological foundation. The 2009
i2b2 medication extraction challenge focused on medication names and modifiers
such as dosage, mode, frequency, duration, and reason. The 2010 i2b2/VA
challenge asked systems to extract problems, tests, and treatments; classify
assertions; and identify relations between medical concepts (Uzuner et al.,
2011). These tasks established an important decomposition: identify the span,
classify the concept, determine whether it is present/absent/hypothetical or
about someone else, and connect it to the right relation or attribute.

This older literature is sometimes treated as obsolete because LLMs can produce
structured JSON directly. That is a mistake. It gives the vocabulary for why a
schema-valid output can still be clinically wrong. A medication entity without
current status is incomplete. A diagnosis without certainty can overclaim. An
investigation without its result or temporality may be unusable. An extracted
seizure type without evidence may be a hallucinated normalization. The
dissertation's evaluation contract should therefore be understood as a modern
LLM version of the clinical NLP lineage rather than an arbitrary layer of
documentation.

## 3. Clinical Letters Before LLMs: ExECT And The Lessons Of Rule-Based Epilepsy Extraction

The most directly relevant pre-LLM epilepsy system is ExECT: Extraction of
Epilepsy Clinical Text (Fonferko-Shadrach et al., 2019). ExECT used the GATE
framework with rule-based and statistical components to extract structured
epilepsy information from clinic letters. The validation set contained 200
previously unseen de-identified epilepsy and general neurology clinic letters,
reviewed against clinician annotations.

ExECT's headline result is strong: 1925 items were identified across 11
categories, with overall per-item precision 91.4%, recall 81.4%, and F1 86.1%.
But the per-category results are more important for this dissertation. Medication
extraction performed very well, with per-item precision 96.1%, recall 94.0%,
and F1 95.0%. Epilepsy diagnosis and epilepsy type were also strong. Seizure
frequency was harder: precision 86.3%, recall 53.6%, and F1 66.1% per item.
Generalized seizure extraction had a similar recall problem, and CT/MRI/EEG
investigation extraction showed uneven performance. On a per-letter basis,
scores improved because repeated mentions within the same letter could be
collapsed, but the pattern remained: structured medication-like fields were
easier than temporally variable seizure-frequency statements.

ExECT is important because it is not a weak straw man. It demonstrates that
open-source, rule-heavy clinical NLP can extract meaningful epilepsy variables
from letters with useful precision. It also identifies the same hard cases that
the present project cares about: seizure frequency, seizure type granularity,
investigation interpretation, and recall from varied prose. The limitation is
not that rules never work. The limitation is that rules are expensive to adapt,
fragile across writing styles and institutions, and less naturally suited to
temporality and uncertain paraphrase.

ExECTv2 and annotation work sharpen this point. The 2024 annotation paper on
epilepsy clinic letters describes synthetic letters written by neurology
consultants, trainees, and epilepsy specialist nurses, and reports that
validation of ExECTv2 against a gold standard produced an overall per-item F1 of
0.87, with seizure frequency again the lowest-performing category at 0.66 and
birth history the highest at 0.97. That result is almost a miniature map of the
field: structured or formulaic content is tractable; temporally complex,
clinician-styled narrative remains stubborn.

For this dissertation, ExECT supplies a baseline narrative even if it is not
implemented as a comparator. The project should not say "NLP could not do this
before LLMs." It should say: "Prior epilepsy NLP can extract many fields well,
but seizure frequency and other temporally qualified fields remain difficult,
and modern LLM systems create new possibilities for training-free,
evidence-grounded, schema-flexible extraction."

## 4. Transformer And Machine-Reading Approaches To Seizure Outcomes

Xie et al. (2022) represent the next methodological step: pretrained neural
models, fine-tuned for seizure outcome extraction. They annotated 1000 notes and
tested BERT, RoBERTa, and Bio_ClinicalBERT for seizure-free classification and
text extraction of seizure frequency and date of last seizure. Their best
combination used Bio_ClinicalBERT for classification and RoBERTa for text
extraction. Reported results were near human performance, with classification
accuracy above 80% and F1 scores above 0.80 for extraction tasks.

Two details matter. First, the framing as machine reading is clinically apt:
the model answers questions over the note, rather than merely tagging entity
strings. Second, most gains from fine-tuning reportedly required roughly 70
annotated notes. That weakens any simplistic argument that task-specific
training is impossible. If a narrow annotation task is well designed,
fine-tuning may be realistic and effective.

Work on seizure control metrics from Boston epilepsy clinic notes extends this
line by combining RoBERTa_for_seizureFrequency_QA with regular expressions to
categorize date of last seizure and seizure frequency into clinically meaningful
bins such as daily, weekly, monthly, once per year, and less than once per year.
This kind of hybrid approach is important: the neural model locates or answers,
while deterministic logic regularizes the output. It is a useful counterpoint to
pure LLM prompting.

The implication is that this dissertation's training-free design needs to be
argued, not assumed. Training-free systems have advantages in portability,
lower annotation burden, rapid schema iteration, and governance, but fine-tuned
models can be strong for narrow tasks. A high-quality review should make that
tension explicit.

## 5. Generative LLMs For Epilepsy Letters: What The New Studies Actually Show

The recent epilepsy LLM literature is directly relevant and should shape the
dissertation's choices.

Holgate et al. (2024) applied Llama 2 13B to seizure-frequency extraction from
NHS epilepsy EHR letters. The data pipeline began with 41,340 EHRs for 6,853
adult patients with epilepsy at King's College Hospital; 3,000 EHRs were
manually annotated for seizure frequency and other categories. The model was
run locally because confidential NHS data could not be sent to off-site APIs.
This governance constraint is crucial: it explains why open-weight models and
local harnesses are not merely ideological preferences but practical clinical
requirements.

Several findings are highly relevant. Temperature mattered: a default of 0.7
produced answers that were too "creative" for clinical extraction, including
false positives and even occasional diagnostic advice; a near-zero temperature
reduced this behaviour. Few-shot prompting mattered: 11 examples were needed to
teach the model the nuanced nine-category seizure-frequency scheme. Prompt
structure mattered: a three-step query helped the model decide whether
frequency information existed and then express frequency in an appropriate
time unit. The task remained difficult. Across the full annotated dataset,
Llama 2 achieved F1 0.73 for the nine-category task, with high apparent
accuracy inflated by true negatives. It did well on unknown/ambiguous cases
but struggled with lower-frequency categories. When categories were collapsed
into frequent, infrequent, and unknown, the model achieved F1 0.87 for unknown,
0.62 for frequent, and 0.30 for infrequent seizures.

This paper is valuable because it is refreshingly concrete about what worked
and what did not. LLM prompting improved feasibility, but label granularity,
class imbalance, vague language, and category sparsity remained limiting. It
also shows why accuracy is a poor headline metric when most letters may not
contain the target signal. The present dissertation's emphasis on field-family
metrics and abstention is therefore well justified.

Fang et al. (2025) broadened the task from seizure frequency to epilepsy type,
seizure type, current anti-seizure medications, and associated symptoms using
280 annotated clinic letters from King's College Hospital. They compared open
LLMs from the Llama and Mistral families using direct extraction,
summarized-direct extraction, contextualized-direct extraction,
contextualized-summarized extraction, role prompting, and few-shot prompting.
Two epileptologists annotated the gold standard, with Cohen's kappa 0.84.
Llama 2 13B direct extraction was strong across several tasks, with F1 0.80
for epilepsy type, 0.76 for seizure type, and 0.90 for current anti-seizure
medications. Mixtral performed best for current ASMs in one comparison, but
only slightly above Llama 2 13B. The study reports that LLMs outperformed a
fine-tuned MedCAT approach by around 0.2 F1.

The most important methodological finding is that direct extraction often
performed best. Summarization and contextualization did not automatically
improve extraction. That matters for the dissertation because multi-step
pipelines are not guaranteed wins. A role-separated architecture may improve
auditability, evidence support, or some fields, but it can also introduce
information loss if early summaries omit decisive detail.

Gan et al. (2026) are even closer to the present project's data strategy. They
propose reproducible synthetic clinical letters for seizure-frequency
extraction, using a high-capacity teacher model to generate NHS-style synthetic
epilepsy follow-up letters paired with normalized labels, rationales, and
evidence spans. Their structured label scheme covers explicit rates, ranges,
cluster descriptions, seizure-free durations, unknown frequency, and explicit
no-seizure statements. They fine-tuned open-weight models between 4B and 14B
parameters, including Qwen2.5, Gemma, MedGemma, Lingshu, Llama 3.1, and
Ministral variants. With 15,000 synthetic training letters, models trained only
on synthetic data generalized to a clinician double-checked held-out set of real
clinic letters, reaching micro-F1 up to 0.788 for fine-grained categories and
0.847 for pragmatic categories. A medically oriented 4B model achieved 0.787
and 0.858. The authors report that structured labels consistently outperformed
direct numeric regression, and that evidence-grounded outputs supported rapid
clinical verification and error analysis.

This is the most direct challenge to a purely training-free dissertation. It
shows that synthetic, task-faithful supervision can work. But it also supports
several choices in the current repo: structured labels beat naive numeric
targets; evidence spans matter; synthetic letters can be useful for safe
development; and model outputs should be designed around clinical language, not
only downstream numeric convenience.

The correct implication is not "abandon training-free extraction." It is:
position training-free extraction as one branch of a larger design space, and
make the dissertation valuable by evaluating the architecture, evidence
contract, and adjudication protocol with unusual care. Fine-tuning with
synthetic supervision becomes a future comparator or sensitivity extension,
not an ignored competitor.

## 6. General Clinical LLM Extraction: From Few-Shot IE To Agentic Pipelines

Outside epilepsy, Agrawal et al. (2022) is a seminal LLM clinical information
extraction paper. It showed that InstructGPT-style models could perform
zero-shot and few-shot clinical IE across span identification, sequence
classification, and relation extraction tasks, outperforming existing
zero/few-shot baselines. Its contribution was not only performance; it made
clinical IE a plausible target for instruction-following LLMs without
task-specific training.

The more recent literature has become more operational. CLINES, the Clinical
LLM-based Information Extraction and Structuring Agent, is particularly
important. Yang et al. (2025) describe a modular agentic pipeline for clinical
concept extraction and structuring: semantic chunking of long notes; LLM
extraction; assignment of assertion, experiencer, numerical values, and SI
units; UMLS normalization; explicit and relative date resolution; and
aggregation into an i2b2-style schema. It was evaluated zero-shot on MIMIC-III
notes, 4CE notes, and CORAL oncology reports. Across datasets, CLINES led
rule/lexicon systems, transformer encoders, and single-prompt LLM baselines.
Reported F1 scores for entity/assertion/value-unit/date were 0.69/0.93/0.90
for MIMIC-III where date was not evaluated, 0.87/0.88/0.79/0.79 for 4CE,
0.81/0.84/0.77/0.73 for CORAL breast, and 0.85/0.87/0.90/0.78 for CORAL
pancreas. Gains over the strongest single-prompt LLM were reported as 0.21 to
0.38 F1 across tasks. Performance remained stable across note-length quantiles,
where transformer baselines lost recall as notes lengthened.

CLINES is not epilepsy-specific, but it is directly relevant because it turns
"multi-agent" into a concrete clinical extraction architecture. It does not
merely ask a model for JSON. It segments, extracts, attributes, normalizes,
resolves time, and aggregates. That resembles the architecture in this repo:
section/timeline, field extractors, verification, and aggregation. The
important difference is that CLINES emphasizes ontology grounding and
large-scale chart-review-like extraction, while this dissertation emphasizes
evidence support, field-family adjudication, and training-free comparison to a
single-prompt baseline.

Other recent work points in the same direction. Builtjes et al. (2025)
evaluated nine open-source generative LLMs on the Dutch DRAGON benchmark,
covering 28 clinical information extraction tasks, using the public
`llm_extractinator` framework. They found that several 14B models, including
Phi-4-14B, Qwen-2.5-14B, and DeepSeek-R1-14B, were competitive, while Llama
3.3 70B performed somewhat better at higher computational cost. Translation to
English degraded performance, supporting native-language extraction where
possible. Spaanderman et al. (2025) evaluated 15 open-weight LLMs across six
pathology and radiology use cases in three countries and multiple languages.
They found that top-ranked models approached inter-rater agreement, that
small-to-medium general-purpose models could be competitive, and that few-shot
and prompt-graph prompting improved performance by around 13%. Importantly,
task-specific complexity and annotation variability explained more variance
than model size or prompting strategy.

Mahbub et al. (2026) address validation rather than extraction alone. Their
multi-stage framework for extracting substance-use disorder diagnoses from
919,783 clinical notes combines prompt calibration, rule-based plausibility
filtering, semantic grounding, confirmatory evaluation by a higher-capacity
judge LLM, selective expert review, and external predictive validity. Rule-based
filtering and semantic grounding removed 14.59% of LLM-positive extractions as
unsupported, irrelevant, or structurally implausible; judge assessments showed
substantial agreement with expert review in high-uncertainty cases (Gwet's
AC1=0.80). This is a strong argument for treating validation as a first-class
pipeline component.

The combined lesson is clear. Clinical LLM extraction is moving from "prompt a
model and score the answer" toward harnessed systems: chunking, schemas,
normalization, verification, grounding, selective review, and cost-aware model
choice. The current dissertation sits squarely in that transition.

## 7. Harnesses: What Coding Agents Teach Clinical Extraction

The user's examples of Pi and Flue are useful because coding-agent research has
become unusually explicit about the harness. In software engineering, the same
model can perform differently depending on the shell, editor, file tools,
search tools, test runner, patch format, memory, planning loop, permissions,
and evaluation scaffold. That is directly analogous to clinical extraction:
the model's apparent ability depends on whether it sees the whole letter,
candidate spans, schema descriptions, examples, validation feedback, and a
verification role.

SWE-bench made this visible by evaluating agents on real GitHub issues rather
than toy code-generation tasks. SWE-agent then showed that the
agent-computer interface itself can change performance. Yang et al. (2024)
argue that language-model agents are a new class of end user and need
interfaces designed for their abilities. SWE-agent's custom interface for
editing, navigating repositories, and running tests improved results on
SWE-bench and HumanEvalFix. The lesson for clinical extraction is not that a
clinic-letter system needs a coding shell. It is that interface design is a
research variable.

OpenHands generalizes this idea into a platform for software agents that can
write code, use a command line, browse, and operate in sandboxed environments.
Terminal-Bench and Terminal-Bench 2.0 evaluate agents on realistic terminal
tasks with unique environments, human-written solutions, and verification
tests; the 2026 Terminal-Bench 2.0 paper reports that frontier models and
agents still score below 65% on 89 hard tasks. SWE-bench-Live was introduced
to reduce contamination by using more recent GitHub issues across many
repositories. These developments are relevant because they show the field
moving from static model benchmarks to executable, environment-based,
contamination-aware harnesses.

Pi and Flue are more recent examples of harnesses as products or frameworks.
Pi describes itself as a minimal terminal coding harness with project
instructions, extension points, skills, prompt templates, themes, multiple
modes, and an SDK. Its design stance is that the harness should be adapted to
the user's workflow rather than impose an overbuilt agent. Flue frames the
agent as "model plus harness": filesystem tools, sandbox bash, skills, memory,
sessions, typed outputs, controlled secrets, and deployable workflows. Its
examples include issue triage, data analysis, coding agents, and support
agents, all controlled through a programmable TypeScript harness.

For this dissertation, coding harnesses supply a vocabulary. A clinical
extraction harness should specify:

- what context the model can see;
- what role-specific instructions it receives;
- whether it can use candidate spans or retrieval;
- how outputs are constrained and parsed;
- how invalid outputs are repaired or rejected;
- how evidence is checked;
- how intermediate artifacts are stored;
- how budgets and latency are recorded;
- how human review enters the loop.

This is why the repo's "harness" abstraction is not incidental code
organization. It is part of the method. The dissertation can borrow the
software-agent lesson without overclaiming: good harnesses do not make models
magical, but they make behaviour more observable, reproducible, and evaluable.

## 8. Single Prompt Versus Role Separation

The literature does not support the claim that multi-agent systems are
inherently better. It supports a narrower and more interesting claim:
decomposition can help when subtasks have different information needs,
failure modes, or validation criteria.

In clinical extraction, a single prompt has real advantages. It sees the whole
letter at once. It avoids lossy summaries. It has lower latency and cost. It
is easier to reproduce. Fang et al. (2025) found that direct extraction often
outperformed more elaborate summarized or contextualized extraction methods
for epilepsy fields. That is a warning against building a theatrical pipeline
whose intermediate steps merely add opportunities to drop information.

Role separation has different strengths. A section/timeline role can identify
where in the document relevant claims occur. Field extractors can focus on
distinct clinical concepts and schemas. A verifier can judge whether a proposed
claim is supported by a cited span. An aggregator can preserve warnings,
deduplicate items, and avoid inventing facts. CLINES suggests that this kind
of modularity can outperform single-prompt baselines for long and heterogeneous
clinical notes. Mahbub et al. suggest that validation and semantic grounding
can remove a meaningful fraction of unsupported LLM-positive claims. Gero et
al.'s self-verification work similarly supports the idea that extraction and
verification should be separated when provenance matters.

The present dissertation should therefore make role separation a hypothesis,
not a belief. It should ask:

- Does role separation improve field-level correctness?
- Does it improve evidence-support grades?
- Does it improve warning quality and error discoverability?
- Does it preserve recall, or does it lose facts through segmentation and
  summarization?
- Are any improvements worth additional calls, tokens, and latency?

The strongest possible outcome is not necessarily "multi-agent beats single
prompt on every metric." A more credible outcome may be: the role-separated
pipeline is similar in value accuracy but produces better evidence support,
more useful warnings, and more inspectable failure modes at higher cost.

## 9. Output Representation: The Label Is Part Of The Method

One of the clearest findings across the epilepsy literature is that the output
representation shapes performance. Holgate et al. (2024) tried nine seizure
frequency categories and found that fine-grained lower-frequency bins were
difficult; collapsing to three categories improved usability but sacrificed
detail. Gan et al. (2026) found that structured label targets outperformed
direct numeric regression for seizure-frequency extraction. ExECT's results
show that medication extraction is easier when the representation resembles
the text pattern: drug name, dose, and frequency.

This is not a cosmetic design issue. A numeric monthly seizure rate is useful
for modelling treatment response, but it can force over-precise conversions
from vague clinical statements. A categorical label is easier to adjudicate but
may hide clinically important nuance. A status object with evidence spans can
preserve uncertainty but may be harder to aggregate statistically.

For this dissertation, the safest representation is a clinical-status object:
extracted value, status/currentness, temporal anchor, specificity, evidence,
confidence, and warnings. Numeric normalization can be included only where the
source supports it or where a deterministic conversion rule is explicitly part
of the evaluated contract. This aligns with the repo's current field-family
contract and avoids pretending that every clinic-letter phrase can be safely
reduced to a rate.

## 10. Evidence, Rationales, And Verification

Evidence support is the hinge between extraction and clinical adjudication.
Many LLM systems can be prompted to provide citations, but a citation is only
useful if it supports the exact claim. A span mentioning "lamotrigine" may not
support current lamotrigine. A span mentioning "focal seizures" may not support
a diagnosis of focal epilepsy. A span in the right section may still be too
broad to adjudicate.

Recent work makes evidence more concrete. Gan et al. generated synthetic
letters with evidence spans and rationales, and report that evidence-grounded
outputs supported rapid clinical verification and error analysis. Mahbub et
al.'s validation framework uses semantic grounding and plausibility filters to
remove unsupported or irrelevant positive extractions. CLINES preserves
attributes, normalization, dates, and aggregation into a schema-ready form.
Gero et al. (2023) explicitly study self-verification for few-shot clinical IE,
showing that provenance and verification can improve clinical extraction.

The dissertation should be careful with chain-of-thought. Some papers use
reasoning traces as training supervision or as interpretability aids. In this
project, the more defensible public artifact is not hidden model reasoning but
source-grounded evidence: the quoted span, field placement, temporal anchor,
verifier grade, and warning. That is enough to support adjudication without
making internal reasoning text the object of trust.

Evidence grades should therefore remain central:

- exact or near-exact evidence;
- overlapping but over-broad evidence;
- section-level but not decisive evidence;
- evidence with wrong temporal/status support;
- unsupported evidence;
- missing evidence.

This will let the dissertation distinguish "the model found the right entity"
from "the model made a clinically supported claim."

## 11. Evaluation: Why Aggregate Accuracy Is Not Enough

The health-care LLM evaluation literature repeatedly warns that tasks, metrics,
data sources, and validation methods vary widely. Bedi et al.'s JAMA systematic
review of health-care LLM testing and broader reviews of LLMs in clinical
workflows emphasize the same pattern: many studies remain retrospective,
benchmark-driven, or in silico; real-world validation is limited; and metrics
often fail to capture clinical risk.

Epilepsy extraction demonstrates the problem at a smaller scale. Holgate et
al. report high accuracy but prefer F1 because unknown/negative examples inflate
accuracy. ExECT reports both per-item and per-letter scores because repeated
mentions change what counts as useful. Fang et al. aggregate true positives,
false positives, and false negatives across labels because each letter can
contain multiple categories. Xie et al. use separate classification and text
extraction tasks. Gan et al. report fine-grained and pragmatic groupings.

This dissertation should therefore evaluate in layers:

1. Field implementation coverage: did the harness attempt the field family?
2. Parse validity: did the output conform to the schema?
3. Recoverability: could invalid output be repaired without semantic change?
4. Proxy support: did it emit values and evidence?
5. Value correctness: is the clinical entity or concept correct?
6. Status and temporality: is currentness and timing correct?
7. Normalization: is the schema label defensible?
8. Evidence support: does the cited text support the full claim?
9. Budget: how many calls, tokens, seconds, and provider costs?
10. Failure categories: what errors remain?

Budget deserves explicit emphasis. Role-separated systems will usually cost
more than single-prompt systems. The only honest comparison is either matched
budget, or deliberately unequal budget reported as part of the intervention.
Coding-agent benchmarks have learned this lesson through terminal tasks,
containerized environments, and tool-call budgets. Clinical extraction needs
the same discipline.

## 12. Governance, Privacy, And Synthetic Data

Clinical-letter extraction is constrained by governance. Holgate et al. ran
open Llama 2 locally because NHS clinical data could not be sent to an external
API. Gan et al. use synthetic letters because real epilepsy correspondence is
hard to share and annotate at scale. Builtjes et al. emphasize open-source
models for privacy-conscious and resource-constrained clinical IE. These are
not peripheral details; they determine what research is reproducible.

Synthetic data is especially important but must be treated carefully. Synthetic
letters can make development reproducible and privacy-preserving. They can
cover rare temporal patterns, cluster descriptions, seizure-free intervals, and
ambiguous cases. But they can also encode teacher-model artifacts, simplify
real-world mess, or create over-regularized labels. Gan et al.'s contribution
is strong precisely because the synthetic letters are task-faithful, paired
with structured labels and evidence, and evaluated on clinician-checked real
letters.

For this repo, synthetic fixtures are useful for development and sensitivity
testing, but claims about clinical performance should remain bounded unless
real adjudicated letters are available. A dissertation can still make a strong
methodological contribution with synthetic or limited data if it is precise
about what the evidence supports.

## 13. What This Literature Means For The Dissertation

The literature now suggests a sharper position than the first draft.

This dissertation is not trying to prove that LLMs are better than clinical
NLP, or that multi-agent systems are inherently better than direct prompting.
It is testing a specific proposition: for epilepsy clinic-letter extraction,
can a training-free, contract-constrained, role-separated LLM harness produce
more reliable, evidence-supported, and auditable structured outputs than a
strong single-prompt harness, when both are evaluated under the same schema,
fixed slices, explicit budgets, and clinical adjudication rules?

The main contribution can be methodological even if the performance result is
mixed. ExECT shows that epilepsy clinic-letter extraction is feasible but
uneven. Xie et al. show that fine-tuned machine reading can perform strongly
for seizure outcomes. Holgate et al. show that local generative LLMs can help
but struggle with fine-grained seizure-frequency categories. Fang et al. show
that open LLMs can extract broader epilepsy fields and that direct extraction
may outperform more elaborate prompting. Gan et al. show that synthetic,
structured, evidence-grounded supervision is a powerful alternative. CLINES
shows that modular agentic clinical extraction can outperform single-prompt
baselines across long, heterogeneous notes. Modern coding-agent harnesses show
that the scaffold around the model is part of the evaluated system.

Taken together, these papers argue for a dissertation that is careful, not
grandiose. The key design principles should be:

- Treat seizure frequency as the anchor, but evaluate field families separately.
- Keep the single-prompt baseline strong.
- Treat role separation as an empirical intervention.
- Avoid lossy summarization unless it is evaluated.
- Use structured outputs, but never confuse schema validity with clinical
  correctness.
- Require evidence and grade whether it supports value, status, temporality,
  and normalization.
- Report budget as a result.
- Discuss fine-tuning and synthetic supervision as serious alternatives.
- Make auditability operational through artifacts, warnings, and adjudication.

## 14. Decision Map Preview

The next document can turn this review into a decision map. The most important
axes are:

| Decision | Options | Evidence From Literature | Recommended Position |
| --- | --- | --- | --- |
| Task scope | Seizure frequency only; broader field families | ExECT and Fang et al. show uneven field difficulty; seizure frequency alone is too narrow | Keep seizure frequency as anchor and report field families separately |
| Frequency representation | Numeric rate; categories; structured status object | Holgate struggles with fine categories; Gan finds structured labels beat numeric regression | Use structured status/evidence object; add numeric only when supported |
| Model strategy | Training-free; few-shot; fine-tuned; synthetic-supervised | Agrawal supports few-shot IE; Xie and Gan show fine-tuning can work | Main study training-free, with fine-tuning/synthetic supervision as explicit alternative |
| Architecture | Single prompt; pipeline; role-separated agents | Fang warns direct extraction can be best; CLINES supports modular extraction for long notes | Compare strong single prompt with role-separated pipeline; do not assume improvement |
| Evidence | Optional citation; required quote; verifier-graded support | Gan, Mahbub, Gero support evidence and grounding | Require evidence and score support quality |
| Harness | Prompt only; schema harness; full artifact harness | SWE-agent, Pi, Flue, CLINES show harness design matters | Treat harness as part of the method and log artifacts/budget |
| Evaluation | Aggregate accuracy; field metrics; adjudication | ExECT, Holgate, and clinical LLM reviews show aggregate metrics mislead | Use layered evaluation and matched adjudication |
| Claim | Deployment readiness; model superiority; curation support | Governance and reporting standards caution against overclaiming | Claim retrospective extraction/auditability evidence only |

## References

- Agrawal M, Hegselmann S, Lang H, Kim Y, Sontag D. Large Language Models are
  Few-Shot Clinical Information Extractors. EMNLP 2022.
  <https://arxiv.org/abs/2205.12689>
- Aronson AR. Effective mapping of biomedical text to the UMLS Metathesaurus:
  the MetaMap program. AMIA 2001.
  <https://pubmed.ncbi.nlm.nih.gov/11825149/>
- Baethge C, Goldbeck-Wood S, Mertens S. SANRA: a scale for the quality
  assessment of narrative review articles. Research Integrity and Peer Review
  2019. <https://pmc.ncbi.nlm.nih.gov/articles/PMC6434870/>
- Bedi S, Liu Y, Orr-Ewing L, et al. Testing and Evaluation of Health Care
  Applications of Large Language Models: A Systematic Review. JAMA 2025.
  <https://jamanetwork.com/journals/jama/fullarticle/2825147>
- Builtjes L, Bosma J, Prokop M, van Ginneken B, Hering A. Leveraging
  Open-Source Large Language Models for Clinical Information Extraction in
  Resource-Constrained Settings. arXiv 2025.
  <https://arxiv.org/abs/2507.20859>
- Fang S, Holgate B, Shek A, et al. Extracting epilepsy-related information
  from unstructured clinic letters using large language models. Epilepsia
  2025. <https://pubmed.ncbi.nlm.nih.gov/40637590/>
- Fonferko-Shadrach B, Lacey AS, Roberts A, et al. Using natural language
  processing to extract structured epilepsy data from unstructured clinic
  letters: development and validation of the ExECT system. BMJ Open 2019.
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC6500195/>
- Gan Y, Barlow SH, Holgate B, et al. Reproducible Synthetic Clinical Letters
  for Seizure Frequency Information Extraction. arXiv 2026.
  <https://arxiv.org/abs/2603.11407>
- Gero Z, Singh C, Cheng H, et al. Self-Verification Improves Few-Shot Clinical
  Information Extraction. arXiv 2023. <https://arxiv.org/abs/2306.00024>
- Holgate B, Fang S, Shek A, et al. Extracting Epilepsy Patient Data with
  Llama 2. BioNLP 2024. <https://aclanthology.org/2024.bionlp-1.43/>
- Mahbub M, Dams GM, Arnold J, et al. A Multi-Stage Validation Framework for
  Trustworthy Large-scale Clinical Information Extraction using Large Language
  Models. arXiv 2026. <https://arxiv.org/abs/2604.06028>
- Page MJ, McKenzie JE, Bossuyt PM, et al. The PRISMA 2020 statement: an
  updated guideline for reporting systematic reviews. BMJ 2021.
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC8005924/>
- Savova GK, Masanz JJ, Ogren PV, et al. Mayo clinical Text Analysis and
  Knowledge Extraction System (cTAKES): architecture, component evaluation and
  applications. JAMIA 2010. <https://pubmed.ncbi.nlm.nih.gov/20819853/>
- Spaanderman DJ, Prathaban K, Zelina P, et al. Evaluating Open-Weight Large
  Language Models for Structured Data Extraction from Narrative Medical Reports
  Across Multiple Use Cases and Languages. arXiv 2025.
  <https://arxiv.org/abs/2511.10658>
- Uzuner O, South BR, Shen S, DuVall SL. 2010 i2b2/VA challenge on concepts,
  assertions, and relations in clinical text. JAMIA 2011.
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC3168320/>
- Xie K, Gallagher RS, Conrad EC, et al. Extracting seizure frequency from
  epilepsy clinic notes: a machine reading approach to natural language
  processing. JAMIA 2022.
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC9006692/>
- Yang J, Jimenez CE, Wettig A, et al. SWE-agent: Agent-Computer Interfaces
  Enable Automated Software Engineering. NeurIPS 2024.
  <https://arxiv.org/abs/2405.15793>
- Yang Z, Yuan H, Sayeed R, et al. CLINES: Clinical LLM-based Information
  Extraction and Structuring Agent. medRxiv 2025.
  <https://www.medrxiv.org/content/10.64898/2025.12.01.25341355v1>
- Terminal-Bench 2.0: Benchmarking Agents on Hard, Realistic Tasks in Command
  Line Interfaces. arXiv 2026. <https://arxiv.org/abs/2601.11868>
- Pi Coding Agent. <https://pi.dev/>
- Flue: The Agent Harness Framework. <https://flueframework.com/>
