/**
 * API client for the Visual Product Matcher backend.
 *
 * Uses native fetch with typed wrappers. In development, requests are
 * proxied through Vite to the Flask backend (see vite.config.ts).
 * In production, the API_BASE_URL env var points to the deployed backend.
 */

import type {
  SearchResponse,
  UploadResponse,
  ProductListResponse,
} from "../types";

const API_BASE = import.meta.env.VITE_API_URL || "/api";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response
      .json()
      .catch(() => ({ error: "Unknown error" }));
    throw new ApiError(
      body.error || `HTTP ${response.status}`,
      response.status,
    );
  }
  return response.json() as Promise<T>;
}

/** Search by uploading an image file. */
export async function searchByFile(
  file: File,
  options: { limit?: number; minScore?: number } = {},
): Promise<SearchResponse> {
  const formData = new FormData();
  formData.append("image", file);

  const params = new URLSearchParams();
  if (options.limit) params.set("limit", String(options.limit));
  if (options.minScore) params.set("min_score", String(options.minScore));

  const qs = params.toString() ? `?${params.toString()}` : "";
  const response = await fetch(`${API_BASE}/search${qs}`, {
    method: "POST",
    body: formData,
  });

  return handleResponse<SearchResponse>(response);
}

/** Search by providing an image URL. */
export async function searchByUrl(
  url: string,
  options: { limit?: number; minScore?: number } = {},
): Promise<SearchResponse> {
  const params = new URLSearchParams();
  if (options.limit) params.set("limit", String(options.limit));
  if (options.minScore) params.set("min_score", String(options.minScore));

  const qs = params.toString() ? `?${params.toString()}` : "";
  const response = await fetch(`${API_BASE}/search-url${qs}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });

  return handleResponse<SearchResponse>(response);
}

/** Upload an image file for preview. */
export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("image", file);

  const response = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });

  return handleResponse<UploadResponse>(response);
}

/** Fetch paginated product listing. */
export async function getProducts(
  page = 1,
  perPage = 20,
  category?: string,
): Promise<ProductListResponse> {
  const params = new URLSearchParams({
    page: String(page),
    per_page: String(perPage),
  });
  if (category) params.set("category", category);

  const response = await fetch(`${API_BASE}/products?${params.toString()}`);
  return handleResponse<ProductListResponse>(response);
}

/** Fetch list of product categories. */
export async function getCategories(): Promise<string[]> {
  const response = await fetch(`${API_BASE}/products/categories`);
  const data = await handleResponse<{ categories: string[] }>(response);
  return data.categories;
}
