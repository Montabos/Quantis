'use client';

import { LucideIcon } from 'lucide-react';

interface AnalysisSectionProps {
  icon: LucideIcon;
  title: string;
  content: React.ReactNode;
}

export function AnalysisSection({ icon: Icon, title, content }: AnalysisSectionProps) {
  return (
    <div className="mb-12">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-7 h-7 rounded-lg bg-[#D4AF37]/10 border border-[#D4AF37]/20 flex items-center justify-center flex-shrink-0">
          <Icon className="w-4 h-4 text-[#D4AF37]" strokeWidth={2} />
        </div>
        <h2 className="text-lg font-semibold text-[#1A1A1A]" style={{ letterSpacing: '-0.01em' }}>{title}</h2>
      </div>
      <div className="pl-10">{content}</div>
    </div>
  );
}

