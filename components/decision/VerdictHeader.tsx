'use client';

import { DecisionTab } from '@/contexts/TabsContext';
import { AlertTriangle, CheckCircle2, AlertCircle } from 'lucide-react';

export function VerdictHeader({ tab }: { tab: DecisionTab }) {
  const chartData = tab.chartData || {
    labels: [],
    datasets: [],
  };

  // Calculer le verdict basé sur les données
  const getVerdict = () => {
    const minValue = Math.min(...(chartData.datasets[1]?.data || []));
    if (minValue < 15000) {
      return {
        status: 'risky',
        badge: 'RISQUÉ',
        title: 'Ce recrutement fait plonger votre trésorerie sous le seuil de sécurité en Mars.',
        color: 'bg-amber-50 border-amber-200 text-amber-900',
        icon: AlertTriangle,
        bgGradient: 'from-amber-50 to-amber-100/50',
      };
    } else if (minValue < 30000) {
      return {
        status: 'warning',
        badge: 'ATTENTION',
        title: 'Cette décision réduit votre marge de sécurité mais reste gérable avec des précautions.',
        color: 'bg-yellow-50 border-yellow-200 text-yellow-900',
        icon: AlertCircle,
        bgGradient: 'from-yellow-50 to-yellow-100/50',
      };
    } else {
      return {
        status: 'favorable',
        badge: 'FAVORABLE',
        title: 'Cette décision est soutenable financièrement sur l\'année.',
        color: 'bg-emerald-50 border-emerald-200 text-emerald-900',
        icon: CheckCircle2,
        bgGradient: 'from-emerald-50 to-emerald-100/50',
      };
    }
  };

  const verdict = getVerdict();
  const VerdictIcon = verdict.icon;

  return (
    <div className={`mb-12 p-8 rounded-2xl border-2 ${verdict.color} bg-gradient-to-br ${verdict.bgGradient}`}>
      <div className="flex items-start gap-6">
        <div className="flex-shrink-0">
          <div className="w-16 h-16 rounded-full bg-white/80 flex items-center justify-center">
            <VerdictIcon className="w-8 h-8" strokeWidth={2} />
          </div>
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-4 mb-3">
            <span className="text-3xl font-bold">{verdict.badge}</span>
            <div className="h-px flex-1 bg-current opacity-20"></div>
          </div>
          <h1 className="text-2xl font-light text-[#1A1A1A] mb-2 leading-relaxed">
            {tab.query}
          </h1>
          <p className="text-lg font-medium leading-relaxed">{verdict.title}</p>
        </div>
      </div>
    </div>
  );
}

