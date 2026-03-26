import { useState, type FormEvent } from 'react';
import { Alert, Button, Card, Form } from 'react-bootstrap';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthProvider';

const authHighlights = [
  'Единый вход в рабочее пространство проектов и отчётов.',
  'Фоновая обработка файлов с контролем статусов и ошибок.',
  'Согласование, экспорт результатов и аналитические панели.',
];

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const updateField = (key: keyof typeof form, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      await register(form);
      navigate('/dashboard');
    } catch {
      setError('Не удалось зарегистрироваться.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-layout">
        <div className="auth-preview-panel">
          <div className="auth-preview-badge">Новая учётная запись</div>
          <h1 className="auth-preview-title">Регистрация в системе обработки отчётности</h1>
          <p className="auth-preview-text">
            После регистрации заявка будет направлена администратору. После подтверждения откроется доступ к основным рабочим разделам платформы.
          </p>
          <ul className="auth-preview-list">
            {authHighlights.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <Card className="auth-card auth-card-elevated">
          <Card.Body>
            <div className="auth-card-topbar">
              <Link to="/" className="btn secondary-pill-button auth-back-button">
                На главную
              </Link>
            </div>

            <h1 className="auth-title">Регистрация</h1>
            <p className="auth-subtitle">Создание учётной записи сотрудника</p>

            {error ? <Alert variant="danger">{error}</Alert> : null}

            <Form onSubmit={handleSubmit}>
              <Form.Group className="mb-3">
                <Form.Label>ФИО</Form.Label>
                <Form.Control
                  className="soft-input"
                  value={form.full_name}
                  onChange={(e) => updateField('full_name', e.target.value)}
                  placeholder="Иванов Иван Иванович"
                />
              </Form.Group>

              <Form.Group className="mb-3">
                <Form.Label>Email</Form.Label>
                <Form.Control
                  className="soft-input"
                  value={form.email}
                  onChange={(e) => updateField('email', e.target.value)}
                  type="email"
                  placeholder="name@company.ru"
                />
              </Form.Group>

              <Form.Group className="mb-4">
                <Form.Label>Пароль</Form.Label>
                <Form.Control
                  className="soft-input"
                  value={form.password}
                  onChange={(e) => updateField('password', e.target.value)}
                  type="password"
                  placeholder="Введите пароль"
                />
              </Form.Group>

              <Button type="submit" className="primary-pill-button w-100" disabled={loading}>
                {loading ? 'Создаём...' : 'Создать аккаунт'}
              </Button>
            </Form>

            <div className="auth-footer">
              Уже есть аккаунт? <Link to="/login">Войти</Link>
            </div>
          </Card.Body>
        </Card>
      </div>
    </div>
  );
}
