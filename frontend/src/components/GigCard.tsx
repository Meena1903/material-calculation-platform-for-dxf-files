import { Gig, logInteraction } from '../lib/api';
import { DollarSign, Clock, Eye, Send } from 'lucide-react';

interface Props {
  gig: Gig;
  onApplied?: () => void;
}

export default function GigCard({ gig, onApplied }: Props) {
  const budget =
    gig.budget_min && gig.budget_max
      ? `$${gig.budget_min.toLocaleString()} – $${gig.budget_max.toLocaleString()}`
      : 'Budget TBD';

  const handleApply = async () => {
    try {
      await logInteraction('gig', gig.id, 'apply');
      onApplied?.();
      alert('Application recorded (POC)');
    } catch {
      alert('Could not record interaction');
    }
  };

  return (
    <article className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
        <h3 className="card-title">{gig.title}</h3>
        {gig.score != null && <span className="score-badge">{(gig.score * 100).toFixed(0)}%</span>}
      </div>
      <div className="card-meta">
        <span>{gig.company.name}</span>
        {gig.company.is_verified && <span className="tag verified">Verified</span>}
        {gig.is_boosted && <span className="tag boosted">Boosted</span>}
      </div>
      <p className="card-desc">{gig.description}</p>
      <div className="tags" style={{ marginBottom: 12 }}>
        {gig.skills.slice(0, 5).map((s) => (
          <span key={s.id} className="tag">
            {s.name}
          </span>
        ))}
      </div>
      <div className="card-meta">
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
          <DollarSign size={13} /> {budget}
        </span>
        {gig.duration_days && (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
            <Clock size={13} /> {gig.duration_days}d
          </span>
        )}
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
          <Eye size={13} /> {gig.views}
        </span>
      </div>
      <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
        <button className="btn btn-primary btn-sm" onClick={handleApply}>
          <Send size={13} /> Apply
        </button>
      </div>
    </article>
  );
}
