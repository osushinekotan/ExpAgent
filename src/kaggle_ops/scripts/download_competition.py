"""Kaggle コンペデータを GCS FUSE 経由で直接ダウンロードするスクリプト"""

import os
import subprocess

from kaggle import KaggleApi

comp_name = os.environ["COMPETITION_NAME"]
bucket_name = os.environ["BUCKET_NAME"]
data_dir = f"/gcs/{bucket_name}/data/input/{comp_name}"

os.makedirs(data_dir, exist_ok=True)

api = KaggleApi()
api.authenticate()
api.competition_download_files(comp_name, path=data_dir, quiet=False)

# zip がダウンロードされた場合は展開して削除
zip_path = os.path.join(data_dir, f"{comp_name}.zip")
if os.path.exists(zip_path):
    subprocess.run(["unzip", "-o", "-q", zip_path, "-d", data_dir], check=False)
    os.remove(zip_path)

print(f"Downloaded to {data_dir}")
print("Files:", os.listdir(data_dir))
