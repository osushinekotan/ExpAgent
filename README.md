# ExpAgent

An AI-powered experiment management framework for data science competitions. Built for [Claude Code](https://claude.ai/claude-code) with skills that automate the full experiment lifecycle.

Designed primarily for Kaggle competitions (including Code Competitions), but adaptable to other data science contest platforms.

## Experiment Workflow

| Phase      | Action                                            |
| ---------- | ------------------------------------------------- |
| Understand | Review competition docs (`backlog doc list`)      |
| Plan       | Review past experiments, create backlog task      |
| Create     | `task new-exp EXP=expXXX` — scaffold experiment   |
| Implement  | Write train.py, settings.py, inference.py         |
| Train      | `task train-local` or `task train-vertex` (GCP)   |
| Record     | Update backlog task with CV / LB scores           |
| Submit     | `task submit-kaggle EXP=expXXX` (Kaggle pipeline) |

```
models/
└── exp001/
    ├── train.py           # Training script (tyro CLI)
    ├── settings.py        # Config & DirectorySettings
    ├── inference.py       # Submission pipeline
    ├── artifacts/         # Trained model weights, OOF predictions
    └── submission/        # Kaggle kernel files (optional: KAGGLE_CODE_SUB=true)
```

## Prerequisites

- [Claude Code](https://claude.ai/claude-code) — AI coding agent
- [uv](https://github.com/astral-sh/uv) — Python package manager
- [Task](https://taskfile.dev/) — Task runner (`Taskfile.yml`)
- [Terraform](https://github.com/hashicorp/terraform) — Infrastructure provisioning
- [Backlog](https://github.com/MrLesk/Backlog.md) — Project management CLI
- [Playwright CLI](https://github.com/microsoft/playwright-cli) — Browser automation
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) — Google Cloud SDK

## Setup

Install third-party Claude Code skills:

```bash
npx skills add wandb/skills --agent claude-code --skill '*' --yes
```
