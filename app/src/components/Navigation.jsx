import { Link, useLocation } from 'react-router-dom';
import './Navigation.css';

export default function Navigation() {
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="nav-header">
      <ul className="nav-tabs">
        <li>
          <Link to="/" className={isActive('/') ? 'active' : ''}>
            🧙‍♂️ Current Season
          </Link>
        </li>
        <li>
          <Link to="/seasons" className={isActive('/seasons') ? 'active' : ''}>
            Past Seasons
          </Link>
        </li>
        <li>
          <Link to="/rules" className={isActive('/rules') ? 'active' : ''}>
            Rules
          </Link>
        </li>
        <li>
          <Link to="/calendar" className={isActive('/calendar') ? 'active' : ''}>
            Calendar
          </Link>
        </li>
      </ul>
    </nav>
  );
}
