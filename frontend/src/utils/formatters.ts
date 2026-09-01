export function formatScore(score: number | undefined | null): string {
  if (score === undefined || score === null) return '0.0';
  return Number(score).toFixed(1);
}

export function formatTime(minutes: number | undefined | null): string {
  if (!minutes || minutes <= 0) return 'Unspecified';
  if (minutes < 60) return `${minutes} mins`;
  const hours = Math.floor(minutes / 60);
  const remaining = minutes % 60;
  return remaining > 0 ? `${hours}h ${remaining}m` : `${hours}h`;
}

export function getScoreColorClass(score: number): string {
  if (score >= 80) return 'score-high';
  if (score >= 50) return 'score-medium';
  return 'score-low';
}

export function getDietaryLabel(code: string | undefined | null): string {
  if (!code) return 'Standard';
  switch (code.toLowerCase()) {
    case 'vegan_compatible':
      return 'Vegan-compatible';
    case 'vegetarian_compatible':
      return 'Vegetarian-compatible';
    case 'non_vegetarian':
      return 'Non-Vegetarian';
    default:
      return code.replace('_', ' ');
  }
}
