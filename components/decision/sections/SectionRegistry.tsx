import React from 'react';
import { AnalysisResult } from '@/hooks/useDecisionAnalysis';
import { DecisionTab } from '@/contexts/TabsContext';
import { Target, AlertTriangle, TrendingUp, Lightbulb, ArrowRight } from 'lucide-react';
import { AnalysisSection } from '../AnalysisSection';
import { KPIWidget } from '../KPIWidget';
import { GeneratedChart } from '../GeneratedChart';
import {
  transformKeyMetrics,
  transformCriticalFactors,
  transformScenarios,
  transformRecommendedActions,
  transformAlternatives,
  transformCharts,
} from '../analysisTransformers';

export interface SectionComponentProps {
  tab: DecisionTab;
  result: AnalysisResult;
}

export type SectionComponent = React.ComponentType<SectionComponentProps>;

interface SectionRegistryEntry {
  id: string;
  component: SectionComponent;
  defaultTitle?: string;
  defaultIcon?: React.ComponentType<{ className?: string }>;
}

class SectionRegistry {
  private sections: Map<string, SectionRegistryEntry> = new Map();

  register(id: string, component: SectionComponent, options?: {
    defaultTitle?: string;
    defaultIcon?: React.ComponentType<{ className?: string }>;
  }) {
    this.sections.set(id, {
      id,
      component,
      defaultTitle: options?.defaultTitle,
      defaultIcon: options?.defaultIcon,
    });
  }

  get(id: string): SectionRegistryEntry | undefined {
    return this.sections.get(id);
  }

  getAll(): SectionRegistryEntry[] {
    return Array.from(this.sections.values());
  }

  has(id: string): boolean {
    return this.sections.has(id);
  }
}

// Create singleton instance
export const sectionRegistry = new SectionRegistry();

// Register default sections
sectionRegistry.register('decision_summary', DecisionSummarySection, {
  defaultTitle: 'La Décision à Analyser',
  defaultIcon: Target,
});

sectionRegistry.register('key_metrics', KeyMetricsSection, {
  defaultTitle: 'Métriques Clés',
});

sectionRegistry.register('critical_factors', CriticalFactorsSection, {
  defaultTitle: 'Ce qu\'il faut prendre en compte',
  defaultIcon: AlertTriangle,
});

sectionRegistry.register('current_context', CurrentContextSection, {
  defaultTitle: 'Contexte actuel de votre entreprise',
  defaultIcon: TrendingUp,
});

sectionRegistry.register('scenarios', ScenariosSection, {
  defaultTitle: 'Possibilités et Prédictions',
  defaultIcon: Lightbulb,
});

sectionRegistry.register('recommended_actions', RecommendedActionsSection, {
  defaultTitle: 'Actions Recommandées',
  defaultIcon: ArrowRight,
});

sectionRegistry.register('alternatives', AlternativesSection, {
  defaultTitle: 'Alternatives Stratégiques',
  defaultIcon: Lightbulb,
});

sectionRegistry.register('charts', ChartsSection, {
  defaultTitle: 'Visualisations',
});

// Section Components
function DecisionSummarySection({ tab, result }: SectionComponentProps) {
  if (!result.decision_summary) return null;

  return (
    <AnalysisSection
      icon={Target}
      title="La Décision à Analyser"
      content={
        <>
          {result.decision_summary.description && (
            <p className="text-[#1A1A1A] leading-relaxed mb-4 text-sm" style={{ letterSpacing: '-0.01em' }}>
              {result.decision_summary.description}
            </p>
          )}
          {result.decision_summary.importance && (
            <div className="bg-[#D4AF37]/5 rounded-lg border border-[#D4AF37]/20 p-4">
              <p className="text-sm text-[#1A1A1A] font-medium leading-relaxed" style={{ letterSpacing: '-0.01em' }}>
                <strong>Pourquoi cette décision est importante :</strong> {result.decision_summary.importance}
              </p>
            </div>
          )}
        </>
      }
    />
  );
}

function KeyMetricsSection({ tab, result }: SectionComponentProps) {
  const kpis = transformKeyMetrics(result?.key_metrics);
  if (!kpis || kpis.length === 0) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 my-10">
      {kpis.map((kpi, index) => (
        <KPIWidget
          key={index}
          label={kpi.label}
          value={kpi.value}
          subtitle={kpi.subtitle}
          gradient=""
          border="border-[#E5E5E5]"
          negative={kpi.negative}
        />
      ))}
    </div>
  );
}

function CriticalFactorsSection({ tab, result }: SectionComponentProps) {
  const factors = transformCriticalFactors(result?.critical_factors);
  if (!factors || factors.length === 0) return null;

  return (
    <AnalysisSection
      icon={AlertTriangle}
      title="Ce qu'il faut prendre en compte"
      content={
        <>
          <p className="text-[#1A1A1A] leading-relaxed mb-6 text-[15px] font-light">
            Avant de valider cette décision, plusieurs facteurs critiques doivent être évalués :
          </p>
          <ul className="space-y-4 mb-4">
            {factors.map((factor, index) => (
              <li key={index} className="flex items-start gap-4">
                <div className="w-6 h-6 rounded bg-[#1A1A1A] flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-xs font-medium text-white">{factor.number}</span>
                </div>
                <div>
                  <p className="text-[#1A1A1A] font-medium mb-1">{factor.factor}</p>
                  <p className="text-[#6B7280] text-sm font-light leading-relaxed">{factor.description}</p>
                </div>
              </li>
            ))}
          </ul>
        </>
      }
    />
  );
}

function CurrentContextSection({ tab, result }: SectionComponentProps) {
  if (!result.current_context) return null;
  const context = result.current_context;
  if (!context.strengths?.length && !context.weaknesses?.length) return null;

  return (
    <AnalysisSection
      icon={TrendingUp}
      title="Contexte actuel de votre entreprise"
      content={
        <>
          <p className="text-[#1A1A1A] leading-relaxed mb-6 text-[15px] font-light">
            Votre situation financière actuelle présente des forces et des fragilités :
          </p>
          <div className="grid grid-cols-2 gap-6 mb-6">
            {context.strengths && context.strengths.length > 0 && (
              <div className="bg-white border border-[#E0E0E0] rounded-lg p-5">
                <p className="text-xs font-medium text-[#6B7280] mb-3 uppercase tracking-wider">Points forts</p>
                <ul className="text-sm text-[#1A1A1A] space-y-2 font-light">
                  {context.strengths.map((strength, index) => (
                    <li key={index} className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                      {strength}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {context.weaknesses && context.weaknesses.length > 0 && (
              <div className="bg-white border border-[#E0E0E0] rounded-lg p-5">
                <p className="text-xs font-medium text-[#6B7280] mb-3 uppercase tracking-wider">Points d&apos;attention</p>
                <ul className="text-sm text-[#1A1A1A] space-y-2 font-light">
                  {context.weaknesses.map((weakness, index) => (
                    <li key={index} className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                      {weakness}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          {context.summary && (
            <p className="text-sm text-[#6B7280] font-light italic">
              {context.summary}
            </p>
          )}
        </>
      }
    />
  );
}

function ScenariosSection({ tab, result }: SectionComponentProps) {
  const scenarios = transformScenarios(result?.scenarios);
  if (!scenarios || scenarios.length === 0) return null;

  return (
    <AnalysisSection
      icon={Lightbulb}
      title="Possibilités et Prédictions"
      content={
        <>
          <p className="text-[#1A1A1A] leading-relaxed mb-6 text-[15px] font-light">
            Voici ce qui pourrait se passer selon différents scénarios :
          </p>
          <div className="space-y-4">
            {scenarios.map((scenario, index) => (
              <div key={index} className={`border-l-2 border-${scenario.color}-500 pl-5 py-4 bg-white border border-[#E0E0E0] rounded-lg`}>
                <p className="font-medium text-[#1A1A1A] mb-2 text-sm">{scenario.name}</p>
                <p className="text-sm text-[#6B7280] font-light leading-relaxed">
                  {scenario.description}
                </p>
              </div>
            ))}
          </div>
        </>
      }
    />
  );
}

function RecommendedActionsSection({ tab, result }: SectionComponentProps) {
  const actions = transformRecommendedActions(result?.recommended_actions);
  if (!actions || actions.length === 0) return null;

  return (
    <AnalysisSection
      icon={ArrowRight}
      title="Actions Recommandées"
      content={
        <>
          <p className="text-[#1A1A1A] leading-relaxed mb-5 text-sm" style={{ letterSpacing: '-0.01em' }}>
            Pour sécuriser cette décision, voici les actions prioritaires :
          </p>
          <div className="space-y-2.5">
            {actions.map((item, index) => (
              <div
                key={index}
                className="flex items-start gap-3 p-4 bg-white border border-[#E5E5E5] rounded-lg hover:border-[#D4AF37]/30 hover:shadow-sm transition-all duration-200"
              >
                <div className="flex-shrink-0">
                  <span
                    className={`text-[10px] font-semibold px-2 py-1 rounded-md uppercase tracking-wider ${
                      item.color === 'red'
                        ? 'bg-red-50 text-red-600 border border-red-200'
                        : item.color === 'amber'
                        ? 'bg-amber-50 text-amber-600 border border-amber-200'
                        : 'bg-emerald-50 text-emerald-600 border border-emerald-200'
                    }`}
                  >
                    {item.priority}
                  </span>
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-[#1A1A1A] mb-1 text-sm" style={{ letterSpacing: '-0.01em' }}>{item.action}</p>
                  {item.impact && <p className="text-xs text-[#737373] font-medium">{item.impact}</p>}
                </div>
              </div>
            ))}
          </div>
        </>
      }
    />
  );
}

function AlternativesSection({ tab, result }: SectionComponentProps) {
  const alternatives = transformAlternatives(result?.alternatives);
  if (!alternatives || alternatives.length === 0) return null;

  return (
    <AnalysisSection
      icon={Lightbulb}
      title="Alternatives Stratégiques"
      content={
        <>
          <p className="text-[#1A1A1A] leading-relaxed mb-6 text-[15px] font-light">
            Si cette décision vous semble trop risquée, voici des alternatives adaptées à votre situation :
          </p>
          <div className="grid grid-cols-2 gap-6">
            {alternatives.map((alt, index) => (
              <div key={index} className="bg-white border border-[#E0E0E0] rounded-lg p-6 hover:border-[#1A1A1A] transition-colors">
                <p className="font-medium text-[#1A1A1A] mb-3 text-sm">{alt.name}</p>
                <p className="text-sm text-[#6B7280] mb-4 font-light leading-relaxed">
                  {alt.description}
                </p>
                {alt.impact && (
                  <div className="flex items-center gap-2 text-xs text-[#6B7280] font-light">
                    <span className="font-medium">Impact tréso :</span>
                    <span>{alt.impact}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      }
    />
  );
}

function ChartsSection({ tab, result }: SectionComponentProps) {
  const charts = transformCharts(result?.charts);
  if (!charts || charts.length === 0) return null;

  return (
    <>
      {charts.map((chart, index) => (
        <GeneratedChart
          key={index}
          data_base64={chart.data_base64}
          mime_type={chart.mime_type}
          filename={chart.filename}
        />
      ))}
    </>
  );
}

// Custom section component for dynamic sections
export function CustomSection({ section }: { section: { id: string; type: string; title: string; content: any } }) {
  return (
    <AnalysisSection
      icon={Lightbulb}
      title={section.title}
      content={
        <div className="text-sm text-[#1A1A1A] leading-relaxed">
          {typeof section.content === 'string' ? (
            <p>{section.content}</p>
          ) : (
            <pre className="whitespace-pre-wrap">{JSON.stringify(section.content, null, 2)}</pre>
          )}
        </div>
      }
    />
  );
}

