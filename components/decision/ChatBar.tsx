'use client';

import { Send } from 'lucide-react';
import { useState } from 'react';
import { ChatMessage, useTabs } from '@/contexts/TabsContext';

export function ChatBar({ tabId, chatHistory }: { tabId: string; chatHistory: ChatMessage[] }) {
  const [input, setInput] = useState('');
  const { addChatMessage } = useTabs();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Ajouter le message utilisateur
    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date(),
    };
    addChatMessage(tabId, userMessage);

    // Simuler une réponse de l'IA
    setTimeout(() => {
      const aiMessage: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: "J'ai pris en compte votre demande. La simulation se met à jour en temps réel.",
        timestamp: new Date(),
      };
      addChatMessage(tabId, aiMessage);
    }, 500);

    setInput('');
  };

  const recentMessages = chatHistory.slice(-3);

  return (
    <div className="relative">
      {/* Historique récent (affiché au-dessus) */}
      {recentMessages.length > 0 && (
        <div className="mb-2 space-y-2">
          {recentMessages.map((msg) => (
            <div
              key={msg.id}
              className={`text-xs px-3 py-2 rounded-lg ${
                msg.role === 'user'
                  ? 'bg-[#1A1A1A]/5 text-[#1A1A1A] ml-auto max-w-[80%]'
                  : 'bg-[#F4F5F7] text-[#6B7280]'
              }`}
            >
              {msg.content}
            </div>
          ))}
        </div>
      )}

      {/* Input */}
      <form onSubmit={handleSubmit} className="relative">
        <div className="flex items-center gap-3 bg-white border border-[#E0E0E0] rounded-full px-4 py-3 hover:border-[#1A1A1A] transition-colors">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Posez une question ou modifiez les paramètres..."
            className="flex-1 bg-transparent border-none outline-none text-sm text-[#1A1A1A] placeholder-[#6B7280]"
          />
          <button
            type="submit"
            disabled={!input.trim()}
            className="flex-shrink-0 w-8 h-8 rounded-full bg-[#1A1A1A] text-white flex items-center justify-center hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Envoyer"
          >
            <Send className="w-4 h-4" strokeWidth={1.8} />
          </button>
        </div>
      </form>
    </div>
  );
}

