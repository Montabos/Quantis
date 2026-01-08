'use client';

import { DecisionTab } from '@/contexts/TabsContext';

export function ProjectionCanvas({ tab }: { tab: DecisionTab }) {
  const chartData = tab.chartData || {
    labels: [],
    datasets: [],
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-6 py-8">
      {/* Titre de la simulation */}
      <div className="mb-6">
        <h1 className="text-2xl font-medium text-[#1A1A1A] mb-2">{tab.query}</h1>
        <p className="text-sm text-[#6B7280]">Simulation en cours...</p>
      </div>

      {/* KPIs Flottants */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-xl border border-[#E0E0E0] p-4">
          <p className="text-xs text-[#6B7280] mb-1">Coût Total</p>
          <p className="text-2xl font-bold text-[#1A1A1A]">85k€</p>
        </div>
        <div className="bg-white rounded-xl border border-[#E0E0E0] p-4">
          <p className="text-xs text-[#6B7280] mb-1">Impact Tréso</p>
          <p className="text-2xl font-bold text-[#1A1A1A]">-12k€</p>
        </div>
        <div className="bg-white rounded-xl border border-[#E0E0E0] p-4">
          <p className="text-xs text-[#6B7280] mb-1">Point Mort</p>
          <p className="text-2xl font-bold text-[#1A1A1A]">+4%</p>
        </div>
      </div>

      {/* Graphique Principal */}
      <div className="bg-white rounded-2xl border border-[#E0E0E0] p-6">
        <h3 className="text-sm font-medium text-[#6B7280] mb-4">Projection de trésorerie</h3>
        
        {/* Graphique simplifié (à remplacer par une vraie librairie de charts) */}
        <div className="h-64 flex items-end justify-between gap-2">
          {chartData.labels.map((label, index) => {
            const value1 = chartData.datasets[0]?.data[index] || 0;
            const value2 = chartData.datasets[1]?.data[index] || 0;
            const maxValue = Math.max(...chartData.datasets.flatMap(d => d.data), 70000);
            
            return (
              <div key={index} className="flex-1 flex flex-col items-center gap-2">
                <div className="w-full flex flex-col items-center gap-1">
                  {/* Barres pour visualisation */}
                  <div className="w-full flex gap-0.5">
                    <div
                      className="flex-1 bg-[#6B7280]/30 rounded-t"
                      style={{ height: `${(value1 / maxValue) * 200}px` }}
                    />
                    <div
                      className="flex-1 bg-[#1A1A1A] rounded-t"
                      style={{ height: `${(value2 / maxValue) * 200}px` }}
                    />
                  </div>
                </div>
                <span className="text-xs text-[#6B7280]">{label}</span>
              </div>
            );
          })}
        </div>

        {/* Légende */}
        <div className="flex items-center gap-4 mt-4 pt-4 border-t border-[#E0E0E0]">
          {chartData.datasets.map((dataset, index) => (
            <div key={index} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: dataset.color }}
              />
              <span className="text-sm text-[#6B7280]">{dataset.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Interprétation Stratégique */}
      <div className="mt-6 bg-white rounded-2xl border border-[#E0E0E0] p-6">
        <h3 className="text-sm font-medium text-[#6B7280] mb-3">Interprétation stratégique</h3>
        <p className="text-sm text-[#1A1A1A] leading-relaxed">
          La simulation indique que cette décision est soutenable, mais attention : votre trésorerie passera en zone de tension (sous les 15k€) en mars. 
          <strong className="text-[#1A1A1A]"> Conseil : </strong>
          Négociez un délai de paiement fournisseur ou décalez l&apos;embauche d&apos;un mois pour sécuriser.
        </p>
      </div>
    </div>
  );
}

