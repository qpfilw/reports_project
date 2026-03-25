import { useAuth } from '../../features/auth/AuthProvider';
import { ContentCard } from '../../shared/ui/ContentCard';

function renderBoolean(value: boolean, trueLabel = 'Да', falseLabel = 'Нет') {
  return (
    <span className={`profile-badge ${value ? 'profile-badge-success' : 'profile-badge-muted'}`}>
      {value ? trueLabel : falseLabel}
    </span>
  );
}

export default function ProfilePage() {
  const { user } = useAuth();

  if (!user) {
    return (
      <ContentCard
        header={
          <div className="section-header">
            <h2 className="section-title">Профиль пользователя</h2>
          </div>
        }
      >
        <div className="profile-empty">Не удалось загрузить данные пользователя.</div>
      </ContentCard>
    );
  }

  return (
    <ContentCard
      header={
        <div className="section-header">
          <h2 className="section-title">Профиль пользователя</h2>
        </div>
      }
    >
      <div className="profile-grid">
        <div className="profile-field">
          <div className="profile-label">ФИО</div>
          <div className="profile-value">{user.full_name}</div>
        </div>

        <div className="profile-field">
          <div className="profile-label">Email</div>
          <div className="profile-value">{user.email}</div>
        </div>

        <div className="profile-field">
          <div className="profile-label">Роль</div>
          <div className="profile-value">
            {user.role.name} <span className="profile-code">({user.role.code})</span>
          </div>
        </div>

        <div className="profile-field">
          <div className="profile-label">Должность</div>
          <div className="profile-value">{user.position ?? '-'}</div>
        </div>

        <div className="profile-field">
          <div className="profile-label">Отдел</div>
          <div className="profile-value">{user.department ?? '-'}</div>
        </div>

        <div className="profile-field">
          <div className="profile-label">Активность</div>
          <div className="profile-value">{renderBoolean(user.is_active)}</div>
        </div>

        <div className="profile-field">
          <div className="profile-label">Блокировка</div>
          <div className="profile-value">
            {renderBoolean(!user.is_blocked, 'Не заблокирован', 'Заблокирован')}
          </div>
        </div>

        <div className="profile-field">
          <div className="profile-label">ID пользователя</div>
          <div className="profile-value">{user.id}</div>
        </div>
      </div>
    </ContentCard>
  );
}