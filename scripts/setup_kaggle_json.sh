#!/usr/bin/env bash
# .env から KAGGLE_USERNAME / KAGGLE_KEY を読み取り ~/.kaggle/kaggle.json を生成する
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Error: .env not found at $ENV_FILE" >&2
  exit 1
fi

# .env から値を取得
KAGGLE_USERNAME="$(grep -E '^KAGGLE_USERNAME=' "$ENV_FILE" | cut -d= -f2-)"
KAGGLE_KEY="$(grep -E '^KAGGLE_KEY=' "$ENV_FILE" | cut -d= -f2-)"

if [[ -z "$KAGGLE_USERNAME" || -z "$KAGGLE_KEY" ]]; then
  echo "Error: KAGGLE_USERNAME or KAGGLE_KEY not found in .env" >&2
  exit 1
fi

mkdir -p ~/.kaggle
if [[ -f ~/.kaggle/kaggle.json ]]; then
  echo "Overwriting existing ~/.kaggle/kaggle.json"
fi
cat > ~/.kaggle/kaggle.json <<EOF
{"username":"${KAGGLE_USERNAME}","key":"${KAGGLE_KEY}"}
EOF
chmod 600 ~/.kaggle/kaggle.json

echo "Created ~/.kaggle/kaggle.json (chmod 600)"
