import json
import logging
import os
import shutil
import subprocess
import tempfile
from fnmatch import fnmatch
from pathlib import Path

from kaggle import KaggleApi

from .utils import get_kaggle_authentication

logger = logging.getLogger(__name__)

KAGGLE_USERNAME, _ = get_kaggle_authentication()

IGNORE_PATTERNS = [
    ".*",
    "__pycache__",
    "checkpoint*",
    "debug",
    "data",
    "scripts",
    "pyproject.toml",
    "uv.lock",
    "docs",
    "tests",
    "terraform",
    "Makefile",
    "submission",
]


def _check_dataset_exists(client: KaggleApi, handle: str) -> bool:
    datasets = client.dataset_list(user=KAGGLE_USERNAME) or []
    return any(str(ds.ref) == handle for ds in datasets)  # type: ignore[union-attr]


def _check_model_exists(client: KaggleApi, handle: str) -> bool:
    models = client.model_list(owner=KAGGLE_USERNAME) or []
    return any(str(m) == handle for m in models)


def _check_model_instance_exists(client: KaggleApi, handle: str) -> bool:
    if len(handle.split("/")) == 5:
        handle = "/".join(handle.split("/")[:-1])
    try:
        client.model_instance_get(model_instance=handle)
        return True
    except Exception as e:
        if "404" in str(e):
            return False
        raise


def _copytree(src: str, dst: str, ignore_patterns: list | None = None) -> None:
    ignore_patterns = ignore_patterns or []
    os.makedirs(dst, exist_ok=True)
    for item in os.listdir(src):
        if any(fnmatch(item, p) for p in ignore_patterns):
            continue
        s, d = os.path.join(src, item), os.path.join(dst, item)
        if os.path.isdir(s):
            _copytree(s, d, ignore_patterns)
        else:
            shutil.copy2(s, d)


def model_upload(
    client: KaggleApi,
    handle: str,
    local_model_dir: str,
    ignore_patterns: list[str] = IGNORE_PATTERNS,
    update: bool = False,
) -> None:
    handle = handle.lower()
    model_handle = "/".join(handle.split("/")[:2])

    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "model-metadata.json").write_text(
            json.dumps(
                {
                    "ownerSlug": model_handle.split("/")[0],
                    "title": model_handle.split("/")[1],
                    "slug": model_handle.split("/")[1],
                    "isPrivate": True,
                    "description": f"{model_handle.split('/')[1]} artifacts",
                },
                indent=4,
            )
        )
        if not _check_model_exists(client, model_handle):
            client.model_create_new(folder=tmpdir)

    parts = handle.split("/")
    assert len(parts) == 4, f"Invalid handle: {handle}"
    instance_meta = {
        "ownerSlug": parts[0],
        "modelSlug": parts[1],
        "instanceSlug": parts[3],
        "framework": parts[2],
        "licenseName": "Apache 2.0",
    }
    exists = _check_model_instance_exists(client, handle)

    if exists and update:
        logger.info(f"Deleting {handle} for re-upload")
        client.model_instance_delete(model_instance=handle, no_confirm=True)
    elif exists and not update:
        logger.warning(f"{handle} already exists, skipping")
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        _copytree(local_model_dir, tmpdir, ignore_patterns)
        Path(tmpdir, "model-instance-metadata.json").write_text(json.dumps(instance_meta, indent=4))
        client.model_instance_create(folder=tmpdir, quiet=False, dir_mode="zip")


def dataset_upload(
    client: KaggleApi,
    handle: str,
    local_dataset_dir: str,
    ignore_patterns: list[str] = IGNORE_PATTERNS,
    update: bool = False,
) -> None:
    handle = handle.lower()
    exists = _check_dataset_exists(client, handle)

    if exists and not update:
        logger.warning(f"{handle} already exists, skipping")
        return

    dataset_name = handle.split("/")[-1]
    meta = {"id": handle, "licenses": [{"name": "CC0-1.0"}], "title": dataset_name}

    with tempfile.TemporaryDirectory() as tmpdir:
        dst = Path(tmpdir) / dataset_name
        _copytree(local_dataset_dir, str(dst), ignore_patterns)
        (dst / "dataset-metadata.json").write_text(json.dumps(meta, indent=4))

        if exists and update:
            client.dataset_create_version(
                folder=str(dst),
                version_notes="latest",
                quiet=False,
                convert_to_csv=False,
                delete_old_versions=False,
                dir_mode="zip",
            )
        else:
            client.dataset_create_new(folder=str(dst), public=False, quiet=False, dir_mode="zip")


def competition_download(
    client: KaggleApi, handle: str, destination: str | Path = "./", force_download: bool = False
) -> None:
    out_dir = Path(destination) / handle
    zipfile_path = out_dir / f"{handle}.zip"
    zipfile_path.parent.mkdir(exist_ok=True, parents=True)

    if not zipfile_path.is_file() or force_download:
        client.competition_download_files(competition=handle, path=str(out_dir), quiet=False, force=force_download)
        subprocess.run(["unzip", "-o", "-q", str(zipfile_path), "-d", str(out_dir)], check=False)
    else:
        logger.info(f"Dataset ({handle}) already exists.")


def datasets_download(
    client: KaggleApi, handles: list[str], destination: str | Path = "./", force_download: bool = False
) -> None:
    for dataset in handles:
        name = dataset.split("/")[1]
        out_dir = Path(destination) / name
        zipfile_path = out_dir / f"{name}.zip"
        out_dir.mkdir(exist_ok=True, parents=True)

        if not zipfile_path.is_file() or force_download:
            client.dataset_download_files(dataset=dataset, quiet=False, unzip=False, path=out_dir, force=force_download)
            subprocess.run(["unzip", "-o", "-q", str(zipfile_path), "-d", str(out_dir)], check=False)
        else:
            logger.info(f"Dataset ({dataset}) already exists.")
