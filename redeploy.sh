#!/usr/bin/env bash

set -euo pipefail

# ==========================================
# Configuration Variables
# ==========================================
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
SERVICE_NAME="lifestyle-app-service"
REPO_NAME="app-repo"
IMAGE_NAME="lifestyle-app"
TAG="rev-$(date +%Y%m%d%H%M%S)" # Auto-generates unique timestamp version

IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${TAG}"

echo "=========================================="
echo "Starting Re-deployment"
echo "Target Service : ${SERVICE_NAME}"
echo "New Image Tag  : ${TAG}"
echo "=========================================="

# 1. Submit the new build
echo "--> 1. Building and tagging updated container..."
gcloud builds submit --tag "${IMAGE_URI}" .

# 2. Deploy the new image revision
echo "--> 2. Deploying revision to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image="${IMAGE_URI}" \
  --region="${REGION}"

# 3. Output deployment summary
echo "=========================================="
echo "Re-deployment complete!"
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --region="${REGION}" --format='value(status.url)')
echo "Live URL: ${SERVICE_URL}"
echo "=========================================="
