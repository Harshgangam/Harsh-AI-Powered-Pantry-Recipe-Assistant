import React from 'react';
import { Search, Refrigerator, Sparkles } from 'lucide-react';

interface EmptyStateProps {
  type: 'initial' | 'no-results';
  onAddStaples?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ type, onAddStaples }) => {
  if (type === 'initial') {
    return (
      <div className="state-container">
        <div className="state-icon">
          <Refrigerator size={48} strokeWidth={1.5} />
        </div>
        <h3 className="state-title">Your Pantry is Ready</h3>
        <p className="state-text">
          Add the ingredients currently available in your kitchen on the left, then click{' '}
          <strong style={{ color: 'var(--color-primary-light)' }}>Find Recipes</strong> to discover
          personalized, zero-waste recipes.
        </p>
      </div>
    );
  }

  return (
    <div className="state-container">
      <div className="state-icon">
        <Search size={48} strokeWidth={1.5} />
      </div>
      <h3 className="state-title">No Matching Recipes Found</h3>
      <p className="state-text">
        We searched over 2.23 million recipes, but none matched your exact combination of pantry
        items and filters.
      </p>
      {onAddStaples && (
        <button
          type="button"
          className="btn-primary"
          onClick={onAddStaples}
          style={{ marginTop: '1.25rem', fontSize: '0.88rem', padding: '0.6rem 1rem' }}
        >
          <Sparkles size={16} />
          <span>Add Common Staples (Tomato, Garlic, Pasta)</span>
        </button>
      )}
    </div>
  );
};
