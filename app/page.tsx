'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/Header';
import { Sidebar } from '@/components/Sidebar';
import { DashboardHeader } from '@/components/DashboardHeader';
import { BentoGrid } from '@/components/BentoGrid';
import { DecisionMode } from '@/components/DecisionMode';
import { useTabs } from '@/contexts/TabsContext';
import { useAuth } from '@/contexts/AuthContext';

export default function Home() {
  const { activeTabId, decisionTabs } = useTabs();
  const activeTab = decisionTabs.find(tab => tab.id === activeTabId);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="text-[#737373]">Chargement...</div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  // Si un onglet de décision est actif, afficher le Decision Mode
  if (activeTabId !== 'dashboard' && activeTab) {
    return (
      <div className="min-h-screen flex flex-col bg-white">
        {/* Header fixe */}
        <Header />
        <div className="flex flex-1 overflow-hidden pt-[49px]">
          {/* Sidebar fixe */}
          <Sidebar onCollapseChange={setIsSidebarCollapsed} />
          {/* Contenu scrollable */}
          <div className={`flex-1 overflow-y-auto transition-all duration-200 ${
            isSidebarCollapsed ? 'ml-16' : 'ml-64'
          }`}>
            <DecisionMode tab={activeTab} />
          </div>
        </div>
      </div>
    );
  }

  // Sinon, afficher le Dashboard
  return (
    <div className="min-h-screen flex flex-col bg-white">
      {/* Header ultra-minimaliste - Fixe en haut */}
      <Header />
      
      {/* Contenu principal avec sidebar */}
      <div className="flex flex-1 overflow-hidden pt-[49px]">
        {/* Sidebar - Fixe à gauche */}
        <Sidebar onCollapseChange={setIsSidebarCollapsed} />
        
        {/* Zone principale - Scroll indépendant */}
        <div className={`flex-1 flex flex-col overflow-y-auto transition-all duration-200 ${
          isSidebarCollapsed ? 'ml-16' : 'ml-64'
        }`}>
          {/* Zone Header enrichie avec KPIs et contexte */}
          <section className="flex-shrink-0 pt-12 pb-8 px-8 max-w-7xl mx-auto w-full">
            <DashboardHeader />
          </section>
          
          {/* Zone 2: Insight Feed (Grille Bento ultra-épurée) */}
          <section className="flex-1 pb-12 px-8">
            <BentoGrid />
          </section>
        </div>
      </div>
    </div>
  );
}

