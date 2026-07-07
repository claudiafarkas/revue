BEGIN;

-- Revert migration 005: Remove Firebase storage path and restore file_data as NOT NULL

ALTER TABLE resumes
    DROP COLUMN IF EXISTS firebase_storage_path;

ALTER TABLE resumes
    ALTER COLUMN file_data SET NOT NULL;

COMMIT;
