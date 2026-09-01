import { useCallback, useState } from 'react';

export interface PreferencesState {
  cuisine: string | null;
  dietary: string | null;
  maxCookingTime: number | null;
}

export function usePreferences() {
  const [cuisine, setCuisine] = useState<string | null>(null);
  const [dietary, setDietary] = useState<string | null>(null);
  const [maxCookingTime, setMaxCookingTime] = useState<number | null>(null);

  const resetPreferences = useCallback(() => {
    setCuisine(null);
    setDietary(null);
    setMaxCookingTime(null);
  }, []);

  return {
    cuisine,
    setCuisine,
    dietary,
    setDietary,
    maxCookingTime,
    setMaxCookingTime,
    resetPreferences,
  };
}
