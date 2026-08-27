import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../lib/auth';
import { LogOut, Briefcase, Users, Building2, LayoutDashboard } from 'lucide-react';

export default function Navbar() {
  const { user, logout } = useAuth();
  const loc = useLocation();
  const nav = useNavigate();

  const isActive = (path: string) => (loc.pathname === path ? 'active' : '');

  return (
    <header className="navbar">
      <Link to="/" className="navbar-brand">
        <span>Skill</span>
        <span className="accent">Bridge</span>
      </Link>

      {user && (
        <nav className="nav-links">
          <Link to="/" className={`nav-link ${isActive('/')}`}>
            <LayoutDashboard size={16} style={{ marginRight: 4, verticalAlign: -2 }} />
            Feed
          </Link>
          <Link to="/gigs" className={`nav-link ${isActive('/gigs')}`}>
            <Briefcase size={16} style={{ marginRight: 4, verticalAlign: -2 }} />
            Gigs
          </Link>
          <Link to="/mentors" className={`nav-link ${isActive('/mentors')}`}>
            <Users size={16} style={{ marginRight: 4, verticalAlign: -2 }} />
            Mentors
          </Link>
          <Link to="/profile" className={`nav-link ${isActive('/profile')}`}>
            <Building2 size={16} style={{ marginRight: 4, verticalAlign: -2 }} />
            Profile
          </Link>
        </nav>
      )}

      <div className="nav-user">
        {user ? (
          <>
            <span>{user.full_name}</span>
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => {
                logout();
                nav('/login');
              }}
            >
              <LogOut size={14} />
              Logout
            </button>
          </>
        ) : (
          <Link to="/login" className="btn btn-primary btn-sm">
            Sign in
          </Link>
        )}
      </div>
    </header>
  );
}
