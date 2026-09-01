import React from 'react';

export const LoadingSkeleton: React.FC = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div style={{ textAlign: 'center', padding: '1rem', color: 'var(--text-muted)' }}>
        <p style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--color-primary-light)' }}>
          Evaluating candidates across 2.23M recipes...
        </p>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
          Computing Ingredient Match & Pantry Utilization scores
        </p>
      </div>

      <div className="recipe-cards-grid">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="skeleton-card">
            <div className="skeleton-shimmer" />
          </div>
        ))}
      </div>
    </div>
  );
};
