'use client';

import { Activity, TrendingUp, DollarSign, Users } from 'lucide-react';

const activities = [
  {
    type: 'decision',
    icon: TrendingUp,
    title: 'Simulation recrutement',
    description: 'Impact analysé sur 12 mois',
    time: 'Il y a 1h',
    color: 'text-[#D4AF37]',
  },
  {
    type: 'file',
    icon: DollarSign,
    title: 'Bilan 2023 uploadé',
    description: 'Traitement terminé',
    time: 'Il y a 3h',
    color: 'text-emerald-500',
  },
  {
    type: 'insight',
    icon: Users,
    title: 'Nouvelle opportunité détectée',
    description: 'Optimisation BFR possible',
    time: 'Hier',
    color: 'text-blue-500',
  },
];

export function RecentActivityWidget() {
  return (
    <div className="bg-white rounded-lg border border-[#E5E5E5] p-6 hover:border-[#D4AF37]/30 hover:shadow-sm transition-all duration-200 cursor-pointer h-full min-h-[280px]">
      <h3 className="text-[11px] font-medium text-[#737373] uppercase tracking-wider mb-6">Activité Récente</h3>
      
      <div className="space-y-4">
        {activities.map((activity, index) => {
          const Icon = activity.icon;
          return (
            <div key={index} className="flex items-start gap-3 pb-4 border-b border-[#F5F5F5] last:border-0 last:pb-0 group/item">
              <div className={`flex-shrink-0 mt-0.5 ${activity.color}`}>
                <Icon className="w-4 h-4" strokeWidth={1.5} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-[#1A1A1A] mb-1" style={{ letterSpacing: '-0.01em' }}>
                  {activity.title}
                </p>
                <p className="text-[11px] text-[#737373] mb-1.5">
                  {activity.description}
                </p>
                <span className="text-[10px] text-[#737373]">
                  {activity.time}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}







