-- Migration pour rendre project_id obligatoire dans files et analyses
-- À exécuter si vous avez déjà créé les tables

-- First, delete files and analyses without project_id (orphaned data)
DELETE FROM files WHERE project_id IS NULL;
DELETE FROM analyses WHERE project_id IS NULL;

-- Add project_id to analyses if it doesn't exist
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'analyses' AND column_name = 'project_id'
  ) THEN
    ALTER TABLE analyses ADD COLUMN project_id UUID REFERENCES projects(id) ON DELETE CASCADE;
  END IF;
END $$;

-- Make project_id NOT NULL in files
ALTER TABLE files ALTER COLUMN project_id SET NOT NULL;

-- Make project_id NOT NULL in analyses
ALTER TABLE analyses ALTER COLUMN project_id SET NOT NULL;

-- Update foreign key constraint to CASCADE delete
ALTER TABLE files DROP CONSTRAINT IF EXISTS files_project_id_fkey;
ALTER TABLE files ADD CONSTRAINT files_project_id_fkey 
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;

-- Update foreign key constraint to CASCADE delete for analyses
ALTER TABLE analyses DROP CONSTRAINT IF EXISTS analyses_project_id_fkey;
ALTER TABLE analyses ADD CONSTRAINT analyses_project_id_fkey 
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;

-- Create index if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_analyses_project_id ON analyses(project_id);

