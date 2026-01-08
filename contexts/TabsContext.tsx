'use client';

import { createContext, useContext, useState, ReactNode, useEffect, useCallback } from 'react';
import { useProjects } from './ProjectsContext';
import { createClient } from '@/lib/supabase/client';
import { useAuth } from './AuthContext';
import { AnalysisResult } from '@/hooks/useDecisionAnalysis';

export interface DecisionTab {
  id: string;
  label: string;
  query: string;
  hypothesis?: HypothesisChip[];
  chartData?: ChartData;
  chatHistory?: ChatMessage[];
  analysisResult?: AnalysisResult;
}

export interface HypothesisChip {
  id: string;
  label: string;
  value: string | number;
  type: 'number' | 'text' | 'date';
}

export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    type: 'line' | 'bar';
    color: string;
  }[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface TabsContextType {
  activeTabId: string;
  decisionTabs: DecisionTab[];
  setActiveTab: (tabId: string) => void;
  createDecisionTab: (query: string) => void;
  closeTab: (tabId: string) => void;
  reopenTab: (tabId: string) => void;
  permanentlyDeleteTab: (tabId: string) => Promise<void>;
  getClosedTabsForProject: (projectId: string) => Promise<DecisionTab[]>;
  updateTabHypothesis: (tabId: string, hypothesis: HypothesisChip[]) => void;
  addChatMessage: (tabId: string, message: ChatMessage) => void;
  updateTabWithAnalysisId: (tempTabId: string, analysisId: string) => void;
  refreshAnalyses: () => Promise<void>;
}

const TabsContext = createContext<TabsContextType | undefined>(undefined);

export function TabsProvider({ children }: { children: ReactNode }) {
  const [activeTabId, setActiveTabId] = useState<string>('dashboard');
  const [decisionTabs, setDecisionTabs] = useState<DecisionTab[]>([]);
  const [lastProjectId, setLastProjectId] = useState<string | null>(null);
  const [closedTabs, setClosedTabs] = useState<Set<string>>(new Set()); // Track closed tab IDs per project
  const { activeProjectId } = useProjects();
  const { user } = useAuth();
  const supabase = createClient();

  // Load closed tabs from localStorage for current project
  useEffect(() => {
    if (!activeProjectId) {
      setClosedTabs(new Set());
      return;
    }
    
    const storageKey = `closed_tabs_${activeProjectId}`;
    const stored = localStorage.getItem(storageKey);
    if (stored) {
      try {
        const closedIds = JSON.parse(stored) as string[];
        setClosedTabs(new Set(closedIds));
      } catch (e) {
        console.error('Error loading closed tabs:', e);
        setClosedTabs(new Set());
      }
    } else {
      setClosedTabs(new Set());
    }
  }, [activeProjectId]);

  // Save closed tabs to localStorage
  const saveClosedTabs = useCallback((projectId: string, closedIds: Set<string>) => {
    const storageKey = `closed_tabs_${projectId}`;
    localStorage.setItem(storageKey, JSON.stringify(Array.from(closedIds)));
  }, []);

  // Load analyses from Supabase when project changes
  const loadAnalyses = useCallback(async () => {
    if (!user || !activeProjectId) {
      setDecisionTabs([]);
      return;
    }

    try {
      console.log(`[TabsContext] Loading analyses for user ${user.id}, project ${activeProjectId}`);
      const { data, error } = await supabase
        .from('analyses')
        .select('*')
        .eq('user_id', user.id)
        .eq('project_id', activeProjectId)
        .order('created_at', { ascending: false });

      if (error) {
        console.error('[TabsContext] Error loading analyses:', error);
        return;
      }

      console.log(`[TabsContext] Loaded ${data?.length || 0} analyses for project ${activeProjectId}`);
      if (data && data.length > 0) {
        console.log(`[TabsContext] Analysis IDs:`, data.map(a => a.id));
        console.log(`[TabsContext] Analysis questions:`, data.map(a => a.question));
        console.log(`[TabsContext] Analysis project_ids:`, data.map(a => a.project_id));
      } else {
        // Debug: Check if there are any analyses at all for this user
        const { data: allAnalyses } = await supabase
          .from('analyses')
          .select('id, project_id, question')
          .eq('user_id', user.id);
        console.log(`[TabsContext] All analyses for user:`, allAnalyses);
      }

      // Load closed tabs from localStorage for THIS project (always fresh, not from state)
      const storageKey = `closed_tabs_${activeProjectId}`;
      const stored = localStorage.getItem(storageKey);
      const closedTabsForProject = stored ? new Set(JSON.parse(stored) as string[]) : new Set<string>();
      console.log(`[TabsContext] Closed tabs from localStorage for project ${activeProjectId}:`, Array.from(closedTabsForProject));
      
      // Filter out closed tabs
      const analysisIds = new Set((data || []).map(a => `analysis-${a.id}`));
      const closedIdsForProject = Array.from(closedTabsForProject).filter(id => analysisIds.has(id));
      
      console.log(`[TabsContext] Closed tabs to filter out:`, closedIdsForProject);
      
      // Convert analyses to DecisionTabs with formatted content, excluding closed ones
      const tabs: DecisionTab[] = (data || [])
        .filter((analysis) => {
          const tabId = `analysis-${analysis.id}`;
          const isClosed = closedTabsForProject.has(tabId);
          if (isClosed) {
            console.log(`[TabsContext] Filtering out closed tab: ${tabId}`);
          }
          return !isClosed;
        })
        .map((analysis) => {
        // Format the analysis result for display
        let content = '';
        const result = analysis.result || {};
        
        // Debug logging
        console.log(`[TabsContext] Processing analysis ${analysis.id}:`, {
          hasResult: !!analysis.result,
          resultKeys: analysis.result ? Object.keys(analysis.result) : [],
          status: analysis.status,
        });
        
        if (result.decision_summary?.description) {
          content += `## 💡 ${result.decision_summary.description}\n\n`;
          if (result.decision_summary.importance) {
            content += `**Pourquoi cette décision est importante :** ${result.decision_summary.importance}\n\n`;
          }
        }
        
        if (result.key_metrics) {
          content += `## 📈 Métriques Clés\n\n`;
          Object.entries(result.key_metrics).forEach(([key, metric]: [string, any]) => {
            const value = typeof metric.value === 'number' ? metric.value.toLocaleString('fr-FR') : metric.value;
            content += `- **${key.replace(/_/g, ' ')}**: ${value}${metric.unit || ''}${metric.period ? ` (${metric.period})` : ''}\n`;
          });
          content += '\n';
        }
        
        if (result.critical_factors && result.critical_factors.length > 0) {
          content += `## ⚠️ Facteurs Critiques\n\n`;
          result.critical_factors.forEach((factor: any) => {
            content += `${factor.number}. **${factor.factor}**\n${factor.description}\n\n`;
          });
        }
        
        if (result.scenarios) {
          content += `## 🔮 Scénarios\n\n`;
          if (result.scenarios.optimistic) {
            content += `**Optimiste:** ${result.scenarios.optimistic.description}\n\n`;
          }
          if (result.scenarios.realistic) {
            content += `**Réaliste:** ${result.scenarios.realistic.description}\n\n`;
          }
          if (result.scenarios.pessimistic) {
            content += `**Pessimiste:** ${result.scenarios.pessimistic.description}\n\n`;
          }
        }
        
        if (result.recommended_actions && result.recommended_actions.length > 0) {
          content += `## ✅ Actions Recommandées\n\n`;
          result.recommended_actions.forEach((action: any) => {
            const priorityEmoji = action.priority === 'critical' ? '🔴' : action.priority === 'important' ? '🟡' : '🟢';
            content += `${priorityEmoji} **${action.priority.toUpperCase()}**: ${action.action}`;
            if (action.impact) content += `\n   Impact: ${action.impact}`;
            if (action.timeline) content += `\n   Timeline: ${action.timeline}`;
            content += '\n\n';
          });
        }
        
        // Fallback to full_analysis_text if available and content is empty
        if (!content && result.full_analysis_text) {
          content = result.full_analysis_text;
        }
        
        // Check if result has meaningful data (not just empty object)
        // Supabase JSONB columns are automatically parsed as objects
        const hasResultData = result && 
          typeof result === 'object' && 
          !Array.isArray(result) &&
          Object.keys(result).length > 0 &&
          (result.decision_summary || result.key_metrics || result.critical_factors || result.scenarios || result.recommended_actions || result.charts || result.current_context || result.alternatives);
        
        console.log(`[TabsContext] Analysis ${analysis.id} - hasResultData:`, hasResultData);
        console.log(`[TabsContext] Analysis ${analysis.id} - result type:`, typeof result);
        console.log(`[TabsContext] Analysis ${analysis.id} - result keys:`, result && typeof result === 'object' ? Object.keys(result) : 'N/A');
        
        // Générer les hypothèses dynamiquement si on a des données d'analyse
        // On utilise les hypothèses initiales pour l'instant, elles seront mises à jour par le useEffect dans CFOAssistant
        const tabHypothesis = generateInitialHypothesis(analysis.question);
        
        // Extract hypotheses from analysis result if available
        let finalHypothesis = tabHypothesis;
        if (hasResultData && result.hypotheses && Array.isArray(result.hypotheses) && result.hypotheses.length > 0) {
          finalHypothesis = result.hypotheses as HypothesisChip[];
        }
        
        const tab: DecisionTab = {
          id: `analysis-${analysis.id}`,
          label: extractShortLabel(analysis.question),
          query: analysis.question,
          hypothesis: finalHypothesis,
          chartData: generateInitialChartData(analysis.question),
          analysisResult: hasResultData ? (result as AnalysisResult) : undefined, // Store structured data only if meaningful
          chatHistory: [
            {
              id: `msg-user-${analysis.id}`,
              role: 'user' as const,
              content: analysis.question,
              timestamp: new Date(analysis.created_at),
            },
            {
              id: `msg-${analysis.id}`,
              role: 'assistant' as const,
              content: content || `Analyse : ${analysis.question}`,
              timestamp: new Date(analysis.created_at),
            },
          ],
        };
        
        // Debug logging for analysisResult
        if (tab.analysisResult) {
          console.log(`[TabsContext] Tab ${tab.id} has analysisResult with keys:`, Object.keys(tab.analysisResult));
        } else {
          console.log(`[TabsContext] Tab ${tab.id} has NO analysisResult (result was empty or null)`);
        }
        
        return tab;
      });

      // Tabs are already filtered above using closedTabsForProject from localStorage
      // No need for additional filtering here
      console.log(`[TabsContext] Created ${tabs.length} tabs (closed tabs already filtered)`);

      // Check if project has changed - if so, clear all temporary tabs
      const projectChanged = lastProjectId !== null && lastProjectId !== activeProjectId;
      
      console.log(`[TabsContext] Project changed: ${projectChanged}, Last: ${lastProjectId}, Current: ${activeProjectId}`);
      
      // Replace all tabs with loaded analyses from Supabase
      // Only preserve temporary tabs if we're still in the same project
      let mergedTabs: DecisionTab[] = [];
      setDecisionTabs((prevTabs) => {
        console.log(`[TabsContext] Previous tabs:`, prevTabs.map(t => t.id));
        const loadedTabIds = new Set(tabs.map(t => t.id));
        console.log(`[TabsContext] Loaded tab IDs (after filtering closed tabs):`, Array.from(loadedTabIds));
        
        // If project changed, remove all temporary tabs
        // Otherwise, keep temporary tabs that are still being created (not yet synced)
        const activeTempTabs = projectChanged 
          ? [] // Clear all temp tabs when project changes
          : prevTabs.filter(t => 
              t.id.startsWith('decision-') && // Temporary tabs
              !loadedTabIds.has(t.id) // That haven't been synced yet
            );
        
        console.log(`[TabsContext] Active temp tabs:`, activeTempTabs.map(t => t.id));
        
        // Merge: active temp tabs + loaded tabs (closed tabs already filtered out above)
        const merged = [...activeTempTabs, ...tabs];
        
        // Remove duplicates (keep the loaded version if exists)
        mergedTabs = merged.reduce((acc, tab) => {
          if (!acc.find(t => t.id === tab.id)) {
            acc.push(tab);
          }
          return acc;
        }, [] as DecisionTab[]);
        
        console.log(`[TabsContext] Merged tabs:`, mergedTabs.map(t => t.id));
        
        return mergedTabs;
      });

      // Update last project ID
      setLastProjectId(activeProjectId);

      // If active tab doesn't exist in merged tabs, go back to dashboard
      setActiveTabId((currentTabId) => {
        if (currentTabId !== 'dashboard' && !mergedTabs.find(t => t.id === currentTabId)) {
          console.log(`[TabsContext] Active tab ${currentTabId} not found, switching to dashboard`);
          return 'dashboard';
        }
        return currentTabId;
      });
    } catch (error) {
      console.error('Error loading analyses:', error);
    }
  }, [user, activeProjectId, supabase]); // Removed closedTabs from dependencies - we load it fresh from localStorage

  useEffect(() => {
    loadAnalyses();
  }, [loadAnalyses]);

  const setActiveTab = (tabId: string) => {
    setActiveTabId(tabId);
  };

  const createDecisionTab = (query: string) => {
    if (!activeProjectId) {
      alert('Veuillez sélectionner un projet avant de créer une analyse.');
      return;
    }

    // Générer un ID unique et un label court
    const id = `decision-${Date.now()}`;
    const label = extractShortLabel(query);
    
    const newTab: DecisionTab = {
      id,
      label,
      query,
      hypothesis: generateInitialHypothesis(query),
      chartData: generateInitialChartData(query),
      chatHistory: [
        {
          id: `msg-${Date.now()}`,
          role: 'assistant',
          content: `J'analyse votre question : "${query}". Laissez-moi préparer une simulation...`,
          timestamp: new Date(),
        },
      ],
    };

    setDecisionTabs((prev) => [...prev, newTab]);
    setActiveTabId(id);
  };

  const closeTab = (tabId: string) => {
    // Only track closed tabs for analysis tabs (not temporary decision tabs)
    if (tabId.startsWith('analysis-') && activeProjectId) {
      setClosedTabs((prev) => {
        const newClosed = new Set(prev);
        newClosed.add(tabId);
        saveClosedTabs(activeProjectId, newClosed);
        return newClosed;
      });
    }
    
    setDecisionTabs((prev) => prev.filter((tab) => tab.id !== tabId));
    if (activeTabId === tabId) {
      setActiveTabId('dashboard');
    }
  };

  const reopenTab = (tabId: string) => {
    if (activeProjectId) {
      setClosedTabs((prev) => {
        const newClosed = new Set(prev);
        newClosed.delete(tabId);
        saveClosedTabs(activeProjectId, newClosed);
        return newClosed;
      });
      // Reload analyses to show the reopened tab
      loadAnalyses();
      setActiveTabId(tabId);
    }
  };

  const permanentlyDeleteTab = async (tabId: string) => {
    // Extract analysis ID from tab ID (format: "analysis-{uuid}")
    const analysisId = tabId.replace('analysis-', '');
    
    if (!user || !analysisId) return;
    
    try {
      const { error } = await supabase
        .from('analyses')
        .delete()
        .eq('id', analysisId)
        .eq('user_id', user.id);
      
      if (error) {
        console.error('Error deleting analysis:', error);
        throw error;
      }
      
      // Remove from closed tabs
      if (activeProjectId) {
        setClosedTabs((prev) => {
          const newClosed = new Set(prev);
          newClosed.delete(tabId);
          saveClosedTabs(activeProjectId, newClosed);
          return newClosed;
        });
      }
      
      console.log(`[TabsContext] Permanently deleted analysis ${analysisId}`);
    } catch (error) {
      console.error('Error permanently deleting tab:', error);
      throw error;
    }
  };

  const getClosedTabsForProject = useCallback(async (projectId: string): Promise<DecisionTab[]> => {
    if (!user || !projectId) return [];
    
    try {
      const { data, error } = await supabase
        .from('analyses')
        .select('*')
        .eq('user_id', user.id)
        .eq('project_id', projectId)
        .order('created_at', { ascending: false });
      
      if (error) {
        console.error('[TabsContext] Error loading closed tabs:', error);
        return [];
      }
      
      // Load closed tabs from localStorage
      const storageKey = `closed_tabs_${projectId}`;
      const stored = localStorage.getItem(storageKey);
      const closedIds = stored ? new Set(JSON.parse(stored) as string[]) : new Set();
      
      // Return only closed tabs
      return (data || [])
        .filter((analysis) => {
          const tabId = `analysis-${analysis.id}`;
          return closedIds.has(tabId);
        })
        .map((analysis) => {
          const result = analysis.result || {};
          const hasResultData = result && 
            typeof result === 'object' && 
            !Array.isArray(result) &&
            Object.keys(result).length > 0;
          
          return {
            id: `analysis-${analysis.id}`,
            label: extractShortLabel(analysis.question),
            query: analysis.question,
            hypothesis: hasResultData && result.hypotheses ? (result.hypotheses as HypothesisChip[]) : generateInitialHypothesis(analysis.question),
            chartData: generateInitialChartData(analysis.question),
            analysisResult: hasResultData ? (result as AnalysisResult) : undefined,
            chatHistory: [],
          };
        });
    } catch (error) {
      console.error('Error getting closed tabs:', error);
      return [];
    }
  }, [user, supabase]);

  const updateTabHypothesis = (tabId: string, hypothesis: HypothesisChip[]) => {
    setDecisionTabs((prev) =>
      prev.map((tab) => (tab.id === tabId ? { ...tab, hypothesis } : tab))
    );
  };

  const addChatMessage = (tabId: string, message: ChatMessage) => {
    setDecisionTabs((prev) =>
      prev.map((tab) =>
        tab.id === tabId
          ? {
              ...tab,
              chatHistory: [...(tab.chatHistory || []), message],
            }
          : tab
      )
    );
  };

  const updateTabWithAnalysisId = (tempTabId: string, analysisId: string) => {
    console.log(`[TabsContext] Updating tab ${tempTabId} to analysis-${analysisId}`);
    setDecisionTabs((prev) => {
      const updated = prev.map((tab) =>
        tab.id === tempTabId
          ? {
              ...tab,
              id: `analysis-${analysisId}`,
            }
          : tab
      );
      console.log(`[TabsContext] Updated tabs:`, updated.map(t => t.id));
      return updated;
    });
    // Update active tab ID if it was the temp tab
    if (activeTabId === tempTabId) {
      console.log(`[TabsContext] Updating active tab ID to analysis-${analysisId}`);
      setActiveTabId(`analysis-${analysisId}`);
    }
  };

  return (
    <TabsContext.Provider
      value={{
        activeTabId,
        decisionTabs,
        setActiveTab,
        createDecisionTab,
        closeTab,
        reopenTab,
        permanentlyDeleteTab,
        getClosedTabsForProject,
        updateTabHypothesis,
        addChatMessage,
        updateTabWithAnalysisId,
        refreshAnalyses: loadAnalyses,
      }}
    >
      {children}
    </TabsContext.Provider>
  );
}

export function useTabs() {
  const context = useContext(TabsContext);
  if (context === undefined) {
    throw new Error('useTabs must be used within a TabsProvider');
  }
  return context;
}

// Helper function pour extraire un label court de la question
function extractShortLabel(query: string): string {
  const lowerQuery = query.toLowerCase();
  
  if (lowerQuery.includes('recrut') || lowerQuery.includes('embauch')) {
    return 'Recrutement';
  }
  if (lowerQuery.includes('stock') || lowerQuery.includes('inventaire')) {
    return 'Stock';
  }
  if (lowerQuery.includes('invest') || lowerQuery.includes('équipement')) {
    return 'Investissement';
  }
  if (lowerQuery.includes('prix') || lowerQuery.includes('tarif')) {
    return 'Prix';
  }
  if (lowerQuery.includes('bfr') || lowerQuery.includes('trésorerie')) {
    return 'Trésorerie';
  }
  
  // Par défaut, prendre les premiers mots
  const words = query.split(' ').slice(0, 2);
  return words.join(' ');
}

// Helper function pour générer des hypothèses initiales selon le type de question
function generateInitialHypothesis(query: string): HypothesisChip[] {
  const lowerQuery = query.toLowerCase();
  
  if (lowerQuery.includes('recrut') || lowerQuery.includes('embauch')) {
    return [
      { id: 'salary', label: 'Salaire brut', value: 60000, type: 'number' },
      { id: 'start-date', label: 'Date d\'embauche', value: '2024-01-01', type: 'date' },
      { id: 'charges', label: 'Charges sociales', value: 42, type: 'number' },
    ];
  }
  if (lowerQuery.includes('stock') || lowerQuery.includes('inventaire')) {
    return [
      { id: 'rotation', label: 'Rotation (jours)', value: 60, type: 'number' },
      { id: 'stock-value', label: 'Valeur stock', value: 50000, type: 'number' },
    ];
  }
  if (lowerQuery.includes('invest') || lowerQuery.includes('équipement')) {
    return [
      { id: 'amount', label: 'Montant investissement', value: 100000, type: 'number' },
      { id: 'duration', label: 'Durée (mois)', value: 60, type: 'number' },
    ];
  }
  if (lowerQuery.includes('prix') || lowerQuery.includes('tarif')) {
    return [
      { id: 'increase', label: 'Augmentation (%)', value: 5, type: 'number' },
      { id: 'volume', label: 'Volume de vente', value: 1000, type: 'number' },
    ];
  }
  
  return [];
}

// Helper function pour générer des données de graphique initiales
function generateInitialChartData(query: string): ChartData {
  const months = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'];
  
  // Générer des données de base pour la simulation
  const baseData = Array.from({ length: 12 }, (_, i) => 50000 + Math.random() * 20000);
  const scenarioData = Array.from({ length: 12 }, (_, i) => {
    if (i < 3) return baseData[i];
    return baseData[i] - 5000 - Math.random() * 10000;
  });

  return {
    labels: months,
    datasets: [
      {
        label: 'Scénario actuel',
        data: baseData,
        type: 'line',
        color: '#6B7280',
      },
      {
        label: 'Scénario simulé',
        data: scenarioData,
        type: 'line',
        color: '#1A1A1A',
      },
    ],
  };
}

