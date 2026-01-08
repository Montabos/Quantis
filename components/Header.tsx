'use client';

import { Settings, Lock, User, X, LogOut, Clock } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useTabs } from '@/contexts/TabsContext';
import { useAuth } from '@/contexts/AuthContext';
import { HistoryModal } from './HistoryModal';

export function Header() {
  const { activeTabId, decisionTabs, setActiveTab, closeTab } = useTabs();
  const { user, signOut } = useAuth();
  const [draggedTab, setDraggedTab] = useState<string | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);
  const [dragPosition, setDragPosition] = useState<{ x: number; y: number } | null>(null);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showHistoryModal, setShowHistoryModal] = useState(false);

  const handleCloseTab = (e: React.MouseEvent, tabId: string) => {
    e.stopPropagation();
    closeTab(tabId);
  };

  const handleTabClick = (tabId: string) => {
    setActiveTab(tabId);
  };

  const handleDragStart = (e: React.DragEvent, tabId: string) => {
    setDraggedTab(tabId);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', '');
    
    const rect = e.currentTarget.getBoundingClientRect();
    const navRect = (e.currentTarget.closest('nav') as HTMLElement)?.getBoundingClientRect();
    
    if (navRect) {
      setDragPosition({
        x: e.clientX,
        y: navRect.top + navRect.height / 2 // Centre vertical de la barre
      });
    }
    
    // Créer un élément de drag invisible
    const dragImage = document.createElement('div');
    dragImage.style.position = 'absolute';
    dragImage.style.top = '-9999px';
    document.body.appendChild(dragImage);
    e.dataTransfer.setDragImage(dragImage, 0, 0);
    
    setTimeout(() => {
      document.body.removeChild(dragImage);
    }, 0);
  };

  // Suivre la position de la souris pendant le drag
  useEffect(() => {
    if (!draggedTab) return;

    const handleDragOver = (e: DragEvent) => {
      const nav = document.querySelector('nav');
      if (nav) {
        const navRect = nav.getBoundingClientRect();
        setDragPosition({
          x: e.clientX,
          y: navRect.top + navRect.height / 2 // Toujours au centre vertical de la barre
        });
      }
    };

    document.addEventListener('dragover', handleDragOver);
    return () => {
      document.removeEventListener('dragover', handleDragOver);
    };
  }, [draggedTab]);

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    if (draggedTab) {
      setDragOverIndex(index);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    // Ne réinitialiser que si on quitte vraiment la zone de drop
    const rect = e.currentTarget.getBoundingClientRect();
    if (
      e.clientX < rect.left ||
      e.clientX > rect.right ||
      e.clientY < rect.top ||
      e.clientY > rect.bottom
    ) {
      setDragOverIndex(null);
    }
  };

  const handleDrop = (e: React.DragEvent, dropIndex: number) => {
    e.preventDefault();
    e.stopPropagation();
    if (!draggedTab) return;

    const draggedIndex = decisionTabs.findIndex(tab => tab.id === draggedTab);
    if (draggedIndex === -1 || draggedIndex === dropIndex) return;

    // Note: Pour simplifier, on ne réordonne pas les onglets pour l'instant
    // On pourrait ajouter une fonction updateTabOrder dans le contexte si nécessaire
    setDraggedTab(null);
    setDragOverIndex(null);
  };

  const handleNavDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDragEnd = () => {
    setDraggedTab(null);
    setDragOverIndex(null);
    setDragPosition(null);
  };

  return (
    <header className="px-6 py-3 bg-white/80 backdrop-blur-xl border-b border-[#E5E5E5]/50 fixed top-0 left-0 right-0 z-50">
      <div className="flex items-center justify-between gap-8">
        {/* Logo - Style Notion/Apple */}
        <div className="flex-shrink-0">
          <span className="text-[#1A1A1A]" style={{ fontSize: '17px', fontWeight: '600', letterSpacing: '-0.03em' }}>
            Quantis
          </span>
        </div>

        {/* Navigation - Style Browser-like Premium */}
        <nav 
          className="flex-1 flex items-center justify-center bg-transparent relative"
          onDragOver={handleNavDragOver}
        >
          {/* Élément fantôme pour le drag (reste aligné verticalement avec la barre) */}
          {draggedTab && dragPosition && (
            <div
              className="fixed pointer-events-none z-50"
              style={{
                left: `${dragPosition.x}px`,
                top: `${dragPosition.y}px`,
                transform: 'translate(-50%, -50%)',
              }}
            >
              <div className="text-[#1A1A1A] px-4 py-1.5 rounded-t-lg bg-white border-b-2 border-[#1A1A1A] shadow-lg flex items-center gap-2">
                <span style={{ fontSize: '13px', fontWeight: '500', letterSpacing: '-0.01em' }}>
                  {decisionTabs.find(t => t.id === draggedTab)?.label || 'Onglet'}
                </span>
              </div>
            </div>
          )}
          <div className="flex items-end gap-0.5">
            {/* Active Tab - Dashboard (fixe) - Style Notion */}
            <button 
              onClick={() => handleTabClick('dashboard')}
              className={`px-4 py-1.5 rounded-t-lg transition-all duration-150 flex items-center ${
                activeTabId === 'dashboard'
                  ? 'bg-white text-[#1A1A1A] border-b-2 border-[#1A1A1A]'
                  : 'bg-transparent text-[#737373] border-b-2 border-transparent hover:text-[#1A1A1A] hover:bg-[#FAFAFA]'
              }`}
              style={{ fontSize: '13px', fontWeight: activeTabId === 'dashboard' ? '500' : '400', letterSpacing: '-0.01em' }}
            >
              Dashboard
            </button>
            
            {/* Onglets dynamiques de décision */}
            {decisionTabs.map((tab, index) => (
              <div key={tab.id} className="flex items-center">
                <div
                  draggable
                  onDragStart={(e) => handleDragStart(e, tab.id)}
                  onDragOver={(e) => handleDragOver(e, index)}
                  onDragLeave={handleDragLeave}
                  onDrop={(e) => handleDrop(e, index)}
                  onDragEnd={handleDragEnd}
                  onClick={() => handleTabClick(tab.id)}
                  className={`px-4 py-1.5 rounded-t-lg transition-all duration-150 cursor-move flex items-center gap-2 group relative border-b-2 ${
                    dragOverIndex === index ? 'bg-white shadow-sm scale-[1.02] z-10' : ''
                  } ${
                    draggedTab === tab.id 
                      ? 'opacity-20' 
                      : activeTabId === tab.id 
                        ? 'bg-white text-[#1A1A1A] border-[#1A1A1A]' 
                        : 'bg-transparent text-[#737373] border-transparent hover:text-[#1A1A1A] hover:bg-[#FAFAFA]'
                  }`}
                  style={{ fontSize: '13px', fontWeight: activeTabId === tab.id ? '500' : '400', letterSpacing: '-0.01em' }}
                >
                  <span className="select-none">{tab.label}</span>
                  <button
                    onClick={(e) => handleCloseTab(e, tab.id)}
                    className="opacity-0 group-hover:opacity-100 transition-opacity duration-150 hover:bg-[#E5E5E5] rounded-md p-0.5 flex items-center justify-center ml-0.5"
                    aria-label={`Fermer ${tab.label}`}
                    onMouseDown={(e) => e.stopPropagation()}
                  >
                    <X className="w-3 h-3 text-[#737373]" strokeWidth={2} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </nav>

        {/* Actions - Style Notion/Apple ultra-minimaliste */}
        <div className="flex items-center gap-1">
          {/* History */}
          <button 
            onClick={() => setShowHistoryModal(true)}
            className="p-1.5 rounded-md hover:bg-[#F5F5F5] transition-colors duration-150 text-[#737373] hover:text-[#1A1A1A]"
            title="Historique des analyses"
          >
            <Clock className="w-4 h-4" strokeWidth={1.5} />
          </button>
          
          {/* Settings */}
          <button className="p-1.5 rounded-md hover:bg-[#F5F5F5] transition-colors duration-150 text-[#737373] hover:text-[#1A1A1A]">
            <Settings className="w-4 h-4" strokeWidth={1.5} />
          </button>
          
          {/* Secure Vault avec indicateur de statut */}
          <button className="p-1.5 rounded-md hover:bg-[#F5F5F5] transition-colors duration-150 text-[#737373] hover:text-[#1A1A1A] relative">
            <Lock className="w-4 h-4" strokeWidth={1.5} />
            {/* Indicateur de statut - très subtil */}
            <span className="absolute top-0.5 right-0.5 w-1.5 h-1.5 bg-emerald-500 rounded-full border border-white"></span>
          </button>
          
          {/* Profile Menu */}
          <div className="relative">
            <button 
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="p-1.5 rounded-md hover:bg-[#F5F5F5] transition-colors duration-150 text-[#737373] hover:text-[#1A1A1A]"
            >
              <User className="w-4 h-4" strokeWidth={1.5} />
            </button>
            
            {showUserMenu && (
              <>
                <div 
                  className="fixed inset-0 z-40" 
                  onClick={() => setShowUserMenu(false)}
                />
                <div className="absolute right-0 top-full mt-2 w-48 bg-white border border-[#E5E5E5] rounded-lg shadow-lg z-50 py-1">
                  <div className="px-4 py-2 border-b border-[#E5E5E5]">
                    <p className="text-xs font-medium text-[#1A1A1A] truncate">
                      {user?.email}
                    </p>
                  </div>
                  <button
                    onClick={async () => {
                      await signOut();
                      setShowUserMenu(false);
                    }}
                    className="w-full px-4 py-2 text-left text-sm text-[#737373] hover:bg-[#FAFAFA] flex items-center gap-2"
                  >
                    <LogOut className="w-4 h-4" strokeWidth={1.5} />
                    Déconnexion
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
      
      {/* History Modal */}
      <HistoryModal isOpen={showHistoryModal} onClose={() => setShowHistoryModal(false)} />
    </header>
  );
}

