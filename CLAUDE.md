@~/.claude/imports/dotnet.md

# AI-103 exam project: claims assistant

The goal is to pass AI-103 by building a claims assistant on Microsoft Foundry. Plan and milestones: [PLAN.md](PLAN.md).
Where we are, how to run things, and the decisions so far: [progress.md](progress.md). Design:
[docs/architecture/source/content.html](docs/architecture/source/content.html).

## Every session

- **Start:** read progress.md § Now and continue from there. If the work needs Azure, remind the user to run
  `infra/up.ps1` (the command is in progress.md).
- **Teach while building.** The user is preparing for the exam: explain each Azure piece as it's used. Keep answers
  short (often one sentence, simple bullets) unless asked for more.
- **After each milestone or notable step, and whenever the user says they're stopping**, without being asked:
  - update progress.md: § Now, the milestones table, and the milestone's "what exists" and decisions;
  - tick the milestone in PLAN.md;
  - append quiz questions to [quiz.md](quiz.md) following [quiz-rules.md](quiz-rules.md);
  - record quiz scores and weak spots in progress.md § Study log.
- **End:** remind the user to stop the local apps and run `infra/down.ps1`. AI Search Basic is billed by the hour.

## Code

- Python scripts in `data/scripts/`, run with the repo's `.venv`. .NET solution `ClaimsAssistant.slnx` (`src/`,
  `tests/`). How to run each is in progress.md.
- Keyless only: managed identity / `DefaultAzureCredential` and RBAC, never API keys.
- Public repo: https://github.com/Ghinduta/foundry-claims-assistant. `progress.md` and `data/raw/` stay local
  (git-ignored); Foundry tenant and endpoint are in .NET user secrets, not `appsettings.json`.
