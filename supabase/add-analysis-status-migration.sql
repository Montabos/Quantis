-- Migration pour ajouter le suivi des étapes d'analyse
-- Ajoute les colonnes nécessaires pour le système d'analyse interactive avec popup

-- Add status column to analyses table
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'analyses' AND column_name = 'status'
  ) THEN
    ALTER TABLE analyses ADD COLUMN status TEXT DEFAULT 'pending' 
      CHECK (status IN ('pending', 'in_progress', 'waiting_for_data', 'completed', 'error'));
  END IF;
END $$;

-- Add current_step column
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'analyses' AND column_name = 'current_step'
  ) THEN
    ALTER TABLE analyses ADD COLUMN current_step TEXT;
  END IF;
END $$;

-- Add progress column (0-100)
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'analyses' AND column_name = 'progress'
  ) THEN
    ALTER TABLE analyses ADD COLUMN progress INTEGER DEFAULT 0 
      CHECK (progress >= 0 AND progress <= 100);
  END IF;
END $$;

-- Add steps column (JSONB array of step objects)
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'analyses' AND column_name = 'steps'
  ) THEN
    ALTER TABLE analyses ADD COLUMN steps JSONB DEFAULT '[]'::jsonb;
  END IF;
END $$;

-- Add missing_data column (JSONB array of missing data requests)
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'analyses' AND column_name = 'missing_data'
  ) THEN
    ALTER TABLE analyses ADD COLUMN missing_data JSONB DEFAULT '[]'::jsonb;
  END IF;
END $$;

-- Add partial_result column (JSONB for partial analysis results)
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'analyses' AND column_name = 'partial_result'
  ) THEN
    ALTER TABLE analyses ADD COLUMN partial_result JSONB DEFAULT '{}'::jsonb;
  END IF;
END $$;

-- Create index on status for faster queries
CREATE INDEX IF NOT EXISTS idx_analyses_status ON analyses(status);

-- Create index on current_step for faster queries
CREATE INDEX IF NOT EXISTS idx_analyses_current_step ON analyses(current_step);

-- Update existing analyses to have default status
UPDATE analyses SET status = 'completed' WHERE status IS NULL;

