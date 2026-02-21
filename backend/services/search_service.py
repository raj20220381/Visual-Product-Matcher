"""
Search service — finds visually similar products using cosine similarity.

Loads pre-computed CLIP embeddings from the product catalog at startup,
then performs fast vectorized similarity search using NumPy.
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)

# Module-level product data — loaded once at startup
_products: list[dict[str, Any]] = []
_embeddings_matrix: Optional[np.ndarray] = None


class SearchError(Exception):
    """Raised when search operations fail."""


def load_catalog(catalog_path: Path) -> None:
    """
    Load product catalog and pre-computed embeddings from JSON.

    Must be called once at application startup. Products without valid
    embeddings are silently skipped with a warning.

    Args:
        catalog_path: Path to the products.json file.

    Raises:
        SearchError: If the catalog file cannot be loaded.
    """
    global _products, _embeddings_matrix

    if not catalog_path.exists():
        logger.warning("Product catalog not found at %s", catalog_path)
        _products = []
        _embeddings_matrix = None
        return

    try:
        with open(catalog_path, "r") as f:
            raw_products = json.load(f)

        valid_products = []
        valid_embeddings = []

        for product in raw_products:
            embedding = product.get("embedding")
            if embedding and isinstance(embedding, list) and len(embedding) > 0:
                valid_products.append({
                    "id": product["id"],
                    "name": product["name"],
                    "category": product.get("category", "unknown"),
                    "brand": product.get("brand", ""),
                    "price": product.get("price", 0),
                    "description": product.get("description", ""),
                    "image": product.get("image", ""),
                    "thumbnail": product.get("thumbnail", ""),
                })
                valid_embeddings.append(np.array(embedding, dtype=np.float32))
            else:
                logger.warning("Skipping product %s — missing embedding", product.get("id"))

        _products = valid_products

        if valid_embeddings:
            _embeddings_matrix = np.stack(valid_embeddings)
            # Normalize rows for cosine similarity (dot product of unit vectors)
            norms = np.linalg.norm(_embeddings_matrix, axis=1, keepdims=True)
            norms[norms == 0] = 1  # Prevent division by zero
            _embeddings_matrix = _embeddings_matrix / norms

        logger.info("Loaded %d products with embeddings from catalog.", len(_products))

    except json.JSONDecodeError as e:
        raise SearchError(f"Invalid JSON in catalog file: {e}") from e
    except Exception as e:
        raise SearchError(f"Failed to load catalog: {e}") from e


def search_similar(
    query_embedding: np.ndarray,
    limit: int = 20,
    min_score: float = 0.0,
) -> list[dict[str, Any]]:
    """
    Find products most similar to the query image.

    Uses cosine similarity (dot product of L2-normalized vectors) for
    fast, vectorized comparison against the entire catalog.

    Args:
        query_embedding: A 1-D normalized embedding vector from CLIP.
        limit: Maximum number of results to return.
        min_score: Minimum similarity score threshold (0.0 to 1.0).

    Returns:
        A list of product dicts, each augmented with a `similarity_score` field,
        sorted by descending similarity.
    """
    if _embeddings_matrix is None or len(_products) == 0:
        logger.warning("Search called with empty catalog.")
        return []

    # Normalize query vector
    query = query_embedding.flatten().astype(np.float32)
    norm = np.linalg.norm(query)
    if norm > 0:
        query = query / norm

    # Cosine similarity = dot product of normalized vectors
    similarities = _embeddings_matrix @ query

    # Convert from [-1, 1] to [0, 1] for UX-friendly percentage display
    scores = (similarities + 1) / 2

    # Build results list, filtered by min_score
    results = []
    for idx in np.argsort(-scores):
        score = float(scores[idx])
        if score < min_score:
            break
        results.append({
            **_products[idx],
            "similarity_score": round(score, 4),
        })
        if len(results) >= limit:
            break

    return results


def get_all_products(
    page: int = 1,
    per_page: int = 20,
    category: Optional[str] = None,
) -> dict[str, Any]:
    """
    Retrieve paginated product listing.

    Args:
        page: Page number (1-indexed).
        per_page: Products per page.
        category: Optional category filter.

    Returns:
        Dict with `products`, `total`, `page`, `per_page`, and `categories` keys.
    """
    filtered = _products
    if category:
        filtered = [p for p in _products if p["category"].lower() == category.lower()]

    total = len(filtered)
    start = (page - 1) * per_page
    end = start + per_page
    page_products = filtered[start:end]

    return {
        "products": page_products,
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def get_product_by_id(product_id: int) -> Optional[dict[str, Any]]:
    """Return a single product by ID, or None if not found."""
    for product in _products:
        if product["id"] == product_id:
            return product
    return None


def get_categories() -> list[str]:
    """Return sorted list of unique product categories."""
    return sorted(set(p["category"] for p in _products))
