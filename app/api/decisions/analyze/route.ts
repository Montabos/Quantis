import { NextRequest, NextResponse } from 'next/server';
import { requireAuth } from '@/lib/supabase/auth-helpers';
import { createClient } from '@/lib/supabase/server';

const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  console.log('[API] /api/decisions/analyze called');
  try {
    // Check authentication
    const user = await requireAuth();
    if (user instanceof NextResponse) {
      console.error('[API] Authentication failed');
      return user; // Return error response
    }
    console.log('[API] User authenticated:', user.id);

    const supabase = await createClient();
    const body = await request.json();
    const { question, file_ids, project_id } = body;

    console.log('[API] Request body:', { question: question?.substring(0, 50), file_ids, project_id });

    if (!question || typeof question !== 'string') {
      console.error('[API] Question is missing or invalid');
      return NextResponse.json(
        { error: 'Question is required' },
        { status: 400 }
      );
    }

    if (!project_id) {
      console.error('[API] Project ID is missing');
      return NextResponse.json(
        { error: 'Project ID is required' },
        { status: 400 }
      );
    }

    // Verify project ownership
    const { data: project, error: projectError } = await supabase
      .from('projects')
      .select('id')
      .eq('id', project_id)
      .eq('user_id', user.id)
      .single();

    if (projectError || !project) {
      return NextResponse.json(
        { error: 'Project not found or access denied' },
        { status: 403 }
      );
    }

    // Verify file ownership and project association if file_ids provided
    if (file_ids && Array.isArray(file_ids) && file_ids.length > 0) {
      const { data: files, error: filesError } = await supabase
        .from('files')
        .select('id')
        .eq('user_id', user.id)
        .eq('project_id', project_id)
        .in('id', file_ids);

      if (filesError || !files || files.length !== file_ids.length) {
        return NextResponse.json(
          { error: 'Some files not found, access denied, or files belong to different project' },
          { status: 403 }
        );
      }
    }

    // Call Python backend
    console.log(`[API] Calling Python backend at ${PYTHON_BACKEND_URL}/api/decisions/analyze`);
    const response = await fetch(`${PYTHON_BACKEND_URL}/api/decisions/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question,
        file_ids: file_ids || undefined,
      }),
    });

    console.log(`[API] Python backend response status: ${response.status}`);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[API] Python backend error:', errorText);
      return NextResponse.json(
        { error: 'Analysis failed', details: errorText },
        { status: response.status }
      );
    }

    const result = await response.json();
    console.log('[API] Python backend returned result, saving to database...');

    // Save analysis to database
    console.log(`[API] Saving analysis for user ${user.id}, project ${project_id}, question: ${question.substring(0, 50)}...`);
    const { data: savedAnalysis, error: saveError } = await supabase
      .from('analyses')
      .insert({
        user_id: user.id,
        project_id: project_id,
        question,
        file_ids: file_ids || [],
        result: result,
      })
      .select()
      .single();

    if (saveError) {
      console.error('[API] Error saving analysis:', saveError);
      console.error('[API] Error details:', JSON.stringify(saveError, null, 2));
      // Still return the result even if save failed
      return NextResponse.json(result);
    }

    console.log(`[API] Analysis saved with ID ${savedAnalysis.id} for project ${project_id}`);
    console.log(`[API] Saved analysis project_id: ${savedAnalysis.project_id}`);

    // Return result with analysis ID for tab synchronization
    return NextResponse.json({
      ...result,
      analysis_id: savedAnalysis.id,
    });
  } catch (error) {
    console.error('Error calling Python backend:', error);
    return NextResponse.json(
      { error: 'Failed to analyze decision', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}




