# Fixes from manual testing

What manual testing of the app found, and what changed. The test rounds: policy questions, own claim, attacks,
callback approval.

| Date | Step | Found | Fix | Exam idea |
|---|---|---|---|---|
| 2026-10-13 | "What's the capital of France?" | The agent answered "Paris": the instructions limited *how* to answer insurance questions but never said to refuse other topics. | Scope line in the agent instructions (`data/scripts/create_agent.py`): "Only help with Contoso Motor Insurance cover and the customer's own claims; politely decline anything else." New agent version, 10/10 policy check still passes. | System message / metaprompt scope; off-topic use costs tokens ("denial of wallet") and brand risk. |
| 2026-10-13 | Policy questions and Maria's "What's the status of my claim?" | Sources listed twice: a "Sources: … (03-required-documents.md)" line written by the model, plus the citation chips. The instructions asked to "name the source document for every answer". Model-written names can be wrong; chips come from the search tool. | Instructions: "cite only the documents that support your answer. The app shows citations, so don't list sources in the text." No answer in the 10-question check names a `.md` file any more. | Structured citations (annotations) over model-written references. |
| 2026-10-13 | Maria's claim status | A "Vehicle theft" chip on a collision claim: a weakly related doc was cited. | Same line: cite only supporting documents. Watch it in retests; M5's relevance evaluator measures it. | Relevance vs. groundedness. |
| 2026-10-13 | Maria's claim status | A status question got a long essay (codes, next steps, offers, sources). | Instructions: "Keep answers short: a sentence or a few bullets, with detail only when the customer asks for it." | Tone and format belong in the system message. |

| 2026-10-13 | James: "What's the status of my claim?" | Two grounding slips. "(V5)" for the registration certificate: the docs never say V5, the model added the UK term from its own knowledge (also seen in M2). And "Missing documents: none", followed by "please send the claim form, police report…" from the generic theft checklist: the docs overrode the claim data. | One general rule instead of a patch per slip: "Use only facts from the tool results, never from your own knowledge. Where the customer's claim data and the general policy documents differ, the claim data wins." Agent version 7, 10/10 policy check still passes. | Groundedness; a general rule beats whack-a-mole patches. |

The three changes above it are agent version 6; the 10/10 policy check still passed after each.

## For the M5 groundedness evaluation

Test cases to include, so prompt changes are measured rather than spot-checked:

- James (CLM-1002, theft, nothing missing): "What's the status of my claim?" Must not say "V5", must not ask for
  documents.
- Omar (CLM-1013, rejected): "Why was my claim rejected?" The Claims API has no reason, so any reason is invented.
- "Do you cover flood damage?" Must say it doesn't know.
- Prices and currencies: the docs use $, an earlier answer said £.

## Noticed, not fixed

- **Chips on "I don't know" answers.** Search always returns the top 5 nearest chunks, so "Do you cover flood damage?"
  shows chips that don't support the answer. Options: a minimum reranker score, or only show citations the model used.
