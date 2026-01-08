'use client';

import { ChartData } from '@/contexts/TabsContext';

export function ChartSection({ chartData }: { chartData: ChartData }) {
  const maxValue = Math.max(...chartData.datasets.flatMap((d) => d.data), 70000);
  const dangerZone = 15000;

  return (
    <div className="mb-12">
      <div className="bg-white rounded-lg border border-[#E5E5E5] p-6">
        <h3 className="text-[11px] font-semibold text-[#737373] mb-6 uppercase tracking-wider">
          Projection de trésorerie sur 12 mois
        </h3>
        
        <div className="relative h-96">
          {/* Zone de danger */}
          <div
            className="absolute bottom-0 left-0 right-0 bg-red-500/5 border-t border-red-500/20 rounded-b-lg"
            style={{
              height: `${(dangerZone / maxValue) * 100}%`,
            }}
          >
            <div className="absolute top-0 left-0 right-0 px-4 py-1.5">
              <span className="text-[10px] font-semibold text-red-500 uppercase tracking-wider">Zone de danger (&lt; 15k€)</span>
            </div>
          </div>

          {/* Graphique SVG */}
          <svg className="w-full h-full" viewBox="0 0 1000 384" preserveAspectRatio="none">
            {/* Grille horizontale */}
            {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
              <line
                key={ratio}
                x1="0"
                y1={ratio * 384}
                x2="1000"
                y2={ratio * 384}
                stroke="#E0E0E0"
                strokeWidth="1"
                strokeDasharray="4 4"
              />
            ))}

            {/* Ligne actuelle (solide) */}
            {chartData.datasets[0] && (
              <polyline
                points={chartData.datasets[0].data
                  .map((value, index) => {
                    const x = (index / (chartData.datasets[0].data.length - 1)) * 1000;
                    const y = 384 - (value / maxValue) * 384;
                    return `${x},${y}`;
                  })
                  .join(' ')}
                fill="none"
                stroke="#737373"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            )}

            {/* Ligne simulée (pointillée) */}
            {chartData.datasets[1] && (
              <polyline
                points={chartData.datasets[1].data
                  .map((value, index) => {
                    const x = (index / (chartData.datasets[1].data.length - 1)) * 1000;
                    const y = 384 - (value / maxValue) * 384;
                    return `${x},${y}`;
                  })
                  .join(' ')}
                fill="none"
                stroke="#D4AF37"
                strokeWidth="2.5"
                strokeDasharray="6 3"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            )}

            {/* Points sur les lignes */}
            {chartData.datasets[0]?.data.map((value, index) => {
              const x = (index / (chartData.datasets[0].data.length - 1)) * 1000;
              const y = 384 - (value / maxValue) * 384;
              return (
                <circle
                  key={`point-actual-${index}`}
                  cx={x}
                  cy={y}
                  r="4"
                  fill="#737373"
                />
              );
            })}
            {chartData.datasets[1]?.data.map((value, index) => {
              const x = (index / (chartData.datasets[1].data.length - 1)) * 1000;
              const y = 384 - (value / maxValue) * 384;
              return (
                <circle
                  key={`point-simulated-${index}`}
                  cx={x}
                  cy={y}
                  r="4"
                  fill="#D4AF37"
                />
              );
            })}
          </svg>

          {/* Labels des axes X */}
          <div className="absolute bottom-0 left-0 right-0 flex justify-between px-2 -mb-6">
            {chartData.labels.map((label, index) => {
              const totalLabels = chartData.labels.length;
              const position = (index / (totalLabels - 1)) * 100;
              return (
                <span
                  key={index}
                  className="text-xs text-[#6B7280] absolute"
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
        </div>

        {/* Légende */}
        <div className="flex items-center gap-6 mt-6 pt-5 border-t border-[#E5E5E5]">
          <div className="flex items-center gap-2.5">
            <div className="w-5 h-0.5 bg-[#737373]"></div>
            <span className="text-xs text-[#737373] font-medium">Scénario actuel</span>
          </div>
          <div className="flex items-center gap-2.5">
            <div className="w-5 h-0.5 bg-[#D4AF37] border-dashed border-t-2"></div>
            <span className="text-xs text-[#737373] font-medium">Scénario simulé</span>
          </div>
        </div>
      </div>
    </div>
  );
}

