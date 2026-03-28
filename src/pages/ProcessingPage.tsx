import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { StepShell } from '../components/StepShell';

const stagedUpdates = [
  'Collecting the uploaded materials',
  'Comparing recurring job requirements',
  'Evaluating resume alignment and gaps',
  'Composing the Revue report',
];

export function ProcessingPage() {
  const navigate = useNavigate();
  const [currentStage, setCurrentStage] = useState(0);

  useEffect(() => {
    if (currentStage >= stagedUpdates.length - 1) {
      const timer = window.setTimeout(() => navigate('/report'), 1800);
      return () => window.clearTimeout(timer);
    }

    const interval = window.setTimeout(() => {
      setCurrentStage((stage) => stage + 1);
    }, 5000);

    return () => window.clearTimeout(interval);
  }, [currentStage, navigate]);

  const percent = useMemo(() => Math.round(((currentStage + 1) / stagedUpdates.length) * 100), [currentStage]);

  return (
    <StepShell
      stepIndex={2}
      eyebrow="Step 3"
      title="We’re analyzing your resume and job postings…"
      description="This UI prototype simulates the staged backend work. In production, the page will poll for status every five to ten seconds while Airflow runs the full pipeline."
      aside={
        <div className="info-panel">
          <p className="eyebrow">Behind the scenes</p>
          <p>Airflow runs the analysis pipeline while the backend updates job status for polling.</p>
        </div>
      }
    >
      <div className="processing-panel">
        <div className="progress-meter" aria-hidden="true">
          <div className="progress-meter__fill" style={{ width: `${percent}%` }} />
        </div>
        <div className="processing-panel__header">
          <strong>{percent}% complete</strong>
          <span>Polling mock backend every 5 seconds</span>
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

        <div className="form-actions form-actions--split">
          <Link to="/resume" className="button button--ghost">
            Back
          </Link>
          {currentStage >= stagedUpdates.length - 1 ? (
            <Link to="/report" className="button button--primary">
              View Revue Report
            </Link>
          ) : null}
        </div>
      </div>
    </StepShell>
  );
}