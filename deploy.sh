#!/usr/bin/env bash

set -euo pipefail

# ==========================================
# Configuration Variables
# ==========================================
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
SERVICE_NAME="remake-app-service"
REPO_NAME="remake-repo"
IMAGE_NAME="remake-app"
TAG="v$(date +%Y%m%d%H%M%S)" # Timestamp-based tag for unique builds
CONTAINER_PORT="8080"

echo "=========================================="
echo "Project ID : ${PROJECT_ID}"
echo "Region     : ${REGION}"
echo "Service    : ${SERVICE_NAME}"
echo "Image Tag  : ${TAG}"
echo "=========================================="

# 1. Enable Required GCP APIs
echo "--> Step 1: Enabling necessary APIs..."
gcloud services enable \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com

# 2. Create Artifact Registry repository if it doesn't exist
echo "--> Step 2: Checking Artifact Registry repository..."
if ! gcloud artifacts repositories describe "${REPO_NAME}" --location="${REGION}" &>/dev/null; then
  echo "    Repository '${REPO_NAME}' not found. Creating it..."
  gcloud artifacts repositories create "${REPO_NAME}" \
    --repository-format=docker \
    --location="${REGION}" \
    --description="Docker repository for ${SERVICE_NAME}"
else
  echo "    Repository '${REPO_NAME}' already exists."
fi

# 3. Build the container image via Cloud Build
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${TAG}"
echo "--> Step 3: Building and pushing image to ${IMAGE_URI}..."
gcloud builds submit --tag "${IMAGE_URI}" .

# 4. Deploy to Cloud Run
echo "--> Step 4: Deploying to Cloud Run..."
# Pass the OpenAI API key through only if it is set in the shell environment.
# The key is never stored in the repo — export it before running this script:
#   export OPENAI_API_KEY=sk-...
ENV_FLAG=()
if [[ -n "${OPENAI_API_KEY:-}" ]]; then
  ENV_FLAG=(--set-env-vars "OPENAI_API_KEY=${OPENAI_API_KEY}")
else
  echo "    WARNING: OPENAI_API_KEY not set — the AI product generator will be disabled."
fi

gcloud run deploy "${SERVICE_NAME}" \
  --image="${IMAGE_URI}" \
  --platform=managed \
  --region="${REGION}" \
  --port="${CONTAINER_PORT}" \
  "${ENV_FLAG[@]}" \
  --allow-unauthenticated

# 5. Retrieve Service URL
echo "=========================================="
echo "Deployment successful!"
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --region="${REGION}" --format='value(status.url)')
echo "Service URL: ${SERVICE_URL}"
echo "=========================================="
