import React from 'react';
import { Clock, Globe, Leaf, Utensils, AlertCircle, ShieldCheck } from 'lucide-react';
import { RecipeRecommendationItem } from '../../types/recipe';
import { formatScore, formatTime, getDietaryLabel } from '../../utils/formatters';
import { ScoreBadge } from './ScoreBadge';

interface RecipeCardProps {
  recipe: RecipeRecommendationItem;
  onSelect: (recipe: RecipeRecommendationItem) => void;
}

export const RecipeCard: React.FC<RecipeCardProps> = ({ recipe, onSelect }) => {
  const hasSubstitutions = recipe.substitutions && recipe.substitutions.length > 0;
  const isNonVeg = recipe.dietary_compatibility === 'non_vegetarian';
  const isDietaryCompatible =
    recipe.dietary_compatibility === 'vegan_compatible' ||
    recipe.dietary_compatibility === 'vegetarian_compatible' ||
    isNonVeg;

  return (
    <div
      className="recipe-card"
      onClick={() => onSelect(recipe)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') onSelect(recipe);
      }}
    >
      <div className="card-top-bar">
        <div>
          <h3 className="card-title">{recipe.title}</h3>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
            Source: {recipe.source || 'RecipeNLG'}
          </span>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>

          <div className="card-score-ring" title="Overall Recommendation Score">
            <span className="card-score-value">{formatScore(recipe.recommendation_score)}</span>
            <span className="card-score-sub">Score</span>
          </div>
        </div>
      </div>

      {/* FRPS Explanation snippet */}
      {recipe.why_this_recipe && (
        <div style={{ background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.2)', padding: '8px 12px', borderRadius: '8px', fontSize: '0.78rem', color: '#a7f3d0', marginBottom: '10px' }}>
          💡 <strong>Why This Recipe:</strong> {recipe.why_this_recipe.slice(0, 130)}...
        </div>
      )}

      {/* Dual Scores Metric Strip */}
      <div className="card-metrics-strip">
        <ScoreBadge score={recipe.ims} label="Ingredient Match (IMS)" isPercent={true} />
        <ScoreBadge score={recipe.pus} label="Pantry Utilized (PUS)" isPercent={true} />
      </div>

      {/* Metadata Pills */}
      <div className="card-tags">
        {recipe.cuisine && (
          <span className="meta-pill">
            <Globe size={12} />
            <span>{recipe.cuisine}</span>
          </span>
        )}

        {recipe.estimated_time_minutes ? (
          <span className="meta-pill">
            <Clock size={12} />
            <span>{formatTime(recipe.estimated_time_minutes)}</span>
          </span>
        ) : null}

        {isDietaryCompatible && (
          <span className={`meta-pill ${isNonVeg ? 'pill-amber' : 'pill-green'}`}>
            {isNonVeg ? <Utensils size={12} /> : <Leaf size={12} />}
            <span>{getDietaryLabel(recipe.dietary_compatibility)}</span>
          </span>
        )}

        {recipe.missing_count > 0 ? (
          <span className="meta-pill pill-amber">
            <AlertCircle size={12} />
            <span>
              {recipe.missing_count} missing
              {hasSubstitutions ? ` (${recipe.substitutions.length} sub available)` : ''}
            </span>
          </span>
        ) : (
          <span className="meta-pill pill-green">
            <ShieldCheck size={12} />
            <span>100% On-Hand</span>
          </span>
        )}
      </div>
    </div>
  );
};
