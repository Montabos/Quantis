import { NextRequest, NextResponse } from 'next/server';
import { requireAuth } from '@/lib/supabase/auth-helpers';
import { createClient } from '@/lib/supabase/server';

const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000';

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  console.log(`[API] /api/decisions/analyze/${params.id}/continue called`);
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
    const body = await request.json();
    const { missing_data } = body;

    // Get analysis to verify ownership and get question/file_ids
    const { data: analysis, error: analysisError } = await supabase
      .from('analyses')
      .select('id, question, file_ids, project_id, user_id')
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

    // Update analysis with provided data and set status back to in_progress
    const { error: updateError } = await supabase
      .from('analyses')
      .update({
        status: 'in_progress',
        missing_data: [], // Clear missing data since we're providing it
        progress: 20, // Reset progress
        current_step: 'analyzing_structure',
      })
      .eq('id', analysisId);

    if (updateError) {
      console.error(`[API] Error updating analysis ${analysisId}:`, updateError);
      return NextResponse.json(
        { error: 'Failed to update analysis' },
        { status: 500 }
      );
    }

    // Relaunch analysis with the provided data
    // The backend will use the missing_data in the analysis context
    launchAnalysisAsync(analysisId, analysis.question, analysis.file_ids || [], missing_data).catch(async (error) => {
      console.error(`[API] Error relaunching analysis ${analysisId}:`, error);
      // Update analysis status to error
      try {
        await supabase
          .from('analyses')
          .update({
            status: 'error',
            progress: 0,
          })
          .eq('id', analysisId);
      } catch (updateError) {
        console.error('[API] Error updating analysis status to error:', updateError);
      }
    });

    return NextResponse.json({
      success: true,
      analysis_id: analysisId,
      status: 'in_progress',
    });
  } catch (error) {
    console.error(`[API] Error in continue endpoint:`, error);
    return NextResponse.json(
      { error: 'Failed to continue analysis', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

// Async function to relaunch analysis with provided data
async function launchAnalysisAsync(
  analysisId: string,
  question: string,
  fileIds: string[],
  providedData: Record<string, any>
) {
  console.log(`[API] Relaunching async analysis for ${analysisId} with provided data`);
  
  const supabaseClient = await createClient();
  
  // Update status to in_progress
  await supabaseClient
    .from('analyses')
    .update({
      status: 'in_progress',
      current_step: 'analyzing_structure',
      progress: 20,
    })
    .eq('id', analysisId);

  try {
    // Call Python backend with analysis ID and provided data
    const response = await fetch(`${PYTHON_BACKEND_URL}/api/decisions/analyze/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question,
        file_ids: fileIds.length > 0 ? fileIds : undefined,
        analysis_id: analysisId,
        provided_data: providedData, // Pass provided data to backend
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[API] Python backend error for ${analysisId}:`, errorText);
      
      // Update analysis status to error
      await supabaseClient
        .from('analyses')
        .update({
          status: 'error',
          progress: 0,
        })
        .eq('id', analysisId);
      
      throw new Error(`Backend analysis failed: ${errorText}`);
    }

    const result = await response.json();
    console.log(`[API] Analysis ${analysisId} completed, saving result...`);

    // Update analysis with final result
    await supabaseClient
      .from('analyses')
      .update({
        status: 'completed',
        current_step: 'creating_recommendations',
        progress: 100,
        result: result,
      })
      .eq('id', analysisId);

    console.log(`[API] Analysis ${analysisId} saved successfully`);
  } catch (error) {
    console.error(`[API] Error in async analysis ${analysisId}:`, error);
    
    // Update analysis status to error
    await supabase
      .from('analyses')
      .update({
        status: 'error',
        progress: 0,
      })
      .eq('id', analysisId);
    
    throw error;
  }
}

