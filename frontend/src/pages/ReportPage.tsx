import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { StepShell } from '../components/StepShell';
import { useRevue } from '../context/RevueContext';
import { getApiBaseUrl, readJsonResponse } from '../utils/api';

type DomainMatch = {
  domain: string;
  confidence: number;
  matched_terms: string[];
};

type Narrative = {
  overview?: string;
  strengths_summary?: string;
  gaps_summary?: string;
  resume_experience_level?: string;
  posting_experience_level?: string;
};

type ReportContent = {
  job_id: string;
  status: string;
  stage: string;
  report_json: {
    summary?: {
      match_score?: number;
      embedding_similarity?: number;
      fit_label?: string;
    };
    highlights?: {
      common_tools?: string[];
      common_achievements?: string[];
      matched_keywords?: string[];
      missing_keywords?: string[];
      posting_keywords?: string[];
      resume_keywords?: string[];
      domain_matches?: DomainMatch[];
    };
    recommendations?: string[];
    narrative?: Narrative;
  };
};

type RenderSection = {
  title: string;
  body?: string;
  items?: string[];
  tone?: 'default' | 'signal' | 'conclusion';
};

type ReportSummary = {
  matchScore: string;
  embeddingSimilarity: string;
  fitLabel: string;
};

type FitBand = {
  label: 'Limited' | 'Emerging' | 'Moderate' | 'Strong';
  minMatchScore: number;
  minEmbeddingSimilarity: number;
  guidance: string;
};

const FIT_BANDS: FitBand[] = [
  {
    label: 'Limited',
    minMatchScore: 0,
    minEmbeddingSimilarity: 0,
    guidance: 'Start with the highest-frequency requirements and add clear evidence of direct experience.',
  },
  {
    label: 'Emerging',
    minMatchScore: 0.15,
    minEmbeddingSimilarity: 0.2,
    guidance: 'Start by adding 3-5 missing requirements with concrete, evidence-backed bullets.',
  },
  {
    label: 'Moderate',
    minMatchScore: 0.4,
    minEmbeddingSimilarity: 0.45,
    guidance: 'Tighten alignment language and increase measurable outcomes tied to required tools.',
  },
  {
    label: 'Strong',
    minMatchScore: 0.65,
    minEmbeddingSimilarity: 0.65,
    guidance: 'Maintain role alignment and tailor top achievements to each posting for final polish.',
  },
];

function toPercent(value: number | undefined): string {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return 'n/a';
  }
  return `${Math.round(value * 100)}%`;
}

function buildSections(content: ReportContent | null): RenderSection[] {
  if (!content) {
    return [];
  }

  const summary = content.report_json.summary || {};
  const highlights = content.report_json.highlights || {};
  const recommendations = content.report_json.recommendations || [];
  const narrative = content.report_json.narrative;
  const commonTools = (highlights.common_tools || []).slice(0, 12);
  const commonAchievements = (highlights.common_achievements || []).slice(0, 12);
  const postingKeywords = (highlights.posting_keywords || []).slice(0, 10);
  const resumeKeywords = (highlights.resume_keywords || []).slice(0, 10);

  const matched = (highlights.matched_keywords || []).slice(0, 12);
  const missing = (highlights.missing_keywords || []).slice(0, 12);

  const topPostingSignals = commonTools.length ? commonTools : postingKeywords.length ? postingKeywords : [...matched, ...missing].slice(0, 10);
  const differentiators = matched.length ? matched : resumeKeywords.slice(0, 8);

  const experienceNote =
    narrative?.resume_experience_level && narrative?.posting_experience_level
      ? ` Your resume signals a ${narrative.resume_experience_level}-level candidate; these postings target ${narrative.posting_experience_level}-level.`
      : '';

  const alignmentSummary =
    narrative?.overview ||
    `Overall fit currently reads as ${summary.fit_label || 'n/a'}, with a match score of ${toPercent(summary.match_score)} and an embedding similarity of ${toPercent(summary.embedding_similarity)}.${differentiators.length ? ` The strongest overlap appears in ${differentiators.slice(0, 6).join(', ')}.` : ''}${experienceNote}`;

  const strengthsBody =
    narrative?.strengths_summary ||
    (differentiators.length
      ? `Your resume clearly addresses the following requirements from the postings: ${differentiators.slice(0, 6).join(', ')}.`
      : 'No dominant strengths were detected in the current pass.');

  const gapsBody =
    narrative?.gaps_summary ||
    (missing.length
      ? 'These signals appear more often in the postings than in your current resume language.'
      : 'No major missing or under-emphasized signals were detected.');

  return [
    {
      title: 'Overall Assessment',
      body: alignmentSummary,
      tone: 'default',
    },
    {
      title: 'Most Common Tools and Requirements',
      items: topPostingSignals,
      body: topPostingSignals.length ? undefined : 'No recurring tools or terms were detected in the postings.',
      tone: 'signal',
    },
    {
      title: 'Where Your Resume Is Strongest',
      items: differentiators,
      body: strengthsBody,
      tone: 'signal',
    },
    {
      title: 'What’s Missing or Under-Emphasized',
      items: missing,
      body: gapsBody,
      tone: 'signal',
    },
    {
      title: 'Recurring Employer Signals',
      items: commonAchievements,
      body: commonAchievements.length ? undefined : 'No recurring achievement signals were detected from the current postings.',
      tone: 'signal',
    },
    {
      title: 'Recommended Next Steps',
      items: recommendations,
      body: recommendations.length ? undefined : 'No recommendations were generated.',
      tone: 'conclusion',
    },
  ];
}

function buildSummary(content: ReportContent | null): ReportSummary {
  const summary = content?.report_json.summary || {};
  return {
    matchScore: toPercent(summary.match_score),
    embeddingSimilarity: toPercent(summary.embedding_similarity),
    fitLabel: summary.fit_label ? summary.fit_label.toUpperCase() : 'N/A',
  };
}

function getActiveFitBand(content: ReportContent | null): FitBand {
  const summary = content?.report_json.summary || {};
  const matchScore = typeof summary.match_score === 'number' ? summary.match_score : 0;
  const embeddingSimilarity = typeof summary.embedding_similarity === 'number' ? summary.embedding_similarity : 0;

  for (let i = FIT_BANDS.length - 1; i >= 0; i -= 1) {
    const band = FIT_BANDS[i];
    if (matchScore >= band.minMatchScore && embeddingSimilarity >= band.minEmbeddingSimilarity) {
      return band;
    }
  }

  return FIT_BANDS[0];
}

function getNextFitBand(activeBand: FitBand): FitBand | null {
  const index = FIT_BANDS.findIndex((band) => band.label === activeBand.label);
  if (index < 0 || index >= FIT_BANDS.length - 1) {
    return null;
  }
  return FIT_BANDS[index + 1];
}

function buildPreviewHtml(content: ReportContent | null): string {
  if (!content) {
    return '<html><body style="font-family: Georgia, serif; padding: 24px;">No report content yet.</body></html>';
  }

  const summary = content.report_json.summary || {};
  const matchScore = toPercent(summary.match_score);
  const fitLabel = summary.fit_label ? summary.fit_label.toUpperCase() : 'N/A';
  const embeddingSimilarity = toPercent(summary.embedding_similarity);

  const metricsMarkup = `
    <div style="display:flex;gap:16px;margin:16px 0 0;">
      <div style="flex:1;padding:16px;border:1px solid #e1d6c3;border-radius:8px;">
        <p style="margin:0 0 4px;font-size:11px;text-transform:uppercase;letter-spacing:0.08em;color:#5b6662;">Match Score</p>
        <p style="margin:0;font-size:28px;font-weight:700;">${matchScore}</p>
      </div>
      <div style="flex:1;padding:16px;border:1px solid #e1d6c3;border-radius:8px;">
        <p style="margin:0 0 4px;font-size:11px;text-transform:uppercase;letter-spacing:0.08em;color:#5b6662;">Fit Level</p>
        <p style="margin:0;font-size:28px;font-weight:700;">${fitLabel}</p>
      </div>
      <div style="flex:1;padding:16px;border:1px solid #e1d6c3;border-radius:8px;">
        <p style="margin:0 0 4px;font-size:11px;text-transform:uppercase;letter-spacing:0.08em;color:#5b6662;">Embedding Similarity</p>
        <p style="margin:0;font-size:28px;font-weight:700;">${embeddingSimilarity}</p>
      </div>
    </div>`;

  const sections = buildSections(content);
  const sectionMarkup = sections
    .map((section) => {
      const itemsMarkup = (section.items || [])
        .map((item) => `<span style="display:inline-block;margin:0 8px 8px 0;padding:6px 12px;border-radius:999px;background:#f2ede3;border:1px solid #e1d6c3;font-size:13px;">${item}</span>`)
        .join('');
      const bodyMarkup = section.body ? `<p style="margin: 10px 0 0; line-height: 1.7; font-size: 15px;">${section.body}</p>` : '';
      return `<section style="margin-top:28px;padding-top:20px;border-top:1px solid #e1d6c3;">
        <h2 style="margin:0 0 10px;font-size:13px;text-transform:uppercase;letter-spacing:0.08em;color:#5b6662;">${section.title}</h2>
        ${itemsMarkup ? `<div style="margin-top:8px;">${itemsMarkup}</div>` : ''}
        ${bodyMarkup}
      </section>`;
    })
    .join('');

  return `<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Revue Report — ${content.job_id}</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: Georgia, serif; color: #202625; background: #fff; margin: 0; padding: 32px 40px; max-width: 820px; }
    @media print {
      body { padding: 0; }
      .no-print { display: none !important; }
      section { page-break-inside: avoid; }
    }
  </style>
</head>
<body>
  <div style="border-bottom:2px solid #202625;padding-bottom:16px;margin-bottom:8px;">
    <h1 style="margin:0 0 4px;font-size:32px;letter-spacing:-0.01em;">Revue Report</h1>
    <p style="margin:0;color:#5b6662;font-size:13px;">Report ID: ${content.job_id} &nbsp;·&nbsp; ${content.status} &nbsp;·&nbsp; ${content.stage}</p>
  </div>
  ${metricsMarkup}
  ${sectionMarkup}
  <p style="margin-top:40px;font-size:12px;color:#9aada8;" class="no-print">Generated by Revue.ai</p>
</body>
</html>`;
}

export function ReportPage() {
  const router = useRouter();
  const { jobId } = useRevue();
  const [reportContent, setReportContent] = useState<ReportContent | null>(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [showFitLegend, setShowFitLegend] = useState(false);

  const activeJobId = useMemo(() => {
    if (typeof router.query.job_id === 'string' && router.query.job_id) {
      return router.query.job_id;
    }
    return jobId;
  }, [jobId, router.query.job_id]);

  useEffect(() => {
    if (!activeJobId) {
      setError('Missing job id. Please run a report first.');
      setIsLoading(false);
      return;
    }

    let cancelled = false;

    async function loadReport() {
      setIsLoading(true);
      try {
        const response = await fetch(`${getApiBaseUrl()}/report/${encodeURIComponent(activeJobId)}/content`);
        const body = (await readJsonResponse(response)) as ReportContent | { detail?: string } | null;
        if (!response.ok) {
          const detail = body && 'detail' in body && typeof body.detail === 'string' ? body.detail : 'Unable to load generated report.';
          throw new Error(detail);
        }

        if (cancelled) {
          return;
        }

        setReportContent(body as ReportContent);
        setError('');
      } catch (loadError) {
        if (cancelled) {
          return;
        }

        const message = loadError instanceof Error ? loadError.message : 'Unable to load generated report.';
        setError(message);
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    loadReport();

    return () => {
      cancelled = true;
    };
  }, [activeJobId]);

  const reportSections = buildSections(reportContent);
  const reportSummary = buildSummary(reportContent);
  const activeFitBand = getActiveFitBand(reportContent);
  const nextFitBand = getNextFitBand(activeFitBand);
  const recommendationSection = reportSections.find((section) => section.title === 'Recommended Next Steps');
  const coreSections = reportSections.filter((section) => section.title !== 'Recommended Next Steps');

  return (
    <StepShell
      className="step-layout--report"
      stepIndex={2}
      eyebrow="Step 3"
      title="Your Revue Report"
      description="A structured analysis of how your resume aligns with the selected job postings."
    >
      <div className="report-container">
        <section className="report-meta">
          <div className="report-meta__identity">
            <p className="eyebrow">Report Metadata</p>
            <p className="report-meta__id">{reportContent ? `Report ID: ${reportContent.job_id}` : 'Report ID pending'}</p>
            <p className="report-meta__status">
              {reportContent
                ? `${reportContent.status} • ${reportContent.stage}`
                : isLoading
                  ? 'Loading generated report...'
                  : 'No report available.'}
            </p>
          </div>
          <button
            type="button"
            className="button button--primary report-toolbar__download"
            disabled={!reportContent}
            onClick={() => {
              const html = buildPreviewHtml(reportContent);
              const win = window.open('', '_blank', 'width=900,height=700');
              if (!win) return;
              win.document.write(html);
              win.document.close();
              win.onload = () => {
                win.focus();
                win.print();
              };
            }}
          >
            <span className="report-toolbar__icon" aria-hidden="true">
              ↓
            </span>
            <span>Download PDF</span>
          </button>
        </section>

        {error ? <p className="field-group__message field-group__message--error">{error}</p> : null}

        <section className="report-fit-overview">
          <p className="eyebrow report-fit-overview__label">Fit Overview</p>
          <div className="report-fit-overview__cards">
            <article className="report-metric-card report-metric-card--score">
              <p>Match Score</p>
              <strong>{reportSummary.matchScore}</strong>
              <span>Overlap with recurring posting keywords.</span>
            </article>
            <article className="report-metric-card report-metric-card--fit">
              <p>Fit Level</p>
              <strong>{reportSummary.fitLabel}</strong>
              <span>Qualitative fit based on current resume signals.</span>
            </article>
            <article className="report-metric-card report-metric-card--feature">
              <p>Embedding Similarity</p>
              <strong>{reportSummary.embeddingSimilarity}</strong>
              <span>Semantic similarity across the combined postings.</span>
            </article>
          </div>
          <div className="report-fit-legend" aria-label="Fit scoring legend">
            <div className="report-fit-legend__header">
              <p className="eyebrow">Fit Legend</p>
              <div className="report-fit-legend__summary-row">
                <p>
                  Fit Level combines Match Score + Embedding Similarity.
                </p>
                <button
                  type="button"
                  className="report-fit-legend__toggle"
                  aria-expanded={showFitLegend}
                  aria-controls="fit-legend-details"
                  onClick={() => setShowFitLegend((value) => !value)}
                >
                  {showFitLegend ? 'Hide legend' : 'Show legend'}
                </button>
              </div>
            </div>
            {showFitLegend ? (
              <div id="fit-legend-details" className="report-fit-legend__details">
                <div className="report-fit-legend__scale" role="list" aria-label="Fit levels scale">
                  {FIT_BANDS.map((band) => {
                    const isActive = band.label.toUpperCase() === reportSummary.fitLabel;
                    return (
                      <article key={band.label} className={`report-fit-band${isActive ? ' report-fit-band--active' : ''}`} role="listitem">
                        <p className="report-fit-band__title">{band.label}</p>
                        <p className="report-fit-band__metric">
                          <span>Match Score:</span>
                          <span>{Math.round(band.minMatchScore * 100)}%+</span>
                        </p>
                        <p className="report-fit-band__metric">
                          <span>Embedding Similarity:</span>
                          <span>{Math.round(band.minEmbeddingSimilarity * 100)}%+</span>
                        </p>
                      </article>
                    );
                  })}
                </div>
                <p className="report-fit-legend__guidance">
                  <strong>Current:</strong> {activeFitBand.label}. {activeFitBand.guidance}{' '}
                  {nextFitBand
                    ? `To reach ${nextFitBand.label}, aim for roughly ${Math.round(nextFitBand.minMatchScore * 100)}%+ Match Score and ${Math.round(nextFitBand.minEmbeddingSimilarity * 100)}%+ Embedding Similarity.`
                    : 'You are already at the top band; focus on role-by-role tailoring to stay strong.'}
                </p>
              </div>
            ) : null}
          </div>
        </section>

        <section className="report-content">

          <div className="report-grid report-grid--single">
            {coreSections.map((section, index) => (
              <article key={section.title} className="report-card report-card--bold">
                <p className="eyebrow report-card__label">Section {String(index + 1).padStart(2, '0')}</p>
                <h2 className="report-card__title">{section.title}</h2>
                {section.items?.length ? (
                  <div className="report-tags">
                    {section.items.map((item) => (
                      <span key={`${section.title}-${item}`} className="report-tag">
                        {item}
                      </span>
                    ))}
                  </div>
                ) : null}
                {section.body ? <p className="report-card__body">{section.body}</p> : null}
              </article>
            ))}
          </div>

          {recommendationSection ? (
            <article className="report-conclusion">
              <p className="eyebrow report-card__label">Conclusion</p>
              <h2 className="report-card__title report-card__title--conclusion">{recommendationSection.title}</h2>
              {recommendationSection.items?.length ? (
                <ul className="report-recommendations">
                  {recommendationSection.items.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : recommendationSection.body ? (
                <p className="report-card__body">{recommendationSection.body}</p>
              ) : null}
            </article>
          ) : null}
        </section>
      </div>

      <div className="form-actions form-actions--report">
        <Link href={activeJobId ? `/processing?job_id=${encodeURIComponent(activeJobId)}` : '/processing'} className="button button--ghost">
          Back
        </Link>
        <Link href="/postings" className="button button--secondary">
          Start another Revue
        </Link>
      </div>
    </StepShell>
  );
}