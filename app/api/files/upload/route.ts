import { NextRequest, NextResponse } from 'next/server';
import { requireAuth } from '@/lib/supabase/auth-helpers';
import { createClient } from '@/lib/supabase/server';

// Configuration
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

export async function POST(request: NextRequest) {
  try {
    // Check authentication
    const user = await requireAuth();
    if (user instanceof NextResponse) {
      return user; // Return error response
    }

    const supabase = await createClient();
    const formData = await request.formData();
    const file = formData.get('file') as File;

    if (!file) {
      return NextResponse.json(
        { error: 'No file provided' },
        { status: 400 }
      );
    }

    // Validate file type
    const fileName = file.name.toLowerCase();
    const isValidType =
      fileName.endsWith('.xlsx') ||
      fileName.endsWith('.xls') ||
      fileName.endsWith('.csv');

    if (!isValidType) {
      return NextResponse.json(
        { error: 'Invalid file type. Only .xlsx, .xls, and .csv files are allowed.' },
        { status: 400 }
      );
    }

    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
      return NextResponse.json(
        { error: `File too large. Maximum size is ${MAX_FILE_SIZE / 1024 / 1024}MB` },
        { status: 400 }
      );
    }

    // Generate unique filename
    const timestamp = Date.now();
    const randomStr = Math.random().toString(36).substring(2, 15);
    const fileExtension = fileName.substring(fileName.lastIndexOf('.'));
    const uniqueFileName = `${user.id}/${timestamp}-${randomStr}${fileExtension}`;

    // Upload to Supabase Storage
    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);
    
    const { error: uploadError } = await supabase.storage
      .from('files')
      .upload(uniqueFileName, buffer, {
        contentType: file.type,
        upsert: false,
      });

    if (uploadError) {
      console.error('Supabase storage error:', uploadError);
      return NextResponse.json(
        { error: 'Failed to upload file to storage' },
        { status: 500 }
      );
    }

    // Call Python backend to process file and extract metadata
    const pythonBackendUrl = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000';
    
    let metadata = {
      numRows: 0,
      numColumns: 0,
      columns: [] as string[],
      fileType: undefined as string | undefined,
      detectedDocumentType: undefined as string | undefined,
    };

    try {
      // Create FormData for Python backend
      const pythonFormData = new FormData();
      const blob = new Blob([buffer], { type: file.type });
      pythonFormData.append('file', blob, file.name);

      const pythonResponse = await fetch(`${pythonBackendUrl}/api/files/process`, {
        method: 'POST',
        body: pythonFormData,
        signal: AbortSignal.timeout(10000), // 10 secondes timeout
      });

      if (pythonResponse.ok) {
        const pythonResult = await pythonResponse.json();
        metadata = {
          numRows: pythonResult.num_rows || 0,
          numColumns: pythonResult.num_columns || 0,
          columns: pythonResult.columns || [],
          fileType: pythonResult.file_type,
          detectedDocumentType: pythonResult.detected_document_type,
        };
      }
    } catch (pythonError: any) {
      // Backend Python non disponible - ce n'est pas critique pour l'upload
      // Les métadonnées seront vides mais le fichier sera quand même sauvegardé
      if (pythonError.code !== 'ECONNREFUSED') {
        console.warn('Python backend unavailable or error:', pythonError.message || pythonError);
      }
      // Continue avec metadata vide - le fichier sera quand même sauvegardé
    }

    // Get project_id from request if provided
    const projectId = formData.get('project_id') as string | null;

    // Save file metadata to database
    const fileType = fileName.endsWith('.csv') ? 'csv' : 'excel';
    const { data: fileRecord, error: dbError } = await supabase
      .from('files')
      .insert({
        user_id: user.id,
        project_id: projectId || null,
        name: uniqueFileName,
        original_name: file.name,
        file_type: fileType,
        size: file.size,
        storage_path: uniqueFileName,
        metadata: metadata,
        status: 'ready',
      })
      .select()
      .single();

    if (dbError) {
      console.error('Database error:', dbError);
      // Try to delete from storage if DB insert fails
      await supabase.storage.from('files').remove([uniqueFileName]);
      return NextResponse.json(
        { error: 'Failed to save file metadata' },
        { status: 500 }
      );
    }

    return NextResponse.json({
      fileId: fileRecord.id,
      fileName: file.name,
      size: file.size,
      metadata: metadata,
    });
  } catch (error) {
    console.error('Error uploading file:', error);
    return NextResponse.json(
      { error: 'Failed to upload file' },
      { status: 500 }
    );
  }
}




