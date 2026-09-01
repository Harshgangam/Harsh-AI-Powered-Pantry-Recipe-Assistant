import React from 'react';
import { formatScore, getScoreColorClass } from '../../utils/formatters';

interface ScoreBadgeProps {
  score: number;
  label: string;
  isPercent?: boolean;
}

export const ScoreBadge: React.FC<ScoreBadgeProps> = ({ score, label, isPercent = true }) => {
  const colorClass = getScoreColorClass(score);

  return (
    <div className="metric-box">
      <span className="metric-label">{label}</span>
      <span className={`metric-value ${colorClass}`}>
        {formatScore(score)}
        {isPercent ? '%' : ''}
      </span>
    </div>
  );
};
