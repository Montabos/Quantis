'use client';

interface KPIWidgetProps {
  label: string;
  value: string;
  subtitle?: string;
  gradient: string;
  border: string;
  negative?: boolean;
}

export function KPIWidget({ label, value, subtitle, gradient, border, negative }: KPIWidgetProps) {
  return (
    <div className={`bg-white rounded-lg border ${border} p-5 hover:border-[#D4AF37]/30 hover:shadow-sm transition-all duration-200`}>
      <p className="text-[11px] font-medium text-[#737373] mb-3 uppercase tracking-wider">{label}</p>
      <p className={`text-3xl font-semibold mb-2 ${negative ? 'text-red-500' : 'text-[#1A1A1A]'}`} style={{ letterSpacing: '-0.02em', fontFamily: value.includes('€') || value.includes('k') ? 'ui-monospace, monospace' : 'inherit' }}>
        {value}
      </p>
      {subtitle && <p className="text-xs text-[#737373] font-medium">{subtitle}</p>}
    </div>
  );
}

