import Link from 'next/link';
import { useRouter } from 'next/router';
import { useEffect, useMemo, useState } from 'react';
import { useAuth } from '../context/AuthContext';

export function LoginPage() {
  const router = useRouter();
  const { user, loading, signInWithEmail } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
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

  async function handleEmailLogin() {
    setError('');
    setIsSubmitting(true);

    try {
      await signInWithEmail(email.trim(), password);
      await router.replace(nextPath);
    } catch (signInError) {
      const message = signInError instanceof Error ? signInError.message : 'Unable to sign in right now.';
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="auth-layout">
      <aside className="auth-layout__brand">
        <p className="eyebrow">Welcome back</p>
        <h1>Hello Revue.ai!</h1>
        <p>
          Turn scattered job descriptions and one resume into a clean, practical action plan in minutes.
        </p>
      </aside>

      <div className="auth-layout__form-shell">
        <div className="auth-card">
          <div className="auth-card__header">
            <p className="eyebrow">Account</p>
            <h2>Sign in</h2>
            <p>Continue where you left off.</p>
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
                placeholder="Enter your password"
                autoComplete="current-password"
              />
            </label>

            {error ? <p className="auth-card__error">{error}</p> : null}
          </div>

          <div className="auth-card__actions">
            <button type="button" className="button button--primary auth-card__button" onClick={handleEmailLogin} disabled={isSubmitting}>
              {isSubmitting ? 'Signing in...' : 'Sign In'}
            </button>
          </div>

          <p className="auth-card__switch">
            Need an account? <Link href="/signup">Create account</Link>
          </p>
        </div>
      </div>
    </section>
  );
}
