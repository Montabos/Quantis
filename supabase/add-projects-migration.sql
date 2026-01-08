-- Migration pour ajouter le système de projets
-- À exécuter si vous avez déjà créé les autres tables

-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add project_id column to files table if it doesn't exist
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'files' AND column_name = 'project_id'
  ) THEN
    ALTER TABLE files ADD COLUMN project_id UUID REFERENCES projects(id) ON DELETE CASCADE;
  END IF;
END $$;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_files_project_id ON files(project_id);

-- Enable Row Level Security
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- RLS Policies for projects
DROP POLICY IF EXISTS "Users can view their own projects" ON projects;
CREATE POLICY "Users can view their own projects"
  ON projects FOR SELECT
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own projects" ON projects;
CREATE POLICY "Users can insert their own projects"
  ON projects FOR INSERT
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own projects" ON projects;
CREATE POLICY "Users can update their own projects"
  ON projects FOR UPDATE
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own projects" ON projects;
CREATE POLICY "Users can delete their own projects"
  ON projects FOR DELETE
  USING (auth.uid() = user_id);

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

-- Make project_id NOT NULL in files (after ensuring all files have a project)
-- Note: You may need to assign existing files to a project first
-- ALTER TABLE files ALTER COLUMN project_id SET NOT NULL;

-- Make project_id NOT NULL in analyses (after ensuring all analyses have a project)
-- Note: You may need to assign existing analyses to a project first
-- ALTER TABLE analyses ALTER COLUMN project_id SET NOT NULL;

-- Create index for analyses project_id
CREATE INDEX IF NOT EXISTS idx_analyses_project_id ON analyses(project_id);

-- Trigger to update updated_at
DROP TRIGGER IF EXISTS update_projects_updated_at ON projects;
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

