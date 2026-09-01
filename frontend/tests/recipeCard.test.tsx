import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { RecipeCard } from '../src/components/recommendations/RecipeCard';
import { RecipeRecommendationItem } from '../src/types/recipe';

const mockRecipe: RecipeRecommendationItem = {
  recipe_id: 12345,
  title: 'Classic Tomato Pasta',
  ingredients: ['2 cups pasta', '1 cup tomato sauce', '2 cloves garlic'],
  directions: ['Boil pasta.', 'Simmer sauce with garlic.', 'Combine and serve.'],
  link: 'example.com/recipe',
  source: 'RecipeNLG',
  ner: ['pasta', 'tomato sauce', 'garlic'],
  matched_ingredients: ['pasta', 'garlic'],
  missing_ingredients: ['tomato sauce'],
  missing_count: 1,
  substitutions: [
    {
      missing_ingredient: 'tomato sauce',
      substitute: 'tomato paste mixed with water',
      ratio: '1:1',
      confidence: 'high',
      reason: 'Reconstituting tomato paste matches sauce consistency.',
      dietary_compatible: true,
    },
  ],
  ims: 66.7,
  pus: 80.0,
  recommendation_score: 87.5,
  explanation: 'Recommended because 2 of 3 ingredients matched.',
  explanation_data: {
    matched_ingredients: ['pasta', 'garlic'],
    missing_ingredients: ['tomato sauce'],
    matched_count: 2,
    total_recipe_ingredients: 3,
    relevant_pantry_used_count: 2,
    relevant_pantry_total_count: 3,
    ims: 66.7,
    pus: 80.0,
    final_score: 87.5,
    cuisine_bonus: 15.0,
    time_adjustment: 0.0,
  },
  cuisine: 'Italian',
  cuisine_confidence: 'high',
  dietary_compatibility: 'vegetarian_compatible',
  estimated_time_minutes: 25,
  preference_matches: {},
};

describe('RecipeCard Component', () => {
  it('renders recipe title, scores, and metadata correctly', () => {
    const handleSelect = vi.fn();
    render(<RecipeCard recipe={mockRecipe} onSelect={handleSelect} />);

    expect(screen.getByText('Classic Tomato Pasta')).toBeInTheDocument();
    expect(screen.getByText('87.5')).toBeInTheDocument();
    expect(screen.getByText('66.7%')).toBeInTheDocument();
    expect(screen.getByText('80.0%')).toBeInTheDocument();
    expect(screen.getByText('Italian')).toBeInTheDocument();
    expect(screen.getByText('25 mins')).toBeInTheDocument();
    expect(screen.getByText('Vegetarian-compatible')).toBeInTheDocument();
    expect(screen.getByText(/1 missing/i)).toBeInTheDocument();

    const card = screen.getByRole('button');
    fireEvent.click(card);
    expect(handleSelect).toHaveBeenCalledWith(mockRecipe);
  });
});
