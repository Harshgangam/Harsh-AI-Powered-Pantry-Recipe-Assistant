import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  Sparkles,
  Send,
  Loader2,
  AlertCircle,
  CheckCircle2,
  HelpCircle,
  ChefHat,
  FileText,
  Lightbulb,
} from 'lucide-react';
import { RecipeRecommendationItem } from '../../types/recipe';
import { AssistantResponse, AssistantTask } from '../../types/api';
import { askRecipeAssistant } from '../../services/api';

interface AiAssistantPanelProps {
  recipe: RecipeRecommendationItem;
  pantryIngredients?: string[];
  appliedPreferences?: {
    cuisine?: string | null;
    dietary_preference?: string | null;
    max_cooking_time_minutes?: number | null;
  };
}

export const AiAssistantPanel: React.FC<AiAssistantPanelProps> = ({
  recipe,
  pantryIngredients = [],
  appliedPreferences = {},
}) => {
  const [task, setTask] = useState<AssistantTask>('explain');
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState<AssistantResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleTriggerTask = async (selectedTask: AssistantTask, customQ?: string) => {
    setLoading(true);
    setError(null);
    setTask(selectedTask);

    try {
      const res = await askRecipeAssistant({
        recipe_id: recipe.recipe_id,
        task: selectedTask,
        question: customQ || (selectedTask === 'question' ? question : undefined),
        pantry_ingredients: pantryIngredients,
        cuisine: appliedPreferences.cuisine,
        dietary_preference: appliedPreferences.dietary_preference,
        max_cooking_time_minutes: appliedPreferences.max_cooking_time_minutes,
      });
      setResponse(res);
      if (selectedTask === 'question') {
        setQuestion('');
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to generate recipe guidance. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || loading) return;
    handleTriggerTask('question', question.trim());
  };

  return (
    <div className="ai-assistant-panel" data-testid="ai-assistant-panel">
      {/* Panel Header */}
      <div className="ai-assistant-header">
        <div className="ai-assistant-title-group">
          <div className="ai-icon-bubble">
            <Sparkles size={18} className="ai-sparkle-icon" />
          </div>
          <div>
            <h4 className="ai-assistant-title">AI Recipe Guidance & Grounded Assistant</h4>
            <span className="ai-assistant-subtitle">
              Entity-Grounded RAG powered strictly by authoritative recipe directions and curated substitutions
            </span>
          </div>
        </div>
        <div className="ai-status-badges">
          <span className="ai-badge-grounded">
            <CheckCircle2 size={12} />
            <span>Grounded in Recipe Data</span>
          </span>
          {response && (
            <span className="ai-badge-provider">
              {response.is_mock ? 'Offline Mode' : response.model}
            </span>
          )}
        </div>
      </div>

      {/* Quick Prompt Action Chips */}
      <div className="ai-chips-container">
        <span className="ai-chips-label">Quick Actions:</span>
        <button
          type="button"
          className={`ai-chip-btn ${task === 'explain' && response ? 'active' : ''}`}
          onClick={() => handleTriggerTask('explain')}
          disabled={loading}
        >
          <Lightbulb size={13} />
          <span>Why this recipe?</span>
        </button>

        <button
          type="button"
          className={`ai-chip-btn ${task === 'simplify' && response ? 'active' : ''}`}
          onClick={() => handleTriggerTask('simplify')}
          disabled={loading}
        >
          <FileText size={13} />
          <span>Simplify instructions</span>
        </button>

        <button
          type="button"
          className={`ai-chip-btn ${task === 'guidance' && response ? 'active' : ''}`}
          onClick={() => handleTriggerTask('guidance')}
          disabled={loading}
        >
          <ChefHat size={13} />
          <span>Pantry prep guidance</span>
        </button>
      </div>

      {/* Custom Question Input Form */}
      <form onSubmit={handleFormSubmit} className="ai-input-form">
        <div className="ai-input-wrapper">
          <HelpCircle size={16} className="ai-input-icon" />
          <input
            type="text"
            className="ai-question-input"
            placeholder="Ask a question (e.g. 'Can I make this without basil?', 'What temperature?')..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            maxLength={300}
            disabled={loading}
            aria-label="Ask AI about this recipe"
          />
          <button
            type="submit"
            className="ai-send-btn"
            disabled={loading || !question.trim()}
            title="Send question to AI Assistant"
            aria-label="Submit question"
          >
            {loading ? <Loader2 size={16} className="spinner-icon" /> : <Send size={16} />}
          </button>
        </div>
        <div className="ai-input-footer">
          <span className="ai-char-count">{question.length}/300 chars</span>
          <span className="ai-grounding-hint">
            The AI only uses verified substitutions from the curated knowledge base.
          </span>
        </div>
      </form>

      {/* Error Display */}
      {error && (
        <div className="ai-error-box">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Response Box */}
      {loading && !response && (
        <div className="ai-loading-box">
          <Loader2 size={24} className="spinner-icon" />
          <span>Retrieving recipe context and generating grounded guidance...</span>
        </div>
      )}

      {response && (
        <div className="ai-response-box" data-testid="ai-response-box">
          <div className="ai-response-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Sparkles size={14} style={{ color: 'var(--color-primary-light)' }} />
              <span className="ai-response-title">
                {response.task === 'explain' && 'Recommendation Grounding'}
                {response.task === 'simplify' && 'Simplified Cooking Directions'}
                {response.task === 'guidance' && 'Pantry Preparation & Cooking Sequence'}
                {response.task === 'question' && 'Grounded Recipe Answer'}
              </span>
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
              Target: {response.recipe_title}
            </span>
          </div>

          <div className="ai-response-content">
            <ReactMarkdown>{response.answer}</ReactMarkdown>
          </div>

          {/* Grounding Citations */}
          {response.citations && response.citations.length > 0 && (
            <div className="ai-citations-section">
              <span className="ai-citations-heading">Grounded Knowledge Citations:</span>
              <div className="ai-citations-list">
                {response.citations.map((cite, idx) => (
                  <span key={idx} className="ai-citation-tag" title={cite.source_type}>
                    🏷️ {cite.detail}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Academic Grounding & Disclaimer Banner */}
          <div className="ai-disclaimer-banner">
            <span style={{ fontWeight: 600 }}>Grounded AI Guidance:</span> Generated using authoritative
            recipe directions, verified pantry match data, and curated substitution intelligence.
            Does not override deterministic ranking scores or invent unverified alternatives.
          </div>
        </div>
      )}
    </div>
  );
};
