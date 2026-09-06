import React, { useState } from 'react';
import { Search, Flame, LayoutDashboard, ShoppingBag, UtensilsCrossed, Repeat, LineChart } from 'lucide-react';
import { Header } from './components/layout/Header';
import { Footer } from './components/layout/Footer';
import { PantryInput } from './components/pantry/PantryInput';
import { PantryTagList } from './components/pantry/PantryTagList';
import { PantryManagement } from './components/pantry/PantryManagement';
import { PreferenceControls } from './components/preferences/PreferenceControls';
import { RecipeCard } from './components/recommendations/RecipeCard';
import { EmptyState } from './components/recommendations/EmptyState';
import { LoadingSkeleton } from './components/common/LoadingSkeleton';
import { ErrorAlert } from './components/common/ErrorAlert';
import { RecipeDetailModal } from './components/detail/RecipeDetailModal';
import { LeftoversAndChains } from './components/leftovers/LeftoversAndChains';
import { SustainabilityDashboard } from './components/analytics/SustainabilityDashboard';
import { usePantry } from './hooks/usePantry';
import { usePreferences } from './hooks/usePreferences';
import { useRecommendations } from './hooks/useRecommendations';
import { RecipeRecommendationItem } from './types/recipe';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'pantry' | 'recipes' | 'leftovers' | 'analytics'>('dashboard');
  const [rescueMode, setRescueMode] = useState<boolean>(false);

  const { ingredients, addIngredient, removeIngredient, clearPantry, addMultiple } = usePantry([]);

  const preferences = usePreferences();
  const { data, loading, error, search } = useRecommendations();
  const [selectedRecipe, setSelectedRecipe] = useState<RecipeRecommendationItem | null>(null);
  // Incrementing this forces PantryManagement to remount and re-fetch from backend
  const [pantryRefreshKey, setPantryRefreshKey] = useState(0);

  const handleSearch = (mode: boolean = rescueMode) => {
    setActiveTab('recipes');
    search(ingredients, preferences, 10, mode);
  };

  const handleAddStaples = () => {
    addMultiple(['tomato', 'garlic', 'onion', 'pasta', 'olive oil']);
  };

  const hasRecommendations = data && data.recommendations && data.recommendations.length > 0;
  const isZeroResults = data && data.recommendations && data.recommendations.length === 0;

  return (
    <div className="app-container">
      <Header />

      {/* Navigation Tabs Bar */}
      <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', marginBottom: '24px', paddingBottom: '4px', borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
        <button
          onClick={() => setActiveTab('dashboard')}
          style={{ background: activeTab === 'dashboard' ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : 'rgba(255,255,255,0.05)', color: '#fff', border: 'none', padding: '10px 18px', borderRadius: '10px', cursor: 'pointer', fontWeight: 600, fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <LayoutDashboard size={16} />
          <span>Dashboard</span>
        </button>
        <button
          onClick={() => setActiveTab('pantry')}
          style={{ background: activeTab === 'pantry' ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : 'rgba(255,255,255,0.05)', color: '#fff', border: 'none', padding: '10px 18px', borderRadius: '10px', cursor: 'pointer', fontWeight: 600, fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <ShoppingBag size={16} />
          <span>Pantry Intelligence ({ingredients.length})</span>
        </button>
        <button
          onClick={() => { setActiveTab('recipes'); if (!data) handleSearch(rescueMode); }}
          style={{ background: activeTab === 'recipes' ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : 'rgba(255,255,255,0.05)', color: '#fff', border: 'none', padding: '10px 18px', borderRadius: '10px', cursor: 'pointer', fontWeight: 600, fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <UtensilsCrossed size={16} />
          <span>Recipe Recommendations</span>
        </button>
        <button
          onClick={() => setActiveTab('leftovers')}
          style={{ background: activeTab === 'leftovers' ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : 'rgba(255,255,255,0.05)', color: '#fff', border: 'none', padding: '10px 18px', borderRadius: '10px', cursor: 'pointer', fontWeight: 600, fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <Repeat size={16} />
          <span>Leftovers & Chain Plan</span>
        </button>
        <button
          onClick={() => setActiveTab('analytics')}
          style={{ background: activeTab === 'analytics' ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : 'rgba(255,255,255,0.05)', color: '#fff', border: 'none', padding: '10px 18px', borderRadius: '10px', cursor: 'pointer', fontWeight: 600, fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <LineChart size={16} />
          <span>Sustainability Analytics</span>
        </button>
      </div>

      {/* Main Tab Views */}
      {activeTab === 'pantry' && <PantryManagement key={pantryRefreshKey} />}

      {activeTab === 'leftovers' && <LeftoversAndChains />}

      {activeTab === 'analytics' && <SustainabilityDashboard />}

      {(activeTab === 'dashboard' || activeTab === 'recipes') && (
        <main className="main-grid">
          {/* Left Column: Pantry & Personalization Controls */}
          <aside className="sidebar-card">
            {/* Pantry Rescue Mode Banner Toggle */}
            <div style={{ background: rescueMode ? 'linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(245, 158, 11, 0.2))' : 'rgba(0,0,0,0.2)', border: rescueMode ? '1px solid #ef4444' : '1px solid rgba(255,255,255,0.1)', padding: '14px', borderRadius: '12px', marginBottom: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Flame size={18} color={rescueMode ? '#ef4444' : '#9ca3af'} />
                  <div>
                    <div style={{ fontWeight: 700, color: '#fff', fontSize: '13px' }}>Pantry Rescue Mode</div>
                    <div style={{ fontSize: '11px', color: '#9ca3af' }}>Prioritizes expiring ingredients (FRPS)</div>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={rescueMode}
                  onChange={e => {
                    setRescueMode(e.target.checked);
                    if (ingredients.length > 0) handleSearch(e.target.checked);
                  }}
                  style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                />
              </div>
            </div>

            <div>
              <div className="section-header">
                <h2 className="section-title">Your Kitchen Pantry</h2>
                <span className="section-badge">{ingredients.length} items</span>
              </div>
              <PantryInput onAdd={addIngredient} />
            </div>




            <PantryTagList
              ingredients={ingredients}
              onRemove={removeIngredient}
              onClear={clearPantry}
            />

            <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '1.5rem' }}>
              <PreferenceControls
                cuisine={preferences.cuisine}
                setCuisine={preferences.setCuisine}
                dietary={preferences.dietary}
                setDietary={preferences.setDietary}
                maxCookingTime={preferences.maxCookingTime}
                setMaxCookingTime={preferences.setMaxCookingTime}
                onReset={preferences.resetPreferences}
              />
            </div>

            <button
              type="button"
              className="btn-primary btn-action-full"
              onClick={() => handleSearch(rescueMode)}
              disabled={loading || ingredients.length === 0}
            >
              <Search size={18} />
              <span>{loading ? 'Finding Recipes...' : `Find Food Rescue Meals (${ingredients.length} Items)`}</span>
            </button>
          </aside>

          {/* Right Column: Recommendations & Results */}
          <section>
            {error && <ErrorAlert message={error} onDismiss={() => {}} />}

            {loading && <LoadingSkeleton />}

            {!loading && !data && (
              <EmptyState type="initial" />
            )}

            {!loading && isZeroResults && (
              <EmptyState type="no-results" onAddStaples={handleAddStaples} />
            )}

            {!loading && hasRecommendations && (
              <div>
                <div className="results-header">
                  <div>
                    <h2 className="results-count">
                      Ranked Food Rescue Recommendations ({data.recommendations.length})
                    </h2>
                    <span style={{ fontSize: '0.82rem', color: 'var(--text-dim)' }}>
                      Evaluated {data.total_candidates_evaluated} candidates from 2.23M corpus {rescueMode ? '• [Pantry Rescue Mode Active]' : ''}
                    </span>
                  </div>
                </div>

                <div className="recipe-cards-grid">
                  {data.recommendations.map((recipe) => (
                    <RecipeCard
                      key={recipe.recipe_id}
                      recipe={recipe}
                      onSelect={setSelectedRecipe}
                    />
                  ))}
                </div>
              </div>
            )}
          </section>
        </main>
      )}

      {/* Recipe Detail & Substitution Modal */}
      <RecipeDetailModal
        recipe={selectedRecipe}
        pantryIngredients={ingredients}
        appliedPreferences={{
          cuisine: preferences.cuisine,
          dietary_preference: preferences.dietary,
          max_cooking_time_minutes: preferences.maxCookingTime,
        }}
        onClose={() => setSelectedRecipe(null)}
        onCooked={(usedNer: string[]) => {
          // Remove cooked ingredients from the frontend tag pills
          for (const ing of usedNer) {
            removeIngredient(ing);
          }
          // Force Dynamic Pantry Intelligence to re-fetch — cooked items will disappear
          setPantryRefreshKey(k => k + 1);
        }}
      />

      <Footer />
    </div>
  );
};

export default App;
