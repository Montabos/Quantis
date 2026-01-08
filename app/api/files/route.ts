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

    const { data, error } = await supabase
      .from('files')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false });

    if (error) {
      console.error('Error fetching files:', error);
      return NextResponse.json(
        { error: 'Failed to fetch files' },
        { status: 500 }
      );
    }

    return NextResponse.json({ files: data || [] });
  } catch (error) {
    console.error('Error in GET /api/files:', error);
    return NextResponse.json(
      { error: 'Failed to fetch files' },
      { status: 500 }
    );
  }
}

