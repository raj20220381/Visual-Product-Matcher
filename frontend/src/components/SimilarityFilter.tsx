import React from "react";

interface SimilarityFilterProps {
  total: number;
  filtered: number;
  minScore: number;
  onMinScoreChange: (val: number) => void;
}

export default function SimilarityFilter({
  total,
  filtered,
  minScore,
  onMinScoreChange,
}: SimilarityFilterProps) {
  return (
    <div className="filter-bar animate-fade-in">
      <div className="filter-bar__info">
        <strong>{filtered}</strong> of {total} products match
      </div>
      <div className="filter-bar__slider-group">
        <span className="filter-bar__label">Min similarity</span>
        <input
          className="filter-bar__slider"
          type="range"
          min="0"
          max="1"
          step="0.01"
          value={minScore}
          onChange={(e) => onMinScoreChange(parseFloat(e.target.value))}
        />
        <span className="filter-bar__value">{Math.round(minScore * 100)}%</span>
      </div>
    </div>
  );
}
