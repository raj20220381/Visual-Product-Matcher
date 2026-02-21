"""
Embedding service — generates CLIP image embeddings using ONNX Runtime.

Uses the combined CLIP ViT-B/32 ONNX model from HuggingFace
(Xenova/clip-vit-base-patch32). The model requires three inputs:
  - pixel_values: preprocessed image tensor (NCHW)
  - input_ids: tokenized text (dummy for image-only embedding)
  - attention_mask: text attention mask (dummy for image-only embedding)

Outputs include `image_embeds` (512-dim) which we extract and normalize.

Zero PyTorch dependency — uses ONNX Runtime + Pillow + NumPy only.
"""

import logging
import os
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# ── Constants ───────────────────────────────────────────────────────────────
ONNX_REPO = "Xenova/clip-vit-base-patch32"
ONNX_FILENAME = "onnx/model.onnx"
CACHE_DIR = Path(os.getenv("MODEL_CACHE_DIR", Path.home() / ".cache" / "clip_onnx"))
EMBEDDING_DIM = 512
IMAGE_SIZE = 224  # CLIP expects 224×224

# ImageNet normalization constants (used by CLIP)
IMAGENET_MEAN = np.array([0.48145466, 0.4578275, 0.40821073], dtype=np.float32)
IMAGENET_STD = np.array([0.26862954, 0.26130258, 0.27577711], dtype=np.float32)

# Dummy text inputs — CLIP ONNX needs text inputs even for image-only mode.
# We use a single empty-ish token sequence. These values correspond to
# the CLIP tokenizer's BOS (49406) and EOS (49407) tokens with padding.
DUMMY_INPUT_IDS = np.array([[49406, 49407] + [0] * 75], dtype=np.int64)  # shape (1, 77)
DUMMY_ATTENTION_MASK = np.array([[1, 1] + [0] * 75], dtype=np.int64)     # shape (1, 77)

# Module-level singleton
_session = None


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""


def _download_model() -> Path:
    """Download the CLIP ONNX model from HuggingFace if not cached."""
    # Check if already downloaded
    model_path = CACHE_DIR / ONNX_FILENAME
    if model_path.exists():
        logger.info("ONNX model found in cache: %s", model_path)
        return model_path

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    try:
        from huggingface_hub import hf_hub_download

        downloaded = hf_hub_download(
            repo_id=ONNX_REPO,
            filename=ONNX_FILENAME,
            cache_dir=str(CACHE_DIR),
            local_dir=str(CACHE_DIR),
        )
        logger.info("Downloaded ONNX model to: %s", downloaded)
        return Path(downloaded)
    except Exception as e:
        logger.error("Failed to download ONNX model: %s", e)
        raise EmbeddingError(f"Cannot download CLIP model: {e}") from e


def _get_session():
    """Lazily load the ONNX Runtime inference session (singleton)."""
    global _session
    if _session is None:
        logger.info("Initializing ONNX Runtime session for CLIP...")
        try:
            import onnxruntime as ort

            model_path = _download_model()
            _session = ort.InferenceSession(
                str(model_path),
                providers=["CPUExecutionProvider"],
            )

            input_names = [i.name for i in _session.get_inputs()]
            output_names = [o.name for o in _session.get_outputs()]
            logger.info("ONNX session ready. Inputs: %s, Outputs: %s", input_names, output_names)

        except Exception as e:
            logger.error("Failed to initialize ONNX session: %s", e)
            raise EmbeddingError(f"Model initialization failed: {e}") from e
    return _session


def _preprocess_image(image: Image.Image) -> np.ndarray:
    """
    Preprocess a PIL image for CLIP inference.

    Pipeline: RGB → resize (shortest side) → center crop 224×224 →
              float32 [0,1] → ImageNet normalize → CHW → NCHW batch
    """
    if image.mode != "RGB":
        image = image.convert("RGB")

    # Resize shortest side to IMAGE_SIZE, preserving aspect ratio
    w, h = image.size
    scale = IMAGE_SIZE / min(w, h)
    new_w, new_h = int(w * scale), int(h * scale)
    image = image.resize((new_w, new_h), Image.BICUBIC)

    # Center crop to IMAGE_SIZE × IMAGE_SIZE
    left = (new_w - IMAGE_SIZE) // 2
    top = (new_h - IMAGE_SIZE) // 2
    image = image.crop((left, top, left + IMAGE_SIZE, top + IMAGE_SIZE))

    # To numpy float32 [0, 1]
    pixel_values = np.array(image, dtype=np.float32) / 255.0

    # ImageNet normalize
    pixel_values = (pixel_values - IMAGENET_MEAN) / IMAGENET_STD

    # HWC → CHW → NCHW
    pixel_values = pixel_values.transpose(2, 0, 1)
    pixel_values = np.expand_dims(pixel_values, axis=0)

    return pixel_values


def generate_embedding(image: Image.Image) -> np.ndarray:
    """
    Generate a normalized 512-dim CLIP embedding for a PIL Image.

    Args:
        image: A PIL Image object (any mode — will be converted to RGB).

    Returns:
        A 1-D NumPy array of shape (512,) with L2-normalized float32 values.

    Raises:
        EmbeddingError: If the image cannot be processed.
    """
    try:
        session = _get_session()
        pixel_values = _preprocess_image(image)

        # The combined CLIP ONNX model requires all three inputs
        feeds = {
            "pixel_values": pixel_values,
            "input_ids": DUMMY_INPUT_IDS,
            "attention_mask": DUMMY_ATTENTION_MASK,
        }

        # Run inference — request only image_embeds output
        output_names = [o.name for o in session.get_outputs()]
        outputs = session.run(output_names, feeds)

        # Find the image_embeds output (index 2 in: logits_per_image, logits_per_text, text_embeds, image_embeds)
        output_dict = dict(zip(output_names, outputs))
        if "image_embeds" in output_dict:
            embedding = output_dict["image_embeds"]
        else:
            # Fallback: last output is typically image_embeds
            embedding = outputs[-1]

        vector = np.array(embedding).flatten().astype(np.float32)

        # Ensure correct dimensionality
        if len(vector) > EMBEDDING_DIM:
            vector = vector[:EMBEDDING_DIM]

        # L2-normalize for cosine similarity
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector

    except EmbeddingError:
        raise
    except Exception as e:
        logger.error("Embedding generation failed: %s", e)
        raise EmbeddingError(f"Failed to process image: {e}") from e


def generate_embedding_from_bytes(image_bytes: bytes) -> np.ndarray:
    """
    Convenience wrapper — generate embedding from raw image bytes.

    Args:
        image_bytes: Raw bytes of a JPEG/PNG/WebP image.

    Returns:
        A 1-D NumPy array of shape (512,).
    """
    try:
        image = Image.open(BytesIO(image_bytes))
        return generate_embedding(image)
    except Exception as e:
        raise EmbeddingError(f"Invalid image data: {e}") from e
