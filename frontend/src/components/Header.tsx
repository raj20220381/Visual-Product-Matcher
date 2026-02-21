import React from "react";

export default function Header() {
  return (
    <header className="header">
      <div className="header__inner">
        <div className="header__logo">
          <div className="header__icon">🔍</div>
          <div>
            <div className="header__title">Visual Product Matcher</div>
            <div className="header__subtitle">
              AI-Powered Visual Similarity Search
            </div>
          </div>
        </div>
        <span className="header__badge">CLIP ViT-B/32</span>
      </div>
    </header>
  );
}
