import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <section className="not-found-panel">
      <p className="eyebrow">Not Found</p>
      <h1>This page is not part of the current issue.</h1>
      <p>Return to the home page to continue through the Revue.ai prototype flow.</p>
      <Link to="/" className="button button--primary">
        Go home
      </Link>
    </section>
  );
}