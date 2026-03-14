import json
import logging
import os
from pathlib import Path

import dotenv
import nbformat
from nbformat.v4 import new_code_cell, new_notebook
from tyro.extras import SubcommandApp

dotenv.load_dotenv()
app = SubcommandApp()
logger = logging.getLogger(__name__)

USERNAME = os.getenv("KAGGLE_USERNAME", "")
COMP = os.getenv("COMPETITION_NAME", "")
KAGGLE_TITLE_MAX_LENGTH = 50


def _shorten_comp_name(name: str) -> str:
    """competition名をハイフン区切りの各単語の先頭文字に短縮する (例: deep-past-initiative-machine-translation -> dpimt)"""
    return "".join(part[0] for part in name.split("-") if part)


def _kaggle_title(suffix: str) -> str:
    """Kaggleのタイトル50文字制限に収まるよう、必要に応じてcompetition名を短縮する"""
    title = f"{COMP}-{suffix}"
    if len(title) <= KAGGLE_TITLE_MAX_LENGTH:
        return title
    return f"{_shorten_comp_name(COMP)}-{suffix}"


@app.command()
def deps_metadata() -> None:
    deps_name = _kaggle_title("deps")
    metadata = {
        "id": f"{USERNAME}/{deps_name}",
        "title": deps_name,
        "code_file": "code.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": "true",
        "enable_gpu": "false",
        "enable_tpu": "false",
        "enable_internet": "true",
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
        "model_sources": [],
    }
    out = Path("deps")
    out.mkdir(parents=True, exist_ok=True)
    (out / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2))
    logger.info(json.dumps(metadata, indent=2))


@app.command()
def submission_metadata(
    exp: str,
    model_source_names: list[str] | None = None,
    dataset_sources: list[str] | None = None,
    enable_gpu: bool = True,
    enable_tpu: bool = False,
) -> None:
    model_source_names = model_source_names or []
    dataset_sources = dataset_sources or []

    deps_name = _kaggle_title("deps")
    sub_name = _kaggle_title("submission")
    models_handle = f"{USERNAME}/{COMP}-models/other"

    metadata = {
        "id": f"{USERNAME}/{sub_name}",
        "title": sub_name,
        "code_file": "code.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": "true",
        "enable_gpu": str(enable_gpu).lower(),
        "enable_tpu": str(enable_tpu).lower(),
        "enable_internet": "false",
        "dataset_sources": sorted(set(dataset_sources)),
        "competition_sources": [COMP],
        "kernel_sources": [f"{USERNAME}/{deps_name}"],
        "model_sources": [f"{models_handle}/{name}/1" for name in model_source_names],
    }
    out = Path(f"models/{exp}/submission")
    out.mkdir(parents=True, exist_ok=True)
    (out / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2))
    logger.info(json.dumps(metadata, indent=2))


@app.command()
def submission_code(exp: str) -> None:
    deps_name = _kaggle_title("deps")
    model_dir = f"/kaggle/input/models/{USERNAME}/{COMP}-models/other/{exp}/1"

    deps_path = f"/kaggle/input/notebooks/{USERNAME}/{deps_name}"
    install = (
        f"!pip install {deps_path}/*.whl "
        f"--force-reinstall --root-user-action ignore --no-deps --no-index --find-links {deps_path}"
    )
    run = f"!KAGGLE_USERNAME={USERNAME} COMPETITION_NAME={COMP} python {model_dir}/inference.py"

    nb = new_notebook(cells=[new_code_cell(source=install), new_code_cell(source=run)])
    nb["metadata"]["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}

    out = Path(f"models/{exp}/submission")
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "code.ipynb", "w") as f:
        nbformat.write(nb, f)


@app.command()
def deps_code() -> None:
    deps_dir = Path("deps")
    req_path = deps_dir / "requirements.txt"
    if not req_path.exists():
        raise FileNotFoundError(f"requirements.txt not found: {req_path}")

    reqs = [
        line.strip() for line in req_path.read_text().splitlines() if line.strip() and not line.strip().startswith("#")
    ]

    if not reqs:
        nb = new_notebook(cells=[new_code_cell(source="pass")])
    else:
        code = (
            "!pip download -d /kaggle/working " + " ".join(reqs) + "\n"
            "!pip install /kaggle/working/*.whl --force-reinstall --root-user-action ignore --no-deps --no-index --find-links /kaggle/working"
        )
        nb = new_notebook(cells=[new_code_cell(source=code)])

    nb["metadata"]["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    with open(deps_dir / "code.ipynb", "w") as f:
        nbformat.write(nb, f)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s", force=True)
    app.cli()
