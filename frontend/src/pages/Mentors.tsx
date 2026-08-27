import { useEffect, useState } from 'react';
import { getMentors, Mentor } from '../lib/api';
import MentorCard from '../components/MentorCard';

export default function Mentors() {
  const [mentors, setMentors] = useState<Mentor[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMentors()
      .then(setMentors)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="spinner" />;

  return (
    <>
      <div className="hero">
        <h1>Mentors</h1>
        <p>Matched by skill overlap and authority (mentees helped × rating).</p>
      </div>
      <div className="grid grid-3">
        {mentors.map((m) => (
          <MentorCard key={m.id} mentor={m} />
        ))}
      </div>
    </>
  );
}
