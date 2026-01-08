'use client';

import { Edit2, RefreshCw } from 'lucide-react';
import { useState } from 'react';
import { HypothesisChip, useTabs, DecisionTab } from '@/contexts/TabsContext';

interface HypothesisBarProps {
  tabId: string;
  hypothesis: HypothesisChip[];
  tab: DecisionTab;
}

export function HypothesisBar({ tabId, hypothesis, tab }: HypothesisBarProps) {
  const [editingChip, setEditingChip] = useState<string | null>(null);
  const [isRelaunching, setIsRelaunching] = useState(false);
  const { updateTabHypothesis } = useTabs();

  const handleChipClick = (chipId: string) => {
    setEditingChip(chipId);
  };

  const handleUpdate = async (chipId: string, newValue: string | number) => {
    const updated = hypothesis.map((chip) =>
      chip.id === chipId ? { ...chip, value: newValue } : chip
    );
    updateTabHypothesis(tabId, updated);
    setEditingChip(null);
    
    // Relancer l'analyse si on a un analysisId
    const analysisId = tabId.startsWith('analysis-') ? tabId.replace('analysis-', '') : null;
    if (analysisId) {
      await relaunchAnalysisWithHypotheses(analysisId, updated);
    }
  };

  const relaunchAnalysisWithHypotheses = async (analysisId: string, hypotheses: HypothesisChip[]) => {
    setIsRelaunching(true);
    try {
      // Convertir les hypothèses en format pour le backend
      const hypothesesData: Record<string, any> = {};
      hypotheses.forEach((hyp) => {
        hypothesesData[hyp.id] = hyp.value;
      });

      const response = await fetch(`/api/decisions/analyze/${analysisId}/continue`, {
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

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Failed to relaunch analysis' }));
        throw new Error(errorData.error || 'Failed to relaunch analysis');
      }

      console.log('[HypothesisBar] Analysis relaunched successfully');
    } catch (error) {
      console.error('[HypothesisBar] Error relaunching analysis:', error);
      alert(`Erreur lors de la relance de l'analyse: ${error instanceof Error ? error.message : 'Erreur inconnue'}`);
    } finally {
      setIsRelaunching(false);
    }
  };

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {hypothesis.map((chip) => (
        <div key={chip.id} className="relative">
          {editingChip === chip.id ? (
            <HypothesisEditor
              chip={chip}
              onSave={(value) => handleUpdate(chip.id, value)}
              onCancel={() => setEditingChip(null)}
            />
          ) : (
            <button
              onClick={() => handleChipClick(chip.id)}
              disabled={isRelaunching}
              className="flex items-center gap-2 px-3 py-1.5 bg-white border border-[#E5E5E5] rounded-md hover:border-[#D4AF37] hover:bg-[#D4AF37]/5 transition-all text-xs text-[#1A1A1A] font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span>
                {chip.label}: <span className="font-semibold">{chip.value}</span>
                {chip.type === 'number' && '€'}
              </span>
              <Edit2 className="w-3 h-3 text-[#737373]" strokeWidth={1.5} />
            </button>
          )}
        </div>
      ))}
      {isRelaunching && (
        <div className="flex items-center gap-2 px-3 py-1.5 bg-[#D4AF37]/10 border border-[#D4AF37]/20 rounded-md text-xs text-[#737373]">
          <RefreshCw className="w-3 h-3 animate-spin" strokeWidth={1.5} />
          <span>Mise à jour...</span>
        </div>
      )}
    </div>
  );
}

function HypothesisEditor({
  chip,
  onSave,
  onCancel,
}: {
  chip: HypothesisChip;
  onSave: (value: string | number) => void;
  onCancel: () => void;
}) {
  const [value, setValue] = useState(chip.value.toString());

  const handleSubmit = () => {
    if (chip.type === 'number') {
      onSave(parseFloat(value) || 0);
    } else {
      onSave(value);
    }
  };

  return (
    <div className="absolute bottom-full left-0 mb-2 bg-white border border-[#E5E5E5] rounded-lg shadow-lg p-3 z-10 min-w-[200px]">
      <label className="text-[11px] text-[#737373] font-medium mb-2 block uppercase tracking-wider">{chip.label}</label>
      <input
        type={chip.type === 'number' ? 'number' : 'text'}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        className="w-full px-3 py-2 border border-[#E5E5E5] rounded-md text-sm text-[#1A1A1A] mb-3 focus:border-[#D4AF37] focus:outline-none transition-colors"
        autoFocus
        onKeyDown={(e) => {
          if (e.key === 'Enter') handleSubmit();
          if (e.key === 'Escape') onCancel();
        }}
      />
      <div className="flex gap-2">
        <button
          onClick={handleSubmit}
          className="flex-1 px-3 py-1.5 bg-[#D4AF37] text-white rounded-md text-xs font-semibold hover:bg-[#B8941F] transition-colors"
        >
          Valider
        </button>
        <button
          onClick={onCancel}
          className="px-3 py-1.5 border border-[#E5E5E5] rounded-md text-xs text-[#737373] hover:bg-[#F5F5F5] transition-colors font-medium"
        >
          Annuler
        </button>
      </div>
    </div>
  );
}

