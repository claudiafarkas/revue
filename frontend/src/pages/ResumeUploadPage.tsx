import { useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { StepShell } from '../components/StepShell';
import { useRevue } from '../context/RevueContext';
import { getApiBaseUrl, readJsonResponse } from '../utils/api';

function formatFileSize(size: number) {
  if (size < 1024 * 1024) {
    return `${Math.round(size / 1024)} KB`;
  }

  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

export function ResumeUploadPage() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const { resumeFile, setResumeFile, jobId, setJobId } = useRevue();
  const [error, setError] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [previewUrl, setPreviewUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!resumeFile) {
      setPreviewUrl('');
      return;
    }

    const objectUrl = URL.createObjectURL(resumeFile);
    setPreviewUrl(objectUrl);

    return () => URL.revokeObjectURL(objectUrl);
  }, [resumeFile]);

  const fileMeta = useMemo(() => {
    if (!resumeFile) {
      return [] as string[];
    }

    return [formatFileSize(resumeFile.size), new Date(resumeFile.lastModified).toLocaleDateString()];
  }, [resumeFile]);

  function acceptFile(file: File | undefined) {
    if (!file) {
      return;
    }

    if (file.type !== 'application/pdf') {
      setError('Please upload a PDF resume.');
      return;
    }

    setError('');
    setResumeFile(file);
  }

  async function handleGenerateReport() {
    if (!resumeFile) {
      setError('Please upload a PDF resume.');
      return;
    }

    const jobIdFromQuery = typeof router.query.job_id === 'string' ? router.query.job_id : '';
    const activeJobId = jobId || jobIdFromQuery;
    if (!activeJobId) {
      setError('Missing job id. Please submit job postings first.');
      return;
    }

    setError('');
    setIsSubmitting(true);

    try {
      const formData = new FormData();
      formData.append('job_id', activeJobId);
      formData.append('file', resumeFile, resumeFile.name);

      const response = await fetch(`${getApiBaseUrl()}/resume`, {
        method: 'POST',
        body: formData,
      });

      const body = (await readJsonResponse(response)) as { job_id?: string; detail?: string } | null;
      if (!response.ok || !body?.job_id) {
        const detail = body?.detail || 'Unable to upload resume.';
        throw new Error(detail);
      }

      setJobId(body.job_id);
      await router.push(`/processing?job_id=${encodeURIComponent(body.job_id)}`);
    } catch (submitError) {
      const message = submitError instanceof Error ? submitError.message : 'Unable to upload resume.';
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <StepShell
      stepIndex={1}
      eyebrow="Step 2"
      title="Upload your resume"
      description="Bring in the latest PDF version of your resume. Once uploaded, the backend will eventually store the file and trigger the analysis pipeline."
      aside={
        <div className="info-panel">
          <p className="eyebrow">Behind the scenes</p>
          <p>FastAPI will store the resume and trigger the Airflow DAG, then redirect the user to processing.</p>
        </div>
      }
    >
      <div className="upload-grid">
        <section className="form-panel">
          <div
            className={isDragging ? 'upload-zone upload-zone--dragging' : 'upload-zone'}
            onDragOver={(event) => {
              event.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(event) => {
              event.preventDefault();
              setIsDragging(false);
              acceptFile(event.dataTransfer.files[0]);
            }}
          >
            <p className="eyebrow">PDF Upload</p>
            <h2>Drag and drop your resume</h2>
            <p>or browse your files to choose a PDF for this prototype flow.</p>
            <button type="button" className="button button--secondary" onClick={() => inputRef.current?.click()}>
              Choose PDF
            </button>
            <input
              ref={inputRef}
              type="file"
              accept="application/pdf"
              hidden
              onChange={(event) => acceptFile(event.target.files?.[0])}
            />
          </div>

          <div className="file-preview-card">
            <p className="eyebrow">File Preview</p>
            {resumeFile ? (
              <>
                <h3>{resumeFile.name}</h3>
                <p>{fileMeta.join(' • ')}</p>
              </>
            ) : (
              <p>No file selected yet.</p>
            )}
            {error ? <p className="field-group__message field-group__message--error">{error}</p> : null}
          </div>
        </section>

        <section className="document-preview">
          <p className="eyebrow">On-page Preview</p>
          <div className="document-preview__stage">
            {previewUrl ? (
              <iframe title="Resume preview" src={previewUrl} className="document-preview__frame" />
            ) : (
              <div className="document-preview__empty">
                <p>Your resume preview will appear here after upload.</p>
              </div>
            )}
          </div>

          <div className="form-actions form-actions--preview">
            <Link href="/postings" className="button button--ghost">
              Back
            </Link>
            <button
              type="button"
              className="button button--primary"
              onClick={handleGenerateReport}
              disabled={!resumeFile || isSubmitting}
            >
              {isSubmitting ? 'Uploading resume...' : 'Generate My Revue Report'}
            </button>
          </div>
        </section>
      </div>
    </StepShell>
  );
}