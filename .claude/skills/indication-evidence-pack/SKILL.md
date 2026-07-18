---
name: indication-evidence-pack
description: >-
  Build a structured, searchable evidence pack for a single disease/indication
  and save it as an organised folder in the working directory (Phase 1 of two).
  Use when the user wants to gather the primary evidence for an indication —
  approved-drug labels, clinical guidelines, reviews, epidemiology, pivotal and
  failed trials, disease biology, and drug/target data — anchored on the Open
  Targets EFO/MONDO disease profile. This is the disease-axis sibling of
  drug-target-evidence-pack (which is organised around a molecule/pathway). The
  companion skill indication-report-from-pack later writes the report from the
  pack produced here.
---

# Indication Evidence Pack (Phase 1)

This skill gathers the primary evidence for a single disease/indication and
saves it as an organised, searchable folder in the working directory. It is
deliberately the first of two steps: this builds the pack;
`indication-report-from-pack` later writes the indication report from it.
Separating them means the pack is stable, reusable, and something both you and
the user can grep and cite later, whereas the report is a synthesis that may be
regenerated many times.

This is the disease-axis sibling of `drug-target-evidence-pack`. Where that
skill is organised around a molecule/pathway, this one is organised around a
disease: the entry point is the indication, and the anchor query is the disease
profile (Open Targets EFO disease → associated targets, known drugs,
tractability).

## Step 1: Identify the indication and resolve its identity

Get the indication from the user's request. An indication is a disease or
condition (e.g. "obesity", "IgA nephropathy", "HFpEF", "geographic atrophy").
Record useful aliases (common name, medical name, abbreviations, key subtypes)
to improve search recall.

Resolve the disease to its Open Targets EFO/MONDO ID as the very first
substantive action. Use the Open Targets `search_entities` tool to map the
disease name to its EFO ID, and note the main subtypes/child terms. Everything
downstream keys off this ID (known drugs, associated targets, tractability), and
disease-name → ID ambiguity is the most common failure point, so pin it down and
state the resolved ID and label before gathering.

If scope is ambiguous, choose sensible defaults and state them rather than
stopping: the disease as a whole (including its major clinical subtypes), global
with US/EU emphasis, and the last two years prioritised for reviews, guidelines,
and news but any date for pivotal/foundational sources.

Start the run clock. Immediately capture a start timestamp so elapsed time can be
recorded later (Step 6a): run `date -u +%FT%TZ` and keep the value.

## Step 2: Scope the approved drugs and pipeline first

Before gathering literature, do a quick pass to enumerate the approved and
late-stage agents used in this indication. This tells you which approval labels
to fetch and which drugs the reviews and trials should cover. Combine:

- Open Targets known-drugs for the disease EFO ID (`query_open_targets_graphql`);
- ChEMBL `drug_search` by indication;
- ClinicalTrials.gov `search_trials` by condition for the late-stage pipeline,
  plus a second pass with `status=[TERMINATED, WITHDRAWN, SUSPENDED]` to surface
  failed and discontinued programmes (these are invisible to an
  active-status-only search);
- a web search for the current standard of care, and a deliberate search for
  notable failures in the indication (e.g. "why did drug/trial X fail in
  {indication}", "failed Phase 3 {indication}", key negative pivotal readouts).

Keep this drug list; it drives the rest of the gathering. Capture, per drug, the
target/mechanism, modality (small molecule / peptide / mAb / other), and
originator, since these organise the report's approved-drugs section. Keep a
parallel "failures" list too: failed or discontinued agents with their
target/mechanism, the phase reached, and the stated reason (efficacy, safety,
futility, commercial), because "what already failed and why" is
decision-critical, especially for judging whether a failure was about the
target, the population, or the modality.

## Step 3: Build the pack folder

Create this structure in the current working directory:

```
{indication-slug}-evidence-pack/
  MANIFEST.md                 # the searchable index + per-artifact summaries; see below
  labels/                     # FDA/EMA approval labels for drugs used in the indication: .pdf + paired .md
  guidelines/                 # clinical practice guidelines (treatment paradigm): .pdf + .md
  reviews/                    # open-access reviews and key papers (disease biology, treatment, unmet need): .pdf + .md
  epidemiology/               # incidence/prevalence sources: papers, registry/GBD exports (.pdf+.md or .md/json)
  trials/                     # key ClinicalTrials.gov records for pipeline + pivotal trials (markdown/JSON)
  failures/                   # failed/discontinued/terminated programmes + why they failed (markdown/JSON)
  disease-biology/            # Open Targets disease profile, associated targets, pathophysiology reviews
  drugs-targets/              # Open Targets known-drugs + ChEMBL by-indication exports (markdown/JSON)
  patents-loe/                # approval dates + exclusivity/LOE source material (see Step 4b)
  abstracts-only/             # citation + abstract + link for anything not downloadable
  _run/                       # run provenance: run-metadata.md + a copy of the skill prompt
```

As soon as the folders exist, copy this skill's own prompt into the pack for
provenance: `cp "<this SKILL.md path>" {indication-slug}-evidence-pack/_run/skill-prompt.md`.
The skill's base directory is given to you at invocation (the "Base directory for
this skill" line), so the file is at `<base directory>/SKILL.md`. Recording the
exact instructions used means a run can be understood and reproduced later even
if the skill is edited afterwards.

Each downloaded PDF is stored in three tiers so the pack is both authoritative
and cheap to search (see Step 4a): the original PDF (ground truth), a paired
full-text Markdown with the same basename (e.g. `labels/semaglutide-fda.pdf` +
`labels/semaglutide-fda.md`), and a short structured summary recorded in
MANIFEST.md. Records that are already text (trials, Open Targets/ChEMBL exports)
need no PDF/MD pair.

## Step 4: Gather comprehensively (~25-40 artifacts)

Aim for a comprehensive pack of roughly 25-40 artifacts. Use the connected tools
as the primary channels, and web search/fetch to fill gaps. Because the
downstream report is disease-centric, deliberately cover all of these areas:

- **Approval labels** — one per approved agent used in the indication. FDA labels
  (DailyMed / accessdata) and EMA EPARs are public; download the PDF into
  `labels/`. This is the highest-value, most-citable content for the
  approved-drugs section, so prioritise the full set.
- **Clinical practice guidelines** — the authoritative source for the treatment
  paradigm and for what the field openly admits is unsolved. Save freely
  available society/consensus guidelines to `guidelines/`. Licensed content (e.g.
  NCCN, UpToDate) is link-only in `abstracts-only/`.
- **Reviews & key papers** — use the PubMed article tools (`search_articles`,
  `get_article_metadata`, `get_copyright_status`, `get_full_text_article`) and
  the bioRxiv/medRxiv tools. Check copyright status before downloading full text.
  Where full text is openly available, save it to `reviews/`; otherwise save the
  citation + abstract + link to `abstracts-only/`. Cover: disease
  pathophysiology, natural history, the treatment landscape, and explicit
  unmet-need reviews.
- **Epidemiology** — capture incidence/prevalence sources into `epidemiology/`,
  deliberately recording the population, geography, and denominator for each
  figure, not just the number. Prefer primary epi studies, systematic
  reviews/meta-analyses, and registry/GBD data. Epidemiology numbers vary widely
  by source, so gather enough to state a range.
- **Trials** — use the ClinicalTrials.gov tools to capture the pivotal trials
  behind the approved drugs and the notable late-stage/recently-read-out pipeline
  trials; save structured records (markdown or JSON) to `trials/`. Bucket by
  phase.
- **Failed and discontinued programmes** — deliberately capture the graveyard,
  not just the live pipeline. Pull terminated/withdrawn/suspended trials (the
  Step 2 status query) and well-known negative pivotal readouts and discontinued
  assets, and for each record the agent, target/mechanism, modality, phase
  reached, and the stated reason for failure (efficacy/futility, safety/tox,
  trial design/population, or commercial). Save to `failures/` (markdown/JSON).
  Prioritise failures that carry a lesson for the modality question (e.g. a
  target that failed as an antibody in an unselected population). Review articles
  that catalogue failures ("why ARDS trials fail" style) belong in `reviews/` but
  should be cross-noted here.
- **Disease biology** — Open Targets disease profile and top associated targets
  (for the disease-overview and peptide-opportunity sections), plus a
  pathophysiology review. Save to `disease-biology/`.
- **Drugs & targets** — save the Open Targets known-drugs export and ChEMBL
  by-indication export to `drugs-targets/`; these enumerate the molecules and
  their targets/modalities.

Rank candidates by relevance and recency before downloading, so the 25-40 slots
go to the most valuable sources. This pack feeds a nine-part report (disease
overview, epidemiology, treatment paradigm, approved drugs, unmet need, pipeline,
emerging options, gap analysis, peptide opportunity), so make sure each of those
areas has some supporting evidence. A pack that only holds the pivotal trials for
approved drugs will starve the report's epidemiology, unmet-need, and peptide
sections.

### Step 4a: Convert to Markdown and summarise (three-tier)

For each downloaded PDF (labels, guidelines, reviews, epi papers), produce the
other two tiers:

- **Full-text Markdown.** Convert the PDF to a paired `.md` alongside it. Use a
  converter such as markitdown or pymupdf4llm (try `python -m markitdown
  <file.pdf>` or a short `pymupdf4llm.to_markdown()` script; fall back to
  whatever PDF-to-text tool is available). This tier exists because PDFs are not
  greppable and are token-expensive to page through, whereas Markdown is
  searchable and cheap for Phase 2 to deep-read. Conversion is lossy for tables
  and figures (dosing tables, prevalence tables, efficacy tables routinely
  mangle). If a file's Markdown looks badly broken, keep the PDF as the
  authoritative source and note in the summary that the Markdown is unreliable,
  rather than trusting a garbled conversion.
- **Structured summary in the manifest.** Write a short summary per artifact
  capturing the facts the report needs. Deliberately extract the table-derived
  facts by hand here (prevalence/incidence with population and denominator;
  dosing per drug; key efficacy/safety numbers; approval dates) since those are
  exactly what the auto-conversion garbles. This is the triage layer: it lets
  both you and Phase 2 scan the whole pack fast and decide which full-text file
  to open.

### Step 4b: Seed the patent-cliff / LOE material (estimates, flagged)

There is no clean free API for reliable loss-of-exclusivity dates, and the report
treats LOE as estimated and flagged for confirmation, never as fact. In this
pack, gather the raw material Phase 2 needs to build those estimates, into
`patents-loe/`:

- For each approved drug, record the FDA/EMA first-approval date (from the label
  or Drugs@FDA) — this is the anchor for an exclusivity estimate.
- Where readily available, capture Orange Book patent/exclusivity listings, known
  biosimilar or generic launch dates/entries, and any analyst or news statements
  about LOE timing, with their source.
- Do not fabricate a cliff date. Save what is sourced; leave the estimate itself
  to Phase 2, which will compute a rough window and mark it "confirm". Note in
  each summary whether the LOE basis is a real listing/launch or only an
  approval-date-plus-standard-window estimate.

## Step 5: Write MANIFEST.md

The manifest is what makes the pack searchable and citable. It has two parts: an
index table for scanning, and a summaries section holding the structured extract
for each artifact (from Step 4a/4b).

Index table, one row per artifact:

```
| ID | Title | Type | Covers | Source | Date | Files | Local path | URL | Relevance |
```

- **ID** — a short stable id: `L01` labels, `G01` guidelines, `R01`
  reviews/papers, `E01` epidemiology, `T01` trials, `F01` failures/discontinued,
  `B01` disease-biology, `D01` drugs-targets, `P01` patents-loe. Phase 2 cites
  these ids.
- **Type** — label / guideline / review / paper / epidemiology / trial / failure
  / biology / drugs-targets / patents-loe.
- **Covers** — which drug(s), disease facet, or topic the artifact is about.
- **Files** — what is on disk: `pdf+md`, `md`, `json`, or `abstract-only` if only
  a pointer. Flag `pdf+md*` when the Markdown conversion was unreliable so the PDF
  is the source of truth.
- **Relevance** — one line on why it is in the pack.

Below the table, add a "## Summaries" section with one short block per ID (e.g.
`### L01 — Semaglutide FDA label`) holding the structured summary from Step
4a/4b, including the hand-extracted table facts (prevalence with population,
dosing, key efficacy/safety figures, approval dates and LOE basis). This section
is the triage layer that lets Phase 2 work from summaries and deep-read the
paired Markdown only when a specific claim needs it.

Add a short header to MANIFEST.md with the indication, resolved EFO/MONDO ID,
aliases, date the pack was built, and total counts by type. Then add a "Gaps and
not-downloaded" section listing strong candidates that could not be retrieved
(paywalled, licensed) and any evidence areas that came up thin (epidemiology and
LOE are the usual thin spots), so the picture is honest about what is actually on
disk.

## Step 6: Build the paywalled "wanted list"

High-value reviews and papers are often paywalled, and the best syntheses of a
disease (e.g. in NEJM, Lancet, Nature Reviews Disease Primers) frequently are.
Rather than let the pack quietly skew toward whatever was free to download, make
the missing items explicit so the user can acquire them manually before Phase 2.

Save a `WANTED.md` file at the top of the pack folder listing the key papers that
could not be downloaded but that would materially improve the report. For each,
give enough to find or buy it: title, authors (first author et al.), journal,
year, DOI, a direct link, and a one-line note on why it matters and which part of
the report it serves. Rank by importance. Only list genuinely high-value items,
not every paywalled hit.

### Step 6a: Record run metadata

Write `_run/run-metadata.md` so the pack carries a provenance record of how it
was built. Be scrupulous about labelling each field as measured, self-reported,
or unavailable, because some values a skill genuinely cannot measure and a
fabricated number is worse than an honest "not available":

- Indication, resolved EFO/MONDO ID, and aliases.
- Date/time: finished timestamp (`date -u +%FT%TZ`) and the start timestamp
  captured in Step 1; compute elapsed wall-clock. (measured)
- User: the user's email from context and OS user (`whoami`). (measured)
- Claude version: the model powering this run, e.g. "Fable 5 (claude-fable-5)".
  Read it from your environment/system prompt. (self-reported — a skill cannot
  measure this)
- Reasoning effort level: if the session effort (low/medium/high/…) is known to
  you, record it; otherwise write "not exposed to the skill". (self-reported or
  unavailable)
- Tokens used: if you gathered via subagents, sum their reported token usage and
  give a per-subagent breakdown. State clearly that the main-loop/orchestration
  tokens are not exposed to a skill, so the figure is a partial (subagent-only)
  total. If no subagents were used, write "not measurable from within the skill".
  (partially measured)
- Time taken: total elapsed wall-clock (measured), plus per-subagent durations if
  applicable.
- Tool availability notes: record any external tools that failed or were degraded
  during the run (e.g. ChEMBL down, Open Targets rate-limited) so the pack's
  provenance is honest.
- Skill prompt: confirm the copy at `_run/skill-prompt.md` (made in Step 3), and
  record the skill name and its base-directory path.

Keep it short and factual.

## Step 7: Report

Tell the user the pack folder path and summarise what was collected (counts by
category). Then output the paywalled "wanted list" directly in the chat (the same
content as WANTED.md), formatted so the user can act on it, so they can manually
find, buy, or retrieve those papers and drop the files into `reviews/` before
proceeding. Explain that Phase 2 will pick up any files they add. Mention that
`_run/run-metadata.md` records the run's provenance. Finally, note that the next
step is to run `indication-report-from-pack` on the same indication once they are
satisfied with the pack.

## Rules and cautions

- Respect copyright and access controls. Only download content that is openly
  available or that the copyright-status check clears. For everything else, save
  the citation and abstract and link, and mark it abstract-only in the manifest.
  Never circumvent a paywall.
- Never fabricate epidemiology or LOE numbers. These are the two areas most prone
  to invented precision. Capture figures only with their source and population;
  if a number is not sourced, do not record it as fact.
- Downloading many files is I/O and token heavy. Rank first, then fetch, so
  effort goes to the most valuable sources.
- If a pack folder already exists for this indication, offer to refresh or extend
  it rather than silently overwriting.
