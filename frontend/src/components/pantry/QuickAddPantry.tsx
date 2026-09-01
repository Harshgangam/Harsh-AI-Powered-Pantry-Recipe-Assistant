import React from 'react';
import { Sparkles } from 'lucide-react';

interface QuickAddPantryProps {
  onAdd: (item: string) => boolean;
  currentIngredients: string[];
}

const COMMON_STAPLES = [
  'tomato',
  'onion',
  'garlic',
  'pasta',
  'olive oil',
  'rice',
  'butter',
  'eggs',
  'chicken',
  'potato',
  'flour',
  'cheese',
];

export const QuickAddPantry: React.FC<QuickAddPantryProps> = ({
  onAdd,
  currentIngredients,
}) => {
  const currentSet = new Set(currentIngredients.map((i) => i.toLowerCase()));

  return (
    <div className="quick-add-section">
      <div className="quick-add-label" style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
        <Sparkles size={13} color="var(--color-accent)" />
        <span>Quick-Add Common Staples</span>
      </div>
      <div className="quick-add-pills">
        {COMMON_STAPLES.map((staple) => {
          const isAdded = currentSet.has(staple);
          return (
            <button
              key={staple}
              type="button"
              className="quick-pill"
              onClick={() => onAdd(staple)}
              disabled={isAdded}
              style={isAdded ? { opacity: 0.4, cursor: 'default', textDecoration: 'line-through' } : {}}
            >
              + {staple}
            </button>
          );
        })}
      </div>
    </div>
  );
};
