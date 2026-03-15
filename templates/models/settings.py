import os
from pathlib import Path

import dotenv
from pydantic import BaseModel, Field, model_validator

dotenv.load_dotenv()


class Config(BaseModel):
    lr: float = 0.001
    epochs: int = 10
    batch_size: int = 32
    model_name: str = "baseline"


class DirectorySettings(BaseModel):
    """Path management for local/vertex/kaggle environments."""

    exp_name: str = Field(..., description="Experiment name")
    run_env: str = Field(default="", description="Runtime environment (auto-detected if empty)")
    competition_name: str = Field(default="", description="Competition name")
    kaggle_username: str = Field(default="", description="Kaggle username (from env)")

    comp_dataset_dir: Path = Field(default=Path(""), description="Competition dataset directory")
    output_dir: Path = Field(default=Path(""), description="Output directory")
    artifact_dir: Path = Field(default=Path(""), description="Artifact directory")

    @staticmethod
    def _get_run_env() -> str:
        """Detect runtime environment."""
        if os.getenv("KAGGLE_DATA_PROXY_TOKEN"):
            return "kaggle"
        elif os.getenv("BUCKET_NAME"):
            bucket_name = os.getenv("BUCKET_NAME")
            if Path(f"/gcs/{bucket_name}").exists():
                return "vertex"
        return "local"

    @staticmethod
    def _get_competition_name() -> str:
        """COMPETITION_NAME env var from Taskfile (local), Vertex AI, or Kaggle."""
        val = os.getenv("COMPETITION_NAME", "")
        if not val:
            raise ValueError("COMPETITION_NAME env var is not set")
        return val

    @model_validator(mode="after")
    def resolve_paths(self) -> "DirectorySettings":
        if not self.run_env:
            self.run_env = self._get_run_env()

        if not self.competition_name:
            self.competition_name = self._get_competition_name()
        if not self.kaggle_username:
            self.kaggle_username = os.getenv("KAGGLE_USERNAME", "")

        if self.run_env == "local":
            self.comp_dataset_dir = Path(f"./data/input/{self.competition_name}")
            self.artifact_dir = Path(f"./models/{self.exp_name}/artifacts")
            self.output_dir = self.artifact_dir

        elif self.run_env == "kaggle":
            self.comp_dataset_dir = Path(f"/kaggle/input/competitions/{self.competition_name}")
            self.output_dir = Path("/kaggle/working")
            self.artifact_dir = Path(
                f"/kaggle/input/models/{self.kaggle_username}/{self.competition_name}-models/other/{self.exp_name}/1/artifacts"
            )

        elif self.run_env == "vertex":
            bucket = os.getenv("BUCKET_NAME") or self.competition_name
            self.comp_dataset_dir = Path(f"/gcs/{bucket}/data/input/{self.competition_name}")
            self.artifact_dir = Path(f"/gcs/{bucket}/models/{self.exp_name}/artifacts")
            self.output_dir = self.artifact_dir

        else:
            raise ValueError(f"Invalid run_env: {self.run_env}")

        return self
