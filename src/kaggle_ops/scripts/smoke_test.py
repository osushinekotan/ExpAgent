"""Vertex AI ジョブの動作確認用スモークテスト。GPU・GCS アクセスを検証する"""

import os
import sys
from pathlib import Path

print("=== Vertex AI Smoke Test ===")
print(f"Python: {sys.version}")

# GPU 確認
try:
    import torch  # type: ignore[import-not-found]

    print(f"PyTorch: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device: {torch.cuda.get_device_name(0)}")
        print(f"CUDA memory: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB")
        x = torch.randn(1000, 1000, device="cuda")
        y = torch.matmul(x, x)
        print(f"GPU matmul test: OK (result shape: {y.shape})")
    else:
        print("No GPU detected")
except ImportError:
    print("PyTorch not installed")

# GCS アクセス確認
bucket_name = os.getenv("BUCKET_NAME", "")
if bucket_name:
    gcs_path = Path(f"/gcs/{bucket_name}")
    print(f"GCS mount ({gcs_path}): {'exists' if gcs_path.exists() else 'NOT FOUND'}")
    if gcs_path.exists():
        items = list(gcs_path.iterdir())[:10]
        print(f"  contents: {[p.name for p in items]}")

print("=== Smoke Test Completed ===")
