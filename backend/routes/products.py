"""
Product routes — CRUD-style access to the product catalog.

Provides read-only endpoints:
  GET /api/products            — paginated product listing
  GET /api/products/categories — unique category list
  GET /api/products/<id>       — single product detail
"""

from flask import Blueprint, jsonify, request

from services.search_service import get_all_products, get_categories, get_product_by_id

bp = Blueprint("products", __name__, url_prefix="/api")


@bp.route("/products", methods=["GET"])
def list_products():
    """
    List products with optional pagination and category filter.

    Query params:
      page     — page number (default: 1)
      per_page — items per page (default: 20, max: 100)
      category — filter by category name
    """
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        per_page = max(1, min(int(request.args.get("per_page", 20)), 100))
    except (ValueError, TypeError):
        per_page = 20

    category = request.args.get("category")

    result = get_all_products(page=page, per_page=per_page, category=category)
    return jsonify(result), 200


@bp.route("/products/categories", methods=["GET"])
def list_categories():
    """Return a sorted list of unique product categories."""
    categories = get_categories()
    return jsonify({"categories": categories}), 200


@bp.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id: int):
    """Return a single product by its ID."""
    product = get_product_by_id(product_id)
    if product is None:
        return jsonify({"error": "Product not found."}), 404
    return jsonify(product), 200
