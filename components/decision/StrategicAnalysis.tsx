'use client';

import { DecisionTab } from '@/contexts/TabsContext';
import { sectionRegistry, CustomSection } from './sections/SectionRegistry';
import { ChartSection } from './ChartSection';

export function StrategicAnalysis({ tab }: { tab: DecisionTab }) {
  const chartData = tab.chartData || {
    labels: [],
    datasets: [],
  };

  // Use real data if available, otherwise fallback to hardcoded content
  const result = tab.analysisResult;
  // Check if we have meaningful data (not just empty object)
  const hasAnalysisData = !!result && 
    typeof result === 'object' && 
    Object.keys(result).length > 0 &&
    (result.decision_summary || result.key_metrics || result.critical_factors || result.scenarios || result.recommended_actions || result.charts || result.current_context);

  // Get report structure from result or use default
  const reportStructure = result?.report_structure;
  let sectionsOrder: string[] = [];
  let sectionsConfig: Record<string, { title?: string; visible: boolean; custom_component?: string }> = {};

  if (reportStructure && reportStructure.sections_order) {
    sectionsOrder = reportStructure.sections_order;
    sectionsConfig = reportStructure.sections_config || {};
  } else {
    // Default order if no structure provided - determine based on available data
    const availableSections: string[] = [];
    if (result?.decision_summary) availableSections.push('decision_summary');
    if (result?.key_metrics) availableSections.push('key_metrics');
    if (result?.critical_factors) availableSections.push('critical_factors');
    if (result?.charts) availableSections.push('charts');
    if (result?.current_context) availableSections.push('current_context');
    if (result?.scenarios) availableSections.push('scenarios');
    if (result?.recommended_actions) availableSections.push('recommended_actions');
    if (result?.alternatives) availableSections.push('alternatives');
    
    sectionsOrder = availableSections.length > 0 ? availableSections : [
      'decision_summary',
      'key_metrics',
      'critical_factors',
      'charts',
      'current_context',
      'scenarios',
      'recommended_actions',
      'alternatives',
    ];
    sectionsConfig = {};
  }

  // Filter sections to only include visible ones and those with data
  const visibleSections = sectionsOrder.filter(sectionId => {
    const config = sectionsConfig[sectionId];
    if (config && config.visible === false) return false;
    
    // Check if section has data (only for real data, not fallback)
    if (hasAnalysisData) {
      if (sectionId === 'decision_summary' && !result?.decision_summary) return false;
      if (sectionId === 'key_metrics' && !result?.key_metrics) return false;
      if (sectionId === 'critical_factors' && !result?.critical_factors) return false;
      if (sectionId === 'current_context' && !result?.current_context) return false;
      if (sectionId === 'scenarios' && !result?.scenarios) return false;
      if (sectionId === 'recommended_actions' && !result?.recommended_actions) return false;
      if (sectionId === 'alternatives' && !result?.alternatives) return false;
      if (sectionId === 'charts' && !result?.charts) return false;
    }
    
    return true;
  });

  // Render sections dynamically
  const renderSection = (sectionId: string) => {
    const sectionEntry = sectionRegistry.get(sectionId);
    if (!sectionEntry) return null;

    const SectionComponent = sectionEntry.component;
    
    // For fallback mode, pass empty result
    const sectionResult = hasAnalysisData && result ? result : ({} as any);
    
    return (
      <SectionComponent
        key={sectionId}
        tab={tab}
        result={sectionResult}
      />
    );
  };

  return (
    <div className="max-w-6xl mx-auto py-12 px-8">
      {/* Titre principal - Style Notion/Apple */}
      <div className="mb-12">
        <h1 className="text-2xl font-semibold text-[#1A1A1A] mb-2 leading-tight" style={{ letterSpacing: '-0.02em' }}>
          {tab.query}
        </h1>
        <div className="h-px w-16 bg-[#D4AF37] mt-4"></div>
      </div>

      {/* Render sections dynamically based on report_structure */}
      {visibleSections.length > 0 ? (
        <>
          {visibleSections.map(sectionId => renderSection(sectionId))}
          
          {/* Render custom sections if any */}
          {reportStructure?.custom_sections && reportStructure.custom_sections.length > 0 && (
            <>
              {reportStructure.custom_sections.map((customSection) => (
                <CustomSection key={customSection.id} section={customSection} />
              ))}
            </>
          )}
        </>
      ) : (
        /* Fallback: render default sections if no structure */
        <>
          {sectionRegistry.getAll()
            .filter(entry => ['decision_summary', 'key_metrics', 'critical_factors'].includes(entry.id))
            .map(entry => (
              <entry.component
                key={entry.id}
                tab={tab}
                result={{} as any}
              />
            ))}
          <ChartSection chartData={chartData} />
        </>
      )}
    </div>
  );
}
