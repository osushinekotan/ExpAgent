---
name: experiment-workflow
description: This skill should be used when the user asks to "create a new experiment", "start an experiment", "新しい実験", "実験を作って", "run training", "train a model", "record results", "結果を記録", "plan next experiment", "次の実験を考えて", "review experiment history", "実験の履歴を見て", or wants to follow the experiment lifecycle (plan, create, implement, train, record).
---

# Experiment Workflow

Guide the full experiment lifecycle: plan, create, implement, train, and record results.

## Workflow Overview

| Phase      | Action                                                                    |
| ---------- | ------------------------------------------------------------------------- |
| Understand | Review competition docs in backlog (`backlog doc list`)                   |
| Plan       | Review backlog and past experiments, create experiment task               |
| Create     | `task new-exp EXP=expXXX` to create experiment directory and backlog task |
| Implement  | Write train.py, settings.py, run code quality checks                      |
| Train      | `task train-local` or `task train-vertex`                                 |
| Record     | Update backlog task with results                                          |

## Phase 0: Understand the Competition

Before planning any experiment, review the competition documentation stored in backlog:

```bash
backlog doc list                    # List all documents
backlog doc view DOC-N              # Read a specific document
```

Competition documents (overview, data description, evaluation metric, etc.) are managed as backlog documents. Check what's available and review relevant materials before designing experiments.

## Phase 1: Plan

Before starting a new experiment, review the backlog and past experiments:

1. Check backlog for experiment history and project state:
   ```bash
   backlog search --type task exp --plain   # Search experiment tasks
   backlog overview                          # Project-level summary
   ```
2. Design the next experiment with a clear hypothesis

### Create Experiment Task in Backlog

Every experiment MUST have a corresponding backlog task. Create it before starting implementation:

```bash
backlog task create "expXXX: Short description of experiment" \
  -d "Hypothesis: ... / Changes from base: ... / Expected outcome: ..." \
  -l exp -l expXXX \
  --ac "Training completes without errors" \
  --ac "CV score recorded" \
  --priority medium
```

**Required conventions:**

- **Label `exp`**: All experiment tasks MUST have the `exp` label for filtering
- **Label `expXXX`**: All experiment tasks MUST have the experiment name (e.g., `exp001`) as a label
- **Title prefix**: Start the title with the experiment name (e.g., `exp002: ...`)
- **Base experiment reference**: If based on a previous experiment, add dependency: `--dep TASK-N` (the parent experiment's task)

## Phase 2: Create

```bash
task new-exp EXP=exp002                              # From template
task new-exp EXP=exp002 SOURCE=exp001                 # Copy from existing experiment
```

This creates `models/exp002/` with train.py, settings.py, and inference.py. A backlog task is automatically created with labels `exp` and `exp002`.

If `models/exp002/submission/` exists after creation, this is a **Kaggle code competition** — the model must be submitted as a Kaggle kernel, not a CSV file. The `submission/` directory is auto-included when `competition_platform: kaggle` and `is_code_competition: true` in `project.yml`. Override with `KAGGLE_CODE_SUB=true` or `KAGGLE_CODE_SUB=false`.

After creation, update the backlog task with experiment details:

```bash
backlog task edit TASK-N -d "Hypothesis: ... / Changes from base: ... / Expected outcome: ..."
backlog task edit TASK-N --plan "Implementation approach: ..."
```

## Phase 3: Implement and Verify

### Decide Validation Strategy

Before implementing train.py, decide the cross-validation strategy. The strategy must match how the test set was constructed.

For the decision flow and code examples, read `.claude/skills/experiment-workflow/references/validation-strategy.md`.

For code competitions where test data is hidden, check public notebooks/discussions or ask the user to confirm assumptions about the test split.

Quick reference:

| Condition                                           | Strategy                   |
| --------------------------------------------------- | -------------------------- |
| Time-series problem                                 | TimeSeriesSplit            |
| Train/test split by distinct groups                 | StratifiedGroupKFold       |
| Categorical target or imbalanced classes            | StratifiedKFold            |
| Multi-label classification                          | MultilabelStratifiedKFold  |
| None of the above                                   | KFold                      |

Record the chosen validation strategy in the backlog task description or plan.

### Implement train.py

`train.py` must use `tyro.cli` with a `main()` function to support CLI arguments (e.g., `--debug`):

```python
from settings import Config, DirectorySettings

def predict(model, df, ...):
    """推論処理。inference.pyからも呼び出される。"""
    ...

def main(debug: bool = False) -> None:
    settings = DirectorySettings(exp_name="expXXX")
    config = Config()

    if debug:
        settings.artifact_dir = settings.artifact_dir / "debug"
        settings.output_dir = settings.artifact_dir
        config.epochs = 1

    # ... data loading, training, model save ...

    # バリデーション推論
    val_predictions = predict(model, val_df)
    # 評価メトリクスを計算し、OOF予測をCSVに保存

if __name__ == "__main__":
    import tyro
    tyro.cli(main)
```

Key conventions:

- **Experiment tracking uses [W&B (Weights & Biases)](https://wandb.ai/)**. Initialize and configure wandb in `train.py` only — do not use wandb in `settings.py` or `inference.py`. Disable wandb in debug mode (`wandb.init(mode="disabled")` or equivalent).
- All training logic goes inside `main()`, invoked via `tyro.cli(main)`
- `if __name__ == "__main__"` guard is required (enables safe import by inference.py)
- `predict()` is defined in train.py; inference.py imports it via `from train import predict`
- `debug: bool = False` is the standard flag; add other CLI args as needed
- After training, run validation inference using `predict()` (same pipeline as submission) and compute evaluation metrics
- Save OOF predictions CSV to `artifact_dir`
- **Save metrics as `metrics.json` to `artifact_dir`**: Include CV score, per-fold scores, and config. This enables programmatic comparison across experiments without relying on wandb.
- **Save OOF analysis plots to `artifact_dir`**: Visualize OOF predictions vs ground truth. Choose plots appropriate for the task (e.g., scatter + residuals for regression, confusion matrix + calibration for classification).
- **All hyperparameters and tunable constants must be defined in `Config`** (in `settings.py`). Do not use module-level constants for tunable values. This centralizes experiment configuration and makes it easy to compare settings across experiments.

### Implement inference.py (Submission Pipeline)

`inference.py` is the submission pipeline that runs on internet-off environment. It must be self-contained and produce the final submission.

**Requirements:**

- **Import `predict()` from train.py**: `from train import predict` — inference logic is defined in train.py and shared
- **`main()` + `if __name__ == "__main__"` guard**: Wrap execution in `main()` with a guard to allow safe imports
- **End-to-end**: Covers the full pipeline from data loading to submission output:
  1. **Data loading** — read test data from `input_dir`
  2. **Preprocessing** — apply the same transforms used during training
  3. **Model loading** — load trained model artifacts from `artifacts_dir`
  4. **Inference** — run predictions on test data
  5. **Postprocessing** — apply any necessary output transforms
  6. **Submission output** — save the final result according to the competition format (e.g., `submission.csv` to `output_dir`, or use the evaluation API if required)

**Submission format**: Follow the competition's specification exactly. Check the competition overview and data description documents in backlog for the expected output format, column names, and file naming conventions.

### Code Quality Checks

After writing code, always run:

1. **Code simplifier**: Run `/simplify` to review and simplify
2. **Format**: `task fmt` (ruff check --fix + ruff format)
3. **Type check**: `task ty` (ty check)

### Commit

After implementation and code quality checks pass, commit the changes using the `/commit-commands:commit` skill.

## Phase 4: Train

**Always run training commands in the background** using `run_in_background: true` on the Bash tool. Training can take minutes to hours, and blocking the conversation prevents the user from doing other work. After launching, inform the user that training is running and they can check progress with `TaskOutput`.

Before starting training, use `AskUserQuestion` to ask the user how they want to run training. Present the available options:

- **Vertex AI with L4 GPU (Recommended)** — `task train-vertex EXP=expXXX ACCELERATOR_TYPE=NVIDIA_L4`
- **Vertex AI with V100 GPU** — `task train-vertex EXP=expXXX ACCELERATOR_TYPE=NVIDIA_TESLA_V100`
- **Vertex AI (CPU only)** — `task train-vertex EXP=expXXX`
- **Local** — `task train-local EXP=expXXX`
- **Debug run (動作確認)** — `task train-local EXP=expXXX EXTRA_ARGS="--debug"` or `task train-vertex EXP=expXXX EXTRA_ARGS="--debug"`
- **Skip** — skip training for now (e.g., user will run it manually later)

GPU-requiring tasks should default to **NVIDIA_L4**. Machine type is auto-resolved from accelerator type by `GpuConfig` in `src/kaggle_ops/vertex.py`.

### Vertex AI GPU options

| Accelerator         | Default Machine Type | Command                                                           |
| ------------------- | -------------------- | ----------------------------------------------------------------- |
| NVIDIA_L4 (default) | `g2-standard-8`      | `task train-vertex EXP=expXXX ACCELERATOR_TYPE=NVIDIA_L4`         |
| NVIDIA_TESLA_V100   | `n1-highmem-8`       | `task train-vertex EXP=expXXX ACCELERATOR_TYPE=NVIDIA_TESLA_V100` |
| NVIDIA_TESLA_A100   | `a2-highgpu-1g`      | `task train-vertex EXP=expXXX ACCELERATOR_TYPE=NVIDIA_TESLA_A100` |
| CPU only            | `n1-highmem-8`       | `task train-vertex EXP=expXXX`                                    |

```bash
task train-local EXP=exp002                                        # Run training locally
task train-vertex EXP=exp002 ACCELERATOR_TYPE=NVIDIA_L4             # Vertex AI with L4 (auto machine type)
task train-local EXP=exp002 EXTRA_ARGS="--debug"                   # Debug run locally (epochs=1, data limited)
task train-vertex EXP=exp002 EXTRA_ARGS="--debug"                  # Debug run on Vertex AI
task run-local SCRIPT=models/exp002/inference.py                    # Run inference locally
```

### Debug mode

Use `EXTRA_ARGS="--debug"` to run in debug mode. This is useful for verifying end-to-end pipeline correctness before launching a full training run.

Debug mode applies these overrides in `train.py`:

- **Config overrides**: epochs=1, reduced max_length, etc.
- **Data limiting**: training data truncated to a small subset
- **artifact_dir isolation**: saves to `artifacts/debug/` to avoid mixing with production artifacts
- **wandb disabled**: no logging to wandb during debug runs

`EXTRA_ARGS` is a generic parameter that passes arbitrary arguments to `train.py`. On Vertex AI, arguments are forwarded via `vertex.py`'s `extra_args` through the container entrypoint.

## Phase 5: Record Results

After training completes, **immediately** record the CV score in the backlog task. Do not wait for user instruction — this is an automatic step after every successful training run.

```bash
# Recode CV score immediately after training completes
backlog task edit TASK-N --append-notes "CV score: 0.8765 (config summary)"
backlog task edit TASK-N --check-ac 1 --check-ac 2
```

**LB score** is recorded later when the user provides feedback after submission (e.g., "Public LB: 0.8750"). At that point, update the task with the full summary:

```bash
backlog task edit TASK-N --append-notes "Public LB: 0.8750"
backlog task edit TASK-N --final-summary "CV=0.8765, LB=0.8750. Next: try feature X (see TASK-M)"
backlog task edit TASK-N -s "Done"
```

## References

- **Directory Settings**: For details on `DirectorySettings` and path resolution across environments, read `.claude/skills/experiment-workflow/references/directory-settings.md`.
- **Tabular Feature Engineering**: For the `engineer_features` pattern (stateless/stateful separation, `f_` prefix, encoder block, polars), read `.claude/skills/experiment-workflow/references/tabular-feature-engineering.md`.
- **Validation Strategy**: For choosing the right cross-validation strategy (TimeSeriesSplit, GroupKFold, StratifiedKFold, MultilabelStratifiedKFold, etc.), read `.claude/skills/experiment-workflow/references/validation-strategy.md`.
- **Backlog**: For backlog CLI usage (task management, documents, decisions), refer to the `backlog` skill.
- **W&B**: For experiment tracking, metrics logging, and run comparison, refer to the `wandb-primary` skill.
