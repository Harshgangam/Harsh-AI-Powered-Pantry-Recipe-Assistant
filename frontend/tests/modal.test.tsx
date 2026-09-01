import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { RecipeDetailModal } from '../src/components/detail/RecipeDetailModal';
import { RecipeRecommendationItem } from '../src/types/recipe';

const mockRecipe: RecipeRecommendationItem = {
  recipe_id: 12345,
  title: 'Classic Tomato Pasta',
  ingredients: ['2 cups pasta', '1 cup tomato sauce', '2 cloves garlic'],
  directions: ['Step 1: Boil pasta in salted water.', 'Step 2: Simmer tomato sauce.', 'Step 3: Toss and serve.'],
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
      notes: 'Add a pinch of salt.',
    },
  ],
  ims: 66.7,
  pus: 80.0,
  recommendation_score: 87.5,
  explanation: 'Recommended because 2 of 3 ingredients matched your pantry.',
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

describe('RecipeDetailModal Component', () => {
  it('renders complete directions, ingredients breakdown, and substitutions', () => {
    const handleClose = vi.fn();
    render(<RecipeDetailModal recipe={mockRecipe} onClose={handleClose} />);

    // Check title and metrics
    expect(screen.getByText('Classic Tomato Pasta')).toBeInTheDocument();
    expect(screen.getByText('66.7%')).toBeInTheDocument();

    // Check directions
    expect(screen.getByText('Step 1: Boil pasta in salted water.')).toBeInTheDocument();
    expect(screen.getByText('Step 2: Simmer tomato sauce.')).toBeInTheDocument();
    expect(screen.getByText('Step 3: Toss and serve.')).toBeInTheDocument();

    // Check ingredient breakdown
    expect(screen.getByText(/Available in Pantry \(2\)/i)).toBeInTheDocument();
    expect(screen.getByText('pasta')).toBeInTheDocument();
    expect(screen.getByText('garlic')).toBeInTheDocument();
    expect(screen.getByText(/Missing from Pantry \(1\)/i)).toBeInTheDocument();

    // Check substitution panel
    expect(screen.getByText('Suggested Culinary Substitutions (1)')).toBeInTheDocument();
    expect(screen.getByText('tomato paste mixed with water')).toBeInTheDocument();
    expect(screen.getByText(/Ratio 1:1/i)).toBeInTheDocument();
    expect(screen.getByText(/high confidence/i)).toBeInTheDocument();

    // Close button
    const closeBtn = screen.getByRole('button', { name: /close modal/i });
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalled();
  });

  it('renders Vegan-compatible label and avoids duplicated Personalization prefix', () => {
    const veganRecipe: RecipeRecommendationItem = {
      ...mockRecipe,
      dietary_compatibility: 'vegan_compatible',
      explanation:
        'Recommended because 2 of 3 ingredients matched. Personalization: matches your Italian cuisine preference (+15.0 pts, high confidence); satisfies your vegetarian dietary preference (vegan_compatible).',
      preference_explanation:
        'matches your Italian cuisine preference (+15.0 pts, high confidence); satisfies your vegetarian dietary preference (vegan_compatible).',
    };

    render(<RecipeDetailModal recipe={veganRecipe} onClose={vi.fn()} />);

    // Should display Vegan-compatible
    expect(screen.getByText('Vegan-compatible')).toBeInTheDocument();

    // Personalization text should appear exactly once in the explanation box
    const explanationSection = screen.getByText(/Why this recipe was recommended/i).closest('.explanation-box');
    expect(explanationSection).toBeInTheDocument();

    // Verify there is NO 'Personalization: Personalization:' anywhere
    expect(screen.queryByText(/Personalization:\s*Personalization:/i)).not.toBeInTheDocument();

    // Verify 'Personalization:' occurs exactly once in the card text
    const textContent = explanationSection?.textContent || '';
    const occurrences = (textContent.match(/Personalization:/g) || []).length;
    expect(occurrences).toBe(1);
  });
});
