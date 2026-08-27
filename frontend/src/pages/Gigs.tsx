import { useEffect, useState } from 'react';
import { getGigs, Gig } from '../lib/api';
import GigCard from '../components/GigCard';

export default function Gigs() {
  const [gigs, setGigs] = useState<Gig[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getGigs()
      .then(setGigs)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="spinner" />;

  return (
    <>
      <div className="hero">
        <h1>Gigs</h1>
        <p>Ranked by skill relevance, company trust, freshness and engagement quality.</p>
      </div>
      <div className="grid grid-2">
        {gigs.map((g) => (
          <GigCard key={g.id} gig={g} />
        ))}
      </div>
    </>
  );
}
