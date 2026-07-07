import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { StepShell } from '../components/StepShell';
import { useRevue } from '../context/RevueContext';
import { authenticatedApiFetch, readJsonResponse } from '../utils/api';
import { formatPipelineStatus } from '../utils/status';

const REPORT_STOPWORDS = new Set([
  'a',
  'about',
  'across',
  'an',
  'and',
  'and/or',
  'are',
  'as',
  'at',
  'be',
  'by',
  'can',
  'complex',
  'develop',
  'ensure',
  'experience',
  'familiarity',
  'for',
  'from',
  'in',
  'into',
  'is',
  'it',
  'more',
  'of',
  'on',
  'or',
  'the',
  'their',
  'these',
  'this',
  'to',
  'using',
  'with',
]);

const TOOL_KEYWORDS = new Set([
  'airflow',
  'api',
  'apis',
  'aws',
  'azure',
  'bigquery',
  'dbt',
  'dagster',
  'ci/cd',
  'docker',
  'etl',
  'fastapi',
  'gcp',
  'github',
  'gitlab',
  'java',
  'jira',
  'kafka',
  'kubernetes',
  'looker',
  'mysql',
  'nextjs',
  'node',
  'postgres',
  'postgresql',
  'redshift',
  'python',
  'react',
  'redis',
  'snowflake',
  'spark',
  'sql',
  'tableau',
  'terraform',
  'typescript',
  'warehouse',
  'pytorch',
  'scikit-learn',
  'pandas',
  'numpy',
  'matplotlib',
  'gensim',
  'spacy',
  'nlp',
  'classification models',
  'databricks',
  'spark sql',
  'datameer',
  'airflow',
  'postgres',
  'aws',
  'serverless compute',
  'serverless functions',
  'relational databases',
  'jenkins',
  'restful apis',
  'docker',
  'firebase',
  'google cloud',
  'terraform',
  'Tableau', 
  'PowerPoint', 
  'Excel', 
  'Word', 
  'Looker', 
  'Mode Analytics', 
  'QlikView', 
  'Kibana', 
  'Grafana', 
  'Salesforce', 
  'HubSpot', 
  'Marketo', 
  'Google Analytics', 
  'Mixpanel', 
  'Amplitude', 
  'Figma', 
  'Sketch', 
  'Adobe Creative Suite',
  'GitHub', 
  'GitLab', 
  'BitBucket', 
  'SVN', 
  'Jira', 
  'Confluence', 
  'Trello', 
  'Atlassian Suite'

]);

function cleanReportKeyword(keyword: string): string {
  return keyword.trim().toLowerCase().replace(/\s+/g, ' ');
}

function filterReportKeywords(keywords: string[]): string[] {
  const seen = new Set<string>();
  const filtered: string[] = [];

  for (const keyword of keywords) {
    const cleaned = cleanReportKeyword(keyword);
    if (!cleaned || cleaned.length <= 2) {
      continue;
    }
    if (REPORT_STOPWORDS.has(cleaned)) {
      continue;
    }
    if (cleaned.replace(/[\s/-]/g, '') === 'andor') {
      continue;
    }
    if (seen.has(cleaned)) {
      continue;
    }
    seen.add(cleaned);
    filtered.push(cleaned);
  }

  return filtered;
}

function selectSectionTwoSignals(highlights: ReportContent['report_json']['highlights']): string[] {
  const explicitTools = filterReportKeywords(highlights?.tool_keywords || []);
  if (explicitTools.length) {
    return explicitTools.slice(0, 10);
  }

  const commonTools = filterReportKeywords(highlights?.common_tools || []);
  if (commonTools.length) {
    return commonTools.slice(0, 10);
  }

  const postingKeywords = filterReportKeywords(highlights?.posting_keywords || []).filter((keyword) => TOOL_KEYWORDS.has(keyword));
  const matchedKeywords = filterReportKeywords(highlights?.matched_keywords || []).filter((keyword) => TOOL_KEYWORDS.has(keyword));

  const candidates = [...commonTools, ...postingKeywords, ...matchedKeywords];
  const seen = new Set<string>();
  const selected: string[] = [];

  for (const keyword of candidates) {
    if (seen.has(keyword)) {
      continue;
    }
    seen.add(keyword);
    selected.push(keyword);
  }

  return selected.slice(0, 10);
}

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
  role_positioning?: {
    current_resume_read?: string;
    better_fit_roles?: string[];
    pivot_summary?: string;
    pivot_tips?: string[];
  };
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
      tool_keywords?: string[];
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

type RoleGuidance = {
  currentResumeRead: string;
  betterFitRoles: string[];
  pivotSummary: string;
  pivotTips: string[];
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
    guidance: 'Start with the top requirement gaps and add direct, evidence-backed bullets for each one.',
  },
  {
    label: 'Emerging',
    minMatchScore: 0.25,
    minEmbeddingSimilarity: 0.5,
    guidance: 'You have partial overlap. Prioritize requirement language and add measurable outcomes for each missing signal.',
  },
  {
    label: 'Moderate',
    minMatchScore: 0.4,
    minEmbeddingSimilarity: 0.62,
    guidance: 'Good baseline alignment. Tighten phrasing to mirror requirements and deepen proof for your key tools.',
  },
  {
    label: 'Strong',
    minMatchScore: 0.58,
    minEmbeddingSimilarity: 0.74,
    guidance: 'Strong fit. Focus on role-specific tailoring and quantifiable impact to maximize competitiveness.',
  },
];

function toPercent(value: number | undefined): string {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return 'n/a';
  }
  return `${Math.round(value * 100)}%`;
}

function parseRewriteRecommendation(item: string): { before: string; after: string; why: string } | null {
  const match = item.match(/^Rewrite\s+"([\s\S]+?)"\s*->\s*"([\s\S]+?)"\s*\|\s*Why:\s*([\s\S]+)$/i);
  if (!match) {
    return null;
  }

  const [, before, after, why] = match;
  return {
    before: before.trim(),
    after: after.trim(),
    why: why.trim(),
  };
}

function splitRecommendations(items: string[]): {
  rewrites: Array<{ key: string; before: string; after: string; why: string }>;
  others: string[];
} {
  const rewrites: Array<{ key: string; before: string; after: string; why: string }> = [];
  const others: string[] = [];

  for (const item of items) {
    const parsed = parseRewriteRecommendation(item);
    if (parsed) {
      rewrites.push({ key: item, ...parsed });
      continue;
    }
    others.push(item);
  }

  return { rewrites, others };
}

const ROLE_CLUSTERS = [
  {
    label: 'Data Analyst',
    signals: ['sql', 'tableau', 'excel', 'looker', 'powerpoint', 'kpi', 'dashboard', 'analytics', 'stakeholder'],
  },
  {
    label: 'Data Engineer',
    signals: ['airflow', 'dbt', 'spark', 'kafka', 'docker', 'terraform', 'etl', 'pipeline', 'warehouse', 'snowflake'],
  },
  {
    label: 'Analytics Engineer',
    signals: ['dbt', 'sql', 'warehouse', 'snowflake', 'bigquery', 'looker', 'tableau', 'semantic layer'],
  },
  {
    label: 'Machine Learning Analyst',
    signals: ['python', 'pandas', 'numpy', 'scikit-learn', 'nlp', 'classification models', 'ml'],
  },
];

function inferRoleGuidance(content: ReportContent | null): RoleGuidance | null {
  if (!content) {
    return null;
  }

  const highlights = content.report_json.highlights || {};
  const narrative = content.report_json.narrative;
  const rolePositioning = narrative?.role_positioning;
  const llmRoles = filterReportKeywords(rolePositioning?.better_fit_roles || []);
  const llmTips = (rolePositioning?.pivot_tips || []).filter((item) => typeof item === 'string' && item.trim());
  if (rolePositioning?.current_resume_read || llmRoles.length || rolePositioning?.pivot_summary || llmTips.length) {
    return {
      currentResumeRead: rolePositioning?.current_resume_read || 'Your resume currently signals an adjacent role family more clearly than the target postings.',
      betterFitRoles: llmRoles,
      pivotSummary: rolePositioning?.pivot_summary || 'Tighten the narrative around the role family you want, then add stronger evidence for the missing requirements.',
      pivotTips: llmTips,
    };
  }

  const resumeSignals = filterReportKeywords([
    ...(highlights.resume_keywords || []),
    ...(highlights.matched_keywords || []),
  ]);
  const missingSignals = filterReportKeywords(highlights.missing_keywords || []);

  const rankedRoles = ROLE_CLUSTERS.map((cluster) => ({
    label: cluster.label,
    score: cluster.signals.reduce((total, signal) => total + (resumeSignals.includes(signal) ? 1 : 0), 0),
    signals: cluster.signals.filter((signal) => resumeSignals.includes(signal)).slice(0, 3),
  }))
    .filter((cluster) => cluster.score > 0)
    .sort((left, right) => right.score - left.score);

  const primaryRole = rankedRoles[0]?.label || 'analyst-leaning data role';
  const primarySignals = rankedRoles[0]?.signals || resumeSignals.slice(0, 3);
  const betterFitRoles = rankedRoles.slice(0, 3).map((cluster) => cluster.label);
  const gapFocus = missingSignals.slice(0, 3).join(', ');

  return {
    currentResumeRead: primarySignals.length
      ? `Your resume currently reads most clearly as a ${primaryRole} profile because it emphasizes ${primarySignals.join(', ')}.`
      : 'Your resume currently reads closer to an adjacent data role than to the full target role scope in these postings.',
    betterFitRoles,
    pivotSummary: gapFocus
      ? `To move toward the target role family, strengthen evidence around ${gapFocus}. The resume will feel more credible when those signals appear in execution-focused bullets, not just keyword mentions.`
      : 'To deepen fit, make the target role explicit in your summary and add stronger execution evidence around the most important requirements.',
    pivotTips: [
      'Rewrite your summary so it names the role family you want and the business problems you solve.',
      'For each target-role gap, add one bullet with tool, scope, stakeholder context, and a measurable result.',
      'Group adjacent projects so the target role pattern reads consistently across the resume, not as isolated keywords.',
    ],
  };
}

function buildRecommendationMarkup(recommendationSection: RenderSection | undefined, roleGuidance: RoleGuidance | null): string {
  if (!recommendationSection) {
    return '';
  }

  const roleMarkup = roleGuidance
    ? `<section style="margin-top:18px;padding:16px;border-radius:16px;border:1px solid rgba(122,109,86,0.22);background:rgba(255,255,255,0.58);">
        <p style="margin:0 0 10px;font-size:12px;letter-spacing:0.09em;text-transform:uppercase;color:#6a624d;font-weight:600;">Role Positioning</p>
        <p style="margin:0;line-height:1.7;font-size:15px;color:#2a3632;">${roleGuidance.currentResumeRead}</p>
        ${roleGuidance.betterFitRoles.length ? `<p style="margin:12px 0 0;font-size:13px;text-transform:uppercase;letter-spacing:0.08em;color:#5b6662;">Better-fit roles right now</p><p style="margin:8px 0 0;line-height:1.7;font-size:15px;color:#2a3632;">${roleGuidance.betterFitRoles.join(', ')}</p>` : ''}
        <p style="margin:12px 0 0;line-height:1.7;font-size:15px;color:#2a3632;">${roleGuidance.pivotSummary}</p>
        ${roleGuidance.pivotTips.length ? `<ul style="margin:12px 0 0;padding-left:18px;display:grid;gap:8px;color:#2f3f39;font-size:14px;line-height:1.58;">${roleGuidance.pivotTips.map((tip) => `<li>${tip}</li>`).join('')}</ul>` : ''}
      </section>`
    : '';

  const grouped = splitRecommendations(recommendationSection.items || []);

  const itemsMarkup = recommendationSection.items?.length
    ? `<ul style="margin:14px 0 0;padding-left:0;list-style:none;display:grid;gap:10px;">
        ${grouped.rewrites.length ? `<li style="margin:0;padding:12px 14px 12px 18px;border-radius:14px;border:1px solid rgba(29,42,38,0.12);background:rgba(255,255,255,0.7);font-size:15px;line-height:1.58;color:#263330;">
          <p style="margin:0 0 10px;font-size:11px;letter-spacing:0.08em;text-transform:uppercase;color:#5f6f69;font-weight:600;">Rewrite suggestions</p>
          <div style="display:grid;gap:14px;">
            ${grouped.rewrites
              .map((parsed) => `<div style="display:grid;gap:0;">
                <p style="margin:0;display:flex;align-items:flex-start;gap:8px;">
                  <span style="flex:0 0 auto;margin-top:2px;padding:2px 7px;border-radius:999px;border:1px solid rgba(122,109,86,0.28);background:rgba(240,235,226,0.75);color:#554c3f;font-size:11px;letter-spacing:0.06em;text-transform:uppercase;">Current</span>
                  <span style="display:inline-block;padding:4px 8px;border-radius:8px;background:rgba(248,244,236,0.9);border:1px solid rgba(29,42,38,0.09);font-style:italic;color:#364742;">${parsed.before}</span>
                </p>
                <p style="margin:8px 0 0;display:flex;align-items:flex-start;gap:8px;">
                  <span style="flex:0 0 auto;margin-top:2px;padding:2px 7px;border-radius:999px;border:1px solid rgba(72,112,86,0.34);background:rgba(228,242,232,0.88);color:#2f5a43;font-size:11px;letter-spacing:0.06em;text-transform:uppercase;">Updated</span>
                  <span style="display:inline-block;padding:4px 8px;border-radius:8px;background:rgba(235,244,236,0.88);border:1px solid rgba(76,124,92,0.24);color:#1f4933;">${parsed.after}</span>
                </p>
                <p style="margin:10px 0 0;padding-bottom:8px;border-bottom:1px dashed rgba(29,42,38,0.14);font-size:14px;color:#3b4f49;">Why this helps: ${parsed.why}</p>
              </div>`)
              .join('')}
          </div>
        </li>` : ''}
        ${grouped.others
          .map((item) => `<li style="position:relative;margin:0;padding:12px 14px 12px 34px;border-radius:14px;border:1px solid rgba(29,42,38,0.12);background:rgba(255,255,255,0.7);font-size:15px;line-height:1.58;color:#263330;">${item}</li>`)
          .join('')}
      </ul>`
    : recommendationSection.body
      ? `<p style="margin:14px 0 0;line-height:1.7;font-size:15px;color:#35413d;">${recommendationSection.body}</p>`
      : '';

  return `<section style="margin-top:28px;padding:24px;border-radius:24px;border:1px solid rgba(202,167,114,0.45);background:linear-gradient(180deg, rgba(255,244,225,0.9), rgba(255,251,243,0.94));box-shadow:0 18px 40px rgba(202,167,114,0.18);">
    <h2 style="margin:0;font-size:13px;text-transform:uppercase;letter-spacing:0.08em;color:#5b6662;">${recommendationSection.title}</h2>
    ${roleMarkup}
    ${itemsMarkup}
  </section>`;
}

function buildSections(content: ReportContent | null): RenderSection[] {
  if (!content) {
    return [];
  }

  const summary = content.report_json.summary || {};
  const highlights = content.report_json.highlights || {};
  const recommendations = content.report_json.recommendations || [];
  const narrative = content.report_json.narrative;
  const commonTools = selectSectionTwoSignals(highlights);
  const postingKeywords = filterReportKeywords(highlights.posting_keywords || []).slice(0, 10);
  const resumeKeywords = filterReportKeywords(highlights.resume_keywords || []).slice(0, 10);

  const matched = filterReportKeywords(highlights.matched_keywords || []).slice(0, 12);
  const missing = filterReportKeywords(highlights.missing_keywords || []).slice(0, 12);

  const topPostingSignals = commonTools.length ? commonTools : filterReportKeywords([...postingKeywords, ...matched]).filter((keyword) => TOOL_KEYWORDS.has(keyword)).slice(0, 10);
  const differentiators = matched.length ? matched : resumeKeywords.slice(0, 8);

  const experienceNote =
    narrative?.resume_experience_level && narrative?.posting_experience_level
      ? ` Your resume signals a ${narrative.resume_experience_level}-level candidate; these postings target ${narrative.posting_experience_level}-level.`
      : '';

  const matchScore = typeof summary.match_score === 'number' ? summary.match_score : 0;
  const embeddingSimilarity = typeof summary.embedding_similarity === 'number' ? summary.embedding_similarity : 0;

  const overviewText =
    narrative?.overview ||
    `Overall fit currently reads as ${summary.fit_label || 'n/a'}, with a match score of ${toPercent(summary.match_score)} and an alignment similarity of ${toPercent(summary.embedding_similarity)}.${differentiators.length ? ` The strongest overlap appears in ${differentiators.slice(0, 6).join(', ')}.` : ''}${experienceNote}`;

  const alignmentSummary = `${overviewText}\n\n${buildSignalInterpretation(matchScore, embeddingSimilarity)}`;

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

function getFitScores(content: ReportContent | null): { matchScore: number; embeddingSimilarity: number } {
  const summary = content?.report_json.summary || {};
  return {
    matchScore: typeof summary.match_score === 'number' ? summary.match_score : 0,
    embeddingSimilarity: typeof summary.embedding_similarity === 'number' ? summary.embedding_similarity : 0,
  };
}

function getBandForMetric(value: number, metric: 'minMatchScore' | 'minEmbeddingSimilarity'): FitBand {
  for (let i = FIT_BANDS.length - 1; i >= 0; i -= 1) {
    const band = FIT_BANDS[i];
    if (value >= band[metric]) {
      return band;
    }
  }
  return FIT_BANDS[0];
}

function buildLegendGuidance(
  activeBand: FitBand,
  nextBand: FitBand | null,
  scores: { matchScore: number; embeddingSimilarity: number },
): string {
  if (!nextBand) {
    return 'You are already at the top band; focus on role-by-role tailoring to stay strong.';
  }

  const neededMatch = Math.max(0, nextBand.minMatchScore - scores.matchScore);
  const neededEmbedding = Math.max(0, nextBand.minEmbeddingSimilarity - scores.embeddingSimilarity);

  if (neededMatch > 0 && neededEmbedding > 0) {
    return `To reach ${nextBand.label}, aim for roughly ${Math.round(nextBand.minMatchScore * 100)}%+ Match Score and ${Math.round(nextBand.minEmbeddingSimilarity * 100)}%+ Alignment Similarity.`;
  }

  if (neededMatch > 0) {
    return `You already meet the ${nextBand.label} Alignment Similarity threshold. To reach ${nextBand.label} overall, raise Match Score from ${Math.round(scores.matchScore * 100)}% to about ${Math.round(nextBand.minMatchScore * 100)}%+ by aligning more exact requirement language.`;
  }

  if (neededEmbedding > 0) {
    return `You already meet the ${nextBand.label} Match Score threshold. To reach ${nextBand.label} overall, raise Alignment Similarity from ${Math.round(scores.embeddingSimilarity * 100)}% to about ${Math.round(nextBand.minEmbeddingSimilarity * 100)}%+ by expanding role-context evidence around your existing skills and tools.`;
  }

  return `${activeBand.guidance}`;
}

function buildSignalInterpretation(matchScore: number, embeddingSimilarity: number): string {
  const highMatch = matchScore >= 0.4;
  const highSimilarity = embeddingSimilarity >= 0.55;
  const lowMatch = matchScore < 0.25;
  const lowSimilarity = embeddingSimilarity < 0.35;

  const matchPct = Math.round(matchScore * 100);
  const simPct = Math.round(embeddingSimilarity * 100);

  if (lowMatch && highSimilarity) {
    return `A ${matchPct}% Match Score alongside ${simPct}% Alignment Similarity suggests your experience context is close, but explicit requirement-language coverage is still thin. Review missing keywords and mirror exact requirement phrasing where it genuinely matches your background.`;
  }
  if (highMatch && highSimilarity) {
    return `A ${matchPct}% Match Score and ${simPct}% Alignment Similarity is a strong result. You are matching both explicit requirements and broader role context. Focus on impact depth and quantified outcomes instead of adding more keywords.`;
  }
  if (highMatch && lowSimilarity) {
    return `A ${matchPct}% Match Score with only ${simPct}% Alignment Similarity means you hit many required terms, but supporting context is thin. Add stronger role-specific examples around those keywords to improve credibility.`;
  }
  if (lowMatch && lowSimilarity) {
    return `A ${matchPct}% Match Score and ${simPct}% Alignment Similarity indicates limited overlap in both requirements and context. Start with the highest-value missing requirements and add direct project evidence for each.`;
  }
  // Moderate zone
  if (matchScore >= 0.25 && embeddingSimilarity >= 0.35) {
    return `A ${matchPct}% Match Score and ${simPct}% Alignment Similarity shows reasonable alignment. Prioritize missing high-signal requirements and strengthen each with tool + scope + metric evidence.`;
  }
  return `Match Score: ${matchPct}%, Alignment Similarity: ${simPct}%. Review the missing keywords and Fit Legend below for guidance on where to focus.`;
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
        <p style="margin:0 0 4px;font-size:11px;text-transform:uppercase;letter-spacing:0.08em;color:#5b6662;">Alignment Similarity</p>
        <p style="margin:0;font-size:28px;font-weight:700;">${embeddingSimilarity}</p>
      </div>
    </div>`;

  const sections = buildSections(content);
  const roleGuidance = inferRoleGuidance(content);
  const recommendationSection = sections.find((section) => section.title === 'Recommended Next Steps');
  const coreSections = sections.filter((section) => section.title !== 'Recommended Next Steps');
  const sectionMarkup = coreSections
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
  const recommendationMarkup = buildRecommendationMarkup(recommendationSection, roleGuidance);

  const humanStatus = formatPipelineStatus(content.status, content.stage);

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
    <p style="margin:0;color:#5b6662;font-size:13px;">Report ID: ${content.job_id} &nbsp;·&nbsp; ${humanStatus}</p>
  </div>
  ${metricsMarkup}
  ${sectionMarkup}
  ${recommendationMarkup}
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
        const response = await authenticatedApiFetch(`/report/${encodeURIComponent(activeJobId)}/content`);
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
  const fitScores = getFitScores(reportContent);
  const reportSummary = buildSummary(reportContent);
  const activeFitBand = getActiveFitBand(reportContent);
  const nextFitBand = getNextFitBand(activeFitBand);
  const matchBand = getBandForMetric(fitScores.matchScore, 'minMatchScore');
  const embeddingBand = getBandForMetric(fitScores.embeddingSimilarity, 'minEmbeddingSimilarity');
  const legendGuidance = buildLegendGuidance(activeFitBand, nextFitBand, fitScores);
  const recommendationSection = reportSections.find((section) => section.title === 'Recommended Next Steps');
  const coreSections = reportSections.filter((section) => section.title !== 'Recommended Next Steps');
  const roleGuidance = inferRoleGuidance(reportContent);
  const groupedRecommendations = splitRecommendations(recommendationSection?.items || []);

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
                ? formatPipelineStatus(reportContent.status, reportContent.stage)
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
              <p>Alignment Similarity</p>
              <strong>{reportSummary.embeddingSimilarity}</strong>
              <span>Blended similarity across requirement language and tool overlap.</span>
            </article>
          </div>
          <div className="report-fit-legend" aria-label="Fit scoring legend">
            <div className="report-fit-legend__header">
              <p className="eyebrow">Fit Legend</p>
              <div className="report-fit-legend__summary-row">
                <p>
                  Fit Level combines Match Score + Alignment Similarity.
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
                <div className="report-fit-legend__axis" aria-label="Per-metric fit tracks">
                  <p className="report-fit-legend__axis-item">
                    <span className="report-fit-legend__axis-label">Keyword Track</span>
                    <strong>{matchBand.label}</strong>
                    <span>{Math.round(fitScores.matchScore * 100)}%</span>
                  </p>
                  <p className="report-fit-legend__axis-item">
                    <span className="report-fit-legend__axis-label">Alignment Track</span>
                    <strong>{embeddingBand.label}</strong>
                    <span>{Math.round(fitScores.embeddingSimilarity * 100)}%</span>
                  </p>
                </div>
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
                          <span>Alignment Similarity:</span>
                          <span>{Math.round(band.minEmbeddingSimilarity * 100)}%+</span>
                        </p>
                      </article>
                    );
                  })}
                </div>
                <p className="report-fit-legend__guidance">
                  <strong>Current:</strong> {activeFitBand.label}. {activeFitBand.guidance}{' '}
                  {legendGuidance}
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
                {section.body
                  ? section.body.split('\n\n').map((paragraph, i) => (
                      <p key={i} className={i === 0 ? 'report-card__body report-card__body--lede' : 'report-card__body'}>{paragraph}</p>
                    ))
                  : null}
              </article>
            ))}
          </div>

          {recommendationSection ? (
            <article className="report-conclusion">
              <p className="eyebrow report-card__label">Conclusion</p>
              <h2 className="report-card__title report-card__title--conclusion">{recommendationSection.title}</h2>
              {roleGuidance ? (
                <section className="report-role-guidance">
                  <p className="report-role-guidance__eyebrow">Role Positioning</p>
                  <p className="report-role-guidance__lead">{roleGuidance.currentResumeRead}</p>
                  {roleGuidance.betterFitRoles.length ? (
                    <div className="report-role-guidance__roles">
                      {roleGuidance.betterFitRoles.map((role) => (
                        <span key={role} className="report-role-guidance__role">{role}</span>
                      ))}
                    </div>
                  ) : null}
                  <p className="report-role-guidance__summary">{roleGuidance.pivotSummary}</p>
                  {roleGuidance.pivotTips.length ? (
                    <ul className="report-role-guidance__tips">
                      {roleGuidance.pivotTips.map((tip) => (
                        <li key={tip}>{tip}</li>
                      ))}
                    </ul>
                  ) : null}
                </section>
              ) : null}
              {recommendationSection.items?.length ? (
                <ul className="report-recommendations">
                  {groupedRecommendations.rewrites.length ? (
                    <li className="report-recommendation report-recommendation--rewrite">
                      <p className="report-recommendation__label">Rewrite suggestions</p>
                      <div className="report-recommendation__group">
                        {groupedRecommendations.rewrites.map((parsed) => (
                          <div key={parsed.key} className="report-recommendation__entry">
                            <p className="report-recommendation__line">
                              <span className="report-recommendation__tag">Current</span>
                              <span className="report-recommendation__quote">{parsed.before}</span>
                            </p>
                            <p className="report-recommendation__line">
                              <span className="report-recommendation__tag report-recommendation__tag--next">Updated</span>
                              <span className="report-recommendation__quote report-recommendation__quote--after">{parsed.after}</span>
                            </p>
                            <p className="report-recommendation__why">Why this helps: {parsed.why}</p>
                          </div>
                        ))}
                      </div>
                    </li>
                  ) : null}
                  {groupedRecommendations.others.map((item) => (
                    <li key={item} className="report-recommendation">{item}</li>
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
        <Link href="/resume" className="button button--ghost">
          Back
        </Link>
        <Link href="/postings" className="button button--secondary">
          Start another Revue
        </Link>
      </div>
    </StepShell>
  );
}