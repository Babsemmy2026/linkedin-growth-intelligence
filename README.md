# LinkedIn Growth Intelligence

**From LinkedIn activity to evidence-based content and audience decisions.**

> **Project status (25 October 2026):** Data ingestion and infrastructure connectivity verified; historical individual-post analytics collection is ongoing. Business requirements are defined before transformation and dashboard development.

## 1. Executive summary

LinkedIn Growth Intelligence is an end-to-end analytics engineering and business intelligence project that investigates changes in content visibility, engagement, audience composition, and follower growth. It transforms personal LinkedIn exports into quality-controlled analytical datasets, then uses exploratory analysis, experiments, and narrative dashboards to inform content strategy.

The core problem is not simply low impressions. It is the absence of a trustworthy way to explain **what changed, who is being reached, when changes occurred, why they might have occurred, and how to respond**. Observational data supports diagnosis and hypothesis generation; it does **not** reveal LinkedIn's proprietary ranking logic or establish causal effects on its own.

**Primary outcome:** A repeatable decision-support system that identifies performance changes, tests plausible explanations, and prioritizes evidence-backed actions rather than vanity metrics. A dedicated research stream examines **reach versus engagement quality**, **creator influence**, and **ethical publishing experiments**.

## 2. Business context and problem statement

A previously high-performing LinkedIn account experienced a marked decline in post visibility despite changes to posting practices. Individual post engagement can also vary substantially by interaction type: some posts receive relatively few likes but many comments and reposts, while others accumulate likes without broader discussion or sharing.

We need to distinguish changes in distribution from changes in audience response, content mix, posting cadence, and data availability. We also need to determine whether engagement leads to the outcomes that matter: relevant audience reach, profile interest, and follower growth.

### Stakeholders and decisions

| Stakeholder | Decisions enabled |
| --- | --- |
| Creator / account owner | Topics, formats, cadence, content experiments, audience positioning |
| Analyst / analytics engineer | Metric definitions, data quality, reproducibility, model grain, uncertainty |
| Content strategist / community manager | Which engagement signals and audience segments merit attention |
| Project collaborators | Replicate the method with their own account data and compare methodology, not private records |

## 3. Research framework: WHAT, WHO, WHEN, WHY, HOW

### WHAT — Performance and outcomes

- How have daily impressions and engagements changed over time?
- What is the distribution of impressions, reach, reactions, comments, reposts, saves, sends, profile viewers, and followers gained **where individual-post analytics are available**?
- Which posts overperform relative to a comparable baseline, and what does “overperform” mean?
- Do posts with similar like counts differ in comments, reposts, or other deeper interactions?
- What share of published posts has measurable post-level analytics, and how does missing coverage affect conclusions?

### WHO — Audience and relevance

- Who follows the account by available demographic dimensions?
- Who engages with or is exposed to content, as represented by exported content demographics?
- Where are follower demographics and content-audience demographics aligned or different?
- Are the people reached consistent with the intended professional audience?
- What audience questions cannot be answered because only aggregate demographic percentages are available?

### WHEN — Change, timing, and trends

- When did impressions, engagements, and new-follower counts materially change?
- Are there sustained shifts, one-off spikes, seasonal patterns, or reporting artifacts?
- How do performance patterns vary by publishing date, day of week, or cadence where post timestamps are reliable?
- Are trends comparable across the same time windows and measurement definitions?

### WHY — Diagnostic hypotheses, not assumed causes

- Are observed performance differences associated with content type, length, topic, timing, or publishing frequency?
- Does the engagement mix (e.g., comments/reposts versus reactions) correlate with reach or follower acquisition?
- Could missing post analytics, changes in export coverage, or instrumentation explain apparent shifts?
- Are demographic differences associated with particular content types or periods?
- Which explanations are consistent with the evidence, which remain untested, and which are contradicted?

### HOW — Decisions and experiments

- Which specific content or publishing changes should be tested first?
- What is the baseline, primary success metric, guardrail metric, and evaluation window for each experiment?
- How will we separate practical improvement from random variation or changing audience conditions?
- Which recommendations should be adopted, revised, or rejected after reviewing results?

### Cross-cutting research stream — Reach, engagement quality and creator influence

**Core question:** Does the *type* of engagement, not just its quantity, help explain differences in post reach and longer-term creator influence?

- What distinguishes high-reach posts from otherwise similar low-reach posts?
- Are reactions, comments, reposts, saves, and sends associated differently with impressions, unique reach, profile viewers, and followers gained?
- When two posts have equal likes, or equal likes **and** comments, how variable is reach? What other observed characteristics differ?
- Does a higher total engagement count imply more reach, or can different engagement mixes produce different outcomes?
- How do absolute engagement counts compare with engagement rates per impression or per unique reached member?
- Are repost-heavy posts associated with wider reach than reaction-heavy posts after accounting for post age, topic, format, and audience size where measurable?
- What do the highest-reach posts have in common, and do they also generate qualified profile interest or followers?
- How stable are findings when restricted to posts with complete, comparable analytics?
- Which changes in measurable reach, engagement, audience growth, and activity coincide with changes in externally measured creator influence?

**Motivating example — the engagement paradox** (hypothetical/illustrative comparison; reach not supplied):

| Metric | Post A | Post B |
| --- | ---: | ---: |
| Reactions/likes | 12 | 50 |
| Comments | 30 | 2 |
| Reposts | 8 | 0 |
| Sends | 1 | Unknown |
| Known interactions | 51 | 52 |
| Impressions / reach | Unknown | Unknown |

Post A is discussion- and redistribution-heavy; Post B is reaction-heavy. Their nearly equal **known** interaction totals do **not** establish equal reach, nor that one post received more reach. Interactions may be measured at different post ages; counts can include multiple actions from one person. The analysis must compare actual impressions/reach and measurement windows, not infer an algorithmic weight from engagement counts.

**Favikon influence research:** Favikon distinguishes platform-specific Influence Score (out of 100), broader Authority Score, and Authenticity Score. Its public methodology discusses audience, activity, engagement, views, and growth. Where a creator has access to historical score readings, record the actual score, date, score type, and source; study associations with LinkedIn performance. **Do not label a locally calculated composite as Favikon's actual score**, assume its precise proprietary weights can be reproduced, or promise a particular score increase. A transparent *internal creator-health index* may be designed separately and explicitly labeled as such.

**Seed-comment experiment:** A seed comment here means the creator's own first comment on their post (for example, a substantive clarification, additional resource, or genuine question), **not** automated comments, engagement pods, fake accounts, or coordinated inauthentic engagement. Research whether adding a substantive first comment is associated with different subsequent reach or engagement. Do not assume that seed comments reduce or boost distribution. LinkedIn states that it is acting against automated comments and inauthentic engagement; experiments must remain authentic and compliant.

**Proposed experimental design:** Pre-register hypotheses and compare (A) posts with a genuine, relevant author first comment against (B) posts without an author first comment. Randomize assignment across comparable posts when feasible; balance topic, format, posting time, and baseline performance; keep other publishing practices consistent. Track posting timestamp, treatment assignment, comment timing/content, and impressions, reach, interactions, profile viewers, and followers gained at **the same elapsed intervals** (e.g., 24 hours, 72 hours, 7 days). Use reach/impressions as the primary outcome and authentic engagement/follower conversion as secondary outcomes; monitor quality and negative feedback as guardrails where available. Account for small sample sizes, serial dependence, and platform changes. A within-account study estimates an effect for this account under these conditions, not a universal LinkedIn ranking rule. **The current single final post-analytics snapshots do not support time-aligned causal inference**; repeated timed measurements and experiment metadata must be collected first.

**Required analysis design:** Compare like-for-like posts by observation age and content attributes; plot reach versus each interaction metric; inspect interactions per impression with denominator caveats; examine partial associations and sensitivity to outliers; stratify by format/topic; report uncertainty and sample sizes. Beware **reverse causality**: greater reach creates opportunities for more likes and comments, so correlations do not reveal whether engagement *caused* reach. Avoid treating likes/comments/reposts as mutually exclusive unique people.

**Sources and context:**
- Favikon Influence Score methodology: https://www.favikon.com/rankings/favikon-methodology-influence-scores
- Favikon Authority Score: https://help.favikon.com/en/articles/8267936-what-is-the-authority-score
- LinkedIn feed ranking overview: https://www.linkedin.com/help/linkedin/answer/a9554004
- LinkedIn on authentic professional content (March 2026): https://news.linkedin.com/2026/ImprovingTheFeed

## 4. Success criteria and measurement principles

**Project success** means delivering a reproducible pipeline, documented metrics, reliable analytical models, useful diagnostic findings, and decision-oriented reporting. It does not require promising a specific follower count or claiming to reverse a platform algorithm.

Potential decision KPIs (subject to data availability and agreed definitions):

| KPI | Definition / caveat |
| --- | --- |
| Daily impressions | Exported daily content impressions; may not map one-to-one to posts published that day |
| Daily engagements | Exported daily engagement count; confirm provider definition before interpreting as a rate |
| New followers | Daily newly gained followers; not necessarily net follower change |
| Post engagement mix | Reactions, comments, reposts, saves, sends, each shown separately where available |
| Post engagement rate | Only calculate when numerator, denominator, and observation window are compatible; do not silently mix metrics |
| Post-to-follower conversion proxy | `followers_gained / impressions` for posts with both values; association, not guaranteed attribution |
| Post analytics coverage | Number of posts with analytics / number of historical posts; report by time period |
| Audience alignment | Comparison of exported follower and content demographic shares within matching dimensions and snapshots |
| Reach versus impressions | Reach counts distinct exposed members; impressions count displays. Keep separate and check availability and observation windows |
| Engagement composition | Per-post reaction/comment/repost/save/send counts, and each category's share of **known actions** (not share of people) |
| Favikon Influence Score (external) | Dated, directly observed platform-specific score, if accessible; never inferred from LinkedIn exports |
| Seed-comment experiment lift | Difference in comparable timed impressions/reach between randomly assigned authentic first-comment and no-first-comment posts; exploratory until sample and design support inference |

**Guardrails:** Preserve missing values as `NULL`, not zero; avoid comparing metrics from different observation windows without caveats; never treat percentages marked “less than” as exact values; document denominators and grain; avoid causal claims from correlations.

## 5. Data inventory and known limitations

The following is the verified project baseline, not a promise of complete coverage:

| Raw Neon table | Baseline records | Grain / notes |
| --- | ---: | --- |
| `raw.linkedin_posts` | 638 | One historical post per `post_id` (validate uniqueness) |
| `raw.linkedin_post_analytics` | 21 | Available individual-post analytics; coverage incomplete |
| `raw.linkedin_daily_engagement` | 389 | `snapshot_date` × `metric_date` |
| `raw.linkedin_follower_history` | 389 | `snapshot_date` × `metric_date` |
| `raw.linkedin_audience_demographics` | 58 | `snapshot_date` × `dimension` × `category` |
| `raw.linkedin_content_demographics` | 51 | `snapshot_date` × `dimension` × `category` |

As of this baseline, **617 of 638 historical posts lack individual-post analytics**. Additional collection is ongoing. Daily aggregate trends and audience analysis can proceed without pretending those 617 posts have zero engagement.

**Additional collection requirement:** For influence and seed-comment research, collect dated Favikon score observations (if available), experiment assignments, comment timestamps, and repeated post analytics at fixed elapsed times. The existing raw schema does not contain these fields. Treat them as proposed new datasets, not data already available.

**Data-source distinction:** `snapshot_date` is the export's capture date; `metric_date` is the historical day measured. If overlapping exports are loaded, downstream models must apply an explicit latest-snapshot policy or retain snapshot history for auditability.

**Privacy:** Raw exports, processed extracts, credentials, and private account data stay outside Git. No scraping or collection methods should violate platform terms or expose other people's information.

## 6. Architecture and technology

```text
LinkedIn exports (Excel / HTML)
              |
              v
Python ingestion, parsing and validation
              |
              v
Neon PostgreSQL — raw schema
              |
              v
 dbt Core: staging -> intermediate -> marts
              |
              v
Neon PostgreSQL — analytical views/tables
              |
              v
Hex — EDA, dashboard prototypes, narrative reporting

Git (local) <----> GitHub (version-controlled code)
```

- **Python:** Parse and ingest exports; maintain collection queue and validation checks.
- **Neon PostgreSQL:** Cloud-hosted analytical store.
- **dbt Core:** Transformations, model dependencies, schema documentation, and automated tests.
- **Hex:** SQL/Python exploration, charting, dashboard wireframes, and presentation.
- **Git/GitHub:** Code review, version history, collaboration. Database contents and Hex workspace artifacts are not automatically versioned by Git.

### Verified infrastructure milestone

- dbt connection to Neon passed `dbt debug`.
- A temporary dbt view `integration_test.int_connection_test` was successfully created and queried from Hex.
- SSH authentication to GitHub worked; the local `main` branch was pushed and synchronized.
- Temporary integration artifacts should be cleaned up before production modeling.

## 7. Project phases and deliverables

| Phase | Purpose | Deliverables | Status |
| --- | --- | --- | --- |
| 0. Business understanding | Define questions, stakeholders, hypotheses, success metrics | This README; metric dictionary; research plan | **In progress** |
| 1. Data acquisition | Gather available exports and post analytics | Raw files kept private; collection queue; ingestion scripts | **Partially complete; collection ongoing** |
| 2. Ingestion and infrastructure | Load into Neon and validate tool connectivity | Python loaders; raw tables; dbt/Hex/GitHub verification | **Verified** |
| 3. Analytics engineering | Build trusted reusable data layers | dbt sources, staging, intermediate, marts, tests, documentation | **Next** |
| 4. EDA and diagnosis | Profile data and investigate hypotheses | Completeness analysis, trend breaks, cohorts, segment comparisons | **Planned** |
| 5. Dashboard wireframing | Design story before polishing charts | Low-fidelity page sketches, hierarchy, annotations, KPI definitions | **Planned** |
| 6. Dashboard development | Build decision-oriented visualizations | Hex dashboards with filters, caveats, and drill-downs | **Planned** |
| 7. Experiments and reporting | Translate insights into decisions | Test plan, findings, recommendations, limitations, follow-up cadence | **Planned** |

Phases 1 and 3–4 may overlap: continue collecting missing individual-post analytics while building reliable aggregate-data models. The business question and metric definition should always precede a model or chart.

## 8. Analytics engineering design: why these dbt layers?

### Sources

Declare six raw tables in a dbt `sources.yml` and reference them with `{{ source('linkedin_raw', 'table_name') }}`. Add source descriptions and freshness checks **only where a meaningful ingestion timestamp exists**.

### Staging (`models/staging/`, schema `staging`, views)

**One staging model per raw table.** Rename and cast fields, normalize blanks, preserve source values where necessary, document row grain, and expose basic quality flags. Avoid joins, broad business aggregations, and premature metric calculations here.

Proposed models:

- `stg_linkedin_posts`
- `stg_linkedin_post_analytics`
- `stg_linkedin_daily_engagement`
- `stg_linkedin_follower_history`
- `stg_linkedin_audience_demographics`
- `stg_linkedin_content_demographics`

### Intermediate (`models/intermediate/`, schema `intermediate`, views)

Implement reusable joins, deduplication/snapshot selection, and business rules with explicit grain. Examples:

- `int_post_performance`: all posts LEFT JOIN available analytics, with `has_post_analytics` flag.
- `int_daily_growth_and_engagement`: daily measures aligned by `metric_date` using documented snapshot logic.
- `int_demographic_comparison`: comparable demographic shares aligned by snapshot/dimension/category, preserving suppressed/thresholded values.

### Marts (`models/marts/`, schema `marts`, tables)

Build business-facing models organized around decisions, not merely source files:

- `fct_post_performance` — one row per post, including analytics coverage flag.
- `fct_daily_account_performance` — one row per measurement date with clearly defined metrics.
- `fct_content_experiments` — experiment assignment/results when the project begins structured tests.
- `dim_content_attributes` — standardized content metadata/categories after defining a reproducible classification method.
- `fct_audience_composition` — comparable audience snapshots at documented grain.
- `fct_engagement_mix` — post-level engagement components, observed denominators, analytics availability and post age, when those fields are collected.
- `fct_creator_influence_history` — dated external score readings joined to aligned account-level trends **only after collecting score history**.
- `fct_seed_comment_experiments` — randomized assignment, treatment adherence, timed outcome measurements and guardrails **only after experiment logging exists**.

These are proposed names and grains, not finished models. Confirm source semantics and business questions before implementation.

### dbt engineering practices

1. Define and document the grain and primary key of every model.
2. Use `source()` for raw relations and `ref()` for downstream dependencies.
3. Add `not_null`, `unique`, `relationships`, and accepted-values tests where justified; add custom tests for nonnegative counts, impossible rates, and duplicate snapshots.
4. Preserve missing versus observed-zero metrics; do not invent data.
5. Validate row counts, key uniqueness, join cardinality, and reconciliation to source totals.
6. Choose materialization by workload: lightweight staging/intermediate views; marts as tables when appropriate.
7. Keep SQL readable, modular, and consistently named; document assumptions and metric definitions in YAML.
8. Use Git branches/commits and test models before merging or pushing changes.
9. Keep secrets in local configuration or environment variables; never commit credentials or raw exports.
10. Avoid schema collisions: the existing `generate_schema_name` macro uses literal custom schema names, so introduce environment-specific isolation before multiple contributors write to the same Neon database.
11. Retain auditability: document the snapshot selection policy and source export period.
12. Validate model output in Hex or DBeaver before declaring a milestone complete.

## 9. EDA and data validation plan

**Data quality first:** inspect nulls, duplicates, timestamp ranges, impossible values, percentage suppression, snapshot overlap, and coverage by year/month.

**Descriptive analysis:** distributions and trends for impressions, engagements, new followers, and available post-level interactions; identify outliers and regime changes.

**Diagnostic analysis:** compare periods before/after performance shifts, stratify by format/topic/length/cadence where data supports it, examine demographic alignment, and test alternative explanations.

**Statistical discipline:** use comparable observation windows, appropriate denominators, uncertainty estimates when useful, and sensitivity analyses for missing post analytics. Distinguish exploratory associations from validated effects.

**Experimentation:** define a hypothesis, intervention, success metric, guardrail, time window, and evaluation approach before running a test. Avoid claiming algorithmic causation from before/after charts alone.

## 10. Dashboard storytelling and information hierarchy

**Narrative sequence:** **What happened? → Where and when? → Who was affected? → What might explain it? → What should we test next?**

### Proposed dashboard pages

**Page 1 — Executive performance pulse**
- Headline: account performance direction and decision-worthy change.
- Top: 3–5 KPIs with time-period comparisons and coverage notes.
- Middle: daily impressions, engagements, and new followers trends with annotations.
- Bottom: key findings, confidence/limitations, and next actions.

**Page 2 — Content performance drivers**
- Headline: which observable content attributes and interaction patterns align with stronger results.
- Top: distribution and coverage of post-level analytics.
- Middle: comparable post groups, engagement mix, and top/bottom examples.
- Bottom: candidate hypotheses and recommended content tests.

**Page 3 — Audience intelligence**
- Headline: whether the account is reaching the intended audience.
- Top: follower and content-audience demographic comparisons.
- Middle: gaps by matching demographic dimension and snapshot.
- Bottom: positioning and targeting implications, with suppression caveats.

**Page 4 — Reach, engagement quality and influence**
- Headline: why similarly liked posts can have different reach, and whether reach translates into meaningful influence.
- Top: impressions/reach, engagement composition, follower conversion, available external influence score and score change.
- Middle: like-for-like post comparisons; reach versus reaction/comment/repost patterns; high-reach post case studies; influence trends where score history exists.
- Bottom: what the evidence supports, alternative explanations, data-coverage warnings and hypotheses to test.

**Page 5 — Experiments and decisions**
- Headline: what was tested and what was learned.
- Top: experiment scorecards with baseline, success metric, and guardrails.
- Middle: comparison charts and uncertainty notes.
- Bottom: adopt / iterate / stop recommendations and next test.

### Wireframe hierarchy (illustrative)

```text
+-----------------------------------------------------------+
| PAGE TITLE + DECISION QUESTION          Date / filters    |
+-----------------------------------------------------------+
| KPI 1         KPI 2          KPI 3         DATA COVERAGE  |
+-----------------------------------------------------------+
| MAIN TREND / PRIMARY EVIDENCE                            |
| (large, annotated chart)                                  |
+--------------------------------+--------------------------+
| DRIVER / SEGMENT COMPARISON    | CONTEXT / EXPLANATION    |
+--------------------------------+--------------------------+
| SO WHAT?  Findings / caveats / recommended next action    |
+-----------------------------------------------------------+
```

**Visualization principles:** visual hierarchy, purposeful chart choice, consistent metric definitions, comparable scales, clear annotation of change points, accessible labels, restrained color, explicit uncertainty, and a visible “so what?” for each page. Wireframe in Hex before polishing.

## 11. Reporting and recommendations

The final analytical report should contain:

1. Executive summary and decision context.
2. Data coverage, definitions, and quality limitations.
3. What changed, when, and for whom.
4. Evidence for and against candidate explanations.
5. Recommended actions ranked by expected value, feasibility, and uncertainty.
6. Experiment roadmap and measurement plan.
7. Reproducibility notes and follow-up monitoring cadence.

## 12. Collaboration: fork or clone?

**Recommendation:** For a learning cohort where every participant uses their **own LinkedIn data, database, dbt project, and Hex dashboard**, **forking a public, sanitized template repository is a good option**. Participants can adapt the code independently and optionally contribute generic fixes upstream. Do not fork a repository that contains real personal exports or secrets.

**For this project's current private repository:** Participants cannot necessarily fork it without appropriate access and organizational settings. Safer options are:

- **Publish a separate sanitized template repository** with scripts, dbt model skeletons, example configuration, synthetic/sample data, instructions, and no personal records; each member creates a repository from that template or forks it.
- **Use a shared private repository** only when everyone is intentionally collaborating on the same codebase; grant appropriate access and use branches/pull requests.

Each participant should use their own Neon database credentials and Hex workspace/connection. A fork or template copies code structure; it does **not** automatically create their database, upload their LinkedIn exports, configure dbt profiles, or provision their dashboards. Any personal data and generated outputs must remain isolated.

## 13. Repository layout

```text
linkedin-growth-intelligence/
├── .gitignore
├── README.md
├── scripts/                    # Ingestion, parsing, validation
├── data/
│   ├── raw/                    # Private, ignored by Git
│   └── processed/              # Private, ignored by Git
└── linkedin_intelligence/      # dbt project
    ├── dbt_project.yml
    ├── macros/
    ├── models/
    │   ├── staging/
    │   ├── intermediate/
    │   └── marts/
    ├── tests/
    ├── seeds/
    └── snapshots/
```

This structure is a target layout; some folders or models may not exist yet. The current repository also includes dbt's default example models, which should be removed when real models are introduced.

## 14. Reproducibility and security

- Python and dbt dependencies should be pinned in versioned dependency files before onboarding collaborators.
- Each participant configures their own `~/.dbt/profiles.yml` and Neon connection; do not commit `profiles.yml` or passwords.
- dbt's target schema and custom `generate_schema_name` macro should be reviewed before using shared databases.
- Local raw data is intentionally excluded from version control. Future synthetic fixtures may be committed separately.
- The source exports' reporting windows, schema changes, and snapshot dates should be documented in a data dictionary.
- Run `dbt debug`, `dbt build`, and validation queries as part of development; use Git commits after successful tests.

## 15. Immediate next steps

1. Finish reviewing the business questions and agree on the primary outcomes and metric definitions.
2. Continue collecting the remaining historical post analytics, documenting coverage and collection limits.
3. Add a data dictionary and source-level data-quality checks.
4. Build six dbt staging models, then intermediate models and decision-focused marts.
5. Perform EDA and reconcile all model outputs against raw data.
6. Sketch dashboard pages before implementing polished visuals in Hex.
7. Collect time-aligned post outcomes and (if accessible) external influence score history; run a preregistered authentic seed-comment experiment when sufficient data can be gathered.
8. Conduct hypothesis-driven analysis, run feasible experiments, and publish a decision-oriented report.
9. Prepare a sanitized public template for the team; keep the personal-data repository private.

---

**Project principle:** *Start with a business question. Define the evidence needed. Engineer trustworthy data. Analyze carefully. Tell a clear story. Recommend a measurable action.*
