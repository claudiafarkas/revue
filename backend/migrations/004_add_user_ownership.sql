BEGIN;

ALTER TABLE job_batches
    ADD COLUMN IF NOT EXISTS user_uid TEXT;

UPDATE job_batches
SET user_uid = COALESCE(user_uid, 'legacy')
WHERE user_uid IS NULL;

ALTER TABLE job_batches
    ALTER COLUMN user_uid SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_job_batches_user_uid
    ON job_batches (user_uid);

ALTER TABLE reports
    ADD COLUMN IF NOT EXISTS user_uid TEXT;

UPDATE reports r
SET user_uid = COALESCE(r.user_uid, jb.user_uid, 'legacy')
FROM job_batches jb
WHERE r.job_id = jb.job_id
  AND r.user_uid IS NULL;

ALTER TABLE reports
    ALTER COLUMN user_uid SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_reports_user_uid
    ON reports (user_uid);

COMMIT;