type ProgressIndicatorProps = {
  value: number;
};

export function ProgressIndicator({ value }: ProgressIndicatorProps) {
  return (
    <div className="progress-meter" aria-hidden="true">
      <div className="progress-meter__fill" style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
    </div>
  );
}