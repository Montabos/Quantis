import { NextRequest, NextResponse } from 'next/server';
import { requireAuth } from '@/lib/supabase/auth-helpers';
import { createClient } from '@/lib/supabase/server';

/**
 * API endpoint pour mettre à jour le statut d'une analyse en cours
 * Appelé par le backend Python pour mettre à jour les étapes en temps réel
 */
export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    // Check authentication
    const user = await requireAuth();
    if (user instanceof NextResponse) {
      return user;
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
    const { 
      status, 
      current_step, 
      progress, 
      steps, 
      message,
      missing_data 
    } = body;

    // Build update object
    const updateData: any = {};
    if (status !== undefined) updateData.status = status;
    if (current_step !== undefined) updateData.current_step = current_step;
    if (progress !== undefined) updateData.progress = progress;
    if (steps !== undefined) updateData.steps = steps;
    if (missing_data !== undefined) updateData.missing_data = missing_data;

    // Update analysis
    const { error: updateError } = await supabase
      .from('analyses')
      .update(updateData)
      .eq('id', analysisId)
      .eq('user_id', user.id); // Ensure user owns this analysis

    if (updateError) {
      console.error(`[API] Error updating analysis ${analysisId}:`, updateError);
      return NextResponse.json(
        { error: 'Failed to update analysis status', details: updateError.message },
        { status: 500 }
      );
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error(`[API] Error in update-status endpoint:`, error);
    return NextResponse.json(
      { error: 'Failed to update analysis status', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

