import { useEffect, useState, type FormEvent } from 'react';
import { Alert, Button, Col, Form, Row } from 'react-bootstrap';
import { useAuth } from '../../features/auth/AuthProvider';
import { authApi } from '../../shared/api/auth';
import { ContentCard } from '../../shared/ui/ContentCard';

interface ProfileFormState {
  email: string;
  full_name: string;
  position: string;
  department: string;
}

interface PasswordFormState {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export default function ProfilePage() {
  const { user, reloadMe } = useAuth();

  const [isSettingsMode, setIsSettingsMode] = useState(false);
  const [profileForm, setProfileForm] = useState<ProfileFormState>({
    email: '',
    full_name: '',
    position: '',
    department: '',
  });

  const [passwordForm, setPasswordForm] = useState<PasswordFormState>({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  const [profileError, setProfileError] = useState('');
  const [profileSuccess, setProfileSuccess] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');

  const [isProfileSubmitting, setIsProfileSubmitting] = useState(false);
  const [isPasswordSubmitting, setIsPasswordSubmitting] = useState(false);

  useEffect(() => {
    if (!user) return;

    setProfileForm({
      email: user.email ?? '',
      full_name: user.full_name ?? '',
      position: user.position ?? '',
      department: user.department ?? '',
    });
  }, [user]);

  const handleProfileSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setProfileError('');
    setProfileSuccess('');

    if (!profileForm.email.trim()) {
      setProfileError('Укажи email.');
      return;
    }

    if (!profileForm.full_name.trim()) {
      setProfileError('Укажи ФИО.');
      return;
    }

    try {
      setIsProfileSubmitting(true);

      await authApi.updateMe({
        email: profileForm.email.trim(),
        full_name: profileForm.full_name.trim(),
        position: profileForm.position.trim() || null,
        department: profileForm.department.trim() || null,
      });

      await reloadMe();
      setProfileSuccess('Профиль успешно обновлён.');
    } catch {
      setProfileError('Не удалось обновить данные профиля.');
    } finally {
      setIsProfileSubmitting(false);
    }
  };

  const handlePasswordSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPasswordError('');
    setPasswordSuccess('');

    if (!passwordForm.current_password.trim()) {
      setPasswordError('Укажи текущий пароль.');
      return;
    }

    if (!passwordForm.new_password.trim()) {
      setPasswordError('Укажи новый пароль.');
      return;
    }

    if (passwordForm.new_password.length < 8) {
      setPasswordError('Новый пароль должен содержать не менее 8 символов.');
      return;
    }

    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setPasswordError('Подтверждение пароля не совпадает.');
      return;
    }

    try {
      setIsPasswordSubmitting(true);

      await authApi.changePassword({
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password,
      });

      setPasswordForm({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });

      setPasswordSuccess('Пароль успешно изменён.');
    } catch {
      setPasswordError('Не удалось изменить пароль.');
    } finally {
      setIsPasswordSubmitting(false);
    }
  };

  return (
    <ContentCard
      header={
        <div className="toolbar-row">
          <div className="toolbar-left">
            <h2 className="section-title mb-0">Профиль пользователя</h2>
          </div>

          <div className="settings-header-actions">
            {isSettingsMode ? (
              <Button className="secondary-pill-button" onClick={() => setIsSettingsMode(false)}>
                Вернуться к профилю
              </Button>
            ) : (
              <Button className="primary-pill-button" onClick={() => setIsSettingsMode(true)}>
                Настройки профиля
              </Button>
            )}
          </div>
        </div>
      }
    >
      <div className="page-content-centered page-content-narrow">
        <div className="profile-overview-grid mb-4">
          <div className="profile-field">
            <div className="profile-label">Email</div>
            <div className="profile-value">{user?.email ?? '-'}</div>
          </div>

          <div className="profile-field">
            <div className="profile-label">ФИО</div>
            <div className="profile-value">{user?.full_name ?? '-'}</div>
          </div>

          <div className="profile-field">
            <div className="profile-label">Должность</div>
            <div className="profile-value">{user?.position ?? 'Не указана'}</div>
          </div>

          <div className="profile-field">
            <div className="profile-label">Подразделение</div>
            <div className="profile-value">{user?.department ?? 'Не указано'}</div>
          </div>
        </div>

        {!isSettingsMode ? (
          <div className="profile-empty">
            Здесь отображается основная информация о пользователе. Для редактирования данных и
            смены пароля открой «Настройки профиля».
          </div>
        ) : (
          <Row className="g-4 profile-settings-grid">
            <Col xl={6}>
              <div className="form-meta-card profile-settings-card h-100">
                <div className="form-meta-label">Редактирование профиля</div>

                {profileError ? <Alert variant="danger">{profileError}</Alert> : null}
                {profileSuccess ? <Alert variant="success">{profileSuccess}</Alert> : null}

                <Form onSubmit={handleProfileSubmit}>
                  <div className="settings-option-list">
                    <Form.Group>
                      <Form.Label>Email</Form.Label>
                      <Form.Control
                        className="soft-input"
                        value={profileForm.email}
                        onChange={(event) =>
                          setProfileForm((prev) => ({ ...prev, email: event.target.value }))
                        }
                      />
                    </Form.Group>

                    <Form.Group>
                      <Form.Label>ФИО</Form.Label>
                      <Form.Control
                        className="soft-input"
                        value={profileForm.full_name}
                        onChange={(event) =>
                          setProfileForm((prev) => ({ ...prev, full_name: event.target.value }))
                        }
                      />
                    </Form.Group>

                    <Row className="g-3">
                      <Col md={6}>
                        <Form.Group>
                          <Form.Label>Должность</Form.Label>
                          <Form.Control
                            className="soft-input"
                            value={profileForm.position}
                            onChange={(event) =>
                              setProfileForm((prev) => ({ ...prev, position: event.target.value }))
                            }
                          />
                        </Form.Group>
                      </Col>

                      <Col md={6}>
                        <Form.Group>
                          <Form.Label>Подразделение</Form.Label>
                          <Form.Control
                            className="soft-input"
                            value={profileForm.department}
                            onChange={(event) =>
                              setProfileForm((prev) => ({ ...prev, department: event.target.value }))
                            }
                          />
                        </Form.Group>
                      </Col>
                    </Row>
                  </div>

                  <div className="form-actions-row mt-4">
                    <Button
                      type="submit"
                      className="primary-pill-button"
                      disabled={isProfileSubmitting}
                    >
                      {isProfileSubmitting ? 'Сохранение...' : 'Сохранить профиль'}
                    </Button>
                  </div>
                </Form>
              </div>
            </Col>

            <Col xl={6}>
              <div className="form-meta-card profile-settings-card h-100">
                <div className="form-meta-label">Смена пароля</div>

                {passwordError ? <Alert variant="danger">{passwordError}</Alert> : null}
                {passwordSuccess ? <Alert variant="success">{passwordSuccess}</Alert> : null}

                <Form onSubmit={handlePasswordSubmit}>
                  <div className="settings-option-list">
                    <Form.Group>
                      <Form.Label>Текущий пароль</Form.Label>
                      <Form.Control
                        type="password"
                        className="soft-input"
                        value={passwordForm.current_password}
                        onChange={(event) =>
                          setPasswordForm((prev) => ({
                            ...prev,
                            current_password: event.target.value,
                          }))
                        }
                      />
                    </Form.Group>

                    <Row className="g-3">
                      <Col md={6}>
                        <Form.Group>
                          <Form.Label>Новый пароль</Form.Label>
                          <Form.Control
                            type="password"
                            className="soft-input"
                            value={passwordForm.new_password}
                            onChange={(event) =>
                              setPasswordForm((prev) => ({
                                ...prev,
                                new_password: event.target.value,
                              }))
                            }
                          />
                        </Form.Group>
                      </Col>

                      <Col md={6}>
                        <Form.Group>
                          <Form.Label>Подтверждение</Form.Label>
                          <Form.Control
                            type="password"
                            className="soft-input"
                            value={passwordForm.confirm_password}
                            onChange={(event) =>
                              setPasswordForm((prev) => ({
                                ...prev,
                                confirm_password: event.target.value,
                              }))
                            }
                          />
                        </Form.Group>
                      </Col>
                    </Row>
                  </div>

                  <div className="form-actions-row mt-4">
                    <Button
                      type="submit"
                      className="primary-pill-button"
                      disabled={isPasswordSubmitting}
                    >
                      {isPasswordSubmitting ? 'Изменение...' : 'Сменить пароль'}
                    </Button>
                  </div>
                </Form>
              </div>
            </Col>
          </Row>
        )}
      </div>
    </ContentCard>
  );
}
