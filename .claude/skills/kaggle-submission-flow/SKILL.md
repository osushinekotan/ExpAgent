---
name: kaggle-submission-flow
description: This skill should be used when the user asks to "submit to kaggle", "kaggle submit", "push submission", "submit experiment", "サブミット", "sub して", "提出して", "kaggle に提出", "check submission results", "結果確認", "スコア確認", "public score", "LBスコア記録", "submission failed", "サブミット失敗", or wants to run the Kaggle submission pipeline (deps push, model upload, kernel push, result check, troubleshooting).
---

# Kaggle Submission Flow

Guide the full Kaggle submission pipeline: metadata setup, dependency push, model upload, kernel push, result verification, and score recording.

## Pipeline Overview

| Step               | Task Command                                                         | Description                                  |
| ------------------ | -------------------------------------------------------------------- | -------------------------------------------- |
| 1. Metadata setup  | `task setup-kaggle-metadata EXP=expXXX`                              | Generate kernel-metadata.json and code.ipynb |
| 2. Full submission | `task submit-kaggle EXP=expXXX`                                      | Push deps + upload model + push kernel       |
| 3. Result check    | `uv run kaggle competitions submissions -c $COMPETITION_NAME` | Check public score via API                   |
| 4. Record results  | Update README.md front matter                                        | Write public_lb score                        |

## Submission Scenarios

### Scenario A: Full Pipeline (First Submission or Model Updated)

Run the full pipeline when the model artifacts have changed:

```bash
task submit-kaggle EXP=expXXX
```

This executes three steps sequentially:

1. `push-kaggle-deps` — Push dependency wheels to Kaggle (skipped if `PUSH_DEPS=false`)
2. `push-kaggle-models` — Upload model artifacts (can take several minutes for large models)
3. `sleep 60` + `push-kaggle-sub` — Wait for model processing, then push submission kernel

Execute `task submit-kaggle` with the Bash tool's `run_in_background: true` parameter, since model upload takes several minutes and blocking the conversation prevents other work.

### Scenario B: Model Already Uploaded (Re-submit Only)

When the model is already uploaded and only the kernel code or metadata changed:

```bash
cd models/<exp>/submission && uv run kaggle k push
```

This only pushes the submission kernel and completes in seconds.

### Scenario C: Dependencies Updated

When `deps/requirements.txt` has changed, ensure deps are pushed first:

```bash
task submit-kaggle EXP=expXXX PUSH_DEPS=true
```

`PUSH_DEPS=true` is the default. Set `PUSH_DEPS=false` to skip deps push when dependencies haven't changed.

### Scenario D: Switch Experiment on Same Kernel

All experiments share the same submission kernel name (auto-shortened from competition name). To submit a different experiment, regenerate metadata and push:

```bash
task setup-kaggle-metadata EXP=expXXX
task submit-kaggle EXP=expXXX PUSH_DEPS=false
```

## Metadata Setup

Metadata generation is typically handled during experiment creation (`task new-exp`), but can be regenerated:

```bash
task setup-kaggle-metadata EXP=expXXX
```

This runs four commands:

1. `deps-metadata` — Generate `deps/kernel-metadata.json`
2. `deps-code` — Generate `deps/code.ipynb`
3. `submission-code` — Generate `models/<exp>/submission/code.ipynb`
4. `submission-metadata` — Generate `models/<exp>/submission/kernel-metadata.json`

Key metadata details:

- **Kernel name**: Shared across experiments, auto-shortened from competition name to fit Kaggle's 50-char title limit
- **GPU**: Enabled by default (`enable_gpu: true`)
- **Model sources**: Points to `{username}/{comp}-models/other/{exp}/1`
- **Deps kernel**: Bundled as a kernel source for offline pip install

## Checking Submission Results

### API Check

```bash
uv run kaggle competitions submissions -c $COMPETITION_NAME
```

Output columns: fileName, date, status, publicScore, privateScore.

Wait for status to become `SubmissionStatus.COMPLETE` before reading scores. While the kernel is still running, status shows `SubmissionStatus.PENDING` or similar.

### Kernel Execution Log

If a submission fails, check the kernel output on Kaggle. Common failures:

- **ModuleNotFoundError** — missing package in deps
- **Model file not found** — model not uploaded or wrong experiment name
- **GPU OOM** — model too large for allocated GPU

## Recording Results

After confirming the public score, update the backlog task:

```bash
backlog task edit TASK-N --append-notes "Public LB: XX.XX"
```

## Troubleshooting

| Issue                          | Cause                           | Fix                                              |
| ------------------------------ | ------------------------------- | ------------------------------------------------ |
| 400 Bad Request on kernel push | Title exceeds 50 chars          | Run `task setup-kaggle-metadata` (auto-shortens) |
| ModuleNotFoundError            | Missing package in deps         | Add to `deps/requirements.txt`, push deps        |
| Model file not found           | Model not uploaded or wrong exp | Run `task push-kaggle-models EXP=expXXX`         |
| GPU OOM                        | Model too large for GPU         | Adjust `enable_gpu` in metadata                  |
| Kernel timeout                 | Inference too slow              | Optimize batch size or model                     |
