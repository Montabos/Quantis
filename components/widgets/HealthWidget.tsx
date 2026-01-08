'use client';

export function HealthWidget() {
  const healthScore = 85;
  const status = healthScore >= 80 ? 'healthy' : healthScore >= 60 ? 'warning' : 'critical';
  
  const getStatusColor = () => {
    switch (status) {
      case 'healthy':
        return 'text-emerald-600';
      case 'warning':
        return 'text-[#D4AF37]';
      case 'critical':
        return 'text-red-500';
      default:
        return 'text-[#737373]';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'healthy':
        return 'Structure saine';
      case 'warning':
        return 'Attention requise';
      case 'critical':
        return 'Action urgente';
      default:
        return 'En analyse';
    }
  };

  return (
    <div className="bg-white rounded-lg border border-[#E5E5E5] p-6 hover:border-[#D4AF37]/30 hover:shadow-sm transition-all duration-200 cursor-pointer h-full min-h-[280px] group">
      <div className="flex flex-col items-center justify-center h-full">
        <h3 className="text-[11px] font-medium text-[#737373] uppercase tracking-wider mb-8">Santé Globale</h3>
        
        {/* Jauge circulaire - Style Notion ultra-épuré */}
        <div className="relative w-32 h-32 mb-6">
          <svg className="transform -rotate-90 w-32 h-32">
            <circle
              cx="64"
              cy="64"
              r="58"
              stroke="#F5F5F5"
              strokeWidth="4"
              fill="none"
            />
            <circle
              cx="64"
              cy="64"
              r="58"
              stroke={status === 'healthy' ? '#10B981' : status === 'warning' ? '#D4AF37' : '#EF4444'}
              strokeWidth="4"
              fill="none"
              strokeDasharray={`${(healthScore / 100) * 364} 364`}
              strokeLinecap="round"
              className="transition-all duration-700 ease-out"
              style={{ filter: status === 'warning' ? 'drop-shadow(0 0 2px rgba(212, 175, 55, 0.3))' : 'none' }}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className={`text-3xl font-semibold ${getStatusColor()}`} style={{ letterSpacing: '-0.03em', fontFamily: 'ui-monospace, monospace' }}>
              {healthScore}
            </span>
          </div>
        </div>
        
        <p className={`text-xs font-medium ${getStatusColor()}`} style={{ letterSpacing: '-0.01em' }}>
          {getStatusText()}
        </p>
      </div>
    </div>
  );
}

