'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, DollarSign, AlertCircle, Sparkles, ArrowRight } from 'lucide-react';
import { HeroDecisionBar } from './HeroDecisionBar';
import { useProjects } from '@/contexts/ProjectsContext';

interface QuickStat {
  label: string;
  value: string;
  change?: string;
  icon: typeof TrendingUp;
  color: string;
  trend?: 'up' | 'down' | 'neutral';
}

const quickStats: QuickStat[] = [
  {
    label: 'Trésorerie',
    value: '145 230 €',
    change: '+12%',
    icon: DollarSign,
    color: 'text-emerald-600',
    trend: 'up',
  },
  {
    label: 'Santé Globale',
    value: '85%',
    change: 'Stable',
    icon: TrendingUp,
    color: 'text-[#D4AF37]',
    trend: 'neutral',
  },
  {
    label: 'Alertes',
    value: '3',
    change: 'À traiter',
    icon: AlertCircle,
    color: 'text-amber-500',
    trend: 'neutral',
  },
];

export function DashboardHeader() {
  const { projects, activeProjectId } = useProjects();
  
  const activeProject = activeProjectId 
    ? projects.find(p => p.id === activeProjectId)
    : null;

  const dashboardTitle = activeProject 
    ? `Dashboard ${activeProject.name}`
    : 'Dashboard';

  return (
    <div className="w-full">
      {/* Titre de bienvenue et contexte */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-[#1A1A1A] mb-2" style={{ letterSpacing: '-0.03em' }}>
          {dashboardTitle}
        </h1>
        <p className="text-sm text-[#737373]" style={{ letterSpacing: '-0.01em' }}>
          Voici un aperçu de votre situation financière aujourd'hui
        </p>
      </div>

      {/* KPIs Rapides - Style Notion */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {quickStats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div
              key={index}
              className="bg-white rounded-lg border border-[#E5E5E5] p-4 hover:border-[#D4AF37]/30 hover:shadow-sm transition-all duration-200"
            >
              <div className="flex items-start justify-between mb-2">
                <div className={`${stat.color} flex-shrink-0`}>
                  <Icon className="w-4 h-4" strokeWidth={1.5} />
                </div>
                {stat.change && (
                  <span className={`text-[10px] font-medium ${
                    stat.trend === 'up' ? 'text-emerald-600' : 
                    stat.trend === 'down' ? 'text-red-500' : 
                    'text-[#737373]'
                  }`}>
                    {stat.change}
                  </span>
                )}
              </div>
              <div className="mb-1">
                <span className="text-lg font-semibold text-[#1A1A1A]" style={{ letterSpacing: '-0.02em', fontFamily: stat.label === 'Trésorerie' ? 'ui-monospace, monospace' : 'inherit' }}>
                  {stat.value}
                </span>
              </div>
              <p className="text-[11px] text-[#737373] font-medium uppercase tracking-wider">
                {stat.label}
              </p>
            </div>
          );
        })}
      </div>

      {/* Section Question & Suggestions - Unifiée et simple */}
      <div className="mb-6">
        <HeroDecisionBar />
        <div className="mt-3">
          <p className="text-[10px] text-[#737373] font-medium mb-2">
            Suggestions basées sur vos données
          </p>
          <div className="flex flex-wrap gap-2">
            <button className="px-3 py-1.5 rounded-md bg-white border border-[#E5E5E5] hover:border-[#D4AF37] hover:bg-[#D4AF37]/5 text-xs text-[#1A1A1A] transition-all duration-150">
              Optimiser le stock <span className="text-emerald-600 font-semibold">+15k€</span>
            </button>
            <button className="px-3 py-1.5 rounded-md bg-white border border-[#E5E5E5] hover:border-[#D4AF37] hover:bg-[#D4AF37]/5 text-xs text-[#1A1A1A] transition-all duration-150">
              Analyser les retards clients
            </button>
            <button className="px-3 py-1.5 rounded-md bg-white border border-[#E5E5E5] hover:border-[#D4AF37] hover:bg-[#D4AF37]/5 text-xs text-[#1A1A1A] transition-all duration-150">
              Projeter la trésorerie Q1
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

