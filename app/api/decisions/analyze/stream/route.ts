import { NextRequest, NextResponse } from 'next/server';
import { requireAuth } from '@/lib/supabase/auth-helpers';
import { createClient } from '@/lib/supabase/server';

const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  console.log('[API] /api/decisions/analyze/stream called');
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

    // Define initial steps
    const initialSteps = [
      {
        name: 'analyzing_question',
        label: 'Analyse de la question',
        status: 'pending' as const,
      },
      {
        name: 'checking_files',
        label: 'Vérification des fichiers disponibles',
        status: 'pending' as const,
      },
      {
        name: 'analyzing_structure',
        label: 'Analyse de la structure des données',
        status: 'pending' as const,
      },
      {
        name: 'calculating_metrics',
        label: 'Calcul des métriques clés',
        status: 'pending' as const,
      },
      {
        name: 'generating_scenarios',
        label: 'Génération des scénarios',
        status: 'pending' as const,
      },
      {
        name: 'creating_recommendations',
        label: 'Création des recommandations',
        status: 'pending' as const,
      },
    ];

    // Create analysis with pending status
    console.log(`[API] Creating analysis for user ${user.id}, project ${project_id}, question: ${question.substring(0, 50)}...`);
    const { data: savedAnalysis, error: saveError } = await supabase
      .from('analyses')
      .insert({
        user_id: user.id,
        project_id: project_id,
        question,
        file_ids: file_ids || [],
        status: 'pending',
        current_step: 'analyzing_question',
        progress: 0,
        steps: initialSteps,
        missing_data: [],
        partial_result: {},
        result: {},
      })
      .select()
      .single();

    if (saveError) {
      console.error('[API] Error creating analysis:', saveError);
      return NextResponse.json(
        { error: 'Failed to create analysis', details: saveError.message },
        { status: 500 }
      );
    }

    console.log(`[API] Analysis created with ID ${savedAnalysis.id}`);

    // Launch analysis asynchronously (don't await)
    // The backend will update the status in the database as it progresses
    launchAnalysisAsync(savedAnalysis.id, question, file_ids || []).catch(async (error) => {
      console.error(`[API] Error launching analysis ${savedAnalysis.id}:`, error);
      // Update analysis status to error
      try {
        await supabase
          .from('analyses')
          .update({
            status: 'error',
            progress: 0,
          })
          .eq('id', savedAnalysis.id);
      } catch (updateError) {
        console.error('[API] Error updating analysis status to error:', updateError);
      }
    });

    // Return immediately with analysis ID
    return NextResponse.json({
      analysis_id: savedAnalysis.id,
      status: 'pending',
      current_step: 'analyzing_question',
      progress: 0,
      steps: initialSteps,
    });
  } catch (error) {
    console.error('[API] Error in stream endpoint:', error);
    return NextResponse.json(
      { error: 'Failed to start analysis', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

// Async function to download files from Supabase Storage
async function downloadFilesForBackend(fileIds: string[], supabaseClient: any) {
  if (!fileIds || fileIds.length === 0) {
    return [];
  }

  // Get file records
  const { data: files, error } = await supabaseClient
    .from('files')
    .select('id, storage_path, original_name, file_type')
    .in('id', fileIds);

  if (error || !files) {
    console.error('[API] Error fetching file records:', error);
    return [];
  }

  // Download files and convert to base64
  const filesData = [];
  for (const file of files) {
    const { data: fileData, error: downloadError } = await supabaseClient.storage
      .from('files')
      .download(file.storage_path);

    if (downloadError || !fileData) {
      console.error(`[API] Error downloading file ${file.id}:`, downloadError);
      continue;
    }

    const arrayBuffer = await fileData.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    const base64 = buffer.toString('base64');

    filesData.push({
      file_id: file.id,
      original_name: file.original_name,
      file_type: file.file_type,
      content_base64: base64,
      mime_type: fileData.type || 'application/octet-stream',
    });
  }

  return filesData;
}

// Helper function to update analysis status
async function updateAnalysisStatus(
  analysisId: string,
  supabaseClient: any,
  updates: {
    status?: string;
    current_step?: string;
    progress?: number;
    steps?: any[];
    message?: string;
  }
) {
  const { error } = await supabaseClient
    .from('analyses')
    .update(updates)
    .eq('id', analysisId);
  
  if (error) {
    console.error(`[API] Error updating analysis status:`, error);
  }
}

// Async function to launch analysis (runs in background)
async function launchAnalysisAsync(analysisId: string, question: string, fileIds: string[]) {
  console.log(`[API] Launching async analysis for ${analysisId}`);
  
  const supabaseClient = await createClient();
  
  // Define detailed steps
  const steps = [
    {
      name: 'analyzing_question',
      label: 'Analyse de la question',
      status: 'in_progress' as const,
      message: 'Analyse de la question et extraction des paramètres clés...',
    },
    {
      name: 'checking_files',
      label: 'Vérification des fichiers disponibles',
      status: 'pending' as const,
      message: '',
    },
    {
      name: 'analyzing_structure',
      label: 'Analyse de la structure des données',
      status: 'pending' as const,
      message: '',
    },
    {
      name: 'calculating_metrics',
      label: 'Calcul des métriques clés',
      status: 'pending' as const,
      message: '',
    },
    {
      name: 'generating_scenarios',
      label: 'Génération des scénarios',
      status: 'pending' as const,
      message: '',
    },
    {
      name: 'creating_recommendations',
      label: 'Création des recommandations',
      status: 'pending' as const,
      message: '',
    },
  ];

  // Update status to in_progress with initial steps
  await updateAnalysisStatus(analysisId, supabaseClient, {
    status: 'in_progress',
    current_step: 'analyzing_question',
    progress: 5,
    steps,
  });

  try {
    // Step 1: Download files
    await updateAnalysisStatus(analysisId, supabaseClient, {
      current_step: 'checking_files',
      progress: 10,
      steps: steps.map((s, i) => ({
        ...s,
        status: i === 1 ? 'in_progress' : i < 1 ? 'completed' : 'pending',
        message: i === 1 ? 'Téléchargement et vérification des fichiers...' : s.message,
      })),
    });

    const filesData = await downloadFilesForBackend(fileIds, supabaseClient);
    console.log(`[API] Downloaded ${filesData.length} files for analysis ${analysisId}`);

    // Step 2: Analyze structure
    await updateAnalysisStatus(analysisId, supabaseClient, {
      current_step: 'analyzing_structure',
      progress: 20,
      steps: steps.map((s, i) => ({
        ...s,
        status: i === 2 ? 'in_progress' : i < 2 ? 'completed' : 'pending',
        message: i === 2 ? 'Analyse de la structure des données et adaptation...' : s.message,
      })),
    });

    // Call Python backend with analysis ID and file data
    const response = await fetch(`${PYTHON_BACKEND_URL}/api/decisions/analyze/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question,
        file_ids: fileIds.length > 0 ? fileIds : undefined,
        files_data: filesData.length > 0 ? filesData : undefined, // Send file content directly
        analysis_id: analysisId,
        update_status_url: `${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'}/api/decisions/analyze/${analysisId}/update-status`,
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

    // Update analysis with final result - mark all steps as completed
    await updateAnalysisStatus(analysisId, supabaseClient, {
      status: 'completed',
      current_step: 'creating_recommendations',
      progress: 100,
      steps: steps.map((s) => ({
        ...s,
        status: 'completed' as const,
        message: s.message || 'Terminé',
      })),
    });

    // Save final result
    await supabaseClient
      .from('analyses')
      .update({
        result: result,
      })
      .eq('id', analysisId);

    console.log(`[API] Analysis ${analysisId} saved successfully`);
  } catch (error) {
    console.error(`[API] Error in async analysis ${analysisId}:`, error);
    
    // Update analysis status to error
    await supabaseClient
      .from('analyses')
      .update({
        status: 'error',
        progress: 0,
      })
      .eq('id', analysisId);
    
    throw error;
  }
}

