import React, { useState, useEffect } from 'react';
import { SustainabilityMetricsResponse } from '../../types/api';
import { fetchSustainabilityAnalytics } from '../../services/api';

export const SustainabilityDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<SustainabilityMetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadMetrics() {
      setLoading(true);
      const data = await fetchSustainabilityAnalytics();
      setMetrics(data);
      setLoading(false);
    }
    loadMetrics();
  }, []);

  if (loading) {
    return <div style={{ color: '#9ca3af', padding: '20px' }}>Loading sustainability analytics...</div>;
  }

  if (!metrics) return null;

  return (
    <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '24px', borderRadius: '16px', border: '1px solid rgba(255, 255, 255, 0.1)', marginBottom: '24px' }}>
      <h2 style={{ margin: '0 0 4px', fontSize: '20px', fontWeight: 700, color: '#f3f4f6' }}>🌱 Sustainability & Food-Waste Analytics</h2>
      <p style={{ margin: '0 0 20px', color: '#9ca3af', fontSize: '13px' }}>Quantifiable impact metrics tracking your household food rescue journey.</p>

      <div style={{ background: 'rgba(16, 185, 129, 0.12)', border: '1px solid #10b981', color: '#a7f3d0', padding: '14px 18px', borderRadius: '10px', marginBottom: '20px', fontWeight: 600, fontSize: '14px' }}>
        {metrics.status_summary}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        <div style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.08)', padding: '16px', borderRadius: '12px' }}>
          <div style={{ fontSize: '12px', color: '#9ca3af' }}>High-Risk Items Rescued</div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: '#ef4444', marginTop: '4px' }}>{metrics.high_risk_rescued_count}</div>
        </div>
        <div style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.08)', padding: '16px', borderRadius: '12px' }}>
          <div style={{ fontSize: '12px', color: '#9ca3af' }}>Food Waste Avoided</div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: '#10b981', marginTop: '4px' }}>{metrics.estimated_food_waste_avoided_kg} kg</div>
        </div>
        <div style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.08)', padding: '16px', borderRadius: '12px' }}>
          <div style={{ fontSize: '12px', color: '#9ca3af' }}>Pantry Utilization Rate</div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: '#3b82f6', marginTop: '4px' }}>{metrics.pantry_utilization_rate}%</div>
        </div>
        <div style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.08)', padding: '16px', borderRadius: '12px' }}>
          <div style={{ fontSize: '12px', color: '#9ca3af' }}>Recipes Prepared</div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: '#8b5cf6', marginTop: '4px' }}>{metrics.recipes_prepared_count}</div>
        </div>
      </div>

      {/* 7-Day Trend Chart */}
      <div>
        <h3 style={{ fontSize: '14px', color: '#e2e8f0', marginBottom: '12px' }}>📊 7-Day Food Rescue Activity</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '8px', alignItems: 'end', height: '140px', background: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '10px' }}>
          {metrics.sustainability_trend.map((dayData, idx) => (
            <div key={idx} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%', justifyContent: 'flex-end' }}>
              <div style={{ fontSize: '11px', color: '#10b981', fontWeight: 700, marginBottom: '4px' }}>{dayData.rescued_items}</div>
              <div
                style={{
                  width: '100%',
                  height: `${Math.max(15, dayData.rescued_items * 20)}px`,
                  background: 'linear-gradient(180deg, #10b981, #059669)',
                  borderRadius: '4px 4px 0 0',
                }}
              />
              <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '6px' }}>{dayData.day}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
