import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { StepShell } from '../components/StepShell';
import { useRevue } from '../context/RevueContext';
import { getApiBaseUrl, readJsonResponse } from '../utils/api';

type ReportStatus = {
  job_id: string;
  status: string;
  stage: string;
  report_available: boolean;
  poll_after_seconds: number;
};

const stagedUpdates = [
  'Collecting the uploaded materials',
  'Extracting and normalizing resume signals',
  'Comparing recurring job requirements',
  'Evaluating resume alignment and gaps',
  'Composing the Revue report',
];

function getStageIndex(stage: string) {
  if (stage === 'resume_stored' || stage === 'extracting_resume_text' || stage === 'loading_postings') {
    return 0;
  }
  if (stage === 'cleaning_text' || stage === 'extracting_resume_features') {
    return 1;
  }
  if (stage === 'comparing_requirements') {
    return 2;
  }
  if (stage === 'generating_embeddings') {
    return 3;
  }
  if (stage === 'generating_report' || stage === 'report_ready') {
    return 4;
  }
  return 0;
}

export function ProcessingPage() {
  const router = useRouter();
  const { jobId } = useRevue();
  const [statusSnapshot, setStatusSnapshot] = useState<ReportStatus | null>(null);
  const [error, setError] = useState('');

  const activeJobId = useMemo(() => {
    if (typeof router.query.job_id === 'string' && router.query.job_id) {
      return router.query.job_id;
    }
    return jobId;
  }, [jobId, router.query.job_id]);

  useEffect(() => {
    if (!activeJobId) {
      return;
    }

    let cancelled = false;
    let timeoutId: number | undefined;

    async function pollStatus() {
      try {
        const response = await fetch(`${getApiBaseUrl()}/report/${encodeURIComponent(activeJobId)}`);
        const body = (await readJsonResponse(response)) as ReportStatus | { detail?: string } | null;

        if (!response.ok) {
          const detail = body && 'detail' in body && typeof body.detail === 'string' ? body.detail : 'Unable to read report status.';
          throw new Error(detail);
        }

        const snapshot = body as ReportStatus;
        if (cancelled) {
          return;
        }

        setStatusSnapshot(snapshot);
        setError('');

        if (snapshot.report_available || snapshot.status === 'completed') {
          await router.push(`/report?job_id=${encodeURIComponent(activeJobId)}`);
          return;
        }

        if (snapshot.status === 'failed') {
          setError('Pipeline failed while processing this job. Please retry from resume upload.');
          return;
        }

        const pollAfterMs = Math.max(snapshot.poll_after_seconds, 2) * 1000;
        timeoutId = window.setTimeout(pollStatus, pollAfterMs);
      } catch (pollError) {
        if (cancelled) {
          return;
        }

        const message = pollError instanceof Error ? pollError.message : 'Unable to read report status.';
        setError(message);
        timeoutId = window.setTimeout(pollStatus, 5000);
      }
    }

    pollStatus();

    return () => {
      cancelled = true;
      if (timeoutId) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [activeJobId, router]);

  const currentStage = statusSnapshot ? getStageIndex(statusSnapshot.stage) : 0;
  const percent = Math.round(((currentStage + 1) / stagedUpdates.length) * 100);

  return (
    <StepShell
      stepIndex={2}
      eyebrow="Step 3"
      title="We’re analyzing your resume and job postings..."
      description="This page now polls the backend report status endpoint while Airflow runs the pipeline."
      aside={
        <div className="info-panel">
          <p className="eyebrow">Behind the scenes</p>
          <p>Airflow updates report stages in PostgreSQL and this page polls them live.</p>
        </div>
      }
    >
      <div className="processing-panel">
        <div className="progress-meter" aria-hidden="true">
          <div className="progress-meter__fill" style={{ width: `${percent}%` }} />
        </div>
        <div className="processing-panel__header">
          <strong>{percent}% complete</strong>
          <span>
            {activeJobId ? `Tracking ${activeJobId}` : 'Waiting for job id'}
            {statusSnapshot ? ` | stage: ${statusSnapshot.stage}` : ''}
          </span>
        </div>

        <ol className="status-list">
          {stagedUpdates.map((stage, index) => {
            const state = index < currentStage ? 'done' : index === currentStage ? 'active' : 'queued';

            return (
              <li key={stage} className={`status-list__item status-list__item--${state}`}>
                <span className="status-list__dot" aria-hidden="true" />
                <div>
                  <strong>{stage}</strong>
                  <p>
                    {state === 'done' && 'Complete'}
                    {state === 'active' && 'In progress'}
                    {state === 'queued' && 'Queued'}
                  </p>
                </div>
              </li>
            );
          })}
        </ol>

        {error ? <p className="field-group__message field-group__message--error">{error}</p> : null}

        <div className="form-actions form-actions--split">
          <Link href="/resume" className="button button--ghost">
            Back
          </Link>
          {statusSnapshot?.report_available ? (
            <Link href={`/report?job_id=${encodeURIComponent(activeJobId)}`} className="button button--primary">
              View Revue Report
            </Link>
          ) : null}
        </div>
      </div>
    </StepShell>
  );
}
