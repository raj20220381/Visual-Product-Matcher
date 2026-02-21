import React from "react";
import type { SearchResult } from "../types";

interface ProductCardProps {
  product: SearchResult;
  index: number;
}

function getScoreClass(score: number): string {
  if (score >= 0.75) return "product-card__score--high";
  if (score >= 0.55) return "product-card__score--medium";
  return "product-card__score--low";
}

export default function ProductCard({ product, index }: ProductCardProps) {
  const scorePercent = Math.round(product.similarity_score * 100);

  return (
    <article
      className="product-card"
      style={{ animationDelay: `${index * 0.05}s` }}
    >
      <div className="product-card__image-wrap">
        <img
          className="product-card__image"
          src={product.thumbnail || product.image}
          alt={product.name}
          loading="lazy"
          onError={(e) => {
            (e.target as HTMLImageElement).src =
              "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Crect fill='%2312121a' width='200' height='200'/%3E%3Ctext fill='%235a5a6e' x='50%25' y='50%25' text-anchor='middle' dy='.3em' font-family='Inter,sans-serif' font-size='14'%3ENo Image%3C/text%3E%3C/svg%3E";
          }}
        />
        <span
          className={`product-card__score ${getScoreClass(product.similarity_score)}`}
        >
          {scorePercent}% match
        </span>
      </div>
      <div className="product-card__body">
        <div className="product-card__category">{product.category}</div>
        <h3 className="product-card__name">{product.name}</h3>
        <div className="product-card__meta">
          <span className="product-card__price">${product.price}</span>
          <span className="product-card__brand">{product.brand}</span>
        </div>
      </div>
    </article>
  );
}
