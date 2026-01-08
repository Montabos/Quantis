'use client';

import { AlertCircle, Clock, FileText } from 'lucide-react';

const alerts = [
  {
    type: 'warning',
    icon: AlertCircle,
    title: 'Retard client',
    amount: '12 500 €',
    time: 'Il y a 2h',
  },
  {
    type: 'info',
    icon: FileText,
    title: 'Échéance fiscale',
    amount: '8 200 €',
    time: 'Dans 5 jours',
  },
  {
    type: 'warning',
    icon: Clock,
    title: 'Paiement en attente',
    amount: '3 400 €',
    time: 'Il y a 1j',
  },
];

export function AlertsWidget() {
  const getIconColor = (type: string) => {
    switch (type) {
      case 'warning':
        return 'text-[#D4AF37]';
      case 'info':
        return 'text-blue-500';
      default:
        return 'text-[#737373]';
    }
  };

  return (
    <div className="bg-white rounded-lg border border-[#E5E5E5] p-6 hover:border-[#D4AF37]/30 hover:shadow-sm transition-all duration-200 cursor-pointer h-full min-h-[280px]">
      <h3 className="text-[11px] font-medium text-[#737373] uppercase tracking-wider mb-6">Flux & Alertes</h3>
      
      <div className="space-y-4">
        {alerts.map((alert, index) => {
          const Icon = alert.icon;
          return (
            <div key={index} className="flex items-start gap-3 pb-4 border-b border-[#F5F5F5] last:border-0 last:pb-0 group/item">
              <div className={`flex-shrink-0 mt-0.5 ${getIconColor(alert.type)}`}>
                <Icon className="w-4 h-4" strokeWidth={1.5} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-[#1A1A1A] mb-1.5" style={{ letterSpacing: '-0.01em' }}>
                  {alert.title}
                </p>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-[#1A1A1A]" style={{ letterSpacing: '-0.02em', fontFamily: 'ui-monospace, monospace' }}>
                    {alert.amount}
                  </span>
                  <span className="text-[11px] text-[#737373] font-medium">
                    {alert.time}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

