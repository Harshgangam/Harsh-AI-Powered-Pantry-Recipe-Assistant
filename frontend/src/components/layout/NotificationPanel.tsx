import React, { useState, useEffect } from 'react';
import { Bell } from 'lucide-react';
import { API_BASE } from '../../services/api';

interface AppNotification {
  id: string;
  message: string;
  type: string;
  read: boolean;
  timestamp: string;
}

export const NotificationPanel: React.FC = () => {
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [isOpen, setIsOpen] = useState(false);

  const fetchNotifications = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/pantry/notifications`);
      if (res.ok) {
        const data = await res.json();
        setNotifications(data);
      }
    } catch (e) {
      console.error('Failed to fetch notifications');
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleOpen = async () => {
    setIsOpen(!isOpen);
    if (!isOpen && unreadCount > 0) {
      try {
        await fetch(`${API_BASE}/api/pantry/notifications/read`, { method: 'POST' });
        setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      } catch (e) {}
    }
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
      <button 
        onClick={handleOpen}
        style={{
          background: 'rgba(255, 255, 255, 0.05)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '50%',
          width: '36px',
          height: '36px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#f3f4f6',
          cursor: 'pointer',
          position: 'relative'
        }}
      >
        <Bell size={18} />
        {unreadCount > 0 && (
          <span style={{
            position: 'absolute',
            top: '-4px',
            right: '-4px',
            background: '#ef4444',
            color: 'white',
            fontSize: '10px',
            fontWeight: 'bold',
            width: '16px',
            height: '16px',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            {unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div style={{
          position: 'absolute',
          top: '50px',
          right: '0',
          width: '320px',
          maxHeight: '400px',
          overflowY: 'auto',
          background: '#1e293b',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '12px',
          boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
          zIndex: 50,
          padding: '12px'
        }}>
          <h3 style={{ margin: '0 0 12px', fontSize: '14px', color: '#f8fafc', paddingBottom: '8px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
            Notifications
          </h3>
          {notifications.length === 0 ? (
            <div style={{ padding: '20px', textAlign: 'center', color: '#9ca3af', fontSize: '13px' }}>
              No notifications yet.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {notifications.map(n => {
                // Clean up weird double/single quotes from backend recipe titles
                const cleanMessage = n.message.replace(/['"]+/g, "'");
                
                return (
                  <div key={n.id} style={{
                    padding: '12px 14px',
                    borderRadius: '10px',
                    background: n.type === 'expired' ? 'rgba(239, 68, 68, 0.08)' : 'rgba(16, 185, 129, 0.08)',
                    border: n.type === 'expired' ? '1px solid rgba(239, 68, 68, 0.15)' : '1px solid rgba(16, 185, 129, 0.15)',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
                  }}>
                    <div style={{ fontSize: '13px', color: '#e2e8f0', lineHeight: '1.5', fontWeight: 500 }}>{cleanMessage}</div>
                    <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '6px', fontWeight: 600, letterSpacing: '0.02em' }}>{n.timestamp}</div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
