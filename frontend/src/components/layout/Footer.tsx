import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer
      style={{
        marginTop: '4rem',
        paddingTop: '2rem',
        borderTop: '1px solid var(--border-subtle)',
        textAlign: 'center',
        color: 'var(--text-dim)',
        fontSize: '0.82rem',
      }}
    >
      <p>
        AI-Powered Pantry Intelligence & Food Rescue Assistant
      </p>
    </footer>
  );
};
