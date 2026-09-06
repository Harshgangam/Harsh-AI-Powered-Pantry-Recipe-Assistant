import React, { useState, useEffect } from 'react';
import { FoodRescueSimulationResponse } from '../../types/api';
import { simulateFoodRescue, cookRecipe } from '../../services/api';

interface FoodRescueSimulatorModalProps {
  recipeId: number;
  recipeTitle: string;
  recipeNer: string[];
  pantryIngredients: string[];
  onClose: () => void;
  onCooked: () => void;
}

export const FoodRescueSimulatorModal: React.FC<FoodRescueSimulatorModalProps> = ({
  recipeId,
  recipeTitle,
  recipeNer,
  pantryIngredients,
  onClose,
  onCooked,
}) => {
  const [simulation, setSimulation] = useState<FoodRescueSimulationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [cookedSuccess, setCookedSuccess] = useState(false);

  useEffect(() => {
    async function runSim() {
      setLoading(true);
      const data = await simulateFoodRescue(recipeId, pantryIngredients);
      setSimulation(data);
      setLoading(false);
    }
    runSim();
  }, [recipeId, pantryIngredients]);

  const handleCookNow = async () => {
    await cookRecipe(recipeId, recipeTitle, recipeNer);
    setCookedSuccess(true);
    setTimeout(() => {
      onCooked();
      onClose();
    }, 1500);
  };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
      <div style={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.15)', borderRadius: '16px', maxWidth: '560px', width: '100%', padding: '24px', color: '#fff' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 700 }}>⚡ Food Rescue Simulator</h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#9ca3af', fontSize: '20px', cursor: 'pointer' }}>✕</button>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '30px', color: '#9ca3af' }}>Running pantry impact simulation...</div>
        ) : simulation ? (
          <div>
            <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10b981', padding: '12px', borderRadius: '8px', marginBottom: '16px', fontSize: '13px', color: '#a7f3d0' }}>
              {simulation.simulation_summary}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '12px', borderRadius: '8px' }}>
                <div style={{ fontSize: '12px', color: '#9ca3af' }}>Utilized High-Risk Items</div>
                <div style={{ fontSize: '20px', fontWeight: 700, color: '#f59e0b', marginTop: '2px' }}>
                  {simulation.high_risk_rescued_count} item(s)
                </div>
              </div>
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '12px', borderRadius: '8px' }}>
                <div style={{ fontSize: '12px', color: '#9ca3af' }}>Pantry Utilization Rate</div>
                <div style={{ fontSize: '20px', fontWeight: 700, color: '#10b981', marginTop: '2px' }}>
                  {simulation.pantry_utilization_pct}%
                </div>
              </div>
            </div>

            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '13px', fontWeight: 600, color: '#e2e8f0', marginBottom: '6px' }}>Ingredients Consumed:</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {simulation.ingredients_consumed.map((ing, i) => (
                  <span key={i} style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#6ee7b7', padding: '4px 8px', borderRadius: '6px', fontSize: '12px' }}>
                    ✓ {ing}
                  </span>
                ))}
              </div>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <div style={{ fontSize: '13px', fontWeight: 600, color: '#e2e8f0', marginBottom: '6px' }}>Remaining Pantry:</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {simulation.remaining_pantry.map((ing, i) => (
                  <span key={i} style={{ background: 'rgba(255, 255, 255, 0.08)', color: '#cbd5e1', padding: '4px 8px', borderRadius: '6px', fontSize: '12px' }}>
                    {ing}
                  </span>
                ))}
              </div>
            </div>

            {cookedSuccess ? (
              <div style={{ background: '#10b981', color: '#fff', padding: '12px', borderRadius: '8px', textAlign: 'center', fontWeight: 600 }}>
                🎉 Cooked! Pantry updated automatically.
              </div>
            ) : (
              <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                <button onClick={onClose} style={{ background: 'rgba(255,255,255,0.1)', color: '#fff', border: 'none', padding: '10px 18px', borderRadius: '8px', cursor: 'pointer' }}>
                  Cancel
                </button>
                <button onClick={handleCookNow} style={{ background: 'linear-gradient(135deg, #10b981, #059669)', color: '#fff', border: 'none', padding: '10px 20px', borderRadius: '8px', cursor: 'pointer', fontWeight: 700 }}>
                  🍳 Cook This Recipe & Deduct Pantry
                </button>
              </div>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
};
