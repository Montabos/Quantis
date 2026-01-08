'use client';

import { Sparkles, Search } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { AnalysisModal } from './decision/AnalysisModal';

export function DecisionBar() {
  const [isFocused, setIsFocused] = useState(false);
  const [query, setQuery] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalQuestion, setModalQuestion] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const suggestions = [
    'Puis-je me permettre de recruter un directeur commercial ce mois-ci ?',
    'Comment optimiser mon stock ?',
    'Quel est l\'impact d\'une augmentation de prix de 5% ?',
    'Dois-je investir dans de nouveaux équipements ?',
    'Comment réduire mon BFR ?',
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      // Ouvrir la modal d'analyse
      setModalQuestion(query);
      setIsModalOpen(true);
      setQuery('');
      setIsFocused(false);
      setShowSuggestions(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  useEffect(() => {
    if (isFocused && query.length === 0) {
      setShowSuggestions(true);
    } else if (!isFocused) {
      setShowSuggestions(false);
    }
  }, [isFocused, query]);

  return (
    <div className="w-full relative">
      <form onSubmit={handleSubmit} className="relative">
        <div
          className={`relative glass-dark rounded-full shadow-2xl border transition-all duration-300 ${
            isFocused
              ? 'border-white/20 shadow-2xl scale-[1.02]'
              : 'border-white/10 shadow-xl'
          }`}
        >
          <div className="flex items-center px-6 py-4 gap-4">
            {/* Icône gauche */}
            <div className="flex-shrink-0">
              <Sparkles 
                className={`w-5 h-5 transition-colors ${
                  isFocused ? 'text-white' : 'text-white/70'
                }`} 
                strokeWidth={1.8} 
              />
            </div>

            {/* Input */}
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => {
                // Délai pour permettre le clic sur les suggestions
                setTimeout(() => setIsFocused(false), 200);
              }}
              placeholder="Quelle décision stratégique voulez-vous prendre ?"
              className="flex-1 bg-transparent border-none outline-none text-white placeholder-white/60 text-base font-normal"
              style={{ fontSize: '15px' }}
            />

            {/* Bouton submit (flèche) */}
            {query.trim() && (
              <button
                type="submit"
                className="flex-shrink-0 w-8 h-8 rounded-full bg-white/20 hover:bg-white/30 text-white flex items-center justify-center transition-colors backdrop-blur-sm"
                aria-label="Poser la question"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 7l5 5m0 0l-5 5m5-5H6"
                  />
                </svg>
              </button>
            )}
          </div>
        </div>

        {/* Dropdown de suggestions (en dessous) */}
        {showSuggestions && (
          <div className="absolute top-full left-0 right-0 mt-2 glass-dark rounded-2xl shadow-2xl border border-white/20 overflow-hidden z-[100]">
            <div className="py-2">
              <div className="px-4 py-2 text-xs font-medium text-white/70 uppercase tracking-wider">
                Questions fréquentes
              </div>
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="w-full text-left px-6 py-3 hover:bg-white/10 transition-colors text-sm text-white flex items-start gap-3 group"
                >
                  <Search className="w-4 h-4 text-white/60 mt-0.5 flex-shrink-0 group-hover:text-white transition-colors" strokeWidth={1.8} />
                  <span className="flex-1">{suggestion}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </form>

      {/* Analysis Modal */}
      <AnalysisModal
        question={modalQuestion}
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setModalQuestion('');
        }}
      />
    </div>
  );
}

