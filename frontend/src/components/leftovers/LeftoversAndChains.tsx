import React, { useState, useEffect } from 'react';
import { LeftoverItem } from '../../types/recipe';
import { fetchLeftovers, addLeftover, fetchMealChainPlan } from '../../services/api';
import { MealChainPlanResponse } from '../../types/api';

export const LeftoversAndChains: React.FC = () => {
  const [leftovers, setLeftovers] = useState<LeftoverItem[]>([]);
  const [dishName, setDishName] = useState('');
  const [ingredients, setIngredients] = useState('');
  const [chainPlan, setChainPlan] = useState<MealChainPlanResponse | null>(null);
  const [loadingChain, setLoadingChain] = useState(false);

  const loadData = async () => {
    const data = await fetchLeftovers();
    setLeftovers(data);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleAddLeftover = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!dishName.trim()) return;
    const ingList = ingredients.split(',').map(i => i.trim()).filter(Boolean);
    await addLeftover(dishName, ingList);
    setDishName('');
    setIngredients('');
    loadData();
  };

  const handleGenerateChain = async () => {
    setLoadingChain(true);
    const planData = await fetchMealChainPlan();
    setChainPlan(planData);
    setLoadingChain(false);
  };

  return (
    <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '24px', borderRadius: '16px', border: '1px solid rgba(255, 255, 255, 0.1)', marginBottom: '24px' }}>
      <h2 style={{ margin: '0 0 4px', fontSize: '20px', fontWeight: 700, color: '#f3f4f6' }}>Leftover Transformation & Multi-Day Chain Planner</h2>
      <p style={{ margin: '0 0 20px', color: '#9ca3af', fontSize: '13px' }}>Repurpose cooked leftovers and plan multi-day meal rescue chains.</p>

      {/* Record Leftovers */}
      <div style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '15px', color: '#e2e8f0', marginBottom: '10px' }}>🍲 Active Cooked Leftovers</h3>
        <form onSubmit={handleAddLeftover} style={{ display: 'flex', gap: '8px', marginBottom: '14px' }}>
          <input
            type="text"
            placeholder="Leftover dish name (e.g. Cooked Basmati Rice)"
            value={dishName}
            onChange={e => setDishName(e.target.value)}
            style={{ flex: 1, background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '8px 12px', borderRadius: '6px' }}
          />
          <input
            type="text"
            placeholder="Primary ingredients (comma separated: rice, chicken)"
            value={ingredients}
            onChange={e => setIngredients(e.target.value)}
            style={{ flex: 1, background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '8px 12px', borderRadius: '6px' }}
          />
          <button type="submit" style={{ background: '#3b82f6', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer', fontWeight: 600 }}>
            + Record Leftover
          </button>
        </form>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '12px' }}>
          {leftovers.map(item => (
            <div key={item.id} style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.08)', padding: '14px', borderRadius: '10px' }}>
              <div style={{ fontWeight: 600, color: '#f3f4f6' }}>{item.dish_name}</div>
              <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '4px' }}>
                Cooked: {item.cooked_date} • {item.quantity} {item.unit}
              </div>
              <div style={{ fontSize: '12px', color: '#60a5fa', marginTop: '4px' }}>
                Ingredients: {item.primary_ingredients.join(', ')}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 3-Day Meal Rescue Chain Planner */}
      <div style={{ borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '15px', color: '#e2e8f0' }}>🔗 3-Day Food Rescue Chain Planner</h3>
            <p style={{ margin: '2px 0 0', color: '#9ca3af', fontSize: '12px' }}>Optimizes 3 consecutive meals to maximize ingredient reuse across days.</p>
          </div>
          <button
            onClick={handleGenerateChain}
            disabled={loadingChain}
            style={{ background: 'linear-gradient(135deg, #10b981, #059669)', color: '#fff', border: 'none', padding: '10px 18px', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '13px' }}
          >
            {loadingChain ? 'Generating Chain...' : '✨ Generate 3-Day Rescue Plan'}
          </button>
        </div>

        {chainPlan && (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px', marginBottom: '12px' }}>
              {chainPlan.plan.map((dayItem, i) => (
                <div key={i} style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid #10b981', padding: '16px', borderRadius: '10px' }}>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: '#34d399', textTransform: 'uppercase' }}>Day {dayItem.day} Meal</div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#fff', margin: '4px 0 8px' }}>{dayItem.meal_name}</div>
                  <div style={{ fontSize: '12px', color: '#cbd5e1', marginBottom: '6px' }}>
                    <strong>Rescued:</strong> {dayItem.primary_ingredients_rescued.join(', ')}
                  </div>
                  <div style={{ fontSize: '12px', color: '#94a3b8' }}>
                    {dayItem.reasoning}
                  </div>
                </div>
              ))}
            </div>
            <div style={{ fontSize: '12px', color: '#34d399', textAlign: 'right', fontWeight: 600 }}>
              {chainPlan.estimated_waste_reduction} (Score: {chainPlan.total_rescue_score}/100)
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
