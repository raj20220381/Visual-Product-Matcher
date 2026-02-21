"""
Upload routes — handle image file uploads and URL downloads.

Provides two endpoints:
  POST /api/upload     — multipart file upload
  POST /api/upload-url — download image from a remote URL
"""

import logging
import os
import uuid
from io import BytesIO
from pathlib import Path

import requests
from flask import Blueprint, current_app, jsonify, request, send_from_directory
from PIL import Image
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)
bp = Blueprint("upload", __name__, url_prefix="/api")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_URL_DOWNLOAD_SIZE = 10 * 1024 * 1024  # 10MB
URL_DOWNLOAD_TIMEOUT = 15  # seconds


def _allowed_file(filename: str) -> bool:
    """Check if file extension is in the allow-list."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _ensure_upload_dir() -> Path:
    """Create the upload directory if it doesn't exist."""
    upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def _save_image(image: Image.Image, original_name: str) -> str:
    """Save a PIL Image to the uploads directory, returning the filename."""
    upload_dir = _ensure_upload_dir()

    # Generate unique filename to prevent collisions
    ext = Path(original_name).suffix.lower() or ".jpg"
    if ext not in {f".{e}" for e in ALLOWED_EXTENSIONS}:
        ext = ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"

    filepath = upload_dir / filename
    image.save(filepath)
    logger.info("Saved uploaded image to %s", filepath)

    return filename


@bp.route("/upload", methods=["POST"])
def upload_file():
    """
    Upload an image file via multipart/form-data.

    Expects a file field named `image`.
    Returns the saved filename and a preview URL.
    """
    if "image" not in request.files:
        return jsonify({"error": "No image file provided. Use field name 'image'."}), 400

    file = request.files["image"]
    if file.filename == "" or file.filename is None:
        return jsonify({"error": "No file selected."}), 400

    if not _allowed_file(file.filename):
        return jsonify({
            "error": f"Invalid file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        }), 400

    try:
        image = Image.open(file.stream)
        image.verify()  # Validate it's a real image
        file.stream.seek(0)
        image = Image.open(file.stream)

        filename = _save_image(image, file.filename)
        return jsonify({
            "filename": filename,
            "preview_url": f"/api/uploads/{filename}",
            "message": "Image uploaded successfully.",
        }), 200

    except Exception as e:
        logger.error("Upload failed: %s", e)
        return jsonify({"error": "Failed to process uploaded image."}), 400


@bp.route("/upload-url", methods=["POST"])
def upload_from_url():
    """
    Download an image from a URL and save it locally.

    Expects JSON body: { "url": "https://..." }
    """
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "Missing 'url' field in request body."}), 400

    if not url.startswith(("http://", "https://")):
        return jsonify({"error": "Invalid URL. Must start with http:// or https://"}), 400

    try:
        response = requests.get(
            url,
            timeout=URL_DOWNLOAD_TIMEOUT,
            stream=True,
            headers={"User-Agent": "VisualProductMatcher/1.0"},
        )
        response.raise_for_status()

        # Validate content type
        content_type = response.headers.get("Content-Type", "")
        if not content_type.startswith("image/"):
            return jsonify({"error": "URL does not point to a valid image."}), 400

        # Validate size
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_URL_DOWNLOAD_SIZE:
            return jsonify({"error": "Image exceeds maximum size of 10MB."}), 400

        # Download with size limit
        chunks = []
        downloaded = 0
        for chunk in response.iter_content(chunk_size=8192):
            downloaded += len(chunk)
            if downloaded > MAX_URL_DOWNLOAD_SIZE:
                return jsonify({"error": "Image exceeds maximum size of 10MB."}), 400
            chunks.append(chunk)

        image_bytes = b"".join(chunks)
        image = Image.open(BytesIO(image_bytes))

        # Derive a name from the URL
        url_path = url.split("?")[0].split("#")[0]
        original_name = Path(url_path).name or "downloaded.jpg"

        filename = _save_image(image, original_name)
        return jsonify({
            "filename": filename,
            "preview_url": f"/api/uploads/{filename}",
            "message": "Image downloaded and saved successfully.",
        }), 200

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out while downloading image."}), 408
    except requests.exceptions.RequestException as e:
        logger.error("URL download failed: %s", e)
        return jsonify({"error": "Failed to download image from URL."}), 400
    except Exception as e:
        logger.error("URL upload processing failed: %s", e)
        return jsonify({"error": "Failed to process downloaded image."}), 400


@bp.route("/uploads/<filename>", methods=["GET"])
def serve_upload(filename: str):
    """Serve uploaded images for preview."""
    filename = secure_filename(filename)
    upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
    if not (upload_dir / filename).exists():
        return jsonify({"error": "File not found."}), 404
    return send_from_directory(str(upload_dir), filename)
