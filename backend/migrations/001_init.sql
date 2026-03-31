BEGIN;

CREATE TABLE IF NOT EXISTS job_batches (
    job_id TEXT PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS job_postings (
    id BIGSERIAL PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES job_batches(job_id) ON DELETE CASCADE,
    posting_index INTEGER NOT NULL,
    posting_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (job_id, posting_index)
);

CREATE TABLE IF NOT EXISTS resumes (
    id BIGSERIAL PRIMARY KEY,
    job_id TEXT NOT NULL UNIQUE REFERENCES job_batches(job_id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    content_type TEXT,
    file_data BYTEA NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMIT;
