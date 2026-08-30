# ReMake — Arav's School Project

Photograph a piece of waste (bottles, a pallet, old denim, e-waste…) and ReMake's
AI reads the material and generates a **finished product image** you could build
from it, along with the tools and steps to get there.

## What's inside

- **Flask app** (`app.py`) serving a multi-page site: Home, About, Contact.
- **AI endpoint** (`POST /api/generate`) that:
  1. Sends the uploaded photo(s) to an OpenAI **vision** model to identify the
     material and design one buildable product, then
  2. Uses an OpenAI **image** model to render a photo of that finished product.
- **Themed frontend** (`templates/`, `assets/theme.css`, `assets/remake.js`) —
  drag-and-drop upload, live status, and a result card with the generated image.

## Run locally

```bash
pip install -r requirements.txt
cp .env.example .env        # then edit .env and add your OPENAI_API_KEY
python app.py               # http://localhost:8080
```

Without an `OPENAI_API_KEY` the site still runs; the generator returns a friendly
"AI not configured" message instead of a product.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | _(required for AI)_ | Your OpenAI API key |
| `OPENAI_VISION_MODEL` | `gpt-4o` | Model that reads the waste photo |
| `OPENAI_IMAGE_MODEL` | `gpt-image-1` | Model that renders the product |
| `OPENAI_IMAGE_SIZE` | `1024x1024` | Generated image size |
| `MAX_UPLOAD_BYTES` | `33554432` | Max total upload size (bytes) |
| `PORT` | `8080` | Server port |

## Deploy (Google Cloud Run)

```bash
export OPENAI_API_KEY=sk-...   # passed through to Cloud Run, never stored in the repo
./deploy.sh                    # first deploy
./redeploy.sh                  # push a new revision
```
