import { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { StepShell } from '../components/StepShell';
import { useRevue } from '../context/RevueContext';

function getValidationMessage(value: string) {
  if (!value.trim()) {
    return 'Please add a job posting URL or paste the posting text.';
  }

  const trimmed = value.trim();

  if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
    return '';
  }

  if (trimmed.length < 80) {
    return 'If you are pasting text, include more detail from the posting.';
  }

  return '';
}

export function JobPostingsPage() {
  const navigate = useNavigate();
  const { postings, setPosting, addPosting } = useRevue();
  const [hasSubmitted, setHasSubmitted] = useState(false);

  const messages = useMemo(() => postings.map((posting) => getValidationMessage(posting)), [postings]);

  const canContinue = postings.slice(0, 3).every((posting) => posting.trim()) && messages.every((message) => !message);

  function handleContinue() {
    setHasSubmitted(true);

    if (!canContinue) {
      return;
    }

    navigate('/resume');
  }

  return (
    <StepShell
      stepIndex={1}
      eyebrow="Step 1"
      title="Collect the job postings"
      description="Paste three role descriptions or URLs. Revue will use them later to identify repeated requirements and themes."
      aside={
        <div className="info-panel">
          <p className="eyebrow">Behind the scenes</p>
          <p>FastAPI will store the raw postings here. No Airflow yet. This is still the user-input stage.</p>
        </div>
      }
    >
      <div className="form-panel">
        {postings.map((posting, index) => {
          const message = hasSubmitted ? messages[index] : '';

          return (
            <label key={`posting-${index}`} className="field-group">
              <span className="field-group__label">Job Posting {index + 1}</span>
              <textarea
                rows={index < 3 ? 6 : 4}
                value={posting}
                onChange={(event) => setPosting(index, event.target.value)}
                placeholder="Paste a job posting or add a URL"
                className={message ? 'field field--error' : 'field'}
              />
              <span className={message ? 'field-group__message field-group__message--error' : 'field-group__message'}>
                {message || 'URLs and pasted text are both accepted.'}
              </span>
            </label>
          );
        })}

        <div className="form-actions form-actions--split">
          <button type="button" className="button button--secondary" onClick={addPosting}>
            Add another posting
          </button>
          <div className="form-actions__inline">
            <Link to="/" className="button button--ghost">
              Back
            </Link>
            <button type="button" className="button button--primary" onClick={handleContinue}>
              Continue to Resume
            </button>
          </div>
        </div>
      </div>
    </StepShell>
  );
}