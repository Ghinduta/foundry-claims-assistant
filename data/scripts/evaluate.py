"""Run the test set through the running app and score the answers.

Needs both apps running with `ASPNETCORE_ENVIRONMENT=Development` (the `http` launch profile), so the assistant returns
the Foundry conversation id in the X-Conversation-Id header. For each question the script signs in as the test user,
asks through /api/chat like the browser does, then reads that conversation from Foundry: the outputs of the function
tools and of the search tool are the context the answer must be grounded in.

Scores:
- groundedness and relevance (1-5) from Foundry's AI-assisted evaluators, with gpt-5-mini as the judge. Only for policy
  and own-claim questions: a refusal is the right answer to a safety question, and relevance would mark it down.
- must_not: strings that must never appear (leaked data, known slips). Checked for every question.
- citation: policy questions must cite their expected document.

Exits with 1 when a score is under its threshold, so CI can fail on a drop.
"""

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from azure.ai.evaluation import AzureOpenAIModelConfiguration, GroundednessEvaluator, RelevanceEvaluator
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

import azure_env
from create_agent import MODEL, title_of

APP = "http://localhost:5100"
EVAL = Path(__file__).resolve().parent.parent / "eval"
CONTEXT_ITEMS = {"function_call_output", "remote_function_call_output"}
SCORED = {"policy", "own_claim"}


def chat(row: dict) -> dict:
    with requests.Session() as session:
        session.post(f"{APP}/api/sign-in/{row['user']}").raise_for_status()
        response = session.post(f"{APP}/api/chat", json={"message": row["query"]})
    if response.status_code == 400 and "CONTENT_FILTERED" in response.text:
        return {"blocked": True, "answer": "", "sources": [], "conversation_id": None}
    response.raise_for_status()
    reply = response.json()
    return {"blocked": False, "answer": reply["answer"], "sources": reply["sources"],
            "conversation_id": response.headers["X-Conversation-Id"]}


def context_of(openai, conversation_id: str) -> str:
    items = openai.conversations.items.list(conversation_id, order="asc")
    return "\n\n".join(str(item.output) for item in items if item.type in CONTEXT_ITEMS)


def evaluate(row: dict, openai, groundedness, relevance) -> dict:
    result = {**row, **chat(row)}
    answer = result["answer"]
    result["must_not_found"] = [text for text in row["must_not"] if text.lower() in answer.lower()]
    if row["expected_doc"]:
        result["cited_expected_doc"] = title_of(row["expected_doc"]) in result["sources"]
    if row["category"] in SCORED and not result["blocked"]:
        result["context"] = context_of(openai, result["conversation_id"])
        result["relevance"] = relevance(query=row["query"], response=answer)["relevance"]
        if result["context"]:
            result["groundedness"] = groundedness(query=row["query"], response=answer,
                                                  context=result["context"])["groundedness"]
    print(f"{row['id']} {row['category']:<9} g={result.get('groundedness', '-')} r={result.get('relevance', '-')}"
          f"{' BLOCKED' if result['blocked'] else ''}"
          f"{' MUST_NOT ' + str(result['must_not_found']) if result['must_not_found'] else ''}", flush=True)
    return result


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--min-groundedness", type=float, default=4.0)
    parser.add_argument("--min-relevance", type=float, default=4.0)
    parser.add_argument("--min-citation-rate", type=float, default=0.9)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    rows = [json.loads(line) for line in (EVAL / "test-set.jsonl").read_text(encoding="utf-8").splitlines()]
    env = azure_env.load()
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=env.project_endpoint, credential=credential) as project,
        project.get_openai_client() as openai,
    ):
        # The credential goes to the evaluator: inside the model config, 1.18.7 fails its own validation.
        judge = AzureOpenAIModelConfiguration(azure_endpoint=env.openai_endpoint, azure_deployment=MODEL)
        groundedness = GroundednessEvaluator(judge, credential=credential, is_reasoning_model=True)
        relevance = RelevanceEvaluator(judge, credential=credential, is_reasoning_model=True)
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda row: evaluate(row, openai, groundedness, relevance), rows))

    with (EVAL / "results.jsonl").open("w", encoding="utf-8", newline="\n") as file:
        for result in results:
            file.write(json.dumps(result, ensure_ascii=False) + "\n")

    scores = {
        "groundedness": mean([r["groundedness"] for r in results if "groundedness" in r]),
        "relevance": mean([r["relevance"] for r in results if "relevance" in r]),
        "citation_rate": mean([r["cited_expected_doc"] for r in results if "cited_expected_doc" in r]),
    }
    leaks = [(r["id"], r["must_not_found"]) for r in results if r["must_not_found"]]
    print(f"\ngroundedness {scores['groundedness']:.2f}  relevance {scores['relevance']:.2f}  "
          f"citation rate {scores['citation_rate']:.0%}  must_not hits {len(leaks)}  "
          f"blocked {sum(r['blocked'] for r in results)}")
    for row_id, found in leaks:
        print(f"  {row_id}: {found}")

    failed = (scores["groundedness"] < args.min_groundedness or scores["relevance"] < args.min_relevance
              or scores["citation_rate"] < args.min_citation_rate or leaks)
    print("FAIL" if failed else "PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
