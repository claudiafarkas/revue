import { Link } from 'react-router-dom';

const workflow = [
  'Add job postings',
  'Upload your resume',
  'Get your personalized Revue Report',
];

const values = [
  'Identify common requirements',
  'See how your resume aligns',
  'Discover gaps and learning priorities',
  'Prepare for interviews with clarity',
];

export function HomePage() {
  return (
    <div className="home-stack">
      <section className="hero-panel">
        <div className="hero-panel__copy">
          <p className="eyebrow">Career Review System</p>
          <h1>Your Career, Thoughtfully Reviewed.</h1>
          <p className="lede">
            Revue.ai turns scattered job descriptions and one resume into a calm,
            structured editorial report you can actually use.
          </p>

          <div className="hero-panel__actions">
            <Link to="/postings" className="button button--primary">
              Start Your Revue
            </Link>
            <a href="#how-it-works" className="button button--secondary">
              Explore the flow
            </a>
          </div>
        </div>

        <div className="hero-panel__feature-card">
          <p className="eyebrow">Editorial Snapshot</p>
          <div className="feature-card__row">
            <span>Common requirements</span>
            <strong>Communication, systems thinking, product intuition</strong>
          </div>
          <div className="feature-card__row">
            <span>Resume alignment</span>
            <strong>Strong on execution, lighter on quantifiable leadership</strong>
          </div>
          <div className="feature-card__row">
            <span>Interview focus</span>
            <strong>Metrics, scope, and cross-functional influence</strong>
          </div>
        </div>
      </section>

      <section className="magazine-grid" id="how-it-works">
        <div className="section-intro">
          <p className="eyebrow">How It Works</p>
          <h2>A measured, four-page flow</h2>
        </div>
        <div className="card-grid card-grid--three">
          {workflow.map((item, index) => (
            <article key={item} className="editorial-card">
              <p className="editorial-card__index">0{index + 1}</p>
              <h3>{item}</h3>
              <p>
                {index === 0 && 'Bring in target roles so Revue can identify what employers repeat.'}
                {index === 1 && 'Upload your resume as a PDF and set the review in motion.'}
                {index === 2 && 'Receive a structured report that highlights fit, gaps, and priorities.'}
              </p>
            </article>
          ))}
        </div>
      </section>

      <section className="magazine-grid">
        <div className="section-intro">
          <p className="eyebrow">Value Proposition</p>
          <h2>Designed for clarity, not overwhelm</h2>
        </div>
        <div className="value-list">
          {values.map((item) => (
            <div key={item} className="value-list__item">
              <span className="value-list__marker" aria-hidden="true" />
              <p>{item}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}