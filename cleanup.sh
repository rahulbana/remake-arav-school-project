#!/usr/bin/env bash

# Set variables to match your deployment
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
SERVICE_NAME="lifestyle-app-service"
REPO_NAME="app-repo"

echo "=========================================="
echo "Cleaning up resources for Project: ${PROJECT_ID}"
echo "=========================================="

# 1. Delete the Cloud Run Service
echo "--> Deleting Cloud Run service: ${SERVICE_NAME}..."
gcloud run services delete "${SERVICE_NAME}" \
  --region="${REGION}" \
  --platform=managed \
  --quiet

# 2. Delete the Artifact Registry Repository and container images
echo "--> Deleting Artifact Registry repository: ${REPO_NAME}..."
gcloud artifacts repositories delete "${REPO_NAME}" \
  --location="${REGION}" \
  --quiet

# 3. Clean up Cloud Build cache bucket (optional storage cleanup)
echo "--> Cleaning up default Cloud Build storage artifacts..."
BUILD_BUCKET="gs://${PROJECT_ID}_cloudbuild"
if gcloud storage buckets describe "${BUILD_BUCKET}" &>/dev/null; then
  gcloud storage rm -r "${BUILD_BUCKET}" --quiet || true
fi

echo "=========================================="
echo "Cleanup completed successfully!"
echo "=========================================="