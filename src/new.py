import os
import shutil
import subprocess
from pathlib import Path
from typing import Literal

import dotenv
from tyro.extras import SubcommandApp

dotenv.load_dotenv()
app = SubcommandApp()


def _post_process(target: Path, name: str, source: str) -> None:
    """コピー後のファイルを実験名に合わせて書き換える。"""
    train_py = target / "train.py"
    if train_py.exists():
        text = train_py.read_text()
        old_name = "template" if source == "template" else source
        text = text.replace(f'exp_name="{old_name}"', f'exp_name="{name}"')
        train_py.write_text(text)


def _create_backlog_task(name: str, source: str) -> None:
    """実験用の親タスクを backlog に作成する。"""
    title = f"{name}: New experiment"
    if source != "template":
        title = f"{name}: Based on {source}"

    cmd = [
        "backlog",
        "task",
        "create",
        title,
        "-d",
        f"Experiment {name} (source: {source})",
        "-l",
        "exp",
        "-l",
        name,
        "--ac",
        "Training completes without errors",
        "--ac",
        "CV score recorded",
    ]
    if source != "template":
        cmd.extend(["-l", source])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Backlog task created: {result.stdout.strip()}")
    else:
        print(f"Warning: Failed to create backlog task: {result.stderr.strip()}")


def _resolve_code_sub(kaggle_code_sub: Literal["auto", "true", "false"]) -> bool:
    """kaggle_code_sub の値を解決する。auto の場合は環境変数から判定。"""
    if kaggle_code_sub == "true":
        return True
    if kaggle_code_sub == "false":
        return False
    # auto: IS_CODE_COMPETITION=true かつ COMPETITION_PLATFORM=kaggle の場合に有効
    platform = os.getenv("COMPETITION_PLATFORM", "").lower()
    is_code = os.getenv("IS_CODE_COMPETITION", "false").lower() == "true"
    return platform == "kaggle" and is_code


@app.command()
def exp(name: str, source: str = "template", kaggle_code_sub: Literal["auto", "true", "false"] = "auto") -> None:
    src = Path("templates/models") if source == "template" else Path(f"models/{source}")
    target = Path(f"models/{name}")
    assert src.exists(), f"Source not found: {src}"
    assert not target.exists(), f"Already exists: {target}"

    include_submission = _resolve_code_sub(kaggle_code_sub)
    ignore_patterns = ["artifacts"]
    if not include_submission:
        ignore_patterns.append("submission")
    shutil.copytree(src, target, ignore=shutil.ignore_patterns(*ignore_patterns))
    _post_process(target, name, source)
    print(f"Created: {target} (from {src})")
    _create_backlog_task(name, source)


if __name__ == "__main__":
    app.cli()
