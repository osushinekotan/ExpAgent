FROM nvidia/cuda:12.6.1-base-ubuntu24.04

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_SYSTEM_PYTHON=1

RUN apt-get update && apt-get install -y python3 unzip && rm -rf /var/lib/apt/lists/*
RUN uv pip install --break-system-packages google-cloud-aiplatform google-cloud-storage

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
