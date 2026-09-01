import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AiAssistantPanel } from '../src/components/detail/AiAssistantPanel';
import { RecipeRecommendationItem } from '../src/types/recipe';
import { AssistantResponse } from '../src/types/api';
import * as api from '../src/services/api';

const mockRecipe: RecipeRecommendationItem = {
  recipe_id: 1316605,
  title: 'Bowtie Pasta & Mushrooms',
  ingredients: ['2 cups pasta', '1 cup sliced mushrooms', '2 cloves garlic', '2 tbsp olive oil', '1 tsp fresh basil'],
  directions: ['Step 1: Boil bowtie pasta.', 'Step 2: Sauté garlic and mushrooms in olive oil.', 'Step 3: Toss with basil and serve.'],
  link: 'example.com/recipe',
  source: 'RecipeNLG',
  ner: ['pasta', 'mushrooms', 'garlic', 'olive oil', 'fresh basil'],
  matched_ingredients: ['pasta', 'garlic', 'olive oil'],
  missing_ingredients: ['mushrooms', 'fresh basil'],
  missing_count: 2,
  substitutions: [
    {
      missing_ingredient: 'fresh basil',
      substitute: 'dried basil',
      ratio: '1:0.33',
      confidence: 'high',
      reason: 'Dried basil infuses flavor into warm pasta.',
      dietary_compatible: true,
    },
  ],
  ims: 60.0,
  pus: 100.0,
  recommendation_score: 91.0,
  explanation: 'Recommended because you have 3 of 5 ingredients.',
  explanation_data: {
    matched_ingredients: ['pasta', 'garlic', 'olive oil'],
    missing_ingredients: ['mushrooms', 'fresh basil'],
    matched_count: 3,
    total_recipe_ingredients: 5,
    relevant_pantry_used_count: 3,
    relevant_pantry_total_count: 3,
    ims: 60.0,
    pus: 100.0,
    final_score: 91.0,
    cuisine_bonus: 15.0,
    time_adjustment: 8.0,
  },
  cuisine: 'Italian',
  cuisine_confidence: 'high',
  dietary_compatibility: 'vegan_compatible',
  estimated_time_minutes: 5,
  preference_matches: {},
};

describe('AiAssistantPanel Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders header, quick action chips, and question form', () => {
    render(
      <AiAssistantPanel
        recipe={mockRecipe}
        pantryIngredients={['tomato', 'garlic', 'pasta', 'olive oil']}
      />
    );

    expect(screen.getByText('AI Recipe Guidance & Grounded Assistant')).toBeInTheDocument();
    expect(screen.getByText('Grounded in Recipe Data')).toBeInTheDocument();
    expect(screen.getByText('Why this recipe?')).toBeInTheDocument();
    expect(screen.getByText('Simplify instructions')).toBeInTheDocument();
    expect(screen.getByText('Pantry prep guidance')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Ask a question/i)).toBeInTheDocument();
  });

  it('triggers explain task and displays response with citations and disclaimer', async () => {
    const mockResponse: AssistantResponse = {
      recipe_id: 1316605,
      recipe_title: 'Bowtie Pasta & Mushrooms',
      task: 'explain',
      answer: 'Bowtie Pasta & Mushrooms was recommended because you have 3 of 5 ingredients on hand (pasta, garlic, olive oil).',
      citations: [
        {
          source_type: 'pantry_match',
          detail: 'Available pantry ingredient: pasta',
        },
      ],
      substitutions_used: [],
      unsupported_inquiries: [],
      provider: 'mock',
      model: 'deterministic-rule-grounded',
      is_mock: true,
    };

    vi.spyOn(api, 'askRecipeAssistant').mockResolvedValueOnce(mockResponse);

    render(
      <AiAssistantPanel
        recipe={mockRecipe}
        pantryIngredients={['garlic', 'pasta', 'olive oil']}
      />
    );

    const explainBtn = screen.getByText('Why this recipe?');
    fireEvent.click(explainBtn);

    await waitFor(() => {
      expect(api.askRecipeAssistant).toHaveBeenCalledWith(
        expect.objectContaining({
          recipe_id: 1316605,
          task: 'explain',
        })
      );
    });

    expect(await screen.findByText(/Bowtie Pasta & Mushrooms was recommended/i)).toBeInTheDocument();
    expect(screen.getByText('Recommendation Grounding')).toBeInTheDocument();
    expect(screen.getByText(/Available pantry ingredient: pasta/i)).toBeInTheDocument();
    expect(screen.getByText(/Grounded AI Guidance:/i)).toBeInTheDocument();
  });

  it('submits a custom question and displays answer', async () => {
    const mockResponse: AssistantResponse = {
      recipe_id: 1316605,
      recipe_title: 'Bowtie Pasta & Mushrooms',
      task: 'question',
      answer: 'Yes, according to our curated knowledge base, you can substitute fresh basil with dried basil.',
      citations: [
        {
          source_type: 'curated_substitution',
          detail: 'Verified substitute for fresh basil: dried basil',
        },
      ],
      substitutions_used: ['fresh basil -> dried basil'],
      unsupported_inquiries: [],
      provider: 'mock',
      model: 'deterministic-rule-grounded',
      is_mock: true,
    };

    vi.spyOn(api, 'askRecipeAssistant').mockResolvedValueOnce(mockResponse);

    render(
      <AiAssistantPanel
        recipe={mockRecipe}
        pantryIngredients={['garlic', 'pasta', 'olive oil']}
      />
    );

    const input = screen.getByPlaceholderText(/Ask a question/i);
    fireEvent.change(input, { target: { value: 'Can I substitute fresh basil?' } });

    const submitBtn = screen.getByTitle('Send question to AI Assistant');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(api.askRecipeAssistant).toHaveBeenCalledWith(
        expect.objectContaining({
          recipe_id: 1316605,
          task: 'question',
          question: 'Can I substitute fresh basil?',
        })
      );
    });

    expect(await screen.findByText(/you can substitute fresh basil with dried basil/i)).toBeInTheDocument();
    expect(screen.getByText(/Verified substitute for fresh basil/i)).toBeInTheDocument();
  });

  it('submits a cooking-step question and renders directions-grounded response with citations', async () => {
    const mockResponse: AssistantResponse = {
      recipe_id: 1670510,
      recipe_title: 'Bow tie pasta a la you',
      task: 'question',
      answer: 'According to the recipe directions for Bow tie pasta a la you, cook and prepare the sausage before adding pasta: Step 1: Place 5 johnsonville italian links into a large skillet and cook. Step 3: When done remove links and slice.',
      citations: [
        {
          source_type: 'recipe_directions',
          detail: 'Step 1: Place 5 johnsonville italian links into a large skillet...',
        },
      ],
      substitutions_used: [],
      unsupported_inquiries: [],
      provider: 'mock',
      model: 'deterministic-rule-grounded',
      is_mock: true,
    };

    vi.spyOn(api, 'askRecipeAssistant').mockResolvedValueOnce(mockResponse);

    render(
      <AiAssistantPanel
        recipe={mockRecipe}
        pantryIngredients={['garlic', 'pasta', 'olive oil']}
      />
    );

    const input = screen.getByPlaceholderText(/Ask a question/i);
    fireEvent.change(input, { target: { value: 'How should I cook the sausage before adding the pasta?' } });

    const submitBtn = screen.getByTitle('Send question to AI Assistant');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(api.askRecipeAssistant).toHaveBeenCalledWith(
        expect.objectContaining({
          question: 'How should I cook the sausage before adding the pasta?',
        })
      );
    });

    expect(await screen.findByText(/cook and prepare the sausage before adding pasta/i)).toBeInTheDocument();
    expect(screen.getByTitle('recipe_directions')).toHaveTextContent(/Step 1: Place 5 johnsonville/i);
  });

  it('renders Markdown formatting like bold and lists into HTML elements instead of literal asterisks', async () => {
    const mockResponse: AssistantResponse = {
      recipe_id: 1670510,
      recipe_title: 'Bow tie pasta a la you',
      task: 'question',
      answer: 'According to the recipe directions:\n\n- **Step 1:** Place **sausage** in skillet.\n- **Step 2:** Start **pasta**.\n\n1. First boil water.\n2. Add salt.',
      citations: [],
      substitutions_used: [],
      unsupported_inquiries: [],
      provider: 'mock',
      model: 'deterministic-rule-grounded',
      is_mock: true,
    };

    vi.spyOn(api, 'askRecipeAssistant').mockResolvedValueOnce(mockResponse);

    const { container } = render(
      <AiAssistantPanel
        recipe={mockRecipe}
        pantryIngredients={['garlic', 'pasta', 'olive oil']}
      />
    );

    const input = screen.getByPlaceholderText(/Ask a question/i);
    fireEvent.change(input, { target: { value: 'How do I make this?' } });
    fireEvent.click(screen.getByTitle('Send question to AI Assistant'));

    await waitFor(() => {
      expect(screen.getByTestId('ai-response-box')).toBeInTheDocument();
    });

    const responseContent = container.querySelector('.ai-response-content');
    expect(responseContent).toBeInTheDocument();

    // Verify <strong> elements exist and contain expected bold phrases
    const strongElements = responseContent?.querySelectorAll('strong');
    expect(strongElements && strongElements.length).toBeGreaterThanOrEqual(3);
    const strongTexts = Array.from(strongElements || []).map((el) => el.textContent);
    expect(strongTexts).toContain('Step 1:');
    expect(strongTexts).toContain('sausage');
    expect(strongTexts).toContain('pasta');

    // Verify literal asterisks are NOT present in the rendered HTML
    expect(responseContent?.textContent).not.toContain('**Step 1:**');
    expect(responseContent?.textContent).not.toContain('**sausage**');

    // Verify lists are rendered as <ul> and <ol> elements
    expect(responseContent?.querySelector('ul')).toBeInTheDocument();
    expect(responseContent?.querySelector('ol')).toBeInTheDocument();
  });

  it('handles error gracefully when API fails', async () => {
    vi.spyOn(api, 'askRecipeAssistant').mockRejectedValueOnce(
      new Error('Assistant service is currently offline.')
    );

    render(
      <AiAssistantPanel
        recipe={mockRecipe}
        pantryIngredients={['garlic', 'pasta', 'olive oil']}
      />
    );

    const explainBtn = screen.getByText('Why this recipe?');
    fireEvent.click(explainBtn);

    expect(await screen.findByText('Assistant service is currently offline.')).toBeInTheDocument();
  });
});
