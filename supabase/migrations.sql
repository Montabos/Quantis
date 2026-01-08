-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create files table
CREATE TABLE IF NOT EXISTS files (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  original_name TEXT NOT NULL,
  file_type TEXT NOT NULL CHECK (file_type IN ('excel', 'csv')),
  size BIGINT NOT NULL,
  storage_path TEXT NOT NULL,
  metadata JSONB DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'ready' CHECK (status IN ('uploading', 'processing', 'ready', 'error')),
  error TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create profiles table
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  first_name TEXT,
  last_name TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create analyses table
CREATE TABLE IF NOT EXISTS analyses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  question TEXT NOT NULL,
  file_ids UUID[] DEFAULT ARRAY[]::UUID[],
  result JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_files_user_id ON files(user_id);
CREATE INDEX IF NOT EXISTS idx_files_project_id ON files(project_id);
CREATE INDEX IF NOT EXISTS idx_files_created_at ON files(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analyses_user_id ON analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_analyses_project_id ON analyses(project_id);
CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at DESC);

-- Enable Row Level Security
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE files ENABLE ROW LEVEL SECURITY;
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;

-- RLS Policies for profiles
CREATE POLICY "Users can view their own profile"
  ON profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
  ON profiles FOR UPDATE
  USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile"
  ON profiles FOR INSERT
  WITH CHECK (auth.uid() = id);

-- RLS Policies for projects
CREATE POLICY "Users can view their own projects"
  ON projects FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own projects"
  ON projects FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own projects"
  ON projects FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own projects"
  ON projects FOR DELETE
  USING (auth.uid() = user_id);

-- RLS Policies for files
CREATE POLICY "Users can view their own files"
  ON files FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own files"
  ON files FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own files"
  ON files FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own files"
  ON files FOR DELETE
  USING (auth.uid() = user_id);

-- RLS Policies for analyses
CREATE POLICY "Users can view their own analyses"
  ON analyses FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own analyses"
  ON analyses FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own analyses"
  ON analyses FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own analyses"
  ON analyses FOR DELETE
  USING (auth.uid() = user_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to create profile when user is created
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO profiles (id, first_name, last_name)
  VALUES (
    NEW.id,
    NEW.raw_user_meta_data->>'first_name',
    NEW.raw_user_meta_data->>'last_name'
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- Triggers to update updated_at
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_files_updated_at BEFORE UPDATE ON files
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_analyses_updated_at BEFORE UPDATE ON analyses
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

