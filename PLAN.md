# AI-103 plan: pass the exam and build the claims assistant

Goal: pass **AI-103: Developing AI Apps and Agents on Azure** (Microsoft Certified: Azure AI Apps and Agents
Developer Associate) in about 4 weeks, and finish a portfolio project that covers most of the exam.

The project design is in [docs/architecture/claims-assistant-architecture.pdf](docs/architecture/claims-assistant-architecture.pdf)
(source in `docs/architecture/source/`, rebuild with `python build.py`).

## Exam facts

| | |
|---|---|
| Exam | AI-103, 120 minutes, proctored, pass mark 700/1000 |
| Language of the code | Python (the audience profile says "experience developing apps by using Python") |
| Open book | Microsoft Learn is available during the exam, so know *where* things are documented |
| Retake | 24 hours after a first fail |
| Renewal | yearly, free online assessment |
| Free practice | Practice Assessment on [AI Skills Navigator](https://aiskillsnavigator.microsoft.com/credentials/cert-3fb198f57997226a824aa5f52a1a22af9a4597941b2288ed39371c7a9e6bd7c9) (sign in), plus the [exam sandbox](https://go.microsoft.com/fwlink/?linkid=2226877) for the question UI |
| Study guide | [aka.ms/AI103-StudyGuide](https://aka.ms/AI103-StudyGuide), skills measured as of April 16, 2026 |
| Register with | your personal Microsoft account, not a work account |

## Skills measured, and where each is learned

| Area | Weight | Where you learn it |
|---|---|---|
| Plan and manage an Azure AI solution | 25–30% | **Project**: Foundry setup, Bicep, keyless auth, quotas, content filters, evaluations, tracing, CI |
| Generative AI and agents | 30–35% | **Project**: agent, RAG, function tools, approval flow, evaluation, observability |
| Information extraction | 10–15% | **Project**: AI Search ingestion + Content Understanding on claim forms |
| Text analysis (language + speech) | 10–15% | **Project** for structured JSON, PII, sentiment, translation. **Study only** for speech |
| Computer vision | 10–15% | **Project** for damage-photo analysis and image safety. **Study only** for image/video generation and editing |

About 80% of the exam is practised in the project. The rest (speech, image and video generation) is
short study plus one small notebook each.

## Data (option A: car insurance)

All public or generated, so the repo can be public. Details in section 3 of the architecture doc.

| Data | Source | License |
|---|---|---|
| Claim records (~1,000) | `insurance_claims.csv`, [Mendeley Data](https://data.mendeley.com/datasets/992mh7dk9y/2); a script adds `status`, `phase`, `missing_documents`, claimant id | CC BY 4.0 (credit in README) |
| Damage photos (use ~30 of 814) | [Car Parts and Car Damages](https://humansintheloop.org/resources/datasets/car-parts-and-car-damages-dataset/), Humans in the Loop | CC0 |
| Policy documents (~15) | Generated for a fictional insurer | yours |
| Claim forms (~50 PDFs + expected-field JSON) | Generated from claim rows, some as noisy "scans" | yours |

Loading scripts are Python (`data/scripts/`), because index, indexer and analyzer setup is exam material.

## Week 0 (day 1): baseline, about 2 hours

- [x] Take the free Practice Assessment once, cold and without AI help. Note the score per area.
- [x] Paste the missed questions or area scores to Claude, and get a ranked gap list (exam weight × weakness).
- [ ] Book the exam for about 4 weeks out.
- [ ] Azure: create the free account, set a budget alert at $10, create the resource group `rg-claims-assistant`.

### Baseline: 7 October 2026, 46% overall (target 80%)

Section scores are estimated from the report's bar chart, which shows no numbers.

| Priority | Area | Weight | Score | Weight × gap |
|---|---|---|---|---|
| 1 | Generative AI and agents | 30–35% | ~38% | 20 |
| 2 | Plan and manage | 25–30% | ~58% | 12 |
| 3 | Computer vision | 10–15% | ~25% | 9 |
| 4 | Information extraction | 10–15% | ~38% | 8 |
| 5 | Text analysis | 10–15% | ~63% | 5 |

Changes from this baseline: weeks 1–2 stay as planned (they cover priorities 1–2); vision gets three study
sessions in week 3 instead of one evening; text analysis gets a lighter review, except speech (below).

### Focus list from the missed questions

From the answer review of 16 of the 50 questions ([practice/2026-10-07-baseline-review.md](practice/2026-10-07-baseline-review.md)):
9 wrong out of 14 that could be graded. No miss was about Python code. Most were **choosing between two plausible
options**, so study each topic as "when X, not Y":

| Topic | Choose between | Area | Week |
|---|---|---|---|
| Foundry deployment types | Standard / Global / Data Zone × Standard / Provisioned / Batch (latency, data residency, cost, async jobs) | Plan | 1 |
| Authentication to AI services | Entra ID (preferred) and keys are both valid; know which pairs of answers count | Plan | 1 |
| Azure CLI basics | `az cognitiveservices account ...` needs `--name` and `--resource-group` | Plan | 1 |
| Grounding source | Azure AI Search for company content vs Grounding with Bing for public web | Plan / GenAI | 1 |
| Agent memory | Foundry Agent Service memory (across sessions) vs thread or session state (one conversation) | GenAI | 2 |
| Monitoring signals | Real signals (validation failure rate, retrieval eval score) vs configuration values (chunk overlap, vector dimensions) | GenAI / Plan | 2 |
| Speech customization | Custom Speech (speech to text: noise, accents, vocabulary) vs Custom Voice (text to speech) | Text | 3 |
| Voice Live audio options | Multilingual voice activity detection, echo cancellation, noise suppression: which solves which problem | Text | 3 |

Exam habit: on "choose two" questions, check that two answers are ticked before moving on.

## Week 1: plan and manage + first agent

Study (Microsoft Learn, AI-103 path): Foundry resources and projects, model choice and deployment types,
keyless auth and RBAC roles, quotas and rate limits.

Build (milestones M0–M2 in the architecture doc):
- [x] M0 Data: download the CSV and photos, generate policy docs and claim forms, write `claims.db`.
- [x] M1 Infrastructure: Foundry resource + project, `gpt-5-mini` and `text-embedding-3-small` deployments, AI Search (Basic, per session), Storage, App Insights, all in Bicep. Managed identity and RBAC only, no keys.
- [x] M2 Knowledge agent: index the policy documents into AI Search (hybrid search), create the Foundry agent with the search tool, answers cite the source document.

Claude: scaffolds the repo with you, explains each resource as it's created, quizzes you at the end of the week.

## Week 2: agents, tools, responsible AI

Study: function calling and tool schemas, conversation threads and memory, multi-agent orchestration,
approval flows, content filters and Prompt Shields, evaluators.

Build:
- [x] M3 Claims tool: mock Claims API (ASP.NET Core) + `get_claim_status` function tool. The claim id comes from the signed-in session, never from the model. Leak tests.
- [x] M4 Approval flow: `request_callback` tool that waits for a human approval before it runs.
- [ ] M5 Guardrails and evaluation: content filter + Prompt Shields, a 40-question test set, Foundry evaluators (groundedness, relevance) run in Python, CI fails on a drop.

Claude: reviews the code, shows the Python equivalent of each .NET piece, writes the week's cheat sheet.

## Week 3: information extraction, vision, text

Study: Content Understanding analyzers (single-task and pro mode), OCR and layout, AI Search skills,
multimodal models, image safety. Light review only for Translator, Language features and speech (strongest area).

Build:
- [ ] M6 Document intake: Content Understanding analyzer turns an uploaded claim form (PDF) into fields + markdown for the agent.
- [ ] M7 Damage photo: multimodal model describes the photo and answers questions grounded in it; image content filter; test a photo with injected text ("ignore your instructions").
- [ ] M8 Handler summary: structured JSON output (summary, sentiment, urgency, PII masked) for each conversation.

Vision (weakest area, about 25% at baseline), three study sessions with a Python notebook each:
- [ ] Image generation and editing: text-to-image, reference images, inpainting and mask edits, generation controls.
- [ ] Video: generation and editing, video analysis with Content Understanding.
- [ ] Multimodal understanding and safety: captions and alt text, visual question answering, object and region detection, unsafe-image filters, prompt injection hidden in images.

Speech (3 of the 9 misses), two sessions: Custom Speech vs Custom Voice, Voice Live audio options, speech to text, text to speech, speech translation.

## Week 4: exam readiness

- [ ] M9 Tracing and costs: OpenTelemetry traces in App Insights, token and latency dashboard. README with the diagram and test results.
- [ ] Retake the Practice Assessment. Target: consistently above 80%.
- [ ] One paid timed practice set (for example Tutorials Dojo AI-103).
- [ ] Drill the weakest area with Claude, then sit the exam.

## Cost guardrails

- Model: `gpt-5-mini`, a small model. (`gpt-4.1-mini` is Deprecated for new subscriptions; the trial has 0 quota for `gpt-5.4-mini`.)
- AI Search: **Basic**, about $75/month if left running, billed hourly. Free can't use a managed identity for the indexer, which would force keys. So `infra/up.ps1` at the start of a session and `infra/down.ps1` at the end.
- Budget alert at $10 in Cost Management.
- Delete `rg-claims-assistant` between work sessions if it holds anything billed hourly. Bicep recreates it in minutes.

## How to work with Claude

- Start each session with: the week, the milestone, and what's blocking.
- "Quiz me on <area>": exam-style scenario questions, focused on what you got wrong before.
- "Show this in Python": the Python SDK version of the .NET code you just wrote.
- "Cheat sheet for <area>": one page, at the end of each week.
