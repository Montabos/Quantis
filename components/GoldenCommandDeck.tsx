'use client';

import { DecisionBar } from './DecisionBar';
import { SuggestionChips } from './SuggestionChips';

export function GoldenCommandDeck() {
  return (
    <section className="relative h-[30vh] min-h-[350px] w-full golden-gradient overflow-visible">
      {/* Overlays mesh subtils pour enrichir le gradient sans nuire au contraste central */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Highlight - Haut (source de lumière) */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-gradient-radial from-[#FFD966]/30 via-transparent to-transparent blur-[100px]"></div>
        
        {/* Profondeur - Bas */}
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[700px] h-[500px] bg-gradient-radial from-[#E6B84D]/25 via-transparent to-transparent blur-[90px]"></div>
      </div>
      
      {/* Contenu centré */}
      <div className="relative h-full flex flex-col items-center justify-center px-6 py-12 z-10">
        {/* Nom de l'entreprise */}
        <div className="mb-4">
          <h2 className="text-white text-3xl font-light tracking-wide text-center" style={{ letterSpacing: '0.05em' }}>
            Acme Corporation
          </h2>
        </div>
        
        {/* Suggestion Chips au-dessus */}
        <div className="mb-6">
          <SuggestionChips />
        </div>
        
        {/* Decision Bar centrée */}
        <div className="w-full max-w-4xl">
          <DecisionBar />
        </div>
      </div>
    </section>
  );
}

