import Link from 'next/link';

export function NotFoundPage() {
  return (
    <section className="not-found-panel">
      <p className="eyebrow">Not Found</p>
      <h1>This page is not part of the current issue.</h1>
      <p>Return to the home page to continue through the Revue.ai prototype flow.</p>
      <Link href="/" className="button button--primary">
        Go home
      </Link>
    </section>
  );
}