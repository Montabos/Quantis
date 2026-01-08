'use client';

import { Send, Lightbulb, Sparkles, Loader2 } from 'lucide-react';
import { useState, useRef, useEffect, useMemo } from 'react';
import { DecisionTab, ChatMessage, useTabs, HypothesisChip } from '@/contexts/TabsContext';
import { HypothesisBar } from './HypothesisBar';
import { useFiles } from '@/contexts/FilesContext';
import { generateHypothesesFromAnalysis } from '@/lib/hypothesisGenerator';

export function CFOAssistant({ tab }: { tab: DecisionTab }) {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { addChatMessage, updateTabHypothesis, refreshAnalyses } = useTabs();
  const { getReadyFiles } = useFiles();
  const chatEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const chatHistory = useMemo(() => tab.chatHistory || [], [tab.chatHistory]);
  const readyFiles = getReadyFiles();
  
  // Extract analysis ID from tab ID (format: "analysis-{uuid}" or "decision-{timestamp}")
  const analysisId = useMemo(() => {
    if (tab.id.startsWith('analysis-')) {
      const id = tab.id.replace('analysis-', '');
      console.log('[CFOAssistant] Extracted analysisId:', id, 'from tab.id:', tab.id);
      return id;
    }
    console.log('[CFOAssistant] Tab ID does not start with "analysis-":', tab.id);
    return null;
  }, [tab.id]);

  // Auto-scroll vers le bas quand de nouveaux messages arrivent
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  // Les hypothèses sont maintenant générées directement lors de l'analyse
  // Elles sont déjà présentes dans tab.hypothesis depuis TabsContext
  // Plus besoin d'appel API séparé

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const message = input.trim();
    
    // Si pas d'analyse ID, on ne peut pas faire de chat contextuel
    if (!analysisId) {
      const errorMessage: ChatMessage = {
        id: `msg-error-${Date.now()}`,
        role: 'assistant',
        content: '❌ Cette analyse n\'est pas encore disponible pour le chat. Veuillez attendre que l\'analyse soit terminée.',
        timestamp: new Date(),
      };
      addChatMessage(tab.id, errorMessage);
      setInput('');
      return;
    }
    
    // Ajouter le message utilisateur
    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: message,
      timestamp: new Date(),
    };
    addChatMessage(tab.id, userMessage);

    // Show loading message
    const loadingId = `msg-loading-${Date.now()}`;
    const loadingMessage: ChatMessage = {
      id: loadingId,
      role: 'assistant',
      content: '💭 Réflexion en cours...',
      timestamp: new Date(),
    };
    addChatMessage(tab.id, loadingMessage);

    setIsLoading(true);
    setError(null);

    try {
      // Appel à l'API de chat contextuel
      const response = await fetch('/api/decisions/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          analysis_id: analysisId,
          message: message,
          chat_history: chatHistory.filter(msg => msg.id !== loadingId).map(msg => ({
            role: msg.role,
            content: msg.content,
          })),
          hypotheses: tab.hypothesis || [],
          should_update_hypotheses: true, // Permettre la mise à jour automatique des hypothèses
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Chat failed' }));
        throw new Error(errorData.error || 'Chat failed');
      }

      const chatResponse = await response.json();
      
      // Remove loading message
      // (We'll filter it out when displaying)
      
      // Add assistant response
      const assistantMessage: ChatMessage = {
        id: `msg-assistant-${Date.now()}`,
        role: 'assistant',
        content: chatResponse.response || 'Je n\'ai pas pu générer de réponse.',
        timestamp: new Date(),
      };
      addChatMessage(tab.id, assistantMessage);

      // Mettre à jour les hypothèses si le chat en a généré de nouvelles
      let hypothesesChanged = false;
      if (chatResponse.updated_hypotheses && Array.isArray(chatResponse.updated_hypotheses)) {
        // Comparer les hypothèses pour voir si elles ont vraiment changé
        const currentHypotheses = tab.hypothesis || [];
        const newHypotheses = chatResponse.updated_hypotheses;
        
        // Vérifier si les valeurs ont changé
        hypothesesChanged = currentHypotheses.length !== newHypotheses.length ||
          currentHypotheses.some((hyp, index) => {
            const newHyp = newHypotheses[index];
            return !newHyp || hyp.id !== newHyp.id || hyp.value !== newHyp.value;
          });
        
        if (hypothesesChanged) {
          console.log('[CFOAssistant] Hypotheses changed, updating...');
          updateTabHypothesis(tab.id, newHypotheses);
        } else {
          console.log('[CFOAssistant] Hypotheses unchanged, skipping update');
        }
      }

      // Ne relancer l'analyse QUE si les hypothèses ont réellement changé
      if (chatResponse.should_relaunch_analysis && hypothesesChanged && analysisId) {
        console.log('[CFOAssistant] Relaunching analysis with updated hypotheses');
        const relaunchMessage: ChatMessage = {
          id: `msg-relaunch-${Date.now()}`,
          role: 'assistant',
          content: '🔄 Je vais relancer l\'analyse avec les nouvelles hypothèses...',
          timestamp: new Date(),
        };
        addChatMessage(tab.id, relaunchMessage);
        
        // Relancer l'analyse avec les nouvelles hypothèses
        try {
          const hypothesesData: Record<string, any> = {};
          (chatResponse.updated_hypotheses || []).forEach((hyp: any) => {
            hypothesesData[hyp.id] = hyp.value;
          });

          const relaunchResponse = await fetch(`/api/decisions/analyze/${analysisId}/continue`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              missing_data: {
                hypotheses: hypothesesData,
              },
            }),
          });

          if (!relaunchResponse.ok) {
            throw new Error('Failed to relaunch analysis');
          }
          
          console.log('[CFOAssistant] Analysis relaunched successfully');
        } catch (relaunchError) {
          console.error('[CFOAssistant] Error relaunching analysis:', relaunchError);
          const errorMessage: ChatMessage = {
            id: `msg-relaunch-error-${Date.now()}`,
            role: 'assistant',
            content: '❌ Erreur lors de la relance de l\'analyse. Veuillez réessayer.',
            timestamp: new Date(),
          };
          addChatMessage(tab.id, errorMessage);
        }
      } else if (chatResponse.should_relaunch_analysis && !hypothesesChanged) {
        console.log('[CFOAssistant] Relaunch suggested but no hypothesis changes detected, skipping');
      }
    } catch (err) {
      console.error('[CFOAssistant] Error during chat:', err);
      // Remove loading message and show error
      const errorMessage: ChatMessage = {
        id: `msg-error-${Date.now()}`,
        role: 'assistant',
        content: `❌ Erreur: ${err instanceof Error ? err.message : 'Une erreur est survenue lors du chat.'}`,
        timestamp: new Date(),
      };
      addChatMessage(tab.id, errorMessage);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
      setInput('');
    }
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header du CFO - Style Notion/Apple */}
      <div className="px-5 py-4 border-b border-[#E5E5E5] bg-white">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#D4AF37]/10 border border-[#D4AF37]/20 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-[#D4AF37]" strokeWidth={2} />
          </div>
          <div>
            <h3 className="font-semibold text-[#1A1A1A] text-sm" style={{ letterSpacing: '-0.01em' }}>CFO Assistant</h3>
            <p className="text-[11px] text-[#737373] font-medium">Votre conseiller financier</p>
          </div>
        </div>
      </div>

      {/* Fil de Discussion (Scrollable) */}
      <div
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto px-5 py-5 space-y-4 bg-white scrollbar-subtle"
      >
        {chatHistory.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-6">
            <div className="w-12 h-12 rounded-lg bg-[#D4AF37]/10 border border-[#D4AF37]/20 flex items-center justify-center mb-4">
              <Sparkles className="w-6 h-6 text-[#D4AF37]" strokeWidth={2} />
            </div>
            <p className="text-sm text-[#737373] font-medium leading-relaxed max-w-xs mb-2">
              Posez une question ou modifiez les paramètres pour commencer la conversation.
            </p>
            <div className="flex flex-wrap gap-2 justify-center mt-3">
              <button className="px-3 py-1.5 rounded-md bg-white border border-[#E5E5E5] hover:border-[#D4AF37] hover:bg-[#D4AF37]/5 text-xs text-[#737373] transition-all">
                "Et si je réduisais le salaire ?"
              </button>
              <button className="px-3 py-1.5 rounded-md bg-white border border-[#E5E5E5] hover:border-[#D4AF37] hover:bg-[#D4AF37]/5 text-xs text-[#737373] transition-all">
                "Quels sont les risques ?"
              </button>
            </div>
          </div>
        ) : (
          chatHistory
            .filter((msg) => !msg.id.startsWith('msg-loading-')) // Filter out loading messages
            .map((msg) => (
              <ChatMessageBubble key={msg.id} message={msg} />
            ))
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Zone de Saisie (En bas) - Style Notion/Apple Premium */}
      <div className="px-5 py-4 border-t border-[#E5E5E5] bg-white">
        {/* Files indicator */}
        {readyFiles.length > 0 && (
          <div className="mb-2 px-2 py-1.5 bg-emerald-50 border border-emerald-200 rounded-md">
            <p className="text-[10px] text-emerald-700 font-medium">
              ✓ {readyFiles.length} fichier{readyFiles.length > 1 ? 's' : ''} disponible{readyFiles.length > 1 ? 's' : ''} pour l'analyse
            </p>
          </div>
        )}

        {/* Hypothesis Chips (juste au-dessus de l'input) */}
        {tab.hypothesis && tab.hypothesis.length > 0 && (
          <div className="mb-3">
            <HypothesisBar tabId={tab.id} hypothesis={tab.hypothesis} tab={tab} />
          </div>
        )}

        {/* Input - Style Premium */}
        <form onSubmit={handleSubmit} className="relative">
          <div className="relative flex items-center gap-2 bg-white border border-[#E5E5E5] rounded-lg px-3 py-2.5 hover:border-[#D4AF37]/40 focus-within:border-[#D4AF37] focus-within:shadow-sm focus-within:shadow-[#D4AF37]/10 transition-all duration-200">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Posez une question ou modifiez les paramètres..."
              className="flex-1 bg-transparent border-none outline-none text-sm text-[#1A1A1A] placeholder-[#737373]"
              style={{ fontSize: '14px', letterSpacing: '-0.01em' }}
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className={`flex-shrink-0 w-7 h-7 rounded-md flex items-center justify-center transition-all duration-200 ${
                input.trim() && !isLoading
                  ? 'bg-[#D4AF37] text-white hover:bg-[#B8941F] hover:scale-105 shadow-sm'
                  : 'bg-[#F5F5F5] text-[#737373] cursor-not-allowed'
              }`}
              aria-label="Envoyer"
            >
              {isLoading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" strokeWidth={2} />
              ) : (
                <Send className="w-3.5 h-3.5" strokeWidth={2} />
              )}
            </button>
          </div>
          
          {/* Indicateur de suggestion */}
          {input.length === 0 && !isLoading && (
            <p className="text-[10px] text-[#737373] mt-2 px-1">
              💡 Essayez : "Et si je réduisais le salaire à 50k€ ?"
            </p>
          )}
        </form>
      </div>
    </div>
  );
}

function ChatMessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';

  // Détecter si le message contient un "Actionable Insight"
  const hasInsight = message.content.includes('💡') || message.content.includes('Conseil');

  return (
    <div className={`flex gap-2.5 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      {!isUser && (
        <div className="flex-shrink-0 w-6 h-6 rounded-lg bg-[#D4AF37]/10 border border-[#D4AF37]/20 flex items-center justify-center">
          <Sparkles className="w-3 h-3 text-[#D4AF37]" strokeWidth={2} />
        </div>
      )}

      {/* Message */}
      <div className={`flex-1 ${isUser ? 'items-end' : 'items-start'} flex flex-col`}>
        <div
          className={`rounded-lg px-3.5 py-2.5 max-w-[85%] ${
            isUser
              ? 'bg-[#1A1A1A] text-white shadow-sm'
              : hasInsight
              ? 'bg-[#D4AF37]/5 border border-[#D4AF37]/30 shadow-sm'
              : 'bg-[#FAFAFA] border border-[#E5E5E5]'
          }`}
        >
          {hasInsight && (
            <div className="flex items-center gap-2 mb-2 pb-2 border-b border-[#D4AF37]/20">
              <div className="w-4 h-4 rounded bg-[#D4AF37]/10 flex items-center justify-center">
                <Lightbulb className="w-3 h-3 text-[#D4AF37]" strokeWidth={2} />
              </div>
              <span className="text-[10px] font-semibold text-[#1A1A1A] uppercase tracking-wider">Conseil</span>
            </div>
          )}
          <p className={`text-sm leading-relaxed whitespace-pre-wrap ${isUser ? 'text-white' : 'text-[#1A1A1A]'}`} style={{ letterSpacing: '-0.01em' }}>
            {message.content}
          </p>
          
          {/* Bouton d'action si c'est un insight */}
          {hasInsight && message.content.includes('Simuler') && (
            <button className="mt-3 px-3 py-1.5 bg-[#D4AF37] text-white rounded-md text-xs font-semibold hover:bg-[#B8941F] transition-colors shadow-sm">
              Simuler décalage
            </button>
          )}
        </div>
        <span className="text-[10px] text-[#737373] mt-1.5 px-1">
          {message.timestamp.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  );
}

// Fonction pour générer des réponses IA contextuelles
function generateAIResponse(userInput: string, tab: DecisionTab): string {
  const lowerInput = userInput.toLowerCase();

  if (lowerInput.includes('50k') || lowerInput.includes('50 000')) {
    return "C'est beaucoup mieux ! Avec 50k€, vous restez en zone verte toute l'année. Voulez-vous valider ce budget ?";
  }

  if (lowerInput.includes('février') || lowerInput.includes('fevrier') || lowerInput.includes('feb')) {
    return "💡 Conseil Stratégique\nSi vous décalez l'embauche au 1er Février, le risque de trésorerie disparaît. [Bouton : Simuler décalage]";
  }

  if (lowerInput.includes('salaire') || lowerInput.includes('paie')) {
    return "J'ai analysé votre demande. Pour sécuriser ce poste, il faudrait idéalement augmenter vos délais fournisseurs de 5 jours ou réduire le salaire de 10k€.";
  }

  if (lowerInput.includes('risque') || lowerInput.includes('danger')) {
    return "Le principal risque identifié est la trésorerie en Mars. Je recommande soit de décaler l'embauche, soit de négocier des délais de paiement avec vos fournisseurs.";
  }

  return "J'ai pris en compte votre demande. La simulation se met à jour en temps réel. Que souhaitez-vous explorer d'autre ?";
}

