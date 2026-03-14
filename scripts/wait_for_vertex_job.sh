#!/bin/bash
set -e

JOB_ID=$1
PROJECT_ID=$2
REGION=$3
TIMEOUT=${4:-1800}  # Default 30 minutes

if [[ -z "$JOB_ID" ]] || [[ -z "$PROJECT_ID" ]] || [[ -z "$REGION" ]]; then
  echo "Usage: $0 <JOB_ID> <PROJECT_ID> <REGION> [TIMEOUT_SECONDS]"
  exit 1
fi

echo "Waiting for Vertex AI job: $JOB_ID"
echo "Project: $PROJECT_ID, Region: $REGION"

START_TIME=$(date +%s)

while true; do
  STATE=$(gcloud ai custom-jobs describe "$JOB_ID" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --format='value(state)')

  echo "Job state: $STATE"

  if [[ "$STATE" == "JOB_STATE_SUCCEEDED" ]]; then
    echo "Job completed successfully!"
    exit 0
  elif [[ "$STATE" == "JOB_STATE_FAILED" ]]; then
    echo "Job failed!"
    exit 1
  elif [[ "$STATE" == "JOB_STATE_CANCELLED" ]]; then
    echo "Job was cancelled!"
    exit 1
  fi

  # Timeout check
  CURRENT_TIME=$(date +%s)
  ELAPSED=$((CURRENT_TIME - START_TIME))
  if [[ $ELAPSED -gt $TIMEOUT ]]; then
    echo "Timeout after ${TIMEOUT}s"
    exit 1
  fi

  sleep 30
done
