import React from 'react';
import { CheckCircle2, AlertCircle } from 'lucide-react';

interface IngredientListProps {
  matchedIngredients: string[];
  missingIngredients: string[];
  rawIngredients: string[];
}

export const IngredientList: React.FC<IngredientListProps> = ({
  matchedIngredients,
  missingIngredients,
  rawIngredients,
}) => {
  return (
    <div>
      <h4 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.05rem', marginBottom: '1rem', color: '#fff' }}>
        Ingredient Availability Breakdown
      </h4>

      <div className="ingredient-split-grid">
        {/* Matched Column */}
        <div style={{ background: 'rgba(16, 185, 129, 0.05)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid rgba(16, 185, 129, 0.15)' }}>
          <div className="ing-col-title ing-matched-title">
            <CheckCircle2 size={16} />
            <span>Available in Pantry ({matchedIngredients.length})</span>
          </div>
          {matchedIngredients.length === 0 ? (
            <span style={{ fontSize: '0.82rem', color: 'var(--text-dim)' }}>No pantry ingredients matched</span>
          ) : (
            matchedIngredients.map((item, idx) => (
              <div key={idx} className="ing-item" style={{ color: 'var(--color-primary-light)' }}>
                <span>&bull;</span>
                <span style={{ fontWeight: 500 }}>{item}</span>
              </div>
            ))
          )}
        </div>

        {/* Missing Column */}
        <div style={{ background: 'rgba(245, 158, 11, 0.05)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid rgba(245, 158, 11, 0.15)' }}>
          <div className="ing-col-title ing-missing-title">
            <AlertCircle size={16} />
            <span>Missing from Pantry ({missingIngredients.length})</span>
          </div>
          {missingIngredients.length === 0 ? (
            <span style={{ fontSize: '0.82rem', color: 'var(--color-primary-light)' }}>
              Complete match! No missing items.
            </span>
          ) : (
            missingIngredients.map((item, idx) => (
              <div key={idx} className="ing-item" style={{ color: 'var(--color-accent)' }}>
                <span>&bull;</span>
                <span style={{ fontWeight: 500 }}>{item}</span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Raw Recipe Ingredient Quantities */}
      {rawIngredients && rawIngredients.length > 0 && (
        <div style={{ marginTop: '1.25rem' }}>
          <span style={{ fontSize: '0.82rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600, display: 'block', marginBottom: '0.5rem' }}>
            Full Recipe Requirements (As Published)
          </span>
          <ul style={{ listStyleType: 'disc', paddingLeft: '1.25rem', fontSize: '0.88rem', color: 'var(--text-muted)' }}>
            {rawIngredients.map((ing, i) => (
              <li key={i} style={{ marginBottom: '0.25rem' }}>{ing}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
