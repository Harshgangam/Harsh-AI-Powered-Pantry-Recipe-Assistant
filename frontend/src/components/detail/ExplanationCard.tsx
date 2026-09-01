import React from 'react';
import { Award, Sparkles } from 'lucide-react';
import { ExplanationData } from '../../types/recipe';
import { formatScore } from '../../utils/formatters';

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
  const bd = explanationData.frps_breakdown;

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

      {/* FRPS 7-Factor Breakdown */}
      {bd && (
        <div style={{ marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid rgba(16, 185, 129, 0.2)' }}>
          <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#34d399', marginBottom: '8px' }}>
            ⚡ Food Rescue Priority Score Breakdown (FRPS: {formatScore(explanationData.frps || explanationData.final_score)})
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '8px', fontSize: '0.75rem' }}>
            <div style={{ background: 'rgba(0,0,0,0.25)', padding: '6px 10px', borderRadius: '6px' }}>
              <span style={{ color: 'var(--text-dim)', display: 'block' }}>IMS (Match)</span>
              <span style={{ fontWeight: 600, color: '#fff' }}>{bd.ims}% (w={bd.w_ims})</span>
            </div>
            <div style={{ background: 'rgba(0,0,0,0.25)', padding: '6px 10px', borderRadius: '6px' }}>
              <span style={{ color: 'var(--text-dim)', display: 'block' }}>PUS (Utilized)</span>
              <span style={{ fontWeight: 600, color: '#fff' }}>{bd.pus}% (w={bd.w_pus})</span>
            </div>
            <div style={{ background: 'rgba(0,0,0,0.25)', padding: '6px 10px', borderRadius: '6px' }}>
              <span style={{ color: 'var(--text-dim)', display: 'block' }}>EPS (Expiry)</span>
              <span style={{ fontWeight: 600, color: '#f59e0b' }}>{bd.eps} (w={bd.w_eps})</span>
            </div>
            <div style={{ background: 'rgba(0,0,0,0.25)', padding: '6px 10px', borderRadius: '6px' }}>
              <span style={{ color: 'var(--text-dim)', display: 'block' }}>QUS (Qty Util)</span>
              <span style={{ fontWeight: 600, color: '#fff' }}>{bd.qus}% (w={bd.w_qus})</span>
            </div>
            <div style={{ background: 'rgba(0,0,0,0.25)', padding: '6px 10px', borderRadius: '6px' }}>
              <span style={{ color: 'var(--text-dim)', display: 'block' }}>DCS (Diet)</span>
              <span style={{ fontWeight: 600, color: '#fff' }}>{bd.dcs} (w={bd.w_dcs})</span>
            </div>
            <div style={{ background: 'rgba(0,0,0,0.25)', padding: '6px 10px', borderRadius: '6px' }}>
              <span style={{ color: 'var(--text-dim)', display: 'block' }}>TCS (Time)</span>
              <span style={{ fontWeight: 600, color: '#fff' }}>{bd.tcs} (w={bd.w_tcs})</span>
            </div>
            <div style={{ background: 'rgba(0,0,0,0.25)', padding: '6px 10px', borderRadius: '6px' }}>
              <span style={{ color: 'var(--text-dim)', display: 'block' }}>MIP (Missing Pen.)</span>
              <span style={{ fontWeight: 600, color: '#ef4444' }}>-{bd.mip} (w={bd.w_mip})</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
