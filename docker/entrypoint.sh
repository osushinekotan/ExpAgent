#!/bin/bash
set -e

# gs://bucket/path → /gcs/bucket/path
SCRIPT="/gcs/${1#gs://}"
shift

if [ -n "$REQUIREMENTS" ]; then
    echo "Installing requirements: $REQUIREMENTS"
    uv pip install --break-system-packages $REQUIREMENTS
fi

echo "Running $SCRIPT"
exec python3 "$SCRIPT" "$@"
