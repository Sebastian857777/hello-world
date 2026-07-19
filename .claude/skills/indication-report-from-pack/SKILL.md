---
name: indication-report-from-pack
description: >-
  Phase 2 of a two-step indication (disease) workflow. Write a comprehensive indication
  report for a disease, drawing primarily on a previously built evidence pack and
  supplementing with fresh web search. The report covers the disease basics, epidemiology,
  treatment paradigm, approved drugs (by target, with modality and patent-cliff/LOE inline
  per molecule), unmet need, clinical pipeline, emerging options, a gap analysis, and a
  dedicated "what a peptide could do" section. Use this whenever the user wants the
  "indication report", "disease report", "indication deep-dive", or "full analysis" for a
  disease AND an evidence pack already exists (an "{indication}-evidence-pack" folder), or
  the user says things like "now write the report from the pack" or "turn the evidence pack
  into the indication report". Pair skill to indication-evidence-pack. If no evidence pack
  exists yet, point the user to build one first with indication-evidence-pack. For a drug
  TARGET or pathway rather than a disease, use drug-target-landscape-from-pack instead.
---

# Indication Report from Evidence Pack (Phase 2)

This skill turns an existing indication evidence pack into a rigorous, nine-part disease
report. It is the second of two steps: `indication-evidence-pack` gathers the sources; this
synthesises them into the report, cross-checked and topped up with fresh web search.
Grounding the synthesis in the pack means every major claim can be traced back to a file the
user actually has on disk.

This is the disease-axis sibling of `drug-target-landscape-from-pack`: same machinery
(pack-as-floor synthesis, citation discipline, deep-mode fan-out, mechanical citation
verification), rotated so the entry point is a disease rather than a molecule.

## Step 1: Locate and load the evidence pack

Identify the indication from the user's request, then find its pack: an
`{indication-slug}-evidence-pack/` folder in the working directory. Read `MANIFEST.md`
first: its index table shows what is available and its Summaries section holds the
structured extract (including hand-pulled prevalence/dosing/efficacy facts and LOE basis)
for each artifact. Work from those summaries to triage, then **deep-read the paired
full-text Markdown** (`.md` next to each PDF) only when a specific claim needs verification.
If a manifest entry is flagged `pdf+md*` (unreliable conversion), read the original PDF for
that artifact rather than trusting its Markdown.

**Pick up anything the user added by hand.** Between Phase 1 and now, the user may have
manually acquired paywalled papers (see the pack's `WANTED.md`) and dropped them into
`reviews/` or elsewhere. Scan the pack folder for files not listed in `MANIFEST.md`, read
them, and add them to the manifest (assign IDs) before synthesising, so their content is
used and cited like everything else.

**Check the pack's age.** Read the build date from the `MANIFEST.md` header and compare it
to today. The pack's primary sources age even though Step 2 refreshes volatile facts: new
approvals, label revisions, and new pivotal readouts since the build date will not be in the
pack. If the pack is more than a few months old, or the disease is in a fast-moving area,
tell the user how old it is and flag that a Phase 1 refresh would capture newer primary
sources. Proceed if they are fine with it, but do not let an old pack silently stand in for
current primary evidence.

If no pack exists for the indication, do not silently proceed. Tell the user and offer to
build one first with `indication-evidence-pack`. Building the report with no pack defeats
the purpose of this two-step flow.

**Start the run clock.** Immediately capture a start timestamp so elapsed time can be
recorded later (final step): run `date -u +%FT%TZ` and keep the value.

## Step 2: Synthesise with the pack as a floor, not a ceiling

Work **part by part** (the nine parts below), treating each as an independent task. The
governing principle: **the evidence pack is a floor, never a ceiling.** It can only add
coverage and provenance; it must never bound what the report looks at. For each part:

1. **Research as if there were no pack.** First decide what evidence this part *needs* and
   run the searches you would have run with no pack at all (web, plus Open Targets, ChEMBL,
   ClinicalTrials.gov, PubMed). This keeps the pack's retrievability bias, its skew toward
   whatever was free to download, from silently becoming the boundary of the analysis.
2. **Reconcile against the pack, with verifiable citations.** Then check the pack for the
   same evidence and cite it under the citation discipline in Step 2a. Where the pack and
   fresh sources disagree, surface the conflict rather than defaulting to either.
3. **Refresh volatile facts unconditionally.** The pack is a snapshot. Always web-check the
   facts that go stale fast: very recent approvals, new pivotal readouts, discontinuations,
   biosimilar/generic launches, and updated guidelines, regardless of what the pack says.

## Step 2a: Citation discipline (make citations verifiable)

Pack citations are only worth anything if they reflect a source you actually consulted. To
keep citations honest, and checkable afterwards, follow these rules:

1. **Quote or locator on load-bearing facts.** Any specific number or hard claim attributed
   to a pack full-text source must carry either a short verbatim quote (in quotation marks,
   ideally under 15 words) or an exact locator, and the manifest ID. Format:
   `(pack: E02, p.3, "prevalence of 1 in 2,000")` or `(pack: L03, §12.3 Pharmacokinetics)`.
   You cannot produce a matching verbatim string or precise locator without having actually
   opened the file, so this both deters writing-from-memory and lets the verification script
   (Step 5) confirm the quote exists.
   **A quoted string must be a single contiguous span copied verbatim from the source**, so
   it survives the mechanical check in Step 5. Two failure modes routinely break that check:
   - **No ellipsis-stitching.** Do not join non-adjacent fragments with `...` inside a quote.
     The verifier looks for the quote as one contiguous string. Quote one contiguous fragment,
     or use two separate quoted citations, or fall back to a section locator.
   - **No paraphrase-as-quote.** Quotation marks mean "these exact characters appear in the
     file". Do not put your own compression or a manifest-summary paraphrase in quotation
     marks. If your wording is a paraphrase, copy the real contiguous string, or drop the
     quotation marks and cite by locator or summary tier. Do not quote against `MANIFEST` as
     if it were a source file; cite the underlying artifact ID with a real quote or locator.
   When in doubt, prefer an honest section locator or `summary` tier over a quote you are not
   sure is verbatim.
2. **Cite the tier you actually used.** Be honest about depth: `(pack: E02, summary)` when
   the claim rests only on the manifest summary, versus `(pack: E02, full-text, p.3, "...")`
   when you opened and read the paired Markdown or PDF. Do not label something full-text
   unless you read the full text.
3. **Extract before you write the dense parts.** For Part 4 (the approved-drugs table and
   per-drug PK/dosing/LOE) and Part 2 (epidemiology figures), first pull the numbers into a
   scratch table with their locators as you read each source, then write the prose from that
   table.
4. **Also cite the source the conventional way.** The pack ID gives *you* traceability, but a
   reader (or the Google Doc this becomes) needs a normal citation too. Alongside the pack
   reference, give a brief conventional citation: an academic-style reference (first author et
   al., journal, year, DOI where known) for papers, the trial acronym plus NCT number for
   trials, and a direct link for labels, guidelines, and web-only facts. **Keep the
   conventional citation OUTSIDE the `(pack: ...)` parentheses** so the verification parser is
   unaffected and DOIs/URLs do not break it. Example: `...reduced body weight by 14.9%
   (STEP 1, NCT03548935; Wilding et al., NEJM 2021) (pack: T02).` A web-only fact carries just
   the conventional citation and no pack ID.

If you genuinely cannot find support for a claim in the pack or on the web, say so and mark
it uncertain rather than attaching a citation that only looks plausible.

Cross-reference the databases where they add rigor: Open Targets (disease-target association,
tractability), ChEMBL (drug mechanism/modality), ClinicalTrials.gov (pipeline verification),
PubMed (mechanism/epidemiology/unmet need). Prefer the pack's saved exports where they answer
the question, but do not treat their absence as evidence of absence.

Throughout: prioritise recent data, **flag where information is thin, conflicting, or
uncertain**, and consistently **distinguish approved use from off-label from investigational**
(make this distinction visible in the text).

## Step 3: Deliver the nine parts to a markdown file

Write the full report to a single markdown file in the working directory, named
`{indication-slug}-indication-report.md`, with the top-level heading:

> **"{INDICATION}: Indication Report and Unmet-Need Analysis"**

Adapt the bracketed generic language below to the specific disease.

## Depth and completeness (this determines the quality of the output)

This report is meant to be **exhaustive, not a summary**, and the evidence pack should make
it *more* detailed, not less: having sources on disk is a reason to write more, never a
licence to shorten. Treat the bullets under each part as a *checklist of what to cover*, not
the shape of the answer: expand each item into **developed prose** (a paragraph or more per
topic, drug, or gap), not terse one-line fragments. A mature indication (many approved drugs,
large pipeline, years of data) warrants a long document that can run to dozens of pages; a
rare disease with one approved drug warrants less, but still gets full prose and full
enumeration. **Completeness, not brevity, is the goal.**

Every run must:
- **Write in prose** under each sub-heading, not bullet fragments.
- **Include summary tables in addition to the prose:** the approved-drugs table (Part 4), a
  pipeline table (Part 6), and a gap-vs-pipeline matrix (Part 8).
- **Enumerate exhaustively:** every approved drug, every meaningful pipeline programme, and
  every distinct unmet need, not just the headline ones. Mine the pack's trial records and
  drugs-targets exports for the full list.
- **Name sources explicitly** in the Source Appendix: pivotal trials (acronym plus NCT),
  key reviews, labels, guidelines, and epi sources.
- If a section is genuinely thin, say so in a sentence and move on; honest thinness is fine,
  silent omission and padding are not.

## Execution: deep mode (default)

**Deep mode is the default: always write the parts by fanning out one writer subagent per
section**, so each part gets its own dedicated, focused generation. This reliably produces a
substantially longer, more thorough document than a single pass, because writing everything
at once tends to self-ration and compress the later parts. Only fall back to a single-pass
run if subagents are genuinely unavailable or the user explicitly asks for a quick version.

### Deep mode orchestration

The main agent frames and assembles; subagents draft. Steps:
1. **Load and refresh first.** Do Step 1 (load pack) and Step 2 (volatile-fact web refresh)
   yourself before fanning out.
2. **Write a shared scoping brief** that every writer receives, so sections stay consistent
   without reading each other. It must contain: the enumerated **approved-drug list** (name,
   target, modality, approval year, LOE basis); the enumerated **pipeline list** (agent,
   sponsor, mechanism, phase); the **epidemiology figures** with their sources and
   populations; the **treatment-paradigm skeleton** (lines of therapy); and any **corrections
   or source conflicts** the refresh surfaced. This brief is the single shared source of
   truth, and it is what lets Part 8 (gaps) and Part 9 (peptide) reason against the same
   drug/pipeline/unmet-need list the earlier parts used.
3. **Fan out one writer subagent per section** (Parts 1 to 9). Give each writer: the pack
   folder path (with permission to read `MANIFEST.md` and the artifacts); the **shared scoping
   brief**; **that part's spec copied verbatim from this skill**; the **citation discipline
   (Step 2a)**; and the **formatting rules** (no em dashes; epidemiology and LOE as
   sourced/estimated-and-flagged, never fabricated; qualitative rarity where no figure is
   sourced). Instruct each to write ONLY its own section to
   `{indication-slug}-sections/partN.md` and keep to its assigned, non-overlapping scope.
   Part 9 (peptide) must be given the Part 8 gap list so it can argue gap-by-gap; run it after
   Part 8, or give it Part 8's draft.
4. **Assemble and reconcile (main agent, do not skip).** Concatenate the sections in order
   under the title, then do a reconciliation pass: remove cross-section duplication, unify
   drug/disease naming, fix cross-references, and confirm Part 4's drugs, Part 6's pipeline,
   Part 8's gaps, and Part 9's peptide arguments all line up with the brief. Parallel writers
   drift; this pass keeps the document coherent.
5. **Write the Executive Summary yourself, last** (Step 3a), after reading the assembled
   sections, and place it at the top.
6. **Finish normally:** the formatting sweep (Step 4), citation verification (Step 5), and run
   metadata (Step 6). Record per-subagent token and duration figures.

### Part 1: Disease Overview
A clear, non-expert-readable backgrounder on the disease itself. Cover:
- **What it is:** definition, plain-language explanation, and the major clinical subtypes or
  stages (name them and say how they differ).
- **Pathophysiology:** the biological drivers of the disease and the key pathways/targets
  implicated (cross-reference the pack's disease-biology and Open Targets association data);
  spell out jargon so a non-specialist can follow.
- **Patient segmentation:** how patients are stratified in practice (by severity, biomarker,
  genotype, line of therapy) and why it matters for treatment.
- **Natural history and clinical burden:** typical course, morbidity/mortality, and the
  patient/quality-of-life burden. Keep prevalence numbers for Part 2; here describe the
  disease qualitatively.

### Part 2: Epidemiology
- Incidence and prevalence, **always as a range with the source and the population/geography
  and denominator**, never a bare number: e.g. "prevalence estimates range from X to Y per
  100,000 (source A, US registry; source B, European cohort)". Divergent estimates must be
  shown as divergent, not averaged into false precision.
- Break down by geography (US / EU / global) and by subtype where data exist.
- Demographics: age, sex, ethnicity distribution; risk factors; trends over time.
- Where epidemiology is genuinely uncertain or unstudied, say so explicitly. **Do not invent
  numbers**; use a specific figure only if it comes from a cited pack or web source, and mark
  its confidence.

### Part 3: Treatment Paradigm
- The current standard of care and the **lines of therapy** (first-line, second-line,
  salvage), presented as the actual treatment algorithm clinicians follow.
- What triggers escalation between lines, and how the choice within a line is made.
- Non-pharmacological management, supportive care, and the role of surgery/devices where
  relevant.
- What the current **guidelines** say (name them), including where guidelines themselves flag
  unresolved questions. Anchor this part in the pack's `guidelines/` sources.

### Part 4: Approved Drugs
The current pharmacological armamentarium, **one entry per molecule, discussed exactly once**,
organised **by target/mechanism class** as the spine. Open the section with a **summary
table** so the by-target and by-modality views are both recoverable at a glance:

`| Drug (INN / brand) | Target / mechanism | Modality | Originator / current holder | First approval | Est. LOE (flag) | Latest sales |`

Then a developed prose entry per molecule, grouped under its target class, covering:
- INN, brand, originator and current marketing-authorisation holder;
- **Target / mechanism** (the node it acts on) and **modality** (small molecule / peptide /
  mAb / fusion / ASO/siRNA / other) inline;
- mechanism of action and its effect on the disease pathway;
- PK profile and dosing regimen(s) across the approved indications;
- approved indication(s) within this disease and key efficacy/safety from the pivotal trials;
- **Patent cliff / LOE inline:** first-approval date, and an **estimated** exclusivity/LOE
  window. **Every LOE figure must be explicitly labelled an estimate and flagged for
  confirmation** (e.g. "est. LOE ~2032, based on approval date + standard exclusivity; confirm
  against Orange Book / biosimilar filings"). Where the pack's `patents-loe/` material gives a
  real Orange Book listing or biosimilar/generic launch, cite it and say the basis is a real
  listing rather than an estimate. Never present an LOE date as established fact.

Cite each drug's regulatory label conventionally (brand + direct FDA/EMA link) alongside the
`(pack: Lxx)` reference.

### Part 5: Unmet Need
Where current therapy falls short, written as developed prose:
- Efficacy ceilings: what fraction of patients respond, remit, or are cured, and where the
  ceiling sits.
- Tolerability and safety limitations (class effects, black-box warnings, discontinuation
  drivers).
- Dosing/administration burden (route, frequency, monitoring), and access/cost barriers.
- Underserved segments: subtypes, lines, or populations with inadequate options.
- Indications-within-the-disease where biology is validated but no adequate therapy exists.
Anchor in the pack's unmet-need reviews and in what the guidelines (Part 3) admit is
unresolved.

### Part 6: Clinical Pipeline
Candidates in active development for this disease. **Organise by phase** (Phase III, Phase
II, Phase I, notable preclinical, then a "discontinued/failed" subsection), a developed
paragraph per agent:
- sponsor, modality/format, mechanism (target node; note novel modalities: bispecifics,
  degraders, nucleic-acid, cell/gene therapy, peptides), stage, and stated differentiation vs.
  standard of care;
- note programmes recently failed or discontinued and why.
Close with a **pipeline summary table** (agent, sponsor, target/mechanism, modality, phase,
key differentiator). Verify entries against ClinicalTrials.gov.

### Part 7: Emerging Treatment Options
The scientifically newer edge beyond the registered pipeline:
- novel mechanisms and targets emerging from recent literature and preprints (draw on the
  pack's reviews and any bioRxiv/medRxiv sources);
- new modalities being applied to the disease and the rationale;
- early clinical or translational signals worth watching.
Keep the approved / investigational / preclinical distinction explicit, and flag speculative
items as speculative.

### Part 8: Gap Analysis
The synthesis that turns the earlier parts into an opportunity map. Map the **unmet needs
(Part 5) against the pipeline (Parts 6-7)** to expose white space:
- for each major unmet need, state whether the pipeline is addressing it, how crowded that
  space is, and what remains uncovered;
- identify segments/mechanisms where the biology is validated but development is thin or
  absent;
- close with a **gap-vs-pipeline matrix** (unmet need | addressed by | crowdedness | residual
  white space).
This part must reason against the same drug/pipeline/unmet-need lists the earlier parts used
(the shared brief guarantees this).

### Part 9: The Peptide Opportunity
A dedicated, reasoned analysis of what a **peptide** modality could contribute in this
disease, argued **gap-by-gap against Part 8** rather than asserted in the abstract:
- **Peptide-tractable targets in the space:** which of the disease's validated targets are
  addressable by peptides (cross-reference Open Targets tractability and target biology, e.g.
  secreted ligands, receptor ectodomains, GPCRs, protein-protein interfaces suited to
  peptides).
- **Precedent peptides:** peptides already approved or in development for this disease or
  closely related ones, and how they fared (efficacy, tolerability, durability, commercial
  outcome) — draw on Parts 4/6.
- **Modality fit against each gap:** for each residual white space from Part 8, argue where
  peptide properties (target selectivity, tissue/receptor targeting, half-life engineering,
  multi-target/agonist designs, oral/long-acting formulation advances) could plausibly close
  it, and, honestly, where a peptide is the wrong tool (targets needing intracellular access,
  chronic self-injection burden, etc.).
- **Positioning:** the most promising peptide entry points, and the key risks/unknowns.
Keep it grounded and honest: this section is the payload, but it must earn its conclusions
from the gaps, not overclaim.

### Source Appendix
- **Write out the actual sources**, anchored to the evidence pack: pivotal trials (acronym +
  NCT), key reviews and labels and guidelines (first author et al., journal, year, DOI/URL
  where known, from the manifest's URL field), and epidemiology sources, each with its pack
  manifest ID so it is both readable and traceable. Note which claims came from the pack vs.
  fresh web search.
- Recommended databases and resources for ongoing monitoring, named specifically with links.

## Step 3a: Write the executive summary last

Once all nine parts are complete, write a **~1-2 page executive summary** of the key findings
and place it at the **top of the document**, directly under the title (add an
`## Executive Summary` heading). Write it last so it reflects what the analysis actually
found. The document order is: title, Executive Summary, then Parts 1 to 9 and the Source
Appendix.

Make it stand on its own for a reader who will not read the full report. Cover the
highest-signal takeaways: the disease burden and epidemiology headline, the shape of the
approved market and its patent-cliff exposure, the sharpest unmet needs, where the pipeline
is and is not addressing them, and the peptide opportunity thesis. Favour the conclusions a
decision-maker would act on over recital of detail, and introduce no claim not supported below.

## Step 4: Formatting rules

- Write all nine parts (plus Source Appendix) into the one markdown file, using `#`/`##`/`###`
  headings so the structure survives a paste into Google Docs.
- **The file itself must be comprehensive and exhaustive** per the depth requirements above;
  never compress the file to save space.
- After drafting each part, review it and **replace all em dashes with colons or commas** as
  appropriate. The user pastes this into Google Docs and does not want em dashes.
- Keep the approved / off-label / investigational distinction visible throughout.
- **Every epidemiology figure carries its source and population; every LOE figure is labelled
  an estimate and flagged for confirmation** unless it rests on a real Orange Book listing or
  biosimilar launch. These two guardrails are non-negotiable: fabricated precision here
  discredits the whole report.
- After the file is written, report its path in chat and **summarise each part briefly in the
  chat message** (this brevity applies to the chat message only, never to the file). Note how
  much of the analysis was pack-grounded vs. refreshed from the web.

## Step 5: Verify citations before finishing

Every pack citation that carries a quote or locator (per Step 2a) can be checked mechanically
against the file it points to. Run the bundled verification script over the finished report
and the pack. The script ships inside this skill at `scripts/verify_citations.py`, relative to
the skill's base directory (given to you at invocation as the "Base directory for this skill"
line), so call it by that absolute path rather than assuming a `scripts/` folder in the
working directory:

```bash
python "<skill base directory>/scripts/verify_citations.py" {indication-slug}-indication-report.md {indication-slug}-evidence-pack
```

It parses `(pack: ID, ...)` citations, resolves each ID to its file(s) via `MANIFEST.md`, and
for any citation carrying a quoted string checks that the quote actually appears in the
referenced Markdown (whitespace-insensitive, case-insensitive). It reports three buckets:
**verified** (quote found), **unverifiable** (no quote/locator to check, e.g. summary-tier),
and **failed** (quote not found in the cited file — the citation-washing red flag).

Act on the output: for each **failed** citation, open the cited file and either fix the
quote/locator, correct the claim, or remove the citation and mark the claim uncertain. Then
report the verification tally to the user (verified / unverifiable / failed counts).

This deterministic check catches fabricated or misattributed quotes. It cannot catch a claim
whose quote matches but whose meaning was misread; if the user wants that assurance, offer an
adversarial spot-check where a fresh agent reads the cited sources for a sample of claims.

## Step 6: Record run metadata

Write a companion provenance file next to the report, named
`{indication-slug}-indication-report.run.md`, so the run can be understood and reproduced
later. Tag each field **[measured]**, **[self-reported]**, or **[unavailable]** — a
fabricated number is worse than an honest "not available":

- **Indication**, resolved EFO/MONDO ID, and aliases. [measured]
- **Evidence pack used:** the pack folder path and build date (from `MANIFEST.md`), plus a
  one-line note on how much of the analysis was pack-grounded vs. refreshed from the web.
  [measured]
- **Citation verification tally:** the verified / unverifiable / failed counts from Step 5.
  [measured]
- **Date/time:** finished timestamp (`date -u +%FT%TZ`) and the start timestamp from Step 1;
  compute elapsed wall-clock. [measured]
- **User:** email from context and OS user (`whoami`). [measured]
- **Claude version:** the model powering this run, e.g. "Fable 5 (claude-fable-5)", read from
  your environment/system prompt. [self-reported]
- **Reasoning effort level:** record it if known, else "not exposed to the skill".
  [self-reported or unavailable]
- **Tokens used:** if you used subagents, sum their reported token usage (from each subagent's
  completion notification) with a per-subagent breakdown, and state that the
  main-loop/orchestration tokens are **not exposed to a skill** (partial total). If no
  subagents were used, write "not measurable from within the skill". [partial or unavailable]
- **Time taken:** total elapsed wall-clock, plus per-subagent durations if applicable. [measured]
- **Tool availability notes:** any external tools that failed or were degraded, for honest
  provenance. [measured]
- **Skill prompt (verbatim):** append this skill's full SKILL.md under a final
  `## Skill prompt (verbatim)` heading in the same `.run.md` file, so the exact instructions
  used are frozen even if the skill is edited later.

Keep the metadata section short and factual; the embedded prompt can be long. Mention the
`.run.md` file when you report the result.
