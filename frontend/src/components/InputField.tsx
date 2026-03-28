import type { PropsWithChildren } from 'react';

type InputFieldProps = PropsWithChildren<{
  label: string;
  hint?: string;
  error?: string;
}>;

export function InputField({ label, hint, error, children }: InputFieldProps) {
  return (
    <label className="field-group">
      <span className="field-group__label">{label}</span>
      {children}
      <span className={error ? 'field-group__message field-group__message--error' : 'field-group__message'}>
        {error || hint || ''}
      </span>
    </label>
  );
}