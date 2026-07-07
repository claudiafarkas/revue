import Link from 'next/link';
import { useRouter } from 'next/router';
import { useEffect } from 'react';
import { StepShell } from '../components/StepShell';
import { useAuth } from '../context/AuthContext';

export function AccountPage() {
  const router = useRouter();
  const { user, loading, signOutUser } = useAuth();

  useEffect(() => {
    if (loading) {
      return;
    }

    if (!user) {
      void router.replace('/login?next=account');
    }
  }, [loading, user, router]);

  if (loading || !user) {
    return (
      <StepShell
        stepIndex={0}
        eyebrow="Account"
        title="Loading account"
        description="Checking your secure session."
      >
        <section className="form-panel auth-panel">
          <p className="field-group__message">Please wait...</p>
        </section>
      </StepShell>
    );
  }

  return (
    <StepShell
      stepIndex={0}
      eyebrow="Account"
      title="Your account"
      description="Placeholder account page for profile and subscription details."
      aside={
        <div className="info-panel">
          <p className="eyebrow">Coming next</p>
          <p>Plan management, usage credits, billing, and account settings.</p>
        </div>
      }
    >
      <section className="form-panel auth-panel">
        <div className="field-group">
          <span className="field-group__label">Email</span>
          <p>{user.email || 'No email available'}</p>
        </div>

        <div className="field-group">
          <span className="field-group__label">User ID</span>
          <p>{user.uid}</p>
        </div>

        <div className="field-group">
          <span className="field-group__label">Plan</span>
          <p>Starter (placeholder)</p>
        </div>

        <div className="form-actions auth-panel__actions">
          <Link href="/postings" className="button button--secondary">
            Continue workflow
          </Link>
          <button
            type="button"
            className="button button--ghost"
            onClick={async () => {
              await signOutUser();
              await router.replace('/login');
            }}
          >
            Sign out
          </button>
        </div>
      </section>
    </StepShell>
  );
}
