import React, { useState, useEffect } from 'react';
import { PantryItem } from '../../types/recipe';
import { fetchPantryItems, addPantryItem, deletePantryItem, scanPantryImage } from '../../services/api';

interface PantryManagementProps {
  onPantryChange?: (items: string[]) => void;
}

export const PantryManagement: React.FC<PantryManagementProps> = ({ onPantryChange }) => {
  const [items, setItems] = useState<PantryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState('');
  const [category, setCategory] = useState('Produce');
  const [quantity, setQuantity] = useState(1);
  const [unit, setUnit] = useState('pcs');
  const [expiryDays, setExpiryDays] = useState(3);
  const [scanning, setScanning] = useState(false);
  const [scanMessage, setScanMessage] = useState('');

  const loadItems = async () => {
    setLoading(true);
    const data = await fetchPantryItems();
    setItems(data);
    setLoading(false);
    if (onPantryChange && data.length > 0) {
      onPantryChange(data.map(i => i.name));
    }
  };

  useEffect(() => {
    loadItems();
  }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    await addPantryItem({ name, category, quantity, unit, expiry_days: expiryDays });
    setName('');
    loadItems();
  };

  const handleDelete = async (id: string) => {
    await deletePantryItem(id);
    loadItems();
  };

  const handleScan = async () => {
    setScanning(true);
    setScanMessage('Scanning image with computer vision & OCR...');
    const res = await scanPantryImage();
    setScanMessage(res.scan_summary);
    setScanning(false);
    loadItems();
  };

  const getRiskBadge = (risk: string, days: number) => {
    if (risk === 'high' || days <= 2) {
      return <span style={{ background: '#ef4444', color: '#fff', padding: '2px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 600 }}>High Expiry Risk ({days}d)</span>;
    } else if (risk === 'medium' || days <= 6) {
      return <span style={{ background: '#f59e0b', color: '#fff', padding: '2px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 600 }}>Medium Risk ({days}d)</span>;
    }
    return <span style={{ background: '#10b981', color: '#fff', padding: '2px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 600 }}>Fresh ({days}d)</span>;
  };

  return (
    <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '24px', borderRadius: '16px', border: '1px solid rgba(255, 255, 255, 0.1)', marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 700, color: '#f3f4f6' }}>Dynamic Pantry Intelligence</h2>
          <p style={{ margin: '4px 0 0', color: '#9ca3af', fontSize: '13px' }}>Monitor quantities, categories, and real-time expiry risk levels.</p>
        </div>
        <button
          onClick={handleScan}
          disabled={scanning}
          style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', color: '#fff', border: 'none', padding: '10px 18px', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '13px' }}
        >
          {scanning ? 'Scanning...' : '📷 Snap Your Pantry'}
        </button>
      </div>

      {scanMessage && (
        <div style={{ background: 'rgba(99, 102, 241, 0.15)', border: '1px solid #6366f1', color: '#c7d2fe', padding: '12px', borderRadius: '8px', marginBottom: '16px', fontSize: '13px' }}>
          {scanMessage}
        </div>
      )}

      <form onSubmit={handleAdd} style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr auto', gap: '8px', marginBottom: '20px' }}>
        <input
          type="text"
          placeholder="Ingredient name (e.g. Tomatoes)"
          value={name}
          onChange={e => setName(e.target.value)}
          style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '8px 12px', borderRadius: '6px' }}
        />
        <select value={category} onChange={e => setCategory(e.target.value)} style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '8px', borderRadius: '6px' }}>
          <option value="Produce">Produce</option>
          <option value="Dairy">Dairy</option>
          <option value="Grains">Grains</option>
          <option value="Meat">Meat</option>
          <option value="Pantry">Pantry</option>
        </select>
        <input
          type="number"
          placeholder="Qty"
          value={quantity}
          onChange={e => setQuantity(Number(e.target.value))}
          style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '8px', borderRadius: '6px' }}
        />
        <input
          type="text"
          placeholder="Unit"
          value={unit}
          onChange={e => setUnit(e.target.value)}
          style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '8px', borderRadius: '6px' }}
        />
        <input
          type="number"
          placeholder="Exp Days"
          value={expiryDays}
          onChange={e => setExpiryDays(Number(e.target.value))}
          style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '8px', borderRadius: '6px' }}
        />
        <button type="submit" style={{ background: '#10b981', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer', fontWeight: 600 }}>
          + Add
        </button>
      </form>

      {loading ? (
        <div style={{ color: '#9ca3af', textAlign: 'center', padding: '20px' }}>Loading pantry inventory...</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '12px' }}>
          {items.map(item => (
            <div key={item.id} style={{ background: 'rgba(0, 0, 0, 0.25)', border: '1px solid rgba(255, 255, 255, 0.08)', padding: '12px 16px', borderRadius: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 600, color: '#f3f4f6', fontSize: '14px' }}>{item.name}</div>
                <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '2px' }}>
                  {item.quantity} {item.unit} • {item.category}
                </div>
                <div style={{ marginTop: '6px' }}>{getRiskBadge(item.expiry_risk, item.expiry_days)}</div>
              </div>
              <button
                onClick={() => handleDelete(item.id)}
                style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '16px', padding: '4px' }}
                title="Remove item"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
