'use client';

import { Sparkles, ArrowRight } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { AnalysisModal } from './decision/AnalysisModal';

export function HeroDecisionBar() {
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
    <div className="w-full">
      <form onSubmit={handleSubmit} className="relative">
        {/* Hero Decision Bar - Style doré élégant et compact */}
        <div
          className={`relative bg-gradient-to-r from-[#D4AF37]/10 via-[#D4AF37]/5 to-white rounded-lg border transition-all duration-200 ${
            isFocused
              ? 'border-[#D4AF37] shadow-lg shadow-[#D4AF37]/20 scale-[1.01]'
              : 'border-[#D4AF37]/30 hover:border-[#D4AF37]/50 hover:shadow-md'
          }`}
          style={{ borderRadius: '10px' }}
        >
          <div className="flex items-center px-4 py-3 gap-3">
            {/* Icône gauche - Sparkles dorée */}
            <div className="flex-shrink-0">
              <Sparkles 
                className={`w-4 h-4 transition-colors duration-200 ${
                  isFocused ? 'text-[#D4AF37]' : 'text-[#D4AF37]/70'
                }`} 
                strokeWidth={2} 
              />
            </div>

            {/* Input - Style compact */}
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => {
                setTimeout(() => setIsFocused(false), 200);
              }}
              placeholder="Ex: Puis-je me permettre de recruter un directeur commercial ?"
              className="flex-1 bg-transparent border-none outline-none text-[#1A1A1A] placeholder-[#737373] font-normal"
              style={{ fontSize: '15px', letterSpacing: '-0.01em' }}
            />

            {/* Bouton submit - Accent doré Quantis */}
            {query.trim() && (
              <button
                type="submit"
                className="flex-shrink-0 w-8 h-8 rounded-md bg-[#D4AF37] hover:bg-[#B8941F] text-white flex items-center justify-center transition-all duration-200 shadow-sm hover:shadow-md hover:scale-105"
                aria-label="Poser la question"
              >
                <ArrowRight className="w-3.5 h-3.5" strokeWidth={2.5} />
              </button>
            )}
          </div>
        </div>

        {/* Dropdown de suggestions - Style Notion ultra-épuré */}
        {showSuggestions && (
          <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-lg shadow-xl border border-[#E5E5E5] overflow-hidden z-50 animate-slide-up">
            <div className="py-1">
              <div className="px-4 py-2 text-[11px] font-medium text-[#737373] uppercase tracking-wider">
                Questions fréquentes
              </div>
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="w-full text-left px-4 py-2.5 hover:bg-[#FAFAFA] transition-colors duration-150 text-sm text-[#1A1A1A] flex items-start gap-3 group"
                >
                  <Sparkles className="w-3.5 h-3.5 text-[#737373] mt-0.5 flex-shrink-0 group-hover:text-[#D4AF37] transition-colors duration-150" strokeWidth={1.5} />
                  <span className="flex-1 leading-relaxed" style={{ letterSpacing: '-0.01em' }}>{suggestion}</span>
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

