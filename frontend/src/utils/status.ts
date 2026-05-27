type StatusKey = string;
type StageKey = string;

const STATUS_LABELS: Record<StatusKey, string> = {
  awaiting_resume: 'Waiting for resume upload',
  queued_for_processing: 'Queued for analysis',
  processing: 'Analyzing your resume and postings',
  completed: 'Report ready',
  failed: 'Processing failed',
};

const STAGE_LABELS: Record<StageKey, string> = {
  postings_stored: 'Job postings saved',
  resume_stored: 'Resume received',
  extracting_resume_text: 'Reading resume text',
  loading_postings: 'Loading job postings',
  cleaning_text: 'Cleaning and normalizing text',
  extracting_resume_features: 'Extracting resume signals',
  comparing_requirements: 'Comparing requirements',
  generating_embeddings: 'Evaluating semantic alignment',
  generating_report: 'Composing final report',
  report_ready: 'Finalizing output',
};

function toHumanLabel(raw: string) {
  return raw
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

export function formatPipelineStatus(status: string, stage: string) {
  const statusLabel = STATUS_LABELS[status] || toHumanLabel(status);
  const stageLabel = STAGE_LABELS[stage] || toHumanLabel(stage);

  // Avoid noisy duplication when both labels convey the same idea.
  if (statusLabel.toLowerCase() === stageLabel.toLowerCase()) {
    return statusLabel;
  }

  return `${statusLabel} - ${stageLabel}`;
}

export function formatPipelineStage(stage: string) {
  return STAGE_LABELS[stage] || toHumanLabel(stage);
}
