'use client';

import { ChartData } from '@/contexts/TabsContext';

export function ProjectionsChart({ chartData }: { chartData: ChartData }) {
  const maxValue = Math.max(...chartData.datasets.flatMap((d) => d.data), 70000);
  const dangerZone = 15000;

  // Générer plusieurs scénarios de projection
  const scenarios = [
    {
      name: 'Scénario Optimiste',
      data: chartData.datasets[1]?.data.map((val, i) => {
        const base = chartData.datasets[0]?.data[i] || 0;
        return Math.min(base * 1.15, val + 10000);
      }) || [],
      color: '#10B981',
      strokeDasharray: '4 4',
    },
    {
      name: 'Scénario Actuel',
      data: chartData.datasets[0]?.data || [],
      color: '#6B7280',
      strokeDasharray: '0',
    },
    {
      name: 'Scénario Simulé',
      data: chartData.datasets[1]?.data || [],
      color: '#1A1A1A',
      strokeDasharray: '8 4',
    },
    {
      name: 'Scénario Pessimiste',
      data: chartData.datasets[1]?.data.map((val) => Math.max(val - 8000, dangerZone - 5000)) || [],
      color: '#EF4444',
      strokeDasharray: '2 2',
    },
  ];

  return (
    <div className="mb-16">
      <div className="bg-white rounded-lg border border-[#E0E0E0] p-8">
        <div className="mb-8">
          <h3 className="text-xs font-medium text-[#6B7280] mb-2 uppercase tracking-wider">
            Projections Multi-Scénarios
          </h3>
          <p className="text-sm text-[#6B7280] font-light leading-relaxed">
            Visualisation de tous les scénarios possibles pour cette décision stratégique
          </p>
        </div>
        
        <div className="relative h-[500px]">
          {/* Zone de danger */}
          <div
            className="absolute bottom-0 left-0 right-0 bg-red-500/8 border-t border-red-500/20 rounded-b-lg"
            style={{
              height: `${(dangerZone / maxValue) * 100}%`,
            }}
          >
            <div className="absolute top-0 left-0 right-0 px-4 py-2">
              <span className="text-xs font-medium text-red-600">Zone de danger (&lt; 15k€)</span>
            </div>
          </div>

          {/* Graphique SVG avec toutes les projections */}
          <svg className="w-full h-full" viewBox="0 0 1000 500" preserveAspectRatio="none">
            {/* Grille horizontale */}
            {[0, 0.2, 0.4, 0.6, 0.8, 1].map((ratio) => (
              <line
                key={ratio}
                x1="0"
                y1={ratio * 500}
                x2="1000"
                y2={ratio * 500}
                stroke="#E0E0E0"
                strokeWidth="1"
                strokeDasharray="2 2"
              />
            ))}

            {/* Lignes de projection pour chaque scénario */}
            {scenarios.map((scenario, scenarioIndex) => (
              <g key={scenarioIndex}>
                <polyline
                  points={scenario.data
                    .map((value, index) => {
                      const x = (index / (scenario.data.length - 1)) * 1000;
                      const y = 500 - (value / maxValue) * 500;
                      return `${x},${y}`;
                    })
                    .join(' ')}
                  fill="none"
                  stroke={scenario.color}
                  strokeWidth={scenarioIndex === 1 ? '3' : '2.5'}
                  strokeDasharray={scenario.strokeDasharray}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  opacity={scenarioIndex === 1 ? 1 : 0.7}
                />
                
                {/* Points sur les lignes */}
                {scenario.data.map((value, index) => {
                  const x = (index / (scenario.data.length - 1)) * 1000;
                  const y = 500 - (value / maxValue) * 500;
                  return (
                    <circle
                      key={`point-${scenarioIndex}-${index}`}
                      cx={x}
                      cy={y}
                      r={scenarioIndex === 1 ? '5' : '4'}
                      fill={scenario.color}
                      opacity={scenarioIndex === 1 ? 1 : 0.7}
                    />
                  );
                })}
              </g>
            ))}
          </svg>

          {/* Labels des axes X */}
          <div className="absolute bottom-0 left-0 right-0 flex justify-between px-2 -mb-6">
            {chartData.labels.map((label, index) => {
              const totalLabels = chartData.labels.length;
              const position = (index / (totalLabels - 1)) * 100;
              return (
                <span
                  key={index}
                  className="text-xs text-[#6B7280] absolute font-light"
                  style={{
                    left: `${position}%`,
                    transform: 'translateX(-50%)',
                  }}
                >
                  {label}
                </span>
              );
            })}
          </div>

          {/* Labels des axes Y */}
          <div className="absolute left-0 top-0 bottom-0 flex flex-col justify-between py-2 -ml-12">
            {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
              const value = Math.round((1 - ratio) * maxValue);
              return (
                <span
                  key={ratio}
                  className="text-xs text-[#6B7280] font-light"
                >
                  {value.toLocaleString('fr-FR')}€
                </span>
              );
            })}
          </div>
        </div>

        {/* Légende détaillée */}
        <div className="mt-8 pt-6 border-t border-[#E0E0E0]">
          <div className="grid grid-cols-2 gap-4">
            {scenarios.map((scenario, index) => (
              <div key={index} className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <div
                    className={`w-6 h-0.5 ${
                      scenario.strokeDasharray !== '0' ? 'border-t-2 border-dashed' : ''
                    }`}
                    style={{
                      backgroundColor: scenario.strokeDasharray === '0' ? scenario.color : 'transparent',
                      borderColor: scenario.color,
                    }}
                  />
                  <span className="text-sm text-[#1A1A1A] font-light">{scenario.name}</span>
                </div>
                <div className="ml-auto">
                  <span className="text-xs text-[#6B7280] font-light">
                    Min: {Math.min(...scenario.data).toLocaleString('fr-FR')}€
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Analyse des scénarios */}
        <div className="mt-6 pt-6 border-t border-[#E0E0E0]">
          <h4 className="text-sm font-medium text-[#1A1A1A] mb-4">Analyse des Scénarios</h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg">
              <p className="text-xs font-medium text-emerald-900 mb-1">Meilleur Cas</p>
              <p className="text-sm text-emerald-800 font-light">
                Le scénario optimiste montre une trésorerie qui remonte à 65k€ en juin, 
                avec un retour sur investissement dès le 7ème mois.
              </p>
            </div>
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-xs font-medium text-red-900 mb-1">Pire Cas</p>
              <p className="text-sm text-red-800 font-light">
                Le scénario pessimiste expose à un risque de découvert en mars-avril, 
                nécessitant des mesures préventives.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

