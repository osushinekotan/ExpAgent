# CLAUDE.md

## Language Rules

- **CLAUDE.md / documentation**: Write in English.
- **User interaction**: Respond in Japanese.
- **Code comments**: Write in Japanese.

## Task Runner (Taskfile)

This project uses [Task](https://taskfile.dev/) (`Taskfile.yml`). Run tasks with:

```bash
task <task-name>          # Run a task
task <task-name> VAR=val  # Pass variables
task --list               # List all available tasks
```

### Key Tasks

| Task                                               | Description                                                            |
| -------------------------------------------------- | ---------------------------------------------------------------------- |
| `task fmt`                                         | Format code (ruff check --fix + ruff format)                           |
| `task ty`                                          | Type check (ty check)                                                  |
| `task train-local EXP=exp001`                      | Run training locally                                                   |
| `task train-vertex EXP=exp001`                     | Run training on Vertex AI                                              |
| `task run-local SCRIPT=models/exp001/inference.py` | Run any Python script locally                                          |
| `task new-exp EXP=exp002`                          | Create a new experiment                                                |
| `task dl-kaggle-comp`                              | Download competition dataset                                           |
| `task push-data` / `task pull-data`                | Sync data with GCS                                                     |
| `task push-artifacts` / `task pull-artifacts`      | Sync model artifacts with GCS                                          |
| `task submit-kaggle EXP=exp001`                    | Full Kaggle submission pipeline (add PUSH_DEPS=true to also push deps) |
| `task build-image`                                 | Build and push training Docker image to GAR                            |
| `task setup-infra`                                 | Apply Terraform + build image                                          |

Competition settings are in `project.yml` (git-tracked, read via `yq` in Taskfile and exported as env vars to all tasks).
Secrets and GCP settings are loaded from `.env` (see `.env.example`). Requires `yq` (`brew install yq`).

## Python / uv

This project uses [uv](https://docs.astral.sh/uv/) for Python package management. Python 3.12+.

```bash
uv sync                   # Install dependencies from pyproject.toml / uv.lock
uv run python <script>    # Run a script in the managed environment
uv add <package>          # Add a dependency
uv add --group dev <pkg>  # Add a dev dependency
```

All `task` commands that run Python use `uv run` internally.

## Commit Messages

- Start with an emoji prefix (e.g., ✨ feature, 🐛 fix, 📝 docs, 💅 style, ♻️ refactor, 🧪 test, 🔧 config, 🚀 experiment).
- Write in English, 1–2 concise sentences focusing on "why" not "what".
- For experiment commits, prefix with the experiment name: `🚀 exp001: <description>`.
- Keep commits focused: separate concerns by topic (e.g., don't mix docs changes with experiment code).
- When AI tools (e.g., Claude Code) create commits, include a `Co-Authored-By` trailer.

## Code Quality

- Run `task fmt` before committing. (auto formatting + linting)
- Run `task ty` to check types.

## Code Comment Style

- Keep comments simple and plain. No decorative banners (`# === ... ===`, `# --- ... ---`, `# *** ... ***`, etc.).
- Do not comment what is obvious from reading the code. Only add comments when the reason behind the code is non-obvious.
- Use `# NOTE:` to explain _why_ a non-obvious implementation choice was made.
- Use `# TODO:` for work that remains to be done.
- After writing or modifying code, run `/simplify` to review and clean up unnecessary comments and code.

## Experiment Workflow

See the `experiment-workflow` skill (`.claude/skills/experiment-workflow/SKILL.md`) for the full experiment lifecycle: plan, create, implement, train, and record results.

## Project Structure

- `src/` - Shared source code
- `models/<exp>/` - Per-experiment code (train.py, settings, etc.)
- `data/` - Competition data (local, synced with GCS)
- `terraform/` - Infrastructure as Code (GCS bucket, Artifact Registry, etc.)
- `docker/` - Training container image
