'use client';

import { Zap, TrendingUp, DollarSign, BarChart3 } from 'lucide-react';

const quickActions = [
  {
    icon: TrendingUp,
    label: 'Analyser la trésorerie',
    color: 'bg-[#D4AF37]/10 text-[#D4AF37] hover:bg-[#D4AF37]/20',
  },
  {
    icon: DollarSign,
    label: 'Optimiser le BFR',
    color: 'bg-emerald-50 text-emerald-600 hover:bg-emerald-100',
  },
  {
    icon: BarChart3,
    label: 'Comparer les scénarios',
    color: 'bg-blue-50 text-blue-600 hover:bg-blue-100',
  },
];

export function QuickActionsWidget() {
  return (
    <div className="bg-white rounded-lg border border-[#E5E5E5] p-6 hover:border-[#D4AF37]/30 hover:shadow-sm transition-all duration-200 h-full min-h-[280px]">
      <h3 className="text-[11px] font-medium text-[#737373] uppercase tracking-wider mb-6">Actions Rapides</h3>
      
      <div className="space-y-2">
        {quickActions.map((action, index) => {
          const Icon = action.icon;
          return (
            <button
              key={index}
              className={`w-full px-4 py-3 rounded-lg transition-all duration-150 flex items-center gap-3 ${action.color}`}
            >
              <Icon className="w-4 h-4 flex-shrink-0" strokeWidth={1.5} />
              <span className="text-sm font-medium" style={{ letterSpacing: '-0.01em' }}>
                {action.label}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}







