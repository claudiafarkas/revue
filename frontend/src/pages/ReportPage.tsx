import Link from 'next/link';
import { StepShell } from '../components/StepShell';

const reportSections = [
  {
    title: 'Common Requirements',
    body: 'Across the sample postings, communication, project ownership, strategic prioritization, and measurable outcomes appear most often.',
  },
  {
    title: 'Resume Alignment',
    body: 'The current resume suggests solid delivery experience and cross-functional collaboration, with room to sharpen impact statements and scope.',
  },
  {
    title: 'Gaps',
    body: 'Leadership metrics, repeated evidence of stakeholder influence, and tool-specific depth are the clearest missing signals.',
  },
  {
    title: 'Learning Priorities',
    body: 'Prioritize evidence-based storytelling, interview-ready case examples, and domain fluency for the roles you selected.',
  },
  {
    title: 'Career Path Fit',
    body: 'The direction appears strongest for roles that blend writing, systems thinking, and collaborative execution over narrowly technical specialization.',
  },
  {
    title: 'Suggested Interview Questions',
    body: 'Expect questions about cross-functional tradeoffs, ownership without authority, and how you measure the quality of your decisions.',
  },
];

export function ReportPage() {
  return (
    <StepShell
      stepIndex={3}
      eyebrow="Step 4"
      title="Your Revue Report"
      description="This page previews the final report structure and tone. The backend will eventually serve a generated PDF and store it in cloud storage."
      aside={
        <div className="info-panel">
          <p className="eyebrow">Behind the scenes</p>
          <p>The final generated PDF will be served by the backend and retrieved from cloud storage.</p>
        </div>
      }
    >
      <div className="report-toolbar">
        <button type="button" className="button button--primary" onClick={() => window.print()}>
          Download PDF
        </button>
        <p>Prototype behavior: this currently opens the browser print dialog so the UI can be reviewed without backend generation.</p>
      </div>

      <div className="report-grid">
        {reportSections.map((section) => (
          <article key={section.title} className="report-card">
            <p className="eyebrow">Section</p>
            <h2>{section.title}</h2>
            <p>{section.body}</p>
          </article>
        ))}
      </div>

      <div className="form-actions form-actions--split">
        <Link href="/processing" className="button button--ghost">
          Back
        </Link>
        <Link href="/postings" className="button button--secondary">
          Start another Revue
        </Link>
      </div>
    </StepShell>
  );
}