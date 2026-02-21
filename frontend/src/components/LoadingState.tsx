import React from "react";

interface LoadingStateProps {
  count?: number;
}

export default function LoadingState({ count = 8 }: LoadingStateProps) {
  return (
    <div className="results__grid">
      {Array.from({ length: count }, (_, i) => (
        <div
          key={i}
          className="skeleton"
          style={{ animationDelay: `${i * 0.05}s` }}
        >
          <div className="skeleton__image" />
          <div className="skeleton__body">
            <div className="skeleton__line skeleton__line--xs" />
            <div className="skeleton__line" />
            <div className="skeleton__line skeleton__line--short" />
          </div>
        </div>
      ))}
    </div>
  );
}
