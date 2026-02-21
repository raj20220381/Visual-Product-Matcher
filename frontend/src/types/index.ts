/**
 * Shared TypeScript type definitions for the Visual Product Matcher.
 */

/** A single product in the catalog. */
export interface Product {
  id: number;
  name: string;
  category: string;
  brand: string;
  price: number;
  description: string;
  image: string;
  thumbnail: string;
  rating: number;
}

/** A search result — a Product augmented with a similarity score. */
export interface SearchResult extends Product {
  similarity_score: number;
}

/** Response shape from the /api/search endpoints. */
export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: {
    type: "file" | "url";
    filename?: string;
    url?: string;
  };
}

/** Response shape from the /api/products endpoint. */
export interface ProductListResponse {
  products: Product[];
  total: number;
  page: number;
  per_page: number;
}

/** Generic API error shape. */
export interface ApiError {
  error: string;
  detail?: string;
}

/** Upload response from the backend. */
export interface UploadResponse {
  filename: string;
  preview_url: string;
  message: string;
}
