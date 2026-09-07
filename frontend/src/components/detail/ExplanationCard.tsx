import React from 'react';
import { Award, Sparkles } from 'lucide-react';
import { ExplanationData } from '../../types/recipe';


interface ExplanationCardProps {
  explanation: string;
  explanationData: ExplanationData;
  preferenceExplanation?: string | null;
}

export const ExplanationCard: React.FC<ExplanationCardProps> = ({
  explanation,
  explanationData,
  preferenceExplanation,
}) => {

  return (
    <div className="explanation-box">
      <div className="explanation-title">
        <Award size={18} />
        <span>Why this recipe was recommended (Explainable AI)</span>
      </div>

      {explanationData.why_this_recipe && (
        <div style={{ background: 'rgba(16, 185, 129, 0.12)', border: '1px solid #10b981', color: '#a7f3d0', padding: '10px 14px', borderRadius: '8px', fontSize: '0.85rem', marginBottom: '12px' }}>
          <Sparkles size={14} style={{ display: 'inline', marginRight: '6px' }} />
          {explanationData.why_this_recipe}
        </div>
      )}

      <p className="explanation-text">{explanation}</p>
      {preferenceExplanation && !explanation.includes('Personalization:') && (
        <p style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: 'var(--color-primary-light)' }}>
          {preferenceExplanation.startsWith('Personalization:')
            ? preferenceExplanation
            : `Personalization: ${preferenceExplanation}`}
        </p>
      )}


    </div>
  );
};
