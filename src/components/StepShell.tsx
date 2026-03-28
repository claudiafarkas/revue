import type { PropsWithChildren, ReactNode } from 'react';
import { ProgressRail } from './ProgressRail';

type StepShellProps = PropsWithChildren<{
  stepIndex: number;
  eyebrow: string;
  title: string;
  description: string;
  aside?: ReactNode;
}>;

export function StepShell({
  stepIndex,
  eyebrow,
  title,
  description,
  aside,
  children,
}: StepShellProps) {
  return (
    <section className="step-layout">
      <div className="step-layout__main">
        <div className="page-heading">
          <p className="eyebrow">{eyebrow}</p>
          <h1>{title}</h1>
          <p className="lede">{description}</p>
        </div>
        {children}
      </div>

      <div className="step-layout__aside">
        {aside}
        <ProgressRail current={stepIndex} />
      </div>
    </section>
  );
}