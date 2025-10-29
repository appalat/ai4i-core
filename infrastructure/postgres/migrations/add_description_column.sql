-- Migration to add description column to configurations table if missing
-- Run this if your table was created before description column was added

\c config_db;

-- Add description column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'configurations' 
        AND column_name = 'description'
    ) THEN
        ALTER TABLE configurations ADD COLUMN description TEXT;
        RAISE NOTICE 'Added description column to configurations table';
    ELSE
        RAISE NOTICE 'Description column already exists in configurations table';
    END IF;
END $$;

