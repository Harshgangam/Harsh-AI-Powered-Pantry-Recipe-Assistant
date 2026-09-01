import React, { useState } from 'react';
import { Plus } from 'lucide-react';

interface PantryInputProps {
  onAdd: (ingredient: string) => boolean;
}

export const PantryInput: React.FC<PantryInputProps> = ({ onAdd }) => {
  const [value, setValue] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (value.trim()) {
      onAdd(value);
      setValue('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="input-group">
      <input
        type="text"
        className="text-input"
        placeholder="Add ingredient (e.g. tomato, pasta)..."
        value={value}
        onChange={(e) => setValue(e.target.value)}
        aria-label="Pantry ingredient"
      />
      <button type="submit" className="btn-primary" disabled={!value.trim()}>
        <Plus size={18} />
        <span>Add</span>
      </button>
    </form>
  );
};
