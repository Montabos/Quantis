'use client';

import { TrendingUp, Users, DollarSign, Package } from 'lucide-react';

const suggestions = [
  { label: 'Tréso', icon: DollarSign },
  { label: 'Recrutement', icon: Users },
  { label: 'Investissement', icon: TrendingUp },
  { label: 'Stock', icon: Package },
];

export function SuggestionChips() {
  const handleChipClick = (label: string) => {
    // TODO: Pré-remplir la Decision Bar avec une question liée
    console.log('Chip cliqué:', label);
  };

  return (
    <div className="flex items-center gap-3 flex-wrap justify-center">
      {suggestions.map((suggestion, index) => {
        const Icon = suggestion.icon;
        return (
          <button
            key={index}
            onClick={() => handleChipClick(suggestion.label)}
            className="glass-light px-4 py-2 rounded-full border border-white/30 text-white/90 hover:text-white hover:bg-white/30 transition-all duration-200 flex items-center gap-2 text-sm font-medium backdrop-blur-md shadow-sm hover:shadow-md"
          >
            <Icon className="w-4 h-4" strokeWidth={1.8} />
            <span>{suggestion.label}</span>
          </button>
        );
      })}
    </div>
  );
}

