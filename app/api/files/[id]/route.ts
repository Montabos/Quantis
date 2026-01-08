import { NextRequest, NextResponse } from 'next/server';
import { requireAuth } from '@/lib/supabase/auth-helpers';
import { createClient } from '@/lib/supabase/server';

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    // Check authentication
    const user = await requireAuth();
    if (user instanceof NextResponse) {
      return user; // Return error response
    }

    const supabase = await createClient();
    const fileId = params.id;

    // Get file record to verify ownership and get storage path
    const { data: fileRecord, error: fetchError } = await supabase
      .from('files')
      .select('storage_path')
      .eq('id', fileId)
      .eq('user_id', user.id)
      .single();

    if (fetchError || !fileRecord) {
      return NextResponse.json(
        { error: 'File not found' },
        { status: 404 }
      );
    }

    // Delete from storage
    const { error: storageError } = await supabase.storage
      .from('files')
      .remove([fileRecord.storage_path]);

    if (storageError) {
      console.error('Storage deletion error:', storageError);
      // Continue with DB deletion even if storage deletion fails
    }

    // Delete from database
    const { error: dbError } = await supabase
      .from('files')
      .delete()
      .eq('id', fileId)
      .eq('user_id', user.id);

    if (dbError) {
      console.error('Database deletion error:', dbError);
      return NextResponse.json(
        { error: 'Failed to delete file from database' },
        { status: 500 }
      );
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error deleting file:', error);
    return NextResponse.json(
      { error: 'Failed to delete file' },
      { status: 500 }
    );
  }
}




