import { useState, useCallback } from 'react';
import { useFiles } from '@/contexts/FilesContext';
import { useProjects } from '@/contexts/ProjectsContext';

export interface AnalysisResult {
  decision_summary?: {
    description?: string;
    importance?: string;
  };
  key_metrics?: Record<string, {
    value: string | number;
    unit?: string;
    period?: string;
    description?: string;
  }>;
  critical_factors?: Array<{
    number: number;
    factor: string;
    description: string;
  }>;
  current_context?: {
    strengths?: string[];
    weaknesses?: string[];
    summary?: string;
  };
  scenarios?: {
    optimistic?: {
      description?: string;
      key_milestones?: string[];
    };
    realistic?: {
      description?: string;
      risk_periods?: string[];
    };
    pessimistic?: {
      description?: string;
      risk_periods?: string[];
    };
    best_case?: string;
    worst_case?: string;
  };
  recommended_actions?: Array<{
    priority: 'critical' | 'important' | 'recommended';
    action: string;
    impact?: string;
    timeline?: string;
  }>;
  alternatives?: Array<{
    name: string;
    description: string;
    impact?: string;
  }>;
  charts?: Array<{
    filename: string;
    mime_type: string;
    data_base64?: string;
  }>;
  hypotheses?: Array<{
    id: string;
    label: string;
    value: string | number;
    type: 'number' | 'date';
  }>;
  report_structure?: {
    sections_order: string[];
    sections_config: Record<string, {
      title?: string;
      visible: boolean;
      custom_component?: string;
    }>;
    custom_sections?: Array<{
      id: string;
      type: string;
      title: string;
      content: any;
    }>;
  };
  full_analysis_text?: string;
  data_quality?: 'good' | 'partial' | 'estimated' | 'unknown';
  estimation_notes?: string[];
}

export function useDecisionAnalysis() {
  const { getReadyFiles } = useFiles();
  const { activeProjectId } = useProjects();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const analyzeDecision = useCallback(async (question: string) => {
    if (!activeProjectId) {
      setError('Veuillez sélectionner un projet avant de créer une analyse.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      // Get ready files automatically
      const readyFiles = getReadyFiles();
      const fileIds = readyFiles.map((f) => f.backendId || f.id).filter(Boolean);

      const response = await fetch('/api/decisions/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question,
          file_ids: fileIds.length > 0 ? fileIds : undefined,
          project_id: activeProjectId,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Analysis failed' }));
        throw new Error(errorData.error || 'Analysis failed');
      }

      const analysisResult = await response.json();
      setResult(analysisResult);
      return analysisResult;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [getReadyFiles, activeProjectId]);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return {
    analyzeDecision,
    isLoading,
    error,
    result,
    reset,
  };
}




