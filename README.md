# Visual Product Matcher 🔍

AI-powered visual similarity search — upload a product image and find visually similar items from a catalog of 60+ products using **CLIP (ViT-B/32)** embeddings.

![Visual Product Matcher](https://img.shields.io/badge/CLIP-ViT--B%2F32-blue) ![Python](https://img.shields.io/badge/Python-3.12-green) ![React](https://img.shields.io/badge/React-19-61DAFB) ![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6)

## Architecture

```
Frontend (Vite + React + TS)        Backend (Python / Flask)
┌──────────────────────┐            ┌──────────────────────────┐
│ Image Upload         │            │ Upload API               │
│ (Drag & Drop / URL)  │──HTTP/REST─▶ Embedding Service       │
│ Search Results       │◀───────────│ (CLIP ONNX Runtime)      │
│ + Similarity Filter  │            │ Cosine Similarity Search │
└──────────────────────┘            │ Product Catalog (JSON)   │
                                    └──────────────────────────┘
```

**Key Design Decisions:**

- **CLIP via ONNX Runtime** — No PyTorch dependency. ~350MB model, runs on CPU
- **Pre-computed embeddings** — Product embeddings stored in JSON, loaded at startup. Fast cosine similarity at query time
- **Service layer pattern** — Clean separation between routes, services, and data
- **DummyJSON API** — 60 real product images with metadata

## Tech Stack

| Layer    | Technologies                         |
| -------- | ------------------------------------ |
| Frontend | Vite, React 19, TypeScript           |
| Backend  | Python 3.12, Flask, Flask-CORS       |
| AI/ML    | CLIP ViT-B/32, ONNX Runtime, NumPy   |
| Styling  | Custom CSS, Glassmorphism, Dark Mode |

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- ~500MB disk space (for CLIP ONNX model, downloaded on first use)

### 1. Clone & Setup Backend

```bash
git clone <repo-url> && cd unthink-proj

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Build Product Catalog (first time only)

```bash
# Still inside backend/ with venv active
python scripts/build_catalog.py
```

This fetches 60 products from DummyJSON, downloads images, computes CLIP embeddings, and saves to `data/products.json`.

### 3. Start Backend

```bash
python app.py
# → Running on http://localhost:5000
```

### 4. Start Frontend

```bash
cd ../frontend
npm install
npm run dev
# → Running on http://localhost:5173
```

Open [http://localhost:5173](http://localhost:5173) and upload an image!

## API Reference

| Method | Endpoint                   | Description                    |
| ------ | -------------------------- | ------------------------------ |
| GET    | `/api/health`              | Health check                   |
| POST   | `/api/search`              | Search by uploaded file        |
| POST   | `/api/search-url`          | Search by image URL            |
| POST   | `/api/upload`              | Upload an image (multipart)    |
| POST   | `/api/upload-url`          | Download & save image from URL |
| GET    | `/api/products`            | List products (paginated)      |
| GET    | `/api/products/:id`        | Get single product             |
| GET    | `/api/products/categories` | List unique categories         |

### Example: Search by URL

```bash
curl -X POST http://localhost:5000/api/search-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://cdn.dummyjson.com/products/images/beauty/Essence%20Mascara%20Lash%20Princess/1.png"}'
```

## Approach (200 words)

This project implements a **visual product search engine** using OpenAI's CLIP model for semantic image understanding. CLIP maps images into a shared 512-dimensional embedding space where visually similar items cluster together. By pre-computing embeddings for all catalog products at build time and storing them alongside product metadata, we achieve zero ML compute for the catalog and sub-second search at query time.

The backend uses a **custom ONNX Runtime integration** (no PyTorch) to keep the deployment lightweight (~350MB). Images are preprocessed following CLIP's pipeline (resize → center-crop → ImageNet normalization) before being fed to the ONNX model. At search time, cosine similarity between the query embedding and all catalog embeddings is computed using NumPy's vectorized dot product, returning ranked results with similarity scores.

The frontend provides a polished dark-themed UI with drag & drop image upload, URL input, and real-time similarity filtering via a range slider. The design uses glassmorphism, smooth animations, and responsive layout.

The architecture follows a clean service layer pattern with separation of concerns: routes handle HTTP, services encapsulate business logic, and data is loaded once at startup. This makes the codebase testable, maintainable, and easy to extend with new features like text-based search.
