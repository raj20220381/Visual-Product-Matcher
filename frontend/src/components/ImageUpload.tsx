import React, {
  useState,
  useRef,
  useCallback,
  type DragEvent,
  type ChangeEvent,
} from "react";

interface ImageUploadProps {
  onFileSelected: (file: File) => void;
  onUrlSubmitted: (url: string) => void;
  isLoading: boolean;
  previewUrl: string | null;
  previewName: string | null;
  onClear: () => void;
}

export default function ImageUpload({
  onFileSelected,
  onUrlSubmitted,
  isLoading,
  previewUrl,
  previewName,
  onClear,
}: ImageUploadProps) {
  const [activeTab, setActiveTab] = useState<"file" | "url">("file");
  const [isDragActive, setIsDragActive] = useState(false);
  const [urlValue, setUrlValue] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── Drag & Drop handlers ─────────────────────────────────────
  const handleDragEnter = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  }, []);

  const handleDragOver = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragActive(false);

      const files = e.dataTransfer.files;
      if (files.length > 0 && files[0].type.startsWith("image/")) {
        onFileSelected(files[0]);
      }
    },
    [onFileSelected],
  );

  // ── File input handler ───────────────────────────────────────
  const handleFileChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        onFileSelected(files[0]);
      }
    },
    [onFileSelected],
  );

  // ── URL submit handler ───────────────────────────────────────
  const handleUrlSubmit = useCallback(() => {
    const trimmed = urlValue.trim();
    if (
      trimmed &&
      (trimmed.startsWith("http://") || trimmed.startsWith("https://"))
    ) {
      onUrlSubmitted(trimmed);
    }
  }, [urlValue, onUrlSubmitted]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") handleUrlSubmit();
    },
    [handleUrlSubmit],
  );

  return (
    <div className="upload-section animate-fade-in">
      {/* Tabs */}
      <div className="upload-tabs">
        <button
          className={`upload-tab ${activeTab === "file" ? "upload-tab--active" : ""}`}
          onClick={() => setActiveTab("file")}
        >
          📁 Upload File
        </button>
        <button
          className={`upload-tab ${activeTab === "url" ? "upload-tab--active" : ""}`}
          onClick={() => setActiveTab("url")}
        >
          🔗 Image URL
        </button>
      </div>

      {/* File Upload Tab */}
      {activeTab === "file" && (
        <div
          className={`dropzone ${isDragActive ? "dropzone--active" : ""}`}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
          aria-label="Upload image"
        >
          <div className="dropzone__icon">📸</div>
          <p className="dropzone__text">
            Drag & drop an image here, or <strong>click to browse</strong>
          </p>
          <p className="dropzone__hint">
            Supports JPEG, PNG, WebP, GIF — Max 10MB
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            style={{ display: "none" }}
            aria-hidden="true"
          />
        </div>
      )}

      {/* URL Input Tab */}
      {activeTab === "url" && (
        <div className="url-input-wrapper">
          <input
            className="url-input"
            type="url"
            placeholder="https://example.com/product-image.jpg"
            value={urlValue}
            onChange={(e) => setUrlValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
          />
          <button
            className="btn"
            onClick={handleUrlSubmit}
            disabled={isLoading || !urlValue.trim()}
          >
            {isLoading ? <span className="spinner" /> : "Search"}
          </button>
        </div>
      )}

      {/* Preview Card */}
      {previewUrl && (
        <div className="preview-card">
          <div className="preview-card__image-wrap">
            <img
              className="preview-card__image"
              src={previewUrl}
              alt="Uploaded preview"
            />
          </div>
          <div className="preview-card__footer">
            <span className="preview-card__filename">
              {previewName || "Uploaded image"}
            </span>
            <div className="preview-card__actions">
              <button
                className="btn btn--secondary"
                onClick={onClear}
                style={{ padding: "8px 16px", fontSize: "0.8rem" }}
              >
                ✕ Clear
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
