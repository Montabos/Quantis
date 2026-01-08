'use client';

import { TrendingUp } from 'lucide-react';

export function DormantMoneyWidget() {
  const amount = 24000;
  const insight = 'Stocks lents détectés';
  
  // Données pour le sparkline (mini-graphique)
  const sparklineData = [20, 25, 22, 28, 30, 27, 32, 28, 35, 32, 38, 35];

  return (
    <div className="bg-white rounded-lg border border-[#E5E5E5] p-6 hover:border-[#D4AF37]/30 hover:shadow-sm transition-all duration-200 cursor-pointer h-full min-h-[280px] group">
      <div className="flex items-center justify-between h-full gap-6">
        {/* Partie gauche : Chiffre et insight */}
        <div className="flex-1 min-w-0">
          <h3 className="text-[11px] font-medium text-[#737373] uppercase tracking-wider mb-5">Argent Dormant</h3>
          <div className="mb-5">
            <span className="text-4xl font-semibold text-[#1A1A1A] block group-hover:text-[#D4AF37] transition-colors duration-200" style={{ letterSpacing: '-0.03em', fontFamily: 'ui-monospace, monospace' }}>
              {amount.toLocaleString('fr-FR')} €
            </span>
          </div>
          <p className="text-xs font-medium text-[#737373] flex items-center gap-2">
            <TrendingUp className="w-3.5 h-3.5 text-[#D4AF37] flex-shrink-0" strokeWidth={1.5} />
            <span style={{ letterSpacing: '-0.01em' }}>{insight}</span>
          </p>
        </div>
        
        {/* Partie droite : Sparkline - Style Notion ultra-minimaliste */}
        <div className="flex-shrink-0 flex items-center justify-end">
          <svg width="120" height="60" className="text-[#D4AF37]">
            <defs>
              <linearGradient id="sparklineGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="currentColor" stopOpacity="0.2" />
                <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
              </linearGradient>
            </defs>
            <polyline
              points={sparklineData.map((value, index) => {
                const x = (index / (sparklineData.length - 1)) * 100 + 10;
                const y = 50 - (value / 40) * 40;
                return `${x},${y}`;
              }).join(' ')}
              fill="url(#sparklineGradient)"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="transition-all duration-300"
            />
          </svg>
        </div>
      </div>
    </div>
  );
}

