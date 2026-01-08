import { NextRequest, NextResponse } from 'next/server';
import { requireAuth } from '@/lib/supabase/auth-helpers';
import { createClient } from '@/lib/supabase/server';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  console.log(`[API] /api/decisions/analyze/${params.id}/status called`);
  try {
    // Check authentication
    const user = await requireAuth();
    if (user instanceof NextResponse) {
      console.error('[API] Authentication failed');
      return user; // Return error response
    }

    const analysisId = params.id;
    if (!analysisId) {
      return NextResponse.json(
        { error: 'Analysis ID is required' },
        { status: 400 }
      );
    }

    const supabase = await createClient();

    // Get analysis status
    const { data: analysis, error: analysisError } = await supabase
      .from('analyses')
      .select('id, status, current_step, progress, steps, missing_data, partial_result, result, question')
      .eq('id', analysisId)
      .eq('user_id', user.id)
      .single();

    if (analysisError || !analysis) {
      console.error(`[API] Error fetching analysis ${analysisId}:`, analysisError);
      return NextResponse.json(
        { error: 'Analysis not found or access denied' },
        { status: 404 }
      );
    }

    // Format response
    const response = {
      analysis_id: analysis.id,
      status: analysis.status || 'pending',
      current_step: analysis.current_step || null,
      progress: analysis.progress || 0,
      steps: analysis.steps || [],
      missing_data: analysis.missing_data || [],
      partial_result: analysis.partial_result || null,
      result: analysis.status === 'completed' ? analysis.result : null,
      question: analysis.question,
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error(`[API] Error in status endpoint:`, error);
    return NextResponse.json(
      { error: 'Failed to get analysis status', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

