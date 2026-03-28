type ProgressStep = {
  label: string;
  detail: string;
};

type ProgressRailProps = {
  current: number;
};

const steps: ProgressStep[] = [
  {
    label: '01. Introduce the workflow',
    detail: 'See the process, value, and tone before you begin.',
  },
  {
    label: '02. Add role signals',
    detail: 'Collect job postings so the report can compare common requirements.',
  },
  {
    label: '03. Upload resume',
    detail: 'Bring in your current story before the analysis starts.',
  },
  {
    label: '04. Review the report',
    detail: 'Read the editorial summary, gaps, and interview preparation cues.',
  },
];

export function ProgressRail({ current }: ProgressRailProps) {
  return (
    <aside className="progress-rail" aria-label="Workflow progress">
      <p className="eyebrow">Workflow</p>
      <ol className="progress-rail__list">
        {steps.map((step, index) => {
          const state = index < current ? 'done' : index === current ? 'current' : 'upcoming';

          return (
            <li key={step.label} className={`progress-rail__item progress-rail__item--${state}`}>
              <strong>{step.label}</strong>
              <span>{step.detail}</span>
            </li>
          );
        })}
      </ol>
    </aside>
  );
}