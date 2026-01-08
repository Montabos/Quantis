'use client';

import { useTabs, DecisionTab } from '@/contexts/TabsContext';
import { StrategicAnalysis } from './decision/StrategicAnalysis';
import { CFOAssistant } from './decision/CFOAssistant';
import { useState, useRef, useEffect } from 'react';
import { GripVertical, ChevronRight, ChevronLeft } from 'lucide-react';

export function DecisionMode({ tab }: { tab: DecisionTab }) {
  const [chatWidth, setChatWidth] = useState(30); // Pourcentage
  const [isChatOpen, setIsChatOpen] = useState(true);
  const [isResizing, setIsResizing] = useState(false);
  const [showScrollbar, setShowScrollbar] = useState(true); // Visible par défaut pour test
  const containerRef = useRef<HTMLDivElement>(null);
  const analysisRef = useRef<HTMLDivElement>(null);
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return;
      
      e.preventDefault();
      e.stopPropagation();
      
      const containerRect = containerRef.current.getBoundingClientRect();
      const containerWidth = containerRect.width;
      const mouseX = e.clientX - containerRect.left;
      
      // Calculer la largeur du chat depuis la droite
      const newWidth = ((containerWidth - mouseX) / containerWidth) * 100;
      
      // Limiter entre 20% et 50%
      const clampedWidth = Math.max(20, Math.min(50, newWidth));
      setChatWidth(clampedWidth);
    };

    const handleMouseUp = (e: MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsResizing(false);
    };

    // Ajouter les listeners avec capture pour s'assurer qu'ils sont appelés
    document.addEventListener('mousemove', handleMouseMove, { passive: false });
    document.addEventListener('mouseup', handleMouseUp, { passive: false });
    
    // Gérer aussi le cas où la souris sort de la fenêtre
    document.addEventListener('mouseleave', handleMouseUp, { passive: false });

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('mouseleave', handleMouseUp);
    };
  }, [isResizing]);

  // Gestion de l'affichage de la scrollbar
  useEffect(() => {
    const analysisElement = analysisRef.current;
    if (!analysisElement) return;

    const handleScroll = () => {
      setShowScrollbar(true);
      
      // Réinitialiser le timeout
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
      
      // Cacher après 1.5 secondes d'inactivité
      scrollTimeoutRef.current = setTimeout(() => {
        setShowScrollbar(false);
      }, 1500);
    };

    const handleMouseEnter = () => {
      setShowScrollbar(true);
      // Annuler le timeout si la souris entre
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };

    const handleMouseLeave = () => {
      // Cacher après un court délai quand la souris quitte
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
      scrollTimeoutRef.current = setTimeout(() => {
        setShowScrollbar(false);
      }, 500);
    };

    // Vérifier si le contenu est scrollable au montage
    const checkScrollable = () => {
      if (analysisElement.scrollHeight > analysisElement.clientHeight) {
        // Afficher brièvement puis masquer
        setShowScrollbar(true);
        setTimeout(() => {
          // Ne masquer que si la souris n'est pas sur l'élément
          if (!analysisElement.matches(':hover')) {
            setShowScrollbar(false);
          }
        }, 2000);
      } else {
        setShowScrollbar(false);
      }
    };

    // Attendre que le contenu soit chargé
    setTimeout(checkScrollable, 100);
    analysisElement.addEventListener('scroll', handleScroll);
    analysisElement.addEventListener('mouseenter', handleMouseEnter);
    analysisElement.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      analysisElement.removeEventListener('scroll', handleScroll);
      analysisElement.removeEventListener('mouseenter', handleMouseEnter);
      analysisElement.removeEventListener('mouseleave', handleMouseLeave);
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, []);

  return (
    <div ref={containerRef} className="flex h-[calc(100vh-49px)] bg-white overflow-hidden relative">
      {/* Zone GAUCHE : Analyse Stratégique Scrollable */}
      <div 
        ref={analysisRef}
        className={`overflow-y-auto bg-white transition-all duration-200 scrollbar-subtle ${
          showScrollbar ? 'scrollbar-visible' : 'scrollbar-hidden'
        }`}
        style={{ 
          width: isChatOpen ? `${100 - chatWidth}%` : '100%',
          scrollbarGutter: 'stable'
        }}
      >
        <StrategicAnalysis tab={tab} />
      </div>

      {/* Poignée de redimensionnement - Style épuré avec zone de capture élargie */}
      {isChatOpen && (
        <div
          className={`absolute top-0 bottom-0 cursor-col-resize z-20 group ${
            isResizing ? 'bg-[#D4AF37]/20' : ''
          }`}
          style={{ 
            right: `${chatWidth}%`,
            width: '4px',
            marginRight: '-2px' // Pour centrer la zone de capture
          }}
          onMouseDown={(e) => {
            e.preventDefault();
            e.stopPropagation();
            setIsResizing(true);
          }}
          onDragStart={(e) => {
            e.preventDefault();
          }}
        >
          {/* Ligne visible */}
          <div className={`absolute top-0 bottom-0 left-1/2 -translate-x-1/2 w-px bg-[#E5E5E5] group-hover:bg-[#D4AF37] transition-colors ${
            isResizing ? 'bg-[#D4AF37]' : ''
          }`} />
          
          {/* Indicateur visuel au hover */}
          <div className={`absolute top-1/2 -translate-y-1/2 -left-2 w-6 h-10 bg-white border border-[#E5E5E5] rounded-md flex items-center justify-center transition-opacity shadow-sm ${
            isResizing ? 'opacity-100 border-[#D4AF37]' : 'opacity-0 group-hover:opacity-100'
          }`}>
            <GripVertical className="w-3 h-3 text-[#737373]" strokeWidth={1.5} />
          </div>
        </div>
      )}

      {/* Zone DROITE : Le CFO Assistant */}
      {isChatOpen && (
        <div 
          className="bg-white flex flex-col transition-all duration-200 relative border-l border-[#E5E5E5]"
          style={{ width: `${chatWidth}%` }}
        >
          {/* Barre de navigation verticale pour fermer */}
          <button
            onClick={() => setIsChatOpen(false)}
            className="absolute left-0 top-0 bottom-0 w-4 bg-transparent hover:bg-[#F5F5F5] transition-colors flex items-center justify-center group z-10"
            aria-label="Fermer le chat"
          >
            <ChevronRight className="w-3 h-3 text-[#737373] group-hover:text-[#1A1A1A] transition-colors" strokeWidth={2} />
          </button>
          <div className="pl-4 h-full">
            <CFOAssistant tab={tab} />
          </div>
        </div>
      )}

      {/* Barre pour rouvrir le chat (quand fermé) */}
      {!isChatOpen && (
        <button
          onClick={() => setIsChatOpen(true)}
          className="absolute right-0 top-0 bottom-0 w-4 bg-transparent hover:bg-[#F5F5F5] transition-colors flex items-center justify-center group z-10"
          aria-label="Ouvrir le chat"
        >
          <ChevronLeft className="w-3 h-3 text-[#737373] group-hover:text-[#1A1A1A] transition-colors" strokeWidth={2} />
        </button>
      )}
    </div>
  );
}
