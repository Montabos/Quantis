import { NextRequest, NextResponse } from 'next/server';
import { requireAuth } from '@/lib/supabase/auth-helpers';
import { createClient } from '@/lib/supabase/server';

const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000';

/**
 * API endpoint pour le chat contextuel sur une analyse existante
 * Permet de poser des questions sur l'analyse actuelle et de mettre à jour les hypothèses
 */
export async function POST(request: NextRequest) {
  console.log('[API] /api/decisions/chat called');
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
      message, 
      chat_history, 
      hypotheses,
      should_update_hypotheses 
    } = body;

    console.log('[API] Chat request:', { 
      analysis_id, 
      message: message?.substring(0, 50),
      has_chat_history: !!chat_history,
      has_hypotheses: !!hypotheses,
      should_update_hypotheses 
    });

    if (!analysis_id || typeof analysis_id !== 'string') {
      return NextResponse.json(
        { error: 'Analysis ID is required' },
        { status: 400 }
      );
    }

    if (!message || typeof message !== 'string') {
      return NextResponse.json(
        { error: 'Message is required' },
        { status: 400 }
      );
    }

    // Get analysis to verify ownership and get context
    const { data: analysis, error: analysisError } = await supabase
      .from('analyses')
      .select('id, question, file_ids, project_id, user_id, result')
      .eq('id', analysis_id)
      .eq('user_id', user.id)
      .single();

    if (analysisError || !analysis) {
      console.error(`[API] Error fetching analysis ${analysis_id}:`, analysisError);
      return NextResponse.json(
        { error: 'Analysis not found or access denied' },
        { status: 404 }
      );
    }

    // Call Python backend for contextual chat
    try {
      const response = await fetch(`${PYTHON_BACKEND_URL}/api/decisions/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          analysis_id: analysis.id,
          question: analysis.question,
          message: message,
          analysis_result: analysis.result || {},
          chat_history: chat_history || [],
          hypotheses: hypotheses || [],
          should_update_hypotheses: should_update_hypotheses || false,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`[API] Python backend chat error:`, errorText);
        throw new Error(`Backend chat failed: ${errorText}`);
      }

      const chatResponse = await response.json();
      console.log('[API] Chat response received:', {
        has_response: !!chatResponse.response,
        updated_hypotheses: !!chatResponse.updated_hypotheses,
      });

      return NextResponse.json({
        response: chatResponse.response || 'Je n\'ai pas pu générer de réponse.',
        updated_hypotheses: chatResponse.updated_hypotheses || null,
        should_relaunch_analysis: chatResponse.should_relaunch_analysis || false,
      });
    } catch (error) {
      console.error('[API] Error calling Python backend for chat:', error);
      return NextResponse.json(
        { 
          error: 'Failed to get chat response',
          details: error instanceof Error ? error.message : 'Unknown error'
        },
        { status: 500 }
      );
    }
  } catch (error) {
    console.error('[API] Error in chat endpoint:', error);
    return NextResponse.json(
      { 
        error: 'Internal server error',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

