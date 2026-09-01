import { useCallback, useState } from 'react';

export function usePantry(initialIngredients: string[] = []) {
  const [ingredients, setIngredients] = useState<string[]>(initialIngredients);

  const addIngredient = useCallback((rawItem: string): boolean => {
    if (!rawItem || !rawItem.trim()) return false;
    
    // Support comma-separated pastes e.g. "tomato, garlic, pasta"
    const items = rawItem
      .split(',')
      .map((i) => i.trim().toLowerCase())
      .filter((i) => i.length > 0);

    let addedCount = 0;
    setIngredients((prev) => {
      const existing = new Set(prev.map((i) => i.toLowerCase()));
      const next = [...prev];
      for (const item of items) {
        if (!existing.has(item)) {
          existing.add(item);
          next.push(item);
          addedCount++;
        }
      }
      return next;
    });

    return addedCount > 0;
  }, []);

  const removeIngredient = useCallback((itemToRemove: string) => {
    setIngredients((prev) =>
      prev.filter((i) => i.toLowerCase() !== itemToRemove.toLowerCase())
    );
  }, []);

  const clearPantry = useCallback(() => {
    setIngredients([]);
  }, []);

  const addMultiple = useCallback((newItems: string[]) => {
    setIngredients((prev) => {
      const existing = new Set(prev.map((i) => i.toLowerCase()));
      const next = [...prev];
      for (const item of newItems) {
        const norm = item.trim().toLowerCase();
        if (norm && !existing.has(norm)) {
          existing.add(norm);
          next.push(norm);
        }
      }
      return next;
    });
  }, []);

  return {
    ingredients,
    addIngredient,
    removeIngredient,
    clearPantry,
    addMultiple,
  };
}
