-- Storage Policies for 'files' bucket
-- Execute these in Supabase SQL Editor after creating the 'files' bucket

-- Policy: Users can view their own files
CREATE POLICY "Users can view their own files"
ON storage.objects FOR SELECT
USING (
  bucket_id = 'files' 
  AND auth.uid()::text = (string_to_array(name, '/'))[1]
);

-- Policy: Users can upload their own files
CREATE POLICY "Users can upload their own files"
ON storage.objects FOR INSERT
WITH CHECK (
  bucket_id = 'files' 
  AND auth.uid()::text = (string_to_array(name, '/'))[1]
);

-- Policy: Users can update their own files
CREATE POLICY "Users can update their own files"
ON storage.objects FOR UPDATE
USING (
  bucket_id = 'files' 
  AND auth.uid()::text = (string_to_array(name, '/'))[1]
);

-- Policy: Users can delete their own files
CREATE POLICY "Users can delete their own files"
ON storage.objects FOR DELETE
USING (
  bucket_id = 'files' 
  AND auth.uid()::text = (string_to_array(name, '/'))[1]
);

