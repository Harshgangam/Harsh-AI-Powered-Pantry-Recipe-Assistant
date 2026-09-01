import React from 'react';
import { RefreshCw, Lightbulb } from 'lucide-react';
import { SubstitutionCandidate } from '../../types/recipe';

interface SubstitutionPanelProps {
  substitutions: SubstitutionCandidate[];
  missingCount: number;
}

export const SubstitutionPanel: React.FC<SubstitutionPanelProps> = ({
  substitutions,
  missingCount,
}) => {
  if (missingCount === 0) {
    return null;
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
        <RefreshCw size={18} color="var(--color-accent)" />
        <h4 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.05rem', color: '#fff' }}>
          Suggested Culinary Substitutions ({substitutions.length})
        </h4>
      </div>

      {substitutions.length === 0 ? (
        <div
          style={{
            padding: '1rem',
            background: 'rgba(255, 255, 255, 0.03)',
            borderRadius: 'var(--radius-md)',
            border: '1px dashed var(--border-subtle)',
            color: 'var(--text-muted)',
            fontSize: '0.85rem',
          }}
        >
          No standard substitutions available for the missing ingredients in this recipe.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {substitutions.map((sub, idx) => (
            <div key={idx} className="substitution-card">
              <div className="sub-header">
                <div className="sub-names">
                  <span style={{ color: 'var(--color-accent)' }}>{sub.missing_ingredient}</span>
                  <span style={{ margin: '0 0.5rem', color: 'var(--text-dim)' }}>&rarr;</span>
                  <span style={{ color: 'var(--color-primary-light)' }}>{sub.substitute}</span>
                </div>
                <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                  {sub.ratio && <span className="sub-ratio-badge">Ratio {sub.ratio}</span>}
                  <span
                    style={{
                      fontSize: '0.72rem',
                      padding: '0.15rem 0.45rem',
                      borderRadius: 'var(--radius-full)',
                      background: sub.confidence === 'high' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                      color: sub.confidence === 'high' ? 'var(--color-primary-light)' : 'var(--color-accent)',
                      textTransform: 'uppercase',
                      fontWeight: 600,
                    }}
                  >
                    {sub.confidence} confidence
                  </span>
                </div>
              </div>
              <p className="sub-reason">{sub.reason}</p>
              {sub.notes && (
                <p style={{ fontSize: '0.78rem', color: 'var(--text-dim)', fontStyle: 'italic' }}>
                  Tip: {sub.notes}
                </p>
              )}
            </div>
          ))}

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              fontSize: '0.76rem',
              color: 'var(--text-dim)',
              marginTop: '0.25rem',
            }}
          >
            <Lightbulb size={13} color="var(--color-accent)" />
            <span>
              Substitutions are culinary suggestions and may slightly alter flavor, browning, or texture.
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
