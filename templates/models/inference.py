from settings import DirectorySettings
from train import predict  # type: ignore[attr-defined]  # noqa: F401


def main() -> None:
    settings = DirectorySettings(exp_name="template")

    print(f"run_env: {settings.run_env}")
    print(f"comp_dataset_dir: {settings.comp_dataset_dir}")
    print(f"output_dir: {settings.output_dir}")
    print(f"artifact_dir: {settings.artifact_dir}")

    # TODO: モデル読み込み、テストデータ読み込み、predict()呼び出し、提出ファイル作成

    print("Inference completed!")


if __name__ == "__main__":
    main()
