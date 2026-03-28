type ReportSectionProps = {
  title: string;
  body: string;
};

export function ReportSection({ title, body }: ReportSectionProps) {
  return (
    <article className="report-card">
      <p className="eyebrow">Section</p>
      <h2>{title}</h2>
      <p>{body}</p>
    </article>
  );
}