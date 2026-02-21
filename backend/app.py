"""
Visual Product Matcher — Flask Application Factory.

Production-ready Flask app with:
  - CORS configuration
  - Global error handlers
  - Request logging middleware
  - Blueprint registration
  - Catalog loading at startup
"""

import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request

load_dotenv()

# Configure logging before anything else
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Application factory — creates and configures the Flask app."""
    from config import get_config

    config = get_config()

    app = Flask(__name__)
    app.config.from_object(config)

    # ── CORS ────────────────────────────────────────────────────────────
    from flask_cors import CORS

    CORS(app, origins=config.CORS_ORIGINS, supports_credentials=True)

    # ── Ensure upload directory exists ──────────────────────────────────
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    # ── Request logging middleware ──────────────────────────────────────
    @app.before_request
    def log_request():
        request._start_time = time.time()

    @app.after_request
    def log_response(response):
        duration = time.time() - getattr(request, "_start_time", time.time())
        logger.info(
            "%s %s %s %.3fs",
            request.method,
            request.path,
            response.status_code,
            duration,
        )
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    # ── Global error handlers ───────────────────────────────────────────
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request.", "detail": str(e)}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found."}), 404

    @app.errorhandler(413)
    def payload_too_large(e):
        return jsonify({"error": "File too large. Maximum size is 10MB."}), 413

    @app.errorhandler(500)
    def internal_error(e):
        logger.error("Internal server error: %s", e)
        return jsonify({"error": "Internal server error. Please try again later."}), 500

    # ── Health check ────────────────────────────────────────────────────
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "visual-product-matcher",
            "version": "1.0.0",
        }), 200

    # ── Register blueprints ─────────────────────────────────────────────
    from routes.upload import bp as upload_bp
    from routes.search import bp as search_bp
    from routes.products import bp as products_bp

    app.register_blueprint(upload_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(products_bp)

    # ── Load product catalog ────────────────────────────────────────────
    from services.search_service import load_catalog

    catalog_path = config.PRODUCTS_FILE
    try:
        load_catalog(catalog_path)
        logger.info("Product catalog loaded from %s", catalog_path)
    except Exception as e:
        logger.warning("Could not load product catalog: %s", e)

    logger.info("Visual Product Matcher API started (env=%s)", os.getenv("FLASK_ENV", "development"))
    return app


# ── Direct execution (development) ──────────────────────────────────────
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
