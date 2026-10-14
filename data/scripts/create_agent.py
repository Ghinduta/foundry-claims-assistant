"""Create the claims assistant agent, then test its knowledge search on policy questions.

Creating or changing an agent is an admin action, so it happens here and not in the app: the app only runs the agent.
Three tools:
- Azure AI Search runs inside Foundry. It reaches the `policy-docs` index through the project's `claims-search`
  connection, signed in as the project's managed identity. No keys anywhere.
- get_claim_status is a function tool: Foundry only returns the call, and src/ClaimsAssistant runs it. It has no
  parameters, because the app takes the claimant from the signed-in session, never from the model.
- request_callback is a function tool with a human in the loop: the app only queues the request, and a claims handler
  approves or rejects it before anyone calls.
"""

import sys
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    AISearchIndexResource,
    AzureAISearchQueryType,
    AzureAISearchTool,
    AzureAISearchToolResource,
    FunctionTool,
    PromptAgentDefinition,
)
from azure.identity import DefaultAzureCredential

import azure_env

AGENT = "claims-assistant"
MODEL = "gpt-5-mini"
INDEX = "policy-docs"
DOCS = Path(__file__).resolve().parent.parent / "policy-docs"

INSTRUCTIONS = """You are the customer assistant of Contoso Motor Insurance.
Only help with Contoso Motor Insurance cover and the customer's own claims; politely decline anything else.
Answer general questions about cover, claims and documents using only the results of the knowledge search tool,
and cite only the documents that support your answer. The app shows citations, so don't list sources in the text.
Keep answers short: a sentence or a few bullets, with detail only when the customer asks for it.
Use only facts from the tool results, never from your own knowledge. Where the customer's claim data and the general
policy documents differ, the claim data wins.
For questions about the customer's own claim, call get_claim_status. It returns the claims of the signed-in customer
only. Never discuss any other claim or person: if asked, say you can only see the signed-in customer's own claims.
Explain its codes in plain words (for example awaiting_documents means we're waiting for documents from you,
claim_form is the signed claim form) and use the knowledge search tool for what the customer should do next.
When the customer asks to be called back, or a question needs a person (a dispute, a complaint, an urgent problem),
call request_callback with a short reason and their preferred time. A claims handler must approve every callback, so
tell the customer the request is waiting for approval; never promise that someone will call.
If no tool answers the question, say you don't know and offer a callback."""

CLAIM_STATUS = FunctionTool(
    name="get_claim_status",
    description="Gets the status, phase and missing documents of the signed-in customer's claims.",
    parameters={"type": "object", "properties": {}, "required": [], "additionalProperties": False},
    strict=True,
)

REQUEST_CALLBACK = FunctionTool(
    name="request_callback",
    description="Asks for a claims handler to call the signed-in customer back. Needs a handler's approval.",
    parameters={
        "type": "object",
        "properties": {
            "reason": {"type": "string", "description": "Why the customer needs a call, in one sentence."},
            "preferred_time": {"type": "string", "description": "When the customer wants the call, or 'any time'."},
        },
        "required": ["reason", "preferred_time"],
        "additionalProperties": False,
    },
    strict=True,
)

# (question, file that should be cited). General wording: "my claim" questions go to get_claim_status,
# which only the app can run.
QUESTIONS = [
    ("Which documents do I need if my car was stolen?", "09-vehicle-theft.md"),
    ("How does the deductible work?", "04-deductible.md"),
    ("My windscreen has a crack. Is it covered and do I pay the deductible?", "11-glass-and-windscreen.md"),
    ("Do I get a rental car while my car is being repaired?", "12-rental-car.md"),
    ("Someone hit my car while it was parked and drove off. What do I do?", "10-parked-car-and-hit-and-run.md"),
    ("Can a rejected claim be appealed?", "14-rejected-claims-and-appeals.md"),
    ("When is a car treated as a total loss?", "13-total-loss.md"),
    ("Can I choose my own garage for the repair?", "08-approved-garages.md"),
    ("How long does a claim take to settle?", "07-claim-steps-and-timelines.md"),
    ("What do you do with my personal data?", "15-privacy-and-your-data.md"),
]


def create_agent(project: AIProjectClient, env: azure_env.AzureEnv) -> str:
    connection = project.connections.get(env.search_connection_name)
    search = AzureAISearchTool(azure_ai_search=AzureAISearchToolResource(indexes=[AISearchIndexResource(
        project_connection_id=connection.id,
        index_name=INDEX,
        query_type=AzureAISearchQueryType.VECTOR_SEMANTIC_HYBRID,  # keyword + vector, then the semantic ranker
        top_k=5,
    )]))
    # Each call adds a new version of the same agent; conversations name the agent, not the version.
    agent = project.agents.create_version(
        agent_name=AGENT,
        definition=PromptAgentDefinition(model=MODEL, instructions=INSTRUCTIONS, tools=[search, CLAIM_STATUS, REQUEST_CALLBACK]),
    )
    print(f"Agent {agent.name} version {agent.version}")
    return agent.name


def title_of(file_name: str) -> str:
    # Citations carry the document's # heading (the index's title field), not the file name.
    return (DOCS / file_name).read_text(encoding="utf-8").splitlines()[0].lstrip("# ")


def ask(openai, agent: str, question: str) -> tuple[str, set[str]]:
    response = openai.responses.create(
        input=question,
        extra_body={"agent_reference": {"name": agent, "type": "agent_reference"}},
    )
    cited = {a.title for item in response.output if item.type == "message"
             for part in item.content if part.type == "output_text"
             for a in part.annotations if a.type == "url_citation"}
    return response.output_text, cited


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # answers contain citation markers like 【4:0†source】
    env = azure_env.load()
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=env.project_endpoint, credential=credential) as project,
        project.get_openai_client() as openai,
    ):
        agent = create_agent(project, env)
        passed = 0
        for question, file_name in QUESTIONS:
            answer, cited = ask(openai, agent, question)
            ok = title_of(file_name) in cited
            passed += ok
            print(f"\n{'PASS' if ok else 'FAIL'}  {question}")
            print(f"  expected: {title_of(file_name)}\n  cited: {sorted(cited)}")
            print("  " + answer.replace("\n", "\n  ")[:600])
        print(f"\n{passed}/{len(QUESTIONS)} answers cite the expected document")


if __name__ == "__main__":
    main()
