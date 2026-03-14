# Directory Settings (settings.py)

`DirectorySettings` in each experiment's `settings.py` resolves paths based on the runtime environment (local / Vertex AI / Kaggle kernel).

## Key Directories

| Directory          | Description                                             |
| ------------------ | ------------------------------------------------------- |
| `comp_dataset_dir` | Competition dataset (read-only input)                   |
| `artifact_dir`     | Trained model artifacts (models, OOF predictions, etc.) |
| `output_dir`       | Output files (submissions, logs)                        |

## Environment-Specific Paths

| Environment | comp_dataset_dir                           | artifact_dir                                                            | output_dir           |
| ----------- | ------------------------------------------ | ----------------------------------------------------------------------- | -------------------- |
| **local**   | `./data/input/{competition}`               | `./models/{exp}/artifacts`                                              | Same as artifact_dir |
| **vertex**  | `/gcs/{bucket}/data/input/{competition}`   | `/gcs/{bucket}/models/{exp}/artifacts`                                  | Same as artifact_dir |
| **kaggle**  | `/kaggle/input/competitions/{competition}` | `/kaggle/input/models/{username}/{comp}-models/other/{exp}/1/artifacts` | `/kaggle/working`    |

Auto-detection uses environment variables: `KAGGLE_DATA_PROXY_TOKEN` (Kaggle), `BUCKET_NAME` (Vertex AI), `.env` variables (local).

## Usage Convention

- **train.py**: Save everything to `artifact_dir` (model weights, OOF predictions, etc.)
- **inference.py**: Load trained models from `artifact_dir`, write submission files and logs to `output_dir`

This convention follows the Kaggle kernel runtime model where `artifact_dir` maps to a read-only input dataset and `output_dir` maps to the writable `/kaggle/working` output directory. On local and Vertex AI, `output_dir` defaults to `artifact_dir` for convenience.
