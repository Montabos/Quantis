'use client';

import { HealthWidget } from './widgets/HealthWidget';
import { DormantMoneyWidget } from './widgets/DormantMoneyWidget';
import { AlertsWidget } from './widgets/AlertsWidget';
import { RecentActivityWidget } from './widgets/RecentActivityWidget';
import { QuickActionsWidget } from './widgets/QuickActionsWidget';

export function BentoGrid() {
  return (
    <div className="w-full max-w-7xl mx-auto">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Widget Santé Globale (1x1) */}
        <div className="lg:col-span-1">
          <HealthWidget />
        </div>
        
        {/* Widget Argent Dormant (2x1) */}
        <div className="lg:col-span-2">
          <DormantMoneyWidget />
        </div>
        
        {/* Widget Alertes (1x1) */}
        <div className="lg:col-span-1">
          <AlertsWidget />
        </div>
        
        {/* Widget Activité Récente (2x1) */}
        <div className="lg:col-span-2">
          <RecentActivityWidget />
        </div>
        
        {/* Widget Actions Rapides (1x1) */}
        <div className="lg:col-span-1">
          <QuickActionsWidget />
        </div>
        
        {/* Widget placeholder pour équilibrer */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg border border-[#E5E5E5] p-6 h-full min-h-[280px] flex items-center justify-center">
            <p className="text-xs text-[#737373]">Plus de widgets à venir</p>
          </div>
        </div>
      </div>
    </div>
  );
}

