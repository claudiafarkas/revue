BEGIN;

ALTER TABLE reports
    ADD COLUMN IF NOT EXISTS status TEXT;

ALTER TABLE reports
    ADD COLUMN IF NOT EXISTS stage TEXT;

UPDATE reports
SET
    status = COALESCE(status, 'awaiting_resume'),
    stage = COALESCE(stage, 'postings_stored');

ALTER TABLE reports
    ALTER COLUMN status SET DEFAULT 'awaiting_resume';

ALTER TABLE reports
    ALTER COLUMN status SET NOT NULL;

ALTER TABLE reports
    ALTER COLUMN stage SET DEFAULT 'postings_stored';

ALTER TABLE reports
    ALTER COLUMN stage SET NOT NULL;

COMMIT;
