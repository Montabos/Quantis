import { AnalysisResult } from '@/hooks/useDecisionAnalysis';
import { HypothesisChip } from '@/contexts/TabsContext';

/**
 * Génère des hypothèses dynamiques basées sur l'analyse actuelle et la question
 * Utilise Gemini pour générer des hypothèses intelligentes
 */
export async function generateHypothesesFromAnalysis(
  analysisResult: AnalysisResult | undefined,
  question: string,
  analysisId?: string
): Promise<HypothesisChip[]> {
  // Si on a un analysisId, utiliser Gemini pour générer des hypothèses intelligentes
  if (analysisId) {
    try {
      const response = await fetch('/api/decisions/generate-hypotheses', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          analysis_id: analysisId,
          question: question,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.hypotheses && Array.isArray(data.hypotheses) && data.hypotheses.length > 0) {
          return data.hypotheses as HypothesisChip[];
        }
      }
    } catch (error) {
      console.error('[hypothesisGenerator] Error generating hypotheses with Gemini:', error);
      // Fallback to manual generation
    }
  }

  // Fallback: génération manuelle si Gemini n'est pas disponible ou échoue
  return generateHypothesesManually(analysisResult, question);
}

/**
 * Génère des hypothèses manuellement (fallback)
 */
function generateHypothesesManually(
  analysisResult: AnalysisResult | undefined,
  question: string
): HypothesisChip[] {
  // D'abord, déterminer le type de décision basé sur la question
  const decisionType = detectDecisionType(question);
  
  // Si pas d'analyse, utiliser les hypothèses initiales basées sur la question
  if (!analysisResult) {
    return generateInitialHypothesis(question);
  }

  const hypotheses: HypothesisChip[] = [];

  // Pour les recrutements, extraire les valeurs pertinentes
  if (decisionType === 'recruitment') {
    // Chercher le salaire dans les métriques ou le résumé
    const salary = extractSalaryFromAnalysis(analysisResult, question);
    if (salary !== null) {
      hypotheses.push({
        id: 'salary',
        label: 'Salaire brut annuel',
        value: salary,
        type: 'number',
      });
    }

    // Chercher les charges sociales (généralement 42% en France)
    const charges = extractChargesFromAnalysis(analysisResult);
    if (charges !== null) {
      hypotheses.push({
        id: 'charges',
        label: 'Charges sociales (%)',
        value: charges,
        type: 'number',
      });
    }

    // Chercher la date d'embauche dans la question ou les scénarios
    const startDate = extractStartDateFromQuestion(question);
    if (startDate) {
      hypotheses.push({
        id: 'start-date',
        label: 'Date d\'embauche',
        value: startDate,
        type: 'date',
      });
    }
  }

  // Pour les investissements
  else if (decisionType === 'investment') {
    const amount = extractInvestmentAmount(analysisResult, question);
    if (amount !== null) {
      hypotheses.push({
        id: 'amount',
        label: 'Montant investissement',
        value: amount,
        type: 'number',
      });
    }

    const duration = extractDuration(analysisResult, question);
    if (duration !== null) {
      hypotheses.push({
        id: 'duration',
        label: 'Durée (mois)',
        value: duration,
        type: 'number',
      });
    }
  }

  // Pour les prix/tarifs
  else if (decisionType === 'pricing') {
    const increase = extractPriceIncrease(analysisResult, question);
    if (increase !== null) {
      hypotheses.push({
        id: 'increase',
        label: 'Augmentation (%)',
        value: increase,
        type: 'number',
      });
    }

    const volume = extractVolume(analysisResult);
    if (volume !== null) {
      hypotheses.push({
        id: 'volume',
        label: 'Volume de vente',
        value: volume,
        type: 'number',
      });
    }
  }

  // Pour les stocks/inventaires
  else if (decisionType === 'inventory') {
    const rotation = extractRotation(analysisResult);
    if (rotation !== null) {
      hypotheses.push({
        id: 'rotation',
        label: 'Rotation (jours)',
        value: rotation,
        type: 'number',
      });
    }

    const stockValue = extractStockValue(analysisResult);
    if (stockValue !== null) {
      hypotheses.push({
        id: 'stock-value',
        label: 'Valeur stock',
        value: stockValue,
        type: 'number',
      });
    }
  }

  // Si aucune hypothèse pertinente n'a été trouvée, utiliser les hypothèses initiales
  if (hypotheses.length === 0) {
    return generateInitialHypothesis(question);
  }

  // Limiter à 5 hypothèses pour ne pas surcharger l'interface
  return hypotheses.slice(0, 5);
}

/**
 * Détecte le type de décision basé sur la question
 */
function detectDecisionType(question: string): 'recruitment' | 'investment' | 'pricing' | 'inventory' | 'other' {
  const lowerQuestion = question.toLowerCase();
  
  if (lowerQuestion.includes('recrut') || lowerQuestion.includes('embauch') || lowerQuestion.includes('salaire') || lowerQuestion.includes('directeur') || lowerQuestion.includes('commercial')) {
    return 'recruitment';
  }
  // Improved detection for investments/machine purchases
  if (lowerQuestion.includes('invest') || lowerQuestion.includes('équipement') || lowerQuestion.includes('achat') || 
      lowerQuestion.includes('machine') || lowerQuestion.includes('acheter') || lowerQuestion.includes('achet') ||
      lowerQuestion.includes('productivité') || lowerQuestion.includes('productivite')) {
    return 'investment';
  }
  if (lowerQuestion.includes('prix') || lowerQuestion.includes('tarif') || lowerQuestion.includes('augment')) {
    return 'pricing';
  }
  if (lowerQuestion.includes('stock') || lowerQuestion.includes('inventaire')) {
    return 'inventory';
  }
  
  return 'other';
}

/**
 * Extrait le salaire depuis l'analyse ou la question
 */
function extractSalaryFromAnalysis(analysisResult: AnalysisResult, question: string): number | null {
  // Chercher dans la question d'abord
  const questionMatch = question.match(/(\d+[\s,.]?\d*)\s*(?:k|K)?\s*(?:€|euros?|net|brut)/i);
  if (questionMatch) {
    let value = parseFloat(questionMatch[1].replace(/[\s,]/g, ''));
    if (questionMatch[0].toLowerCase().includes('k')) {
      value *= 1000;
    }
    // Si c'est un salaire mensuel, convertir en annuel
    if (question.toLowerCase().includes('mois') || question.toLowerCase().includes('mensuel')) {
      value *= 12;
    }
    return value;
  }

  // Chercher dans les métriques
  if (analysisResult.key_metrics) {
    for (const [key, metric] of Object.entries(analysisResult.key_metrics)) {
      if (key.toLowerCase().includes('salaire') || key.toLowerCase().includes('coût') || key.toLowerCase().includes('charge')) {
        const value = extractNumericValue(metric.value);
        if (value !== null && value > 0) {
          return value;
        }
      }
    }
  }

  // Chercher dans le résumé
  if (analysisResult.decision_summary?.description) {
    const summaryValue = extractValueFromText(analysisResult.decision_summary.description);
    if (summaryValue !== null && summaryValue > 10000) { // Probablement un salaire si > 10k
      return summaryValue;
    }
  }

  return null;
}

/**
 * Extrait les charges sociales (par défaut 42% en France)
 */
function extractChargesFromAnalysis(analysisResult: AnalysisResult): number | null {
  // Chercher dans les métriques
  if (analysisResult.key_metrics) {
    for (const [key, metric] of Object.entries(analysisResult.key_metrics)) {
      if (key.toLowerCase().includes('charge') || key.toLowerCase().includes('social')) {
        const value = extractNumericValue(metric.value);
        if (value !== null && value > 0 && value < 100) {
          return value;
        }
      }
    }
  }
  
  // Par défaut, 42% en France
  return 42;
}

/**
 * Extrait la date d'embauche depuis la question
 */
function extractStartDateFromQuestion(question: string): string | null {
  // Chercher des patterns comme "ce mois-ci", "en janvier", "le 1er février"
  const monthMatch = question.match(/(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre|jan|fév|mar|avr|mai|jun|jul|aoû|sep|oct|nov|déc)/i);
  if (monthMatch) {
    // Pour simplifier, retourner une date par défaut
    return '2024-01-01';
  }
  
  // Chercher "ce mois-ci"
  if (question.toLowerCase().includes('ce mois')) {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-01`;
  }
  
  return null;
}

/**
 * Extrait le montant d'investissement
 */
function extractInvestmentAmount(analysisResult: AnalysisResult, question: string): number | null {
  // Chercher dans la question
  const questionMatch = question.match(/(\d+[\s,.]?\d*)\s*(?:k|K)?\s*(?:€|euros?)/i);
  if (questionMatch) {
    let value = parseFloat(questionMatch[1].replace(/[\s,]/g, ''));
    if (questionMatch[0].toLowerCase().includes('k')) {
      value *= 1000;
    }
    return value;
  }

  // Chercher dans les métriques
  if (analysisResult.key_metrics) {
    for (const [key, metric] of Object.entries(analysisResult.key_metrics)) {
      if (key.toLowerCase().includes('invest') || key.toLowerCase().includes('montant') || key.toLowerCase().includes('coût')) {
        const value = extractNumericValue(metric.value);
        if (value !== null && value > 0) {
          return value;
        }
      }
    }
  }

  return null;
}

/**
 * Extrait la durée d'un investissement
 */
function extractDuration(analysisResult: AnalysisResult, question: string): number | null {
  // Chercher dans la question (ex: "60 mois", "5 ans")
  const questionMatch = question.match(/(\d+)\s*(?:mois|ans|années|année)/i);
  if (questionMatch) {
    let value = parseInt(questionMatch[1]);
    if (questionMatch[0].toLowerCase().includes('ans') || questionMatch[0].toLowerCase().includes('année')) {
      value *= 12;
    }
    return value;
  }

  return null;
}

/**
 * Extrait l'augmentation de prix
 */
function extractPriceIncrease(analysisResult: AnalysisResult, question: string): number | null {
  // Chercher dans la question (ex: "5%", "10 pourcent")
  const questionMatch = question.match(/(\d+[\s,.]?\d*)\s*%/i);
  if (questionMatch) {
    return parseFloat(questionMatch[1].replace(/,/g, '.'));
  }

  return null;
}

/**
 * Extrait le volume de vente
 */
function extractVolume(analysisResult: AnalysisResult): number | null {
  if (analysisResult.key_metrics) {
    for (const [key, metric] of Object.entries(analysisResult.key_metrics)) {
      if (key.toLowerCase().includes('volume') || key.toLowerCase().includes('vente')) {
        const value = extractNumericValue(metric.value);
        if (value !== null && value > 0) {
          return value;
        }
      }
    }
  }
  return null;
}

/**
 * Extrait la rotation de stock
 */
function extractRotation(analysisResult: AnalysisResult): number | null {
  if (analysisResult.key_metrics) {
    for (const [key, metric] of Object.entries(analysisResult.key_metrics)) {
      if (key.toLowerCase().includes('rotation')) {
        const value = extractNumericValue(metric.value);
        if (value !== null && value > 0) {
          return value;
        }
      }
    }
  }
  return null;
}

/**
 * Extrait la valeur du stock
 */
function extractStockValue(analysisResult: AnalysisResult): number | null {
  if (analysisResult.key_metrics) {
    for (const [key, metric] of Object.entries(analysisResult.key_metrics)) {
      if (key.toLowerCase().includes('stock') || key.toLowerCase().includes('inventaire')) {
        const value = extractNumericValue(metric.value);
        if (value !== null && value > 0) {
          return value;
        }
      }
    }
  }
  return null;
}

/**
 * Extrait une valeur numérique depuis une valeur de métrique
 */
function extractNumericValue(value: string | number): number | null {
  if (typeof value === 'number') {
    return value;
  }
  if (typeof value === 'string') {
    const match = value.match(/[\d,.\s]+/);
    if (match) {
      return parseFloat(match[0].replace(/[\s,]/g, ''));
    }
  }
  return null;
}

/**
 * Génère des hypothèses initiales basées sur la question
 */
function generateInitialHypothesis(query: string): HypothesisChip[] {
  const lowerQuery = query.toLowerCase();
  
  if (lowerQuery.includes('recrut') || lowerQuery.includes('embauch')) {
    return [
      { id: 'salary', label: 'Salaire brut', value: 60000, type: 'number' },
      { id: 'start-date', label: 'Date d\'embauche', value: '2024-01-01', type: 'date' },
      { id: 'charges', label: 'Charges sociales (%)', value: 42, type: 'number' },
    ];
  }
  if (lowerQuery.includes('stock') || lowerQuery.includes('inventaire')) {
    return [
      { id: 'rotation', label: 'Rotation (jours)', value: 60, type: 'number' },
      { id: 'stock-value', label: 'Valeur stock', value: 50000, type: 'number' },
    ];
  }
  if (lowerQuery.includes('invest') || lowerQuery.includes('équipement') || lowerQuery.includes('machine') || lowerQuery.includes('achat')) {
    // Extract amount from query if mentioned
    const amountMatch = lowerQuery.match(/(\d+[\s,.]?\d*)\s*(?:€|euros?|k|K)/);
    const defaultAmount = amountMatch ? parseFloat(amountMatch[1].replace(/[\s,]/g, '')) * (lowerQuery.includes('k') || lowerQuery.includes('K') ? 1000 : 1) : 80000;
    
    return [
      { id: 'amount', label: 'Montant investissement', value: defaultAmount, type: 'number' },
      { id: 'productivity_gain', label: 'Gain de productivité (%)', value: 20, type: 'number' },
      { id: 'payback_period', label: 'Période de retour (mois)', value: 24, type: 'number' },
      { id: 'maintenance_cost', label: 'Coût maintenance annuel', value: 5000, type: 'number' },
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

/**
 * Formate une clé de métrique en label lisible
 */
function formatMetricLabel(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (l) => l.toUpperCase())
    .replace(/Ca/g, 'CA')
    .replace(/Treso/g, 'Trésorerie');
}

/**
 * Extrait une valeur numérique d'un texte
 */
function extractValueFromText(text: string): number | null {
  // Chercher des montants en euros (ex: "60 000€", "60k€", "60,000€")
  const euroMatch = text.match(/(\d[\d\s,.]*)\s*(?:k|K|€|euros?)/i);
  if (euroMatch) {
    const value = parseFloat(euroMatch[1].replace(/[\s,]/g, ''));
    if (!isNaN(value)) {
      return euroMatch[1].includes('k') || euroMatch[1].includes('K') ? value * 1000 : value;
    }
  }

  // Chercher des pourcentages
  const percentMatch = text.match(/(\d[\d,.]*)\s*%/);
  if (percentMatch) {
    const value = parseFloat(percentMatch[1].replace(/,/g, '.'));
    if (!isNaN(value)) {
      return value;
    }
  }

  // Chercher des nombres simples
  const numberMatch = text.match(/(\d[\d\s,.]*)/);
  if (numberMatch) {
    const value = parseFloat(numberMatch[1].replace(/[\s,]/g, ''));
    if (!isNaN(value) && value > 0) {
      return value;
    }
  }

  return null;
}

