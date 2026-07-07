BEGIN;

ALTER TABLE resumes
    ADD COLUMN IF NOT EXISTS firebase_storage_path TEXT;

ALTER TABLE resumes
    ALTER COLUMN file_data DROP NOT NULL;

CREATE INDEX IF NOT EXISTS idx_resumes_firebase_storage_path
    ON resumes (firebase_storage_path);

COMMIT;