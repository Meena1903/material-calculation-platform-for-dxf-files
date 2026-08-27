import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getSkills, updateSkills, Skill } from '../lib/api';
import { useAuth } from '../lib/auth';

export default function Onboarding() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const { refresh } = useAuth();
  const nav = useNavigate();

  useEffect(() => {
    getSkills()
      .then(setSkills)
      .finally(() => setLoading(false));
  }, []);

  const toggle = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else if (next.size < 8) next.add(id);
      return next;
    });
  };

  const save = async () => {
    if (selected.size < 3) {
      alert('Pick at least 3 skills');
      return;
    }
    setSaving(true);
    try {
      await updateSkills(Array.from(selected));
      await refresh();
      nav('/');
    } catch {
      alert('Could not save skills');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="spinner" />;

  return (
    <div style={{ maxWidth: 640, margin: '0 auto' }}>
      <div className="hero">
        <h1>What are your skills?</h1>
        <p>Select 3–8 skills from the taxonomy. This seeds your long-term vector for ranking.</p>
      </div>
      <div className="card">
        <div className="skills-grid">
          {skills.map((s) => (
            <button
              key={s.id}
              type="button"
              className={`skill-chip ${selected.has(s.id) ? 'selected' : ''}`}
              onClick={() => toggle(s.id)}
            >
              {s.name}
            </button>
          ))}
        </div>
        <div style={{ marginTop: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            {selected.size} selected
          </span>
          <button className="btn btn-primary" onClick={save} disabled={saving}>
            {saving ? 'Saving…' : 'Continue to feed'}
          </button>
        </div>
      </div>
    </div>
  );
}
