import logging
import os
import tomllib
from pathlib import Path
from typing import Annotated, Literal, TypedDict

import dotenv
import tyro
from google.cloud import aiplatform, storage
from pydantic import BaseModel, model_validator

from .compile import compile_train_script

dotenv.load_dotenv()
logger = logging.getLogger(__name__)

AcceleratorType = Literal["NVIDIA_L4", "NVIDIA_TESLA_V100", "NVIDIA_TESLA_A100"]


class _GpuMachineConfig(TypedDict):
    default_machine_type: str
    allowed_prefixes: list[str]


# GPU タイプごとのデフォルト machine type と許可される machine type プレフィックス
_GPU_CONFIGS: dict[str, _GpuMachineConfig] = {
    "NVIDIA_L4": {
        "default_machine_type": "g2-standard-8",
        "allowed_prefixes": ["g2-"],
    },
    "NVIDIA_TESLA_V100": {
        "default_machine_type": "n1-highmem-8",
        "allowed_prefixes": ["n1-"],
    },
    "NVIDIA_TESLA_A100": {
        "default_machine_type": "a2-highgpu-1g",
        "allowed_prefixes": ["a2-"],
    },
}

# GPU なしの場合のデフォルト machine type
_DEFAULT_CPU_MACHINE_TYPE = "n1-highmem-8"


class GpuConfig(BaseModel):
    """GPU と machine type の組み合わせをバリデーションする"""

    machine_type: str = ""
    accelerator_type: AcceleratorType | None = None
    accelerator_count: int = 1

    @model_validator(mode="after")
    def validate_gpu_machine_combination(self) -> "GpuConfig":
        if self.accelerator_type is None:
            # GPU なしの場合、machine_type 未指定ならデフォルトを設定
            if not self.machine_type:
                self.machine_type = _DEFAULT_CPU_MACHINE_TYPE
            return self

        config = _GPU_CONFIGS.get(self.accelerator_type)
        if config is None:
            raise ValueError(f"未知の accelerator_type: {self.accelerator_type}")

        # machine_type 未指定ならデフォルトを自動設定
        if not self.machine_type:
            self.machine_type = config["default_machine_type"]
            return self

        # 指定された machine_type が許可されたプレフィックスか検証
        allowed = config["allowed_prefixes"]
        if not any(self.machine_type.startswith(p) for p in allowed):
            raise ValueError(
                f"{self.accelerator_type} には {allowed} シリーズの machine type が必要です "
                f"(指定: {self.machine_type}, デフォルト: {config['default_machine_type']})"
            )

        return self

    def to_job_kwargs(self) -> dict:
        """aiplatform job.run() に渡す kwargs を生成"""
        kwargs: dict = {"machine_type": self.machine_type}
        if self.accelerator_type is not None:
            kwargs["accelerator_type"] = self.accelerator_type
            kwargs["accelerator_count"] = self.accelerator_count
        return kwargs

    def display_info(self) -> str:
        if self.accelerator_type:
            return f"{self.machine_type} + {self.accelerator_type} x{self.accelerator_count}"
        return f"{self.machine_type} (CPU only)"


def _upload_to_gcs(local_path: str, bucket_name: str, blob_path: str) -> str:
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    blob.upload_from_filename(local_path)
    uri = f"gs://{bucket_name}/{blob_path}"
    logger.info("Uploaded: %s", uri)
    return uri


def _get_common_env() -> tuple[str, str, str]:
    """共通の環境変数（project_id, region, bucket_name）を取得"""
    project_id = os.environ["PROJECT_ID"]
    region = os.environ["REGION"]
    bucket_name = os.getenv("BUCKET_NAME") or os.environ["COMPETITION_NAME"]
    return project_id, region, bucket_name


def _get_container_uri(region: str, project_id: str, container_uri: str) -> str:
    return container_uri or f"{region}-docker.pkg.dev/{project_id}/training-images/training:latest"


def train(
    exp: str,
    machine_type: str = "",
    container_uri: Annotated[
        str, "GAR image URI. Defaults to {REGION}-docker.pkg.dev/{PROJECT_ID}/training-images/training:latest"
    ] = "",
    accelerator_type: AcceleratorType | None = None,
    accelerator_count: int = 1,
    extra_args: tuple[str, ...] = (),
) -> None:
    gpu = GpuConfig(machine_type=machine_type, accelerator_type=accelerator_type, accelerator_count=accelerator_count)
    project_id, region, bucket_name = _get_common_env()
    container_uri = _get_container_uri(region, project_id, container_uri)

    compiled_path = compile_train_script(exp=exp)
    script_gcs_uri = _upload_to_gcs(compiled_path, bucket_name, f"scripts/{exp}/{Path(compiled_path).name}")

    # トレーニング用の依存パッケージを読み取り
    pyproject_path = Path("pyproject.toml")
    reqs: list[str] = []
    if pyproject_path.exists():
        pyproject = tomllib.loads(pyproject_path.read_text())
        reqs = pyproject.get("project", {}).get("dependencies", [])

    aiplatform.init(project=project_id, location=region, staging_bucket=f"gs://{bucket_name}")

    job = aiplatform.CustomContainerTrainingJob(
        display_name=exp,
        container_uri=container_uri,
    )

    env_vars: dict[str, str] = {
        "BUCKET_NAME": bucket_name,
        "COMPETITION_NAME": os.environ["COMPETITION_NAME"],
    }
    if os.getenv("WANDB_API_KEY"):
        env_vars["WANDB_API_KEY"] = os.environ["WANDB_API_KEY"]
    if reqs:
        env_vars["REQUIREMENTS"] = " ".join(reqs)

    kwargs = gpu.to_job_kwargs()
    kwargs["args"] = [script_gcs_uri, *extra_args]
    kwargs["environment_variables"] = env_vars

    logger.info("Submitting: %s on %s", exp, gpu.display_info())
    if extra_args:
        logger.info("Extra args: %s", list(extra_args))
    job.run(**kwargs)
    logger.info("Training completed")


def download_kaggle_competition_data(
    machine_type: str = "n1-standard-4",
    container_uri: Annotated[
        str, "GAR image URI. Defaults to {REGION}-docker.pkg.dev/{PROJECT_ID}/training-images/training:latest"
    ] = "",
) -> None:
    """Kaggle コンペデータを Vertex AI ジョブ経由で GCS に直接ダウンロード"""
    project_id, region, bucket_name = _get_common_env()
    container_uri = _get_container_uri(region, project_id, container_uri)

    # ダウンロードスクリプトを GCS にアップロード
    script_path = str(Path(__file__).parent / "scripts" / "download_competition.py")
    script_gcs_uri = _upload_to_gcs(script_path, bucket_name, "scripts/download_competition.py")

    aiplatform.init(project=project_id, location=region, staging_bucket=f"gs://{bucket_name}")

    job = aiplatform.CustomContainerTrainingJob(
        display_name="download-kaggle-competition-data",
        container_uri=container_uri,
    )

    env_vars: dict[str, str] = {
        "BUCKET_NAME": bucket_name,
        "COMPETITION_NAME": os.environ["COMPETITION_NAME"],
        "KAGGLE_USERNAME": os.environ["KAGGLE_USERNAME"],
        "KAGGLE_KEY": os.environ["KAGGLE_KEY"],
        "REQUIREMENTS": "kaggle",
    }

    logger.info("Submitting download job on %s", machine_type)
    job.run(
        machine_type=machine_type,
        args=[script_gcs_uri],
        environment_variables=env_vars,
    )
    logger.info("Download completed: gs://%s/data/input/%s/", bucket_name, os.environ["COMPETITION_NAME"])


def smoke_test(
    machine_type: str = "",
    container_uri: Annotated[
        str, "GAR image URI. Defaults to {REGION}-docker.pkg.dev/{PROJECT_ID}/training-images/training:latest"
    ] = "",
    accelerator_type: AcceleratorType | None = None,
    accelerator_count: int = 1,
) -> None:
    """Vertex AI ジョブの動作確認用スモークテスト。GPU・GCS アクセスを検証する"""
    gpu = GpuConfig(machine_type=machine_type, accelerator_type=accelerator_type, accelerator_count=accelerator_count)
    project_id, region, bucket_name = _get_common_env()
    container_uri = _get_container_uri(region, project_id, container_uri)

    script_path = str(Path(__file__).parent / "scripts" / "smoke_test.py")
    script_gcs_uri = _upload_to_gcs(script_path, bucket_name, "scripts/smoke_test.py")

    aiplatform.init(project=project_id, location=region, staging_bucket=f"gs://{bucket_name}")

    job = aiplatform.CustomContainerTrainingJob(
        display_name="smoke-test",
        container_uri=container_uri,
    )

    env_vars: dict[str, str] = {
        "BUCKET_NAME": bucket_name,
        "REQUIREMENTS": "torch",
    }

    kwargs = gpu.to_job_kwargs()
    kwargs["args"] = [script_gcs_uri]
    kwargs["environment_variables"] = env_vars

    logger.info("Submitting smoke test on %s", gpu.display_info())
    job.run(**kwargs)
    logger.info("Smoke test completed")


# tyro SubcommandApp でサブコマンドを定義
# tyro は関数を型引数として使うため、ty の型チェッカーでは検証不可
SubcommandType = (
    Annotated[train, tyro.conf.subcommand("train")]  # type: ignore[type-var]
    | Annotated[download_kaggle_competition_data, tyro.conf.subcommand("download-kaggle-competition-data")]  # type: ignore[type-var]
    | Annotated[smoke_test, tyro.conf.subcommand("smoke-test")]  # type: ignore[type-var]
)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s", force=True)
    tyro.cli(SubcommandType)  # type: ignore[arg-type]
