import { NextRequest, NextResponse } from 'next/server';
import { requireAuth } from '@/lib/supabase/auth-helpers';
import { createClient } from '@/lib/supabase/server';

const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000';

/**
 * API endpoint pour générer des hypothèses intelligentes avec Gemini
 */
export async function POST(request: NextRequest) {
  console.log('[API] /api/decisions/generate-hypotheses called');
  try {
    // Check authentication
    const user = await requireAuth();
    if (user instanceof NextResponse) {
      console.error('[API] Authentication failed');
      return user;
    }

    const supabase = await createClient();
    const body = await request.json();
    const { 
      analysis_id,
      question,
    } = body;

    console.log('[API] Generate hypotheses request:', { 
      analysis_id,
      question: question?.substring(0, 50),
    });

    if (!question || typeof question !== 'string') {
      return NextResponse.json(
        { error: 'Question is required' },
        { status: 400 }
      );
    }

    // Get analysis result if analysis_id is provided
    let analysisResult = null;
    if (analysis_id) {
      const { data: analysis, error: analysisError } = await supabase
        .from('analyses')
        .select('id, question, result')
        .eq('id', analysis_id)
        .eq('user_id', user.id)
        .single();

      if (!analysisError && analysis) {
        analysisResult = analysis.result || {};
      }
    }

    // Call Python backend to generate hypotheses with Gemini
    try {
      const response = await fetch(`${PYTHON_BACKEND_URL}/api/decisions/generate-hypotheses`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: question,
          analysis_result: analysisResult,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`[API] Python backend generate-hypotheses error:`, errorText);
        throw new Error(`Backend failed: ${errorText}`);
      }

      const hypothesesResponse = await response.json();
      console.log('[API] Hypotheses generated:', {
        count: hypothesesResponse.hypotheses?.length || 0,
      });

      return NextResponse.json({
        hypotheses: hypothesesResponse.hypotheses || [],
      });
    } catch (error) {
      console.error('[API] Error calling Python backend for hypotheses:', error);
      return NextResponse.json(
        { 
          error: 'Failed to generate hypotheses',
          details: error instanceof Error ? error.message : 'Unknown error'
        },
        { status: 500 }
      );
    }
  } catch (error) {
    console.error('[API] Error in generate-hypotheses endpoint:', error);
    return NextResponse.json(
      { 
        error: 'Internal server error',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

