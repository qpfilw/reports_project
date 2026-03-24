import { NavLink, useNavigate } from 'react-router-dom';
import { Button } from 'react-bootstrap';
import { useAuth } from '../../features/auth/AuthProvider';

const navItems = [
  { label: 'Главная', to: '/' },
  { label: 'Отчетность', to: '/reports' },
  { label: 'Аналитика', to: '/analytics' },
  { label: 'Администратор', to: '/admin', onlyAdmin: true },
];

function getInitials(fullName?: string) {
  if (!fullName) return 'ИИ';

  const parts = fullName.trim().split(/\s+/).filter(Boolean);

  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase();
  }

  return `${parts[0][0] ?? ''}${parts[1][0] ?? ''}`.toUpperCase();
}

function getSidebarDisplayName(fullName?: string) {
  if (!fullName) return 'Пользователь';

  const parts = fullName.trim().split(/\s+/).filter(Boolean);

  if (parts.length === 1) {
    return parts[0];
  }

  if (parts.length === 2) {
    return `${parts[0]} ${parts[1][0]}.`;
  }

  return `${parts[0]} ${parts[1][0]}. ${parts[2][0]}.`;
}

export function AppSidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <aside className="app-sidebar">
      <div>
        <div className="brand-block">
          <div className="brand-avatar" />
          <div className="brand-title">ReportRT</div>
        </div>

        <nav className="sidebar-nav">
          {navItems
            .filter((item) => !item.onlyAdmin || user?.role.code === 'admin')
            .map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `sidebar-link ${isActive ? 'sidebar-link-active' : ''}`
                }
              >
                {item.label}
              </NavLink>
            ))}
        </nav>
      </div>

      <div className="sidebar-bottom">
        <Button className="sidebar-link sidebar-link-ghost" onClick={handleLogout}>
          Выйти
        </Button>

        <NavLink
          to="/profile"
          title={user?.full_name ?? 'Профиль пользователя'}
          className={({ isActive }) =>
            `user-block-link ${isActive ? 'user-block-active' : ''}`
          }
        >
          <div className="user-badge">{getInitials(user?.full_name)}</div>

          <div className="user-info">
            <div className="user-name">
              {getSidebarDisplayName(user?.full_name)}
            </div>
            <div className="user-role">{user?.role.name ?? 'Роль не указана'}</div>
          </div>
        </NavLink>
      </div>
    </aside>
  );
}