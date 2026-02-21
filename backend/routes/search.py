"""
Search routes — visual similarity search endpoints.

Provides two endpoints:
  POST /api/search     — search by uploaded file
  POST /api/search-url — search by image URL
"""

import logging
from io import BytesIO

import requests
from flask import Blueprint, jsonify, request
from PIL import Image

from services.embedding_service import EmbeddingError, generate_embedding
from services.search_service import search_similar

logger = logging.getLogger(__name__)
bp = Blueprint("search", __name__, url_prefix="/api")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
URL_DOWNLOAD_TIMEOUT = 15


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _parse_search_params() -> tuple[int, float]:
    """Extract and validate limit / min_score query parameters."""
    try:
        limit = int(request.args.get("limit", 20))
        limit = max(1, min(limit, 100))
    except (ValueError, TypeError):
        limit = 20

    try:
        min_score = float(request.args.get("min_score", 0.0))
        min_score = max(0.0, min(min_score, 1.0))
    except (ValueError, TypeError):
        min_score = 0.0

    return limit, min_score


@bp.route("/search", methods=["POST"])
def search_by_file():
    """
    Search for visually similar products by uploading an image file.

    Expects a multipart form with an `image` field.
    Returns a ranked list of similar products with similarity scores.
    """
    if "image" not in request.files:
        return jsonify({"error": "No image file provided. Use field name 'image'."}), 400

    file = request.files["image"]
    if file.filename == "" or file.filename is None:
        return jsonify({"error": "No file selected."}), 400

    if not _allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Allowed: png, jpg, jpeg, gif, webp"}), 400

    limit, min_score = _parse_search_params()

    try:
        image = Image.open(file.stream)
        embedding = generate_embedding(image)
        results = search_similar(embedding, limit=limit, min_score=min_score)

        return jsonify({
            "results": results,
            "total": len(results),
            "query": {"type": "file", "filename": file.filename},
        }), 200

    except EmbeddingError as e:
        logger.error("Embedding error during search: %s", e)
        return jsonify({"error": "Failed to analyze the uploaded image."}), 422
    except Exception as e:
        logger.error("Search failed: %s", e)
        return jsonify({"error": "Search failed. Please try again."}), 500


@bp.route("/search-url", methods=["POST"])
def search_by_url():
    """
    Search for visually similar products using an image URL.

    Expects JSON body: { "url": "https://..." }
    """
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "Missing 'url' field in request body."}), 400

    if not url.startswith(("http://", "https://")):
        return jsonify({"error": "Invalid URL format."}), 400

    limit, min_score = _parse_search_params()

    try:
        response = requests.get(
            url,
            timeout=URL_DOWNLOAD_TIMEOUT,
            headers={"User-Agent": "VisualProductMatcher/1.0"},
        )
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        if not content_type.startswith("image/"):
            return jsonify({"error": "URL does not point to a valid image."}), 400

        image = Image.open(BytesIO(response.content))
        embedding = generate_embedding(image)
        results = search_similar(embedding, limit=limit, min_score=min_score)

        return jsonify({
            "results": results,
            "total": len(results),
            "query": {"type": "url", "url": url},
        }), 200

    except requests.exceptions.Timeout:
        return jsonify({"error": "Timed out downloading image from URL."}), 408
    except requests.exceptions.RequestException as e:
        logger.error("URL download failed: %s", e)
        return jsonify({"error": "Failed to download image from URL."}), 400
    except EmbeddingError as e:
        logger.error("Embedding error during URL search: %s", e)
        return jsonify({"error": "Failed to analyze the image."}), 422
    except Exception as e:
        logger.error("URL search failed: %s", e)
        return jsonify({"error": "Search failed. Please try again."}), 500
