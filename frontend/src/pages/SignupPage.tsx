import Link from 'next/link';
import { useRouter } from 'next/router';
import { useEffect, useMemo, useState } from 'react';
import { useAuth } from '../context/AuthContext';

export function SignupPage() {
  const router = useRouter();
  const { user, loading, signUpWithEmail } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const nextPath = useMemo(() => {
    if (typeof router.query.next === 'string' && router.query.next.trim()) {
      return `/${router.query.next.replace(/^\/+/, '')}`;
    }

    return '/postings';
  }, [router.query.next]);

  useEffect(() => {
    if (loading || !user) {
      return;
    }

    void router.replace(nextPath);
  }, [loading, user, router, nextPath]);

  async function handleEmailSignup() {
    setError('');

    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setIsSubmitting(true);

    try {
      await signUpWithEmail(email.trim(), password);
      await router.replace(nextPath);
    } catch (signUpError) {
      const message = signUpError instanceof Error ? signUpError.message : 'Unable to create your account right now.';
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="auth-layout">
      <aside className="auth-layout__brand">
        <p className="eyebrow">Get started</p>
        <h1>Hello Revue.ai!</h1>
        <p>
          Build a stronger application story by mapping your resume directly to the real language employers use.
        </p>
      </aside>

      <div className="auth-layout__form-shell">
        <div className="auth-card">
          <div className="auth-card__header">
            <p className="eyebrow">Account</p>
            <h2>Create account</h2>
            <p>Set up your workspace and start analyzing.</p>
          </div>

          <div className="auth-card__fields">
            <label className="auth-field">
              <span>Email</span>
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
              />
            </label>

            <label className="auth-field">
              <span>Password</span>
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="At least 8 characters"
                autoComplete="new-password"
              />
            </label>

            <label className="auth-field">
              <span>Confirm password</span>
              <input
                type="password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                placeholder="Re-enter your password"
                autoComplete="new-password"
              />
            </label>

            {error ? <p className="auth-card__error">{error}</p> : null}
          </div>

          <div className="auth-card__actions">
            <button type="button" className="button button--primary auth-card__button" onClick={handleEmailSignup} disabled={isSubmitting}>
              {isSubmitting ? 'Creating account...' : 'Create account'}
            </button>
          </div>

          <p className="auth-card__switch">
            Already have an account? <Link href="/login">Sign in</Link>
          </p>
        </div>
      </div>
    </section>
  );
}
