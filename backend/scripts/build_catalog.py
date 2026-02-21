#!/usr/bin/env python3
"""
Build Product Catalog — one-time data pipeline script.

Fetches 50+ products from the DummyJSON public API, downloads their images,
computes CLIP embeddings using our custom ONNX-based embedding service,
and saves the complete catalog with embeddings to data/products.json.

Usage:
  cd backend
  python scripts/build_catalog.py
"""

import json
import logging
import sys
import time
from io import BytesIO
from pathlib import Path

import numpy as np
import requests
from PIL import Image

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

DUMMYJSON_API = "https://dummyjson.com/products"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_FILE = DATA_DIR / "products.json"
BATCH_SIZE = 30  # DummyJSON returns up to 30 per page


def fetch_products(total: int = 60) -> list[dict]:
    """Fetch products from DummyJSON API with pagination."""
    products = []
    skip = 0

    while len(products) < total:
        url = f"{DUMMYJSON_API}?limit={BATCH_SIZE}&skip={skip}"
        logger.info("Fetching products from %s", url)

        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        batch = data.get("products", [])
        if not batch:
            break

        products.extend(batch)
        skip += BATCH_SIZE
        time.sleep(0.5)  # Be respectful to the API

    logger.info("Fetched %d products total.", len(products))
    return products[:total]


def download_image(url: str) -> Image.Image | None:
    """Download an image from URL with error handling."""
    try:
        response = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "VisualProductMatcher/1.0"},
        )
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        if image.mode != "RGB":
            image = image.convert("RGB")
        return image
    except Exception as e:
        logger.warning("Failed to download %s: %s", url, e)
        return None


def build_catalog():
    """Main pipeline: fetch → embed → save."""
    logger.info("=" * 60)
    logger.info("Building product catalog with CLIP embeddings")
    logger.info("=" * 60)

    # Step 1: Fetch products
    raw_products = fetch_products(total=60)

    # Step 2: Import embedding service (triggers model download on first use)
    from services.embedding_service import generate_embedding
    logger.info("Embedding service loaded.")

    # Step 3: Process each product
    catalog = []
    failed = 0

    for i, product in enumerate(raw_products):
        product_id = product["id"]
        name = product.get("title", f"Product {product_id}")
        image_url = product.get("thumbnail", "")

        if not image_url:
            # Fallback to first image in images array
            images = product.get("images", [])
            image_url = images[0] if images else ""

        logger.info("[%d/%d] Processing: %s", i + 1, len(raw_products), name)

        if not image_url:
            logger.warning("  → Skipped (no image URL)")
            failed += 1
            continue

        # Download image
        image = download_image(image_url)
        if image is None:
            failed += 1
            continue

        # Compute embedding
        try:
            vector = generate_embedding(image)

            catalog.append({
                "id": product_id,
                "name": name,
                "category": product.get("category", "unknown"),
                "brand": product.get("brand", "Unknown"),
                "price": product.get("price", 0),
                "description": product.get("description", ""),
                "image": image_url,
                "thumbnail": product.get("thumbnail", image_url),
                "rating": product.get("rating", 0),
                "embedding": vector.tolist(),
            })
            logger.info("  → Embedded (%d dims)", len(vector))

        except Exception as e:
            logger.warning("  → Embedding failed: %s", e)
            failed += 1

        # Small delay to avoid overwhelming resources
        time.sleep(0.1)

    # Step 4: Save catalog
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(catalog, f, indent=2)

    logger.info("=" * 60)
    logger.info("Catalog built successfully!")
    logger.info("  Products saved: %d", len(catalog))
    logger.info("  Failed: %d", failed)
    logger.info("  Output: %s", OUTPUT_FILE)
    logger.info("  File size: %.1f KB", OUTPUT_FILE.stat().st_size / 1024)
    logger.info("=" * 60)


if __name__ == "__main__":
    build_catalog()
