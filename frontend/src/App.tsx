import { useState, useCallback } from "react";
import Header from "./components/Header";
import ImageUpload from "./components/ImageUpload";
import ProductCard from "./components/ProductCard";
import SimilarityFilter from "./components/SimilarityFilter";
import LoadingState from "./components/LoadingState";
import { useSearch } from "./hooks/useSearch";

export default function App() {
  const {
    filteredResults,
    results,
    isLoading,
    error,
    minScore,
    setMinScore,
    searchFile,
    searchUrl,
    clearResults,
  } = useSearch();

  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewName, setPreviewName] = useState<string | null>(null);

  // ── File upload → search ─────────────────────────────────────
  const handleFileSelected = useCallback(
    (file: File) => {
      // Create a local preview URL
      const objectUrl = URL.createObjectURL(file);
      setPreviewUrl(objectUrl);
      setPreviewName(file.name);
      searchFile(file);
    },
    [searchFile],
  );

  // ── URL submit → search ──────────────────────────────────────
  const handleUrlSubmitted = useCallback(
    (url: string) => {
      setPreviewUrl(url);
      setPreviewName(url.split("/").pop() || "Image URL");
      searchUrl(url);
    },
    [searchUrl],
  );

  // ── Clear everything ─────────────────────────────────────────
  const handleClear = useCallback(() => {
    if (previewUrl && previewUrl.startsWith("blob:")) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
    setPreviewName(null);
    clearResults();
  }, [previewUrl, clearResults]);

  const hasResults = results.length > 0;

  return (
    <>
      <Header />

      {/* Hero */}
      <section className="hero">
        <h1 className="hero__title">
          Find <span>Visually Similar</span> Products
        </h1>
        <p className="hero__desc">
          Upload a product image and our CLIP AI model will find the most
          visually similar items from our catalog instantly.
        </p>
      </section>

      {/* Upload Section */}
      <ImageUpload
        onFileSelected={handleFileSelected}
        onUrlSubmitted={handleUrlSubmitted}
        isLoading={isLoading}
        previewUrl={previewUrl}
        previewName={previewName}
        onClear={handleClear}
      />

      {/* Error Banner */}
      {error && (
        <div
          className="error-banner"
          style={{ maxWidth: 720, margin: "0 auto 24px", padding: "0 24px" }}
        >
          <div
            style={{
              maxWidth: 720,
              margin: "0 auto",
              width: "100%",
              padding: "16px 20px",
              borderRadius: "var(--radius-md)",
              background: "rgba(239, 68, 68, 0.1)",
              border: "1px solid rgba(239, 68, 68, 0.2)",
              color: "#fca5a5",
              fontSize: "0.9rem",
              display: "flex",
              alignItems: "center",
              gap: 10,
            }}
          >
            <span className="error-banner__icon">⚠️</span>
            {error}
          </div>
        </div>
      )}

      {/* Filter + Results */}
      {(hasResults || isLoading) && (
        <section className="results container">
          {hasResults && !isLoading && (
            <SimilarityFilter
              total={results.length}
              filtered={filteredResults.length}
              minScore={minScore}
              onMinScoreChange={setMinScore}
            />
          )}

          {isLoading ? (
            <LoadingState count={8} />
          ) : filteredResults.length > 0 ? (
            <div className="results__grid">
              {filteredResults.map((product, i) => (
                <ProductCard key={product.id} product={product} index={i} />
              ))}
            </div>
          ) : (
            <div className="state-message">
              <div className="state-message__icon">🔍</div>
              <h3 className="state-message__title">No matches found</h3>
              <p className="state-message__desc">
                Try lowering the minimum similarity threshold or upload a
                different image.
              </p>
            </div>
          )}
        </section>
      )}

      {/* Empty state — no search yet */}
      {!hasResults && !isLoading && !error && (
        <section className="state-message animate-fade-in">
          <div className="state-message__icon">✨</div>
          <h3 className="state-message__title">Ready to search</h3>
          <p className="state-message__desc">
            Upload a product image above to find visually similar items from our
            catalog of 60+ products across multiple categories.
          </p>
        </section>
      )}
    </>
  );
}
