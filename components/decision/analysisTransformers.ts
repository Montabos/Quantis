import { AnalysisResult } from '@/hooks/useDecisionAnalysis';

export interface TransformedKPI {
  label: string;
  value: string;
  subtitle?: string;
  negative?: boolean;
}

export interface TransformedAction {
  priority: string;
  action: string;
  impact?: string;
  timeline?: string;
  color: 'red' | 'amber' | 'emerald';
}

/**
 * Transform key metrics from AnalysisResult to format suitable for KPIWidget
 * Includes validation and normalization
 */
export function transformKeyMetrics(
  metrics?: Record<string, { value: string | number; unit?: string; period?: string; description?: string }>
): TransformedKPI[] {
  if (!metrics || typeof metrics !== 'object') return [];

  return Object.entries(metrics)
    .filter(([key, metric]) => {
      // Validate: metric must be an object with a value
      if (!metric || typeof metric !== 'object') return false;
      if (metric.value === null || metric.value === undefined || metric.value === '') return false;
      return true;
    })
    .map(([key, metric]) => {
      // Normalize value
      let normalizedValue: string | number = metric.value;
      
      // Convert string numbers to numbers
      if (typeof normalizedValue === 'string') {
        const trimmed = normalizedValue.trim();
        // Try to parse as number
        const parsed = parseFloat(trimmed);
        if (!isNaN(parsed)) {
          normalizedValue = parsed;
        }
      }
      
      // Format the value
      let value: string;
      const numValue = typeof normalizedValue === 'number' ? normalizedValue : parseFloat(String(normalizedValue));
      
      if (!isNaN(numValue)) {
        // Format number with unit
        const absValue = Math.abs(numValue);
        const unit = metric.unit || '€';
        
        if (absValue >= 1000) {
          const formatted = (absValue / 1000).toFixed(absValue % 1000 === 0 ? 0 : 1);
          value = `${numValue < 0 ? '-' : ''}${formatted}k${unit}`;
        } else if (absValue >= 1) {
          value = `${numValue.toFixed(absValue % 1 === 0 ? 0 : 2)}${unit}`;
        } else {
          // Very small numbers - show as percentage or decimal
          if (unit === '%' || unit === 'percent') {
            value = `${(numValue * 100).toFixed(1)}%`;
          } else {
            value = `${numValue.toFixed(2)}${unit}`;
          }
        }
      } else {
        // Non-numeric value - use as-is
        value = `${normalizedValue}${metric.unit || ''}`;
      }

      // Create label from key (convert snake_case to Title Case)
      const label = key
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ')
        .trim() || key; // Fallback to key if empty

      // Create subtitle - normalize period format
      let subtitle: string | undefined;
      if (metric.period) {
        const period = String(metric.period).trim();
        subtitle = period.includes('mois') || period.includes('month') 
          ? `Sur ${period}` 
          : period.includes('jour') || period.includes('day')
          ? `Sur ${period}`
          : `Sur ${period}`;
      } else if (metric.description) {
        subtitle = String(metric.description).trim();
      }

      // Detect negative values
      const negative = numValue < 0 || (typeof metric.value === 'string' && metric.value.trim().startsWith('-'));

      return {
        label,
        value,
        subtitle,
        negative,
      };
    })
    .slice(0, 6); // Limit to 6 KPIs max for display
}

/**
 * Transform critical factors - validate and normalize format
 */
export function transformCriticalFactors(
  factors?: Array<{ number?: number; factor?: string; description?: string }>
): Array<{ number: number; factor: string; description: string }> {
  if (!factors || !Array.isArray(factors)) return [];

  return factors
    .filter((factor) => {
      // Validate: must have factor and description
      return factor && 
             typeof factor === 'object' &&
             factor.factor && 
             factor.description &&
             String(factor.factor).trim() !== '' &&
             String(factor.description).trim() !== '';
    })
    .map((factor, index) => {
      // Normalize: ensure number is set
      const number = typeof factor.number === 'number' && factor.number > 0 
        ? factor.number 
        : index + 1;
      
      return {
        number,
        factor: String(factor.factor).trim(),
        description: String(factor.description).trim(),
      };
    });
}

/**
 * Transform scenarios - validate and normalize format
 */
export function transformScenarios(scenarios?: AnalysisResult['scenarios']): TransformedScenario[] {
  if (!scenarios || typeof scenarios !== 'object') return [];

  const transformed: TransformedScenario[] = [];
  
  // Validate and transform optimistic scenario
  if (scenarios.optimistic && typeof scenarios.optimistic === 'object') {
    const opt = scenarios.optimistic;
    if (opt.description && String(opt.description).trim()) {
      transformed.push({
        name: 'Scénario Optimiste',
        description: String(opt.description).trim(),
        color: 'emerald',
      });
    }
  }
  
  // Validate and transform realistic scenario
  if (scenarios.realistic && typeof scenarios.realistic === 'object') {
    const real = scenarios.realistic;
    if (real.description && String(real.description).trim()) {
      transformed.push({
        name: 'Scénario Réaliste',
        description: String(real.description).trim(),
        color: 'gray',
      });
    }
  }
  
  // Validate and transform pessimistic scenario
  if (scenarios.pessimistic && typeof scenarios.pessimistic === 'object') {
    const pess = scenarios.pessimistic;
    if (pess.description && String(pess.description).trim()) {
      transformed.push({
        name: 'Scénario Pessimiste',
        description: String(pess.description).trim(),
        color: 'red',
      });
    }
  }
  
  return transformed;
}

export interface TransformedScenario {
  name: string;
  description: string;
  color: 'emerald' | 'gray' | 'red';
}

/**
 * Transform recommended actions to format with colors
 * Includes validation and normalization
 */
export function transformRecommendedActions(
  actions?: Array<{ priority?: 'critical' | 'important' | 'recommended' | string; action?: string; impact?: string; timeline?: string }>
): TransformedAction[] {
  if (!actions || !Array.isArray(actions)) return [];

  const colorMap: Record<string, 'red' | 'amber' | 'emerald'> = {
    critical: 'red',
    important: 'amber',
    recommended: 'emerald',
    critique: 'red',
    importante: 'amber',
    recommandé: 'emerald',
  };

  return actions
    .filter((action) => {
      // Validate: must have action text
      return action && 
             typeof action === 'object' &&
             action.action &&
             String(action.action).trim() !== '';
    })
    .map((action) => {
      // Normalize priority
      const priority = action.priority 
        ? String(action.priority).toLowerCase().trim()
        : 'recommended';
      
      // Map priority to color
      const color = colorMap[priority] || 'emerald';
      
      // Normalize priority label
      let normalizedPriority = priority;
      if (priority === 'critical' || priority === 'critique') {
        normalizedPriority = 'critical';
      } else if (priority === 'important' || priority === 'importante') {
        normalizedPriority = 'important';
      } else {
        normalizedPriority = 'recommended';
      }

      return {
        priority: normalizedPriority,
        action: String(action.action).trim(),
        impact: action.impact ? String(action.impact).trim() : undefined,
        timeline: action.timeline ? String(action.timeline).trim() : undefined,
        color,
      };
    });
}

/**
 * Transform alternatives - validate and normalize format
 */
export function transformAlternatives(
  alternatives?: Array<{ name?: string; description?: string; impact?: string }>
): Array<{ name: string; description: string; impact?: string }> {
  if (!alternatives || !Array.isArray(alternatives)) return [];

  return alternatives
    .filter((alt) => {
      // Validate: must have name and description
      return alt && 
             typeof alt === 'object' &&
             alt.name &&
             alt.description &&
             String(alt.name).trim() !== '' &&
             String(alt.description).trim() !== '';
    })
    .map((alt) => {
      return {
        name: String(alt.name).trim(),
        description: String(alt.description).trim(),
        impact: alt.impact ? String(alt.impact).trim() : undefined,
      };
    });
}

/**
 * Transform charts - ensure data_base64 is present and valid
 * Includes validation and normalization
 */
export function transformCharts(
  charts?: Array<{ filename?: string; mime_type?: string; data_base64?: string }>
): Array<{ filename: string; mime_type: string; data_base64: string }> {
  if (!charts || !Array.isArray(charts)) return [];
  
  return charts
    .filter((chart) => {
      // Validate: must have data_base64 and it must be a non-empty string
      if (!chart || typeof chart !== 'object') return false;
      if (!chart.data_base64 || typeof chart.data_base64 !== 'string') return false;
      if (chart.data_base64.trim() === '') return false;
      return true;
    })
    .map((chart) => {
      // Normalize: ensure filename and mime_type have defaults
      const filename = chart.filename && String(chart.filename).trim()
        ? String(chart.filename).trim()
        : `chart_${Date.now()}.png`;
      
      const mime_type = chart.mime_type && String(chart.mime_type).trim()
        ? String(chart.mime_type).trim()
        : 'image/png';
      
      return {
        filename,
        mime_type,
        data_base64: String(chart.data_base64).trim(),
      };
    });
}

