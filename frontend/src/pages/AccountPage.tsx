import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import { buildPreviewHtml, type ReportContent } from './ReportPage';
import { StepShell } from '../components/StepShell';
import { useAuth } from '../context/AuthContext';
import { authenticatedApiFetch, readJsonResponse } from '../utils/api';

type HistoryItem = {
  job_id: string;
  workflow_date: string | null;
  resume_name: string | null;
  job_family_name: string | null;
  fit_overview: {
    match_score: number | null;
    fit_level: string | null;
    alignment_similarity: number | null;
  };
  report_preview: {
    overview: string;
    strengths_summary: string;
    gaps_summary: string;
    recommendations: string[];
  };
};

function toPercent(value: number | null | undefined): string {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return 'n/a';
  }
  return `${Math.round(value * 100)}%`;
}

function formatDate(value: string | null | undefined): string {
  if (!value) {
    return 'n/a';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return 'n/a';
  }
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function AccountPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [activeTab, setActiveTab] = useState<'profile' | 'history'>('profile');
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState('');
  const [previewLoadingJobId, setPreviewLoadingJobId] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState('');

  useEffect(() => {
    if (loading) {
      return;
    }

    if (!user) {
      void router.replace('/login?next=account');
    }
  }, [loading, user, router]);

  useEffect(() => {
    if (!user) {
      return;
    }

    let cancelled = false;

    async function loadHistory() {
      setHistoryLoading(true);
      try {
        const response = await authenticatedApiFetch('/report/history');
        const body = (await readJsonResponse(response)) as { items?: HistoryItem[]; detail?: string } | null;
        if (!response.ok) {
          const detail = body && typeof body.detail === 'string' ? body.detail : 'Unable to load workflow history.';
          throw new Error(detail);
        }

        if (cancelled) {
          return;
        }

        setHistoryItems(Array.isArray(body?.items) ? body.items : []);
        setHistoryError('');
      } catch (historyLoadError) {
        if (cancelled) {
          return;
        }
        const message = historyLoadError instanceof Error ? historyLoadError.message : 'Unable to load workflow history.';
        setHistoryError(message);
      } finally {
        if (!cancelled) {
          setHistoryLoading(false);
        }
      }
    }

    loadHistory();

    return () => {
      cancelled = true;
    };
  }, [user]);

  if (loading || !user) {
    return (
      <StepShell
        stepIndex={0}
        eyebrow="Account"
        title="Loading account"
        description="Checking your secure session."
      >
        <section className="form-panel auth-panel">
          <p className="field-group__message">Please wait...</p>
        </section>
      </StepShell>
    );
  }

  async function openWorkflowPreview(jobId: string) {
    const win = window.open('', '_blank', 'width=1100,height=820');
    if (!win) {
      setPreviewError('Unable to open preview window. Please allow popups and retry.');
      return;
    }

    setPreviewError('');
    setPreviewLoadingJobId(jobId);

    try {
      const response = await authenticatedApiFetch(`/report/${encodeURIComponent(jobId)}/content`);
      const body = (await readJsonResponse(response)) as ReportContent | { detail?: string } | null;
      if (!response.ok) {
        const detail = body && 'detail' in body && typeof body.detail === 'string' ? body.detail : 'Unable to load report preview.';
        throw new Error(detail);
      }

      let resumePdfObjectUrl: string | undefined;
      try {
        const resumeResponse = await authenticatedApiFetch(`/report/${encodeURIComponent(jobId)}/resume-file`);
        if (resumeResponse.ok) {
          const blob = await resumeResponse.blob();
          if (blob.size > 0) {
            resumePdfObjectUrl = URL.createObjectURL(blob);
          }
        }
      } catch {
        // Keep preview functional even if resume file retrieval fails.
      }

      const html = buildPreviewHtml(body as ReportContent, resumePdfObjectUrl);
      win.document.write(html);
      win.document.close();

      if (resumePdfObjectUrl) {
        win.addEventListener('beforeunload', () => {
          URL.revokeObjectURL(resumePdfObjectUrl as string);
        });
      }
    } catch (previewLoadError) {
      win.close();
      const message = previewLoadError instanceof Error ? previewLoadError.message : 'Unable to load report preview.';
      setPreviewError(message);
    } finally {
      setPreviewLoadingJobId(null);
    }
  }

  return (
    <StepShell
      className="step-layout--account"
      stepIndex={0}
      eyebrow="Account"
      title="Your account"
      description="Manage your profile details and review your past workflow reports."
      aside={
        <div className="info-panel">
          <p className="eyebrow">Coming next</p>
          <p>Plan management, usage credits, billing, and account settings.</p>
        </div>
      }
    >
      <section className="account-main">
        <div className="account-tabbar" role="tablist" aria-label="Account sections">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'profile'}
            className={`account-tab${activeTab === 'profile' ? ' account-tab--active' : ''}`}
            onClick={() => setActiveTab('profile')}
          >
            Profile
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'history'}
            className={`account-tab${activeTab === 'history' ? ' account-tab--active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            Workflow History
          </button>
        </div>

        {activeTab === 'profile' ? (
          <section className="account-view" aria-label="Profile details">
            <div className="account-kv">
              <span className="account-kv__label">Email</span>
              <p>{user.email || 'No email available'}</p>
            </div>

            <div className="account-kv">
              <span className="account-kv__label">User ID</span>
              <p>{user.user_id}</p>
            </div>

            <div className="account-kv">
              <span className="account-kv__label">Plan</span>
              <p>Starter (placeholder)</p>
            </div>

            <div className="account-kv">
              <span className="account-kv__label">Authentication</span>
              <p>Email + password (local account)</p>
            </div>

            <div className="account-kv">
              <span className="account-kv__label">Session Status</span>
              <p>Signed in</p>
            </div>
          </section>
        ) : (
          <section className="account-view account-history" aria-label="Workflow history">
            <p className="account-history__intro">Use Preview in the Report Summary column to quickly inspect a stored workflow report.</p>
            {historyError ? <p className="field-group__message field-group__message--error">{historyError}</p> : null}
            {previewError ? <p className="field-group__message field-group__message--error">{previewError}</p> : null}
            {historyLoading ? <p className="field-group__message">Loading workflow history...</p> : null}
            {!historyLoading && !historyItems.length ? (
              <p className="field-group__message">No completed workflows yet.</p>
            ) : null}

            {historyItems.length ? (
              <div className="account-history__table-wrap">
                <table className="account-history__table">
                  <thead>
                    <tr>
                      <th scope="col">Date</th>
                      <th scope="col">Resume</th>
                      <th scope="col">Job Family</th>
                      <th scope="col">Fit Overview</th>
                      <th scope="col">Report Summary</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historyItems.map((item) => (
                      <tr key={item.job_id}>
                        <td>{formatDate(item.workflow_date)}</td>
                        <td>{item.resume_name || 'n/a'}</td>
                        <td>{item.job_family_name || 'n/a'}</td>
                        <td>
                          <div className="account-history__fit">
                            <span>{toPercent(item.fit_overview.match_score)}</span>
                            <span>{item.fit_overview.fit_level ? item.fit_overview.fit_level.toUpperCase() : 'N/A'}</span>
                            <span>{toPercent(item.fit_overview.alignment_similarity)}</span>
                          </div>
                        </td>
                        <td>
                          <button
                            type="button"
                            className="button button--ghost account-history__preview"
                            disabled={previewLoadingJobId === item.job_id}
                            onClick={() => {
                              void openWorkflowPreview(item.job_id);
                            }}
                          >
                            {previewLoadingJobId === item.job_id ? 'Opening...' : 'Preview'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
          </section>
        )}
      </section>
    </StepShell>
  );
}
