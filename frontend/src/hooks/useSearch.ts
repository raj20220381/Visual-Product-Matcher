/**
 * useSearch — custom hook encapsulating the visual similarity search flow.
 *
 * Manages loading state, error state, results, and filtering.
 * Supports both file upload and URL-based search.
 */

import { useState, useCallback, useMemo } from "react";
import type { SearchResult, SearchResponse } from "../types";
import { searchByFile, searchByUrl } from "../api/client";

interface UseSearchReturn {
  results: SearchResult[];
  filteredResults: SearchResult[];
  isLoading: boolean;
  error: string | null;
  minScore: number;
  setMinScore: (score: number) => void;
  searchFile: (file: File) => Promise<void>;
  searchUrl: (url: string) => Promise<void>;
  clearResults: () => void;
  queryInfo: SearchResponse["query"] | null;
}

export function useSearch(): UseSearchReturn {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [minScore, setMinScore] = useState(0);
  const [queryInfo, setQueryInfo] = useState<SearchResponse["query"] | null>(
    null,
  );

  const filteredResults = useMemo(
    () => results.filter((r) => r.similarity_score >= minScore),
    [results, minScore],
  );

  const searchFile = useCallback(async (file: File) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await searchByFile(file, { limit: 60 });
      setResults(data.results);
      setQueryInfo(data.query);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Search failed";
      setError(message);
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const searchUrl = useCallback(async (url: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await searchByUrl(url, { limit: 60 });
      setResults(data.results);
      setQueryInfo(data.query);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Search failed";
      setError(message);
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearResults = useCallback(() => {
    setResults([]);
    setError(null);
    setQueryInfo(null);
    setMinScore(0);
  }, []);

  return {
    results,
    filteredResults,
    isLoading,
    error,
    minScore,
    setMinScore,
    searchFile,
    searchUrl,
    clearResults,
    queryInfo,
  };
}
