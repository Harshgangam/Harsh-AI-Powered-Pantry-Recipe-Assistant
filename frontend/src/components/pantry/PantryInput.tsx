import React, { useState, useEffect, useCallback } from 'react';
import { Plus } from 'lucide-react';

type FreshnessLevel = 'fresh' | 'few_days_old' | 'use_immediately';

interface FreshnessOption {
  key: FreshnessLevel;
  emoji: string;
  label: string;
  color: string;
  bg: string;
}

const FRESHNESS_OPTIONS: FreshnessOption[] = [
  { key: 'fresh',           emoji: '🟢', label: 'Fresh',          color: '#10b981', bg: 'rgba(16,185,129,0.15)' },
  { key: 'few_days_old',    emoji: '🟡', label: 'Few Days Old',   color: '#f59e0b', bg: 'rgba(245,158,11,0.15)' },
  { key: 'use_immediately', emoji: '🔴', label: 'Use Now',        color: '#ef4444', bg: 'rgba(239,68,68,0.15)'  },
];

interface PantryInputProps {
  onAdd: (ingredient: string, expiryDays?: number) => boolean;
}

export const PantryInput: React.FC<PantryInputProps> = ({ onAdd }) => {
  const [value, setValue] = useState('');
  const [freshness, setFreshness] = useState<FreshnessLevel>('fresh');
  const [baseShelfLife, setBaseShelfLife] = useState<number>(7);
  const [fetchingShelfLife, setFetchingShelfLife] = useState(false);
  const [showFreshness, setShowFreshness] = useState(false);

  // Compute final expiry days from freshness button
  const computedExpiryDays =
    freshness === 'use_immediately' ? 1
    : freshness === 'few_days_old'  ? Math.max(1, Math.floor(baseShelfLife * 0.5))
    : baseShelfLife;

  // Auto-fetch shelf life from FoodKeeper as user types (debounced 600ms)
  const fetchShelfLife = useCallback(async (ingredient: string) => {
    if (!ingredient.trim()) return;
    setFetchingShelfLife(true);
    try {
      const res = await fetch(`/api/pantry/shelf-life/${encodeURIComponent(ingredient.trim())}`);
      if (res.ok) {
        const data = await res.json();
        setBaseShelfLife(data.base_shelf_life_days ?? 7);
      }
    } catch (_) {
      setBaseShelfLife(7);
    } finally {
      setFetchingShelfLife(false);
    }
  }, []);

  useEffect(() => {
    if (!value.trim()) { setShowFreshness(false); return; }
    setShowFreshness(true);
    const timer = setTimeout(() => fetchShelfLife(value), 600);
    return () => clearTimeout(timer);
  }, [value, fetchShelfLife]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (value.trim()) {
      onAdd(value, computedExpiryDays);
      setValue('');
      setFreshness('fresh');
      setBaseShelfLife(7);
      setShowFreshness(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {/* Input row */}
      <div className="input-group">
        <div style={{ position: 'relative', flex: 1 }}>
          <input
            type="text"
            className="text-input"
            placeholder="Add ingredient (e.g. tomato, pasta)..."
            value={value}
            onChange={(e) => setValue(e.target.value)}
            aria-label="Pantry ingredient"
            style={{ width: '100%', boxSizing: 'border-box' }}
          />
          {fetchingShelfLife && (
            <span style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', fontSize: '11px', color: '#9ca3af' }}>
              looking up...
            </span>
          )}
        </div>
        <button type="submit" className="btn-primary" disabled={!value.trim()}>
          <Plus size={18} />
          <span>Add</span>
        </button>
      </div>

      {/* Freshness buttons — appear once user starts typing */}
      {showFreshness && (
        <div style={{ background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '10px', padding: '10px 12px' }}>
          <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '7px', display: 'flex', justifyContent: 'space-between' }}>
            <span>How fresh is <strong style={{ color: '#f3f4f6' }}>{value}</strong>?</span>
            {!fetchingShelfLife && (
              <span style={{ color: '#6366f1' }}>
                Base shelf life: <strong>{baseShelfLife}d</strong>
              </span>
            )}
          </div>

          {/* 3 Freshness Buttons */}
          <div style={{ display: 'flex', gap: '6px', marginBottom: '8px' }}>
            {FRESHNESS_OPTIONS.map(opt => (
              <button
                key={opt.key}
                type="button"
                onClick={() => setFreshness(opt.key)}
                style={{
                  flex: 1,
                  padding: '6px 8px',
                  borderRadius: '7px',
                  border: freshness === opt.key
                    ? `2px solid ${opt.color}`
                    : '2px solid rgba(255,255,255,0.08)',
                  background: freshness === opt.key ? opt.bg : 'rgba(0,0,0,0.15)',
                  color: freshness === opt.key ? opt.color : '#9ca3af',
                  cursor: 'pointer',
                  fontWeight: freshness === opt.key ? 700 : 400,
                  fontSize: '12px',
                  transition: 'all 0.15s',
                }}
              >
                {opt.emoji} {opt.label}
              </button>
            ))}
          </div>

          {/* Live expiry preview */}
          <div style={{ fontSize: '11px', color: '#9ca3af' }}>
            Will expire in:{' '}
            <span style={{
              fontWeight: 700,
              color: computedExpiryDays <= 2 ? '#ef4444'
                   : computedExpiryDays <= 6 ? '#f59e0b'
                   : '#10b981',
            }}>
              {computedExpiryDays} day{computedExpiryDays !== 1 ? 's' : ''} from today
            </span>
            {' '}— will show live countdown in Pantry Intelligence
          </div>
        </div>
      )}
    </form>
  );
};
