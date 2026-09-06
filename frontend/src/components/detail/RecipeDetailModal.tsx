import React, { useEffect, useState } from 'react';
import { X, ExternalLink, Zap } from 'lucide-react';
import { RecipeRecommendationItem } from '../../types/recipe';
import { formatScore, formatTime, getDietaryLabel } from '../../utils/formatters';
import { ExplanationCard } from './ExplanationCard';
import { IngredientList } from './IngredientList';
import { SubstitutionPanel } from './SubstitutionPanel';
import { AiAssistantPanel } from './AiAssistantPanel';
import { FoodRescueSimulatorModal } from '../recommendations/FoodRescueSimulatorModal';

interface RecipeDetailModalProps {
  recipe: RecipeRecommendationItem | null;
  pantryIngredients?: string[];
  appliedPreferences?: {
    cuisine?: string | null;
    dietary_preference?: string | null;
    max_cooking_time_minutes?: number | null;
  };
  onClose: () => void;
  onCooked?: (usedNer: string[]) => void;
}

export const RecipeDetailModal: React.FC<RecipeDetailModalProps> = ({
  recipe,
  pantryIngredients,
  appliedPreferences,
  onClose,
  onCooked,
}) => {
  const [showSimulator, setShowSimulator] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!recipe) return null;

  return (
    <>
      <div className="modal-backdrop" onClick={onClose}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          {/* Modal Header */}
          <div className="modal-header">
            <div>
              <h2 className="modal-title">{recipe.title}</h2>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', color: 'var(--text-dim)', fontSize: '0.82rem' }}>
                <span>Source: {recipe.source || 'RecipeNLG'}</span>
                {recipe.link && (
                  <a
                    href={`https://${recipe.link.replace(/^https?:\/\//, '')}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ color: 'var(--color-primary-light)', display: 'inline-flex', alignItems: 'center', gap: '0.25rem', textDecoration: 'none' }}
                  >
                    <span>Original Link</span>
                    <ExternalLink size={12} />
                  </a>
                )}
              </div>
            </div>
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <button
                type="button"
                onClick={() => setShowSimulator(true)}
                style={{ background: 'linear-gradient(135deg, #10b981, #059669)', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <Zap size={14} />
                <span>Simulate Food Rescue</span>
              </button>
              
              <button 
                onClick={() => setShowSimulator(true)}
                style={{
                  background: 'linear-gradient(135deg, #10b981, #059669)',
                  color: 'white',
                  border: 'none',
                  padding: '6px 12px',
                  borderRadius: '6px',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <span>🍳 I made this!</span>
              </button>
              
              <button
                type="button"
                className="modal-close-btn"
                onClick={onClose}
                aria-label="Close modal"
              >
                <X size={24} />
              </button>
            </div>
          </div>

          {/* Modal Body */}
          <div className="modal-body">
            {/* Quick Metrics Bar */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
                gap: '0.75rem',
                padding: '1rem',
                background: 'rgba(0, 0, 0, 0.3)',
                borderRadius: 'var(--radius-md)',
              }}
            >
              {recipe.frps !== undefined && (
                <div>
                  <span className="metric-label">Food Rescue Score</span>
                  <span className="metric-value score-high" style={{ fontSize: '1.25rem', color: '#34d399' }}>
                    {formatScore(recipe.frps)}
                  </span>
                </div>
              )}
              <div>
                <span className="metric-label">Recommendation Score</span>
                <span className="metric-value score-high" style={{ fontSize: '1.25rem' }}>
                  {formatScore(recipe.recommendation_score)}
                </span>
              </div>
              <div>
                <span className="metric-label">Ingredient Match (IMS)</span>
                <span className="metric-value score-high">
                  {formatScore(recipe.ims)}%
                </span>
              </div>
              <div>
                <span className="metric-label">Pantry Utilized (PUS)</span>
                <span className="metric-value score-high">
                  {formatScore(recipe.pus)}%
                </span>
              </div>
              <div>
                <span className="metric-label">Cuisine</span>
                <span className="metric-value" style={{ fontSize: '0.9rem' }}>
                  {recipe.cuisine || 'Unclassified'}
                </span>
              </div>
              <div>
                <span className="metric-label">Active Time</span>
                <span className="metric-value" style={{ fontSize: '0.9rem' }}>
                  {formatTime(recipe.estimated_time_minutes)}
                </span>
              </div>
              <div>
                <span className="metric-label">Dietary</span>
                <span className="metric-value" style={{ fontSize: '0.9rem' }}>
                  {getDietaryLabel(recipe.dietary_compatibility)}
                </span>
              </div>
            </div>

            {/* Explanation Breakdown */}
            <ExplanationCard
              explanation={recipe.explanation}
              explanationData={recipe.explanation_data}
              preferenceExplanation={recipe.preference_explanation}
            />

            {/* Ingredient Match vs Missing Split */}
            <IngredientList
              matchedIngredients={recipe.matched_ingredients}
              missingIngredients={recipe.missing_ingredients}
              rawIngredients={recipe.ingredients}
            />

            {/* Substitutions Section */}
            <SubstitutionPanel
              substitutions={recipe.substitutions}
              missingCount={recipe.missing_count}
            />

            {/* AI-Assisted Grounded Recipe Guidance (Milestone 6) */}
            <AiAssistantPanel
              recipe={recipe}
              pantryIngredients={pantryIngredients}
              appliedPreferences={appliedPreferences}
            />

            {/* Step-by-Step Directions */}
            <div>
              <h4 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.05rem', marginBottom: '1rem', color: '#fff' }}>
                Cooking Directions
              </h4>
              <div className="directions-list">
                {recipe.directions && recipe.directions.length > 0 ? (
                  recipe.directions.map((step, idx) => (
                    <div key={idx} className="direction-step">
                      <div className="step-number">{idx + 1}</div>
                      <div style={{ color: 'var(--text-main)' }}>{step}</div>
                    </div>
                  ))
                ) : (
                  <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>
                    No step-by-step directions recorded for this recipe.
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {showSimulator && (
        <FoodRescueSimulatorModal
          recipeId={recipe.recipe_id}
          recipeTitle={recipe.title}
          recipeNer={recipe.ner}
          pantryIngredients={pantryIngredients || recipe.matched_ingredients}
          onClose={() => setShowSimulator(false)}
          onCooked={() => {
            setShowSimulator(false);
            if (onCooked) onCooked(recipe.ner);
            onClose(); // Also close the recipe detail modal once cooked
          }}
        />
      )}
    </>
  );
};
