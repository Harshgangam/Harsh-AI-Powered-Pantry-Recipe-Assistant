import React from 'react';
import { SlidersHorizontal, RotateCcw } from 'lucide-react';

interface PreferenceControlsProps {
  cuisine: string | null;
  setCuisine: (c: string | null) => void;
  dietary: string | null;
  setDietary: (d: string | null) => void;
  maxCookingTime: number | null;
  setMaxCookingTime: (t: number | null) => void;
  onReset: () => void;
}

const CUISINES = [
  'Italian',
  'Mexican',
  'American',
  'Chinese',
  'French',
  'Indian',
  'Mediterranean',
  'Japanese',
  'Thai',
  'Middle Eastern',
  'Korean',
];

const TIME_OPTIONS = [
  { label: 'Any', value: null },
  { label: '15m', value: 15 },
  { label: '30m', value: 30 },
  { label: '45m', value: 45 },
  { label: '60m', value: 60 },
];

export const PreferenceControls: React.FC<PreferenceControlsProps> = ({
  cuisine,
  setCuisine,
  dietary,
  setDietary,
  maxCookingTime,
  setMaxCookingTime,
  onReset,
}) => {
  const hasActivePrefs = Boolean(cuisine || dietary || maxCookingTime);

  return (
    <div>
      <div className="section-header">
        <h3 className="section-title">
          <SlidersHorizontal size={17} />
          <span>Personalization</span>
        </h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span className="section-badge">Optional</span>
          {hasActivePrefs && (
            <button
              type="button"
              onClick={onReset}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-dim)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                padding: '0.2rem',
              }}
              title="Reset all preferences"
            >
              <RotateCcw size={13} />
            </button>
          )}
        </div>
      </div>

      {/* Cuisine Selector */}
      <div className="pref-field">
        <label className="pref-label" htmlFor="cuisine-select">
          <span>Preferred Cuisine</span>
          {cuisine && <span style={{ color: 'var(--color-primary-light)' }}>{cuisine}</span>}
        </label>
        <select
          id="cuisine-select"
          className="pref-select"
          value={cuisine || ''}
          onChange={(e) => setCuisine(e.target.value ? e.target.value : null)}
        >
          <option value="">Any Cuisine (Default)</option>
          {CUISINES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      {/* Dietary Preference */}
      <div className="pref-field">
        <label className="pref-label">
          <span>Dietary Lifestyle</span>
          {dietary && (
            <span style={{ color: 'var(--color-primary-light)', textTransform: 'capitalize' }}>
              {dietary.replace('_', '-')}
            </span>
          )}
        </label>
        <div className="dietary-group" style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '6px' }}>
          <button
            type="button"
            className={`dietary-btn ${dietary === null ? 'active' : ''}`}
            onClick={() => setDietary(null)}
          >
            None
          </button>
          <button
            type="button"
            className={`dietary-btn ${dietary === 'vegetarian' ? 'active' : ''}`}
            onClick={() => setDietary(dietary === 'vegetarian' ? null : 'vegetarian')}
          >
            Vegetarian
          </button>
          <button
            type="button"
            className={`dietary-btn ${dietary === 'vegan' ? 'active' : ''}`}
            onClick={() => setDietary(dietary === 'vegan' ? null : 'vegan')}
          >
            Vegan
          </button>
          <button
            type="button"
            className={`dietary-btn ${dietary === 'non_vegetarian' ? 'active' : ''}`}
            onClick={() => setDietary(dietary === 'non_vegetarian' ? null : 'non_vegetarian')}
          >
            Non-Veg
          </button>
        </div>
      </div>

      {/* Max Cooking Time */}
      <div className="pref-field">
        <label className="pref-label">
          <span>Max Active Time</span>
          <span style={{ color: maxCookingTime ? 'var(--color-primary-light)' : 'var(--text-dim)' }}>
            {maxCookingTime ? `≤ ${maxCookingTime} mins` : 'Any time'}
          </span>
        </label>
        <div className="dietary-group">
          {TIME_OPTIONS.map((opt) => (
            <button
              key={opt.label}
              type="button"
              className={`dietary-btn ${maxCookingTime === opt.value ? 'active' : ''}`}
              onClick={() => setMaxCookingTime(opt.value)}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
