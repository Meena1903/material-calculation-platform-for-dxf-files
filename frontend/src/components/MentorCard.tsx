import { Mentor } from '../lib/api';
import { Star, Users } from 'lucide-react';

interface Props {
  mentor: Mentor;
}

export default function MentorCard({ mentor }: Props) {
  return (
    <article className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <h3 className="card-title">{mentor.full_name}</h3>
        {mentor.score != null && <span className="score-badge">{(mentor.score * 100).toFixed(0)}%</span>}
      </div>
      <div className="card-meta">
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
          <Star size={13} color="#fbbf24" /> {mentor.rating.toFixed(1)}
        </span>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
          <Users size={13} /> {mentor.mentees_helped} mentees
        </span>
        <span className="tag">{mentor.availability}</span>
      </div>
      <p className="card-desc">{mentor.bio || 'No bio yet.'}</p>
      <div className="tags">
        {mentor.skills.map((s) => (
          <span key={s.id} className="tag">
            {s.name}
          </span>
        ))}
      </div>
      {mentor.hourly_rate && (
        <div className="card-meta" style={{ marginTop: 10 }}>
          ${mentor.hourly_rate}/hr
        </div>
      )}
    </article>
  );
}
