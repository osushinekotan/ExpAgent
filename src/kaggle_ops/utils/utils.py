import os
from pathlib import Path


def get_run_env() -> str:
    if os.getenv("KAGGLE_DATA_PROXY_TOKEN"):
        return "kaggle"
    if os.getenv("BUCKET_NAME") and Path(f"/gcs/{os.getenv('BUCKET_NAME')}").exists():
        return "vertex"
    return "local"


def get_kaggle_authentication() -> tuple[str, str]:
    username = os.environ["KAGGLE_USERNAME"]
    key = os.environ["KAGGLE_KEY"]
    return username, key
