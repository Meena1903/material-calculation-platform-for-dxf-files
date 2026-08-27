import { useEffect, useState } from 'react';
import { getSkills, updateSkills, Skill } from '../lib/api';
import { useAuth } from '../lib/auth';

export default function Profile() {
  const { user, refresh } = useAuth();
  const [skills, setSkills] = useState<Skill[]>([]);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getSkills().then(setSkills);
  }, []);

  useEffect(() => {
    if (user?.skills) {
      setSelected(new Set(user.skills.map((s) => s.id)));
    }
  }, [user]);

  const toggle = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const save = async () => {
    setSaving(true);
    try {
      await updateSkills(Array.from(selected));
      await refresh();
      alert('Skills updated');
    } catch {
      alert('Failed to update');
    } finally {
      setSaving(false);
    }
  };

  if (!user) return null;

  return (
    <>
      <div className="hero">
        <h1>{user.full_name}</h1>
        <p>{user.email} · Trust {(user.trust_score * 100).toFixed(0)}% · {user.interaction_count} interactions</p>
      </div>
      <div className="card" style={{ marginBottom: 16 }}>
        <h3 className="card-title">Bio</h3>
        <p className="card-desc" style={{ WebkitLineClamp: 10 }}>{user.bio || 'No bio set.'}</p>
      </div>
      <div className="card">
        <h3 className="card-title" style={{ marginBottom: 12 }}>Your skills</h3>
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
        <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={save} disabled={saving}>
          {saving ? 'Saving…' : 'Save skills'}
        </button>
      </div>
    </>
  );
}
