import { NextRequest, NextResponse } from 'next/server';
import { requireAuth } from '@/lib/supabase/auth-helpers';
import { createClient } from '@/lib/supabase/server';

export async function POST(request: NextRequest) {
  try {
    // Check authentication
    const user = await requireAuth();
    if (user instanceof NextResponse) {
      return user; // Return error response
    }

    const supabase = await createClient();
    const body = await request.json();
    const { file_ids } = body;

    if (!file_ids || !Array.isArray(file_ids) || file_ids.length === 0) {
      return NextResponse.json(
        { error: 'file_ids array is required' },
        { status: 400 }
      );
    }

    // Get file records from database
    const { data: files, error: filesError } = await supabase
      .from('files')
      .select('id, storage_path, original_name, file_type')
      .eq('user_id', user.id)
      .in('id', file_ids);

    if (filesError || !files || files.length !== file_ids.length) {
      return NextResponse.json(
        { error: 'Some files not found or access denied' },
        { status: 403 }
      );
    }

    // Download files from Supabase Storage and create signed URLs
    const filesData = await Promise.all(
      files.map(async (file) => {
        // Create signed URL (valid for 1 hour)
        const { data: signedUrlData, error: urlError } = await supabase.storage
          .from('files')
          .createSignedUrl(file.storage_path, 3600); // 1 hour expiry

        if (urlError || !signedUrlData) {
          console.error(`Error creating signed URL for ${file.id}:`, urlError);
          return null;
        }

        // Download file content
        const { data: fileData, error: downloadError } = await supabase.storage
          .from('files')
          .download(file.storage_path);

        if (downloadError || !fileData) {
          console.error(`Error downloading file ${file.id}:`, downloadError);
          return null;
        }

        // Convert blob to base64 for transmission
        const arrayBuffer = await fileData.arrayBuffer();
        const buffer = Buffer.from(arrayBuffer);
        const base64 = buffer.toString('base64');

        return {
          file_id: file.id,
          original_name: file.original_name,
          file_type: file.file_type,
          storage_path: file.storage_path,
          signed_url: signedUrlData.signedUrl,
          content_base64: base64,
          mime_type: fileData.type || 'application/octet-stream',
        };
      })
    );

    // Filter out null values (failed downloads)
    const successfulFiles = filesData.filter((f) => f !== null);

    if (successfulFiles.length === 0) {
      return NextResponse.json(
        { error: 'Failed to download any files' },
        { status: 500 }
      );
    }

    return NextResponse.json({
      files: successfulFiles,
    });
  } catch (error) {
    console.error('Error in download endpoint:', error);
    return NextResponse.json(
      { error: 'Failed to download files', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

