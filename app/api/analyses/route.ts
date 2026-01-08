import { NextRequest, NextResponse } from 'next/server';
import { requireAuth } from '@/lib/supabase/auth-helpers';
import { createClient } from '@/lib/supabase/server';

export async function GET(request: NextRequest) {
  try {
    // Check authentication
    const user = await requireAuth();
    if (user instanceof NextResponse) {
      return user; // Return error response
    }

    const supabase = await createClient();
    const { searchParams } = new URL(request.url);
    const projectId = searchParams.get('project_id');

    if (!projectId) {
      return NextResponse.json(
        { error: 'Project ID is required' },
        { status: 400 }
      );
    }

    // Verify project ownership
    const { data: project, error: projectError } = await supabase
      .from('projects')
      .select('id')
      .eq('id', projectId)
      .eq('user_id', user.id)
      .single();

    if (projectError || !project) {
      return NextResponse.json(
        { error: 'Project not found or access denied' },
        { status: 403 }
      );
    }

    // Get analyses for this project
    const { data, error } = await supabase
      .from('analyses')
      .select('*')
      .eq('user_id', user.id)
      .eq('project_id', projectId)
      .order('created_at', { ascending: false });

    if (error) {
      console.error('Error fetching analyses:', error);
      return NextResponse.json(
        { error: 'Failed to fetch analyses' },
        { status: 500 }
      );
    }

    return NextResponse.json({ analyses: data || [] });
  } catch (error) {
    console.error('Error in GET /api/analyses:', error);
    return NextResponse.json(
      { error: 'Failed to fetch analyses' },
      { status: 500 }
    );
  }
}

