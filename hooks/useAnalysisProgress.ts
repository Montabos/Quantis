import { useState, useEffect, useCallback, useRef } from 'react';

export interface AnalysisStep {
  name: string;
  label: string;
  status: 'pending' | 'in_progress' | 'completed' | 'error';
  message?: string;
  started_at?: string;
  completed_at?: string;
}

export interface MissingData {
  id: string;
  type: string;
  description: string;
  required: boolean;
}

export interface AnalysisStatus {
  analysis_id: string;
  status: 'pending' | 'in_progress' | 'waiting_for_data' | 'completed' | 'error';
  current_step: string | null;
  progress: number;
  steps: AnalysisStep[];
  missing_data: MissingData[];
  partial_result: any | null;
  result: any | null;
  question: string;
}

const POLLING_INTERVAL = 2000; // 2 seconds
const MAX_POLLING_TIME = 300000; // 5 minutes max

export function useAnalysisProgress(analysisId: string | null) {
  const [status, setStatus] = useState<AnalysisStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const isPollingRef = useRef(false);

  const pollStatus = useCallback(async () => {
    if (!analysisId || isPollingRef.current) return;

    isPollingRef.current = true;
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/decisions/analyze/${analysisId}/status`);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Failed to fetch status' }));
        throw new Error(errorData.error || 'Failed to fetch analysis status');
      }

      const data: AnalysisStatus = await response.json();
      setStatus(data);

      // Stop polling if analysis is completed or error
      if (data.status === 'completed' || data.status === 'error') {
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
        isPollingRef.current = false;
        setIsLoading(false);
        return;
      }

      // Check timeout
      if (startTimeRef.current) {
        const elapsed = Date.now() - startTimeRef.current;
        if (elapsed > MAX_POLLING_TIME) {
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
          isPollingRef.current = false;
          setIsLoading(false);
          setError('Analysis timeout: The analysis is taking longer than expected.');
          return;
        }
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      setIsLoading(false);
      
      // Stop polling on error
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
      isPollingRef.current = false;
    } finally {
      isPollingRef.current = false;
    }
  }, [analysisId]);

  const startPolling = useCallback(() => {
    if (!analysisId) return;

    // Clear any existing polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    // Reset start time
    startTimeRef.current = Date.now();

    // Initial poll
    pollStatus();

    // Set up polling interval
    pollingIntervalRef.current = setInterval(() => {
      pollStatus();
    }, POLLING_INTERVAL);
  }, [analysisId, pollStatus]);

  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    isPollingRef.current = false;
    setIsLoading(false);
  }, []);

  // Start polling when analysisId changes
  useEffect(() => {
    if (analysisId) {
      startPolling();
    } else {
      stopPolling();
      setStatus(null);
      setError(null);
    }

    // Cleanup on unmount
    return () => {
      stopPolling();
    };
  }, [analysisId, startPolling, stopPolling]);

  // Manual refresh function
  const refresh = useCallback(() => {
    if (analysisId) {
      pollStatus();
    }
  }, [analysisId, pollStatus]);

  return {
    status,
    isLoading,
    error,
    refresh,
    stopPolling,
  };
}

