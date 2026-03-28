import Link from 'next/link';

type ProgressStep = {
  label: string;
  detail: string;
  href: string;
};

type ProgressRailProps = {
  current: number;
};

const steps: ProgressStep[] = [
  {
    label: '01. Add role signals',
    detail: 'Collect job postings so the report can compare common requirements.',
    href: '/postings',
  },
  {
    label: '02. Upload resume',
    detail: 'Bring in your current story before the analysis starts.',
    href: '/resume',
  },
  {
    label: '03. Review the report',
    detail: 'Read the editorial summary, gaps, and interview preparation cues.',
    href: '/report',
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
            <li
              key={step.label}
              className={`progress-rail__item progress-rail__item--section-${index + 1} progress-rail__item--${state}`}
            >
              <Link href={step.href} className="progress-rail__link">
                <strong>{step.label}</strong>
                <span>{step.detail}</span>
              </Link>
            </li>
          );
        })}
      </ol>
    </aside>
  );
}