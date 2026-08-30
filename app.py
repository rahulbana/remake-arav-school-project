import base64
import json
import os
from datetime import datetime

from flask import Flask, render_template, request, jsonify

try:
    # python-dotenv is optional; load a local .env if present (dev only).
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is a convenience only
    pass

# Initialize Flask application. Static assets (css/js/images) live in ./assets
# and are served from the /assets URL prefix so existing links keep working.
app = Flask(__name__, static_folder="assets", static_url_path="/assets")

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "default-dev-secret-key-change-in-prod"
)
# Max upload size for the whole request (default 32 MB → ~4 photos @ 8 MB).
app.config["MAX_CONTENT_LENGTH"] = int(
    os.environ.get("MAX_UPLOAD_BYTES", 32 * 1024 * 1024)
)

# ---- AI configuration -------------------------------------------------------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
VISION_MODEL = os.environ.get("OPENAI_VISION_MODEL", "gpt-4o")
IMAGE_MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1")
IMAGE_SIZE = os.environ.get("OPENAI_IMAGE_SIZE", "1024x1024")

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
MAX_IMAGES = 4

# The vision model is asked to return this exact shape as JSON.
ANALYSIS_SYSTEM_PROMPT = (
    "You are ReMake, an expert in upcycling and circular product design. "
    "You are shown one or more photos of a piece of waste or scrap material "
    "that a person wants to reuse. Identify the material(s), then invent ONE "
    "genuinely useful, buildable product they could make from it using simple "
    "hand tools. Be realistic and safe.\n\n"
    "Respond with STRICT JSON only, no markdown, using exactly these keys:\n"
    "{\n"
    '  "material": "short label of the main material identified",\n'
    '  "product_name": "catchy name of the product to build",\n'
    '  "description": "1-2 sentence description of the finished product",\n'
    '  "tools": ["up to 4 common tools needed"],\n'
    '  "steps": ["4 to 6 short build steps"],\n'
    '  "effort": "Easy | Medium | Hard",\n'
    '  "time": "rough time, e.g. 1-2 hours",\n'
    '  "impact": "one short line on waste saved / benefit",\n'
    '  "image_prompt": "a vivid prompt to generate a clean product photo of '
    'the finished item on a neutral studio background, photorealistic"\n'
    "}"
)


def _client():
    """Create an OpenAI client, or raise a clear error if unconfigured."""
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "The AI service is not configured yet. Set the OPENAI_API_KEY "
            "environment variable to enable product generation."
        )
    from openai import OpenAI

    return OpenAI(api_key=OPENAI_API_KEY)


def _data_url(mime, raw_bytes):
    return "data:%s;base64,%s" % (mime, base64.b64encode(raw_bytes).decode("ascii"))


def _analyze_images(client, images, note):
    """Send the uploaded photos to the vision model and parse its JSON."""
    content = [
        {
            "type": "text",
            "text": (
                "Here are photo(s) of my waste material. "
                + ("Extra context from me: " + note if note else "")
                + " Suggest one product I can build and fill in the JSON."
            ),
        }
    ]
    for mime, raw in images:
        content.append(
            {"type": "image_url", "image_url": {"url": _data_url(mime, raw)}}
        )

    completion = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        response_format={"type": "json_object"},
        max_tokens=800,
        temperature=0.7,
    )
    return json.loads(completion.choices[0].message.content)


def _generate_image(client, prompt):
    """Generate a finished-product image, returned as a data URL (or None)."""
    result = client.images.generate(
        model=IMAGE_MODEL,
        prompt=prompt,
        size=IMAGE_SIZE,
        n=1,
    )
    item = result.data[0]
    b64 = getattr(item, "b64_json", None)
    if b64:
        return "data:image/png;base64," + b64
    # Some models/config return a URL instead of base64.
    return getattr(item, "url", None)


# ---- Page routes ------------------------------------------------------------
@app.context_processor
def inject_globals():
    return {"current_year": datetime.utcnow().year}


@app.route("/", methods=["GET"])
def home():
    """Landing page: hero + upload/scan studio."""
    return render_template("index.html", active_page="home")


@app.route("/about", methods=["GET"])
def about():
    """About us page."""
    return render_template("about.html", active_page="about")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    """Contact page with a simple message form."""
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        # In a school project we simply acknowledge; wire up email/storage later.
        app.logger.info(
            "Contact message from %s <%s>",
            name,
            request.form.get("email"),
        )
        return render_template(
            "contact.html", active_page="contact", sent=True, name=name
        )
    return render_template("contact.html", active_page="contact", sent=False)


@app.route("/health", methods=["GET"])
def health_check():
    """Basic health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "remake-portal",
        "ai_configured": bool(OPENAI_API_KEY),
    }, 200


# ---- AI endpoint ------------------------------------------------------------
@app.route("/api/generate", methods=["POST"])
def api_generate():
    """Accept uploaded waste photo(s), analyze them and generate a product."""
    uploads = request.files.getlist("images")
    uploads = [f for f in uploads if f and f.filename]
    if not uploads:
        return jsonify({"error": "Please upload at least one photo."}), 400
    if len(uploads) > MAX_IMAGES:
        return jsonify({"error": "Please upload at most %d photos." % MAX_IMAGES}), 400

    images = []
    for f in uploads:
        raw = f.read()
        if not raw:
            continue
        mime = f.mimetype or "image/jpeg"
        if mime not in ALLOWED_MIME:
            return (
                jsonify({"error": "Unsupported image type: %s" % mime}),
                400,
            )
        images.append((mime, raw))

    if not images:
        return jsonify({"error": "The uploaded file(s) were empty."}), 400

    note = (request.form.get("note") or "").strip()[:300]

    try:
        client = _client()
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503

    try:
        analysis = _analyze_images(client, images, note)
    except Exception as exc:  # noqa: BLE001 - surface a friendly message
        app.logger.exception("Vision analysis failed")
        return (
            jsonify({"error": "We couldn't read that image. Please try another photo."}),
            502,
        )

    # Generate the product image from the model's suggested prompt.
    image_data_url = None
    image_prompt = analysis.get("image_prompt") or (
        "A photorealistic studio photo of %s made from upcycled %s, neutral background"
        % (analysis.get("product_name", "a product"), analysis.get("material", "waste"))
    )
    try:
        image_data_url = _generate_image(client, image_prompt)
    except Exception:  # noqa: BLE001 - the idea is still useful without an image
        app.logger.exception("Image generation failed")

    return jsonify(
        {
            "material": analysis.get("material"),
            "product_name": analysis.get("product_name"),
            "description": analysis.get("description"),
            "tools": analysis.get("tools", []),
            "steps": analysis.get("steps", []),
            "effort": analysis.get("effort"),
            "time": analysis.get("time"),
            "impact": analysis.get("impact"),
            "image": image_data_url,
        }
    )


if __name__ == "__main__":
    # Development server configuration
    port = int(os.environ.get("PORT", 8080))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "t")
    app.run(host="0.0.0.0", port=port, debug=debug)
