import { useEffect, useState } from 'react';
import { getFeed, RankedFeed } from '../lib/api';
import { useAuth } from '../lib/auth';
import GigCard from '../components/GigCard';
import MentorCard from '../components/MentorCard';
import { Link } from 'react-router-dom';

export default function Feed() {
  const { user } = useAuth();
  const [feed, setFeed] = useState<RankedFeed | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getFeed()
      .then(setFeed)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="spinner" />;
  if (!feed) return <div className="empty-state">Could not load feed.</div>;

  return (
    <>
      <div className="hero">
        <h1>Hi, {user?.full_name?.split(' ')[0] || 'there'}</h1>
        <p>
          Ranked opportunities based on your skills. Scores combine relevance, trust, freshness &amp;
          engagement (pure Python ranking).
        </p>
      </div>

      <section style={{ marginBottom: '2rem' }}>
        <div className="section-header">
          <h2>Recommended gigs</h2>
          <Link to="/gigs" className="btn btn-ghost btn-sm">
            View all
          </Link>
        </div>
        <div className="grid grid-2">
          {feed.gigs.slice(0, 6).map((g) => (
            <GigCard key={g.id} gig={g} />
          ))}
        </div>
      </section>

      <section style={{ marginBottom: '2rem' }}>
        <div className="section-header">
          <h2>Mentors for you</h2>
          <Link to="/mentors" className="btn btn-ghost btn-sm">
            View all
          </Link>
        </div>
        <div className="grid grid-3">
          {feed.mentors.map((m) => (
            <MentorCard key={m.id} mentor={m} />
          ))}
        </div>
      </section>

      <section>
        <div className="section-header">
          <h2>Companies</h2>
        </div>
        <div className="grid grid-3">
          {feed.companies.map((c) => (
            <div key={c.id} className="card">
              <h3 className="card-title">{c.name}</h3>
              <div className="card-meta">
                {c.is_verified && <span className="tag verified">Verified</span>}
                <span>Trust {(c.trust_score * 100).toFixed(0)}%</span>
              </div>
              <p className="card-desc">{c.description || ''}</p>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
