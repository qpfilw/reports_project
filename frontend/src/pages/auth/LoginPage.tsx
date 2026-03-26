import { useState, type FormEvent } from 'react';
import { Alert, Button, Card, Form } from 'react-bootstrap';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthProvider';

const authHighlights = [
  'Загрузка и обработка отчётных файлов в едином интерфейсе.',
  'Контроль статусов, согласование, уведомления и экспорт.',
  'Аналитика по проектам и сохранённые пользовательские дашборды.',
];

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('admin@gmail.com');
  const [password, setPassword] = useState('adminpasswd123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login({ email, password });
      navigate('/dashboard');
    } catch {
      setError('Не удалось выполнить вход. Проверь email и пароль.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-layout">
        <div className="auth-preview-panel">
          <div className="auth-preview-badge">ReportRT</div>
          <h1 className="auth-preview-title">Веб-платформа для автоматизированной обработки отчётности</h1>
          <p className="auth-preview-text">
            Работайте с проектами, отчётами, обработкой, согласованием и аналитикой в едином контуре.
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

            <h1 className="auth-title">Вход в систему</h1>
            <p className="auth-subtitle">Платформа обработки отчётности</p>

            {error ? <Alert variant="danger">{error}</Alert> : null}

            <Form onSubmit={handleSubmit}>
              <Form.Group className="mb-3">
                <Form.Label>Email</Form.Label>
                <Form.Control
                  className="soft-input"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  type="email"
                  placeholder="Введите email"
                />
              </Form.Group>

              <Form.Group className="mb-4">
                <Form.Label>Пароль</Form.Label>
                <Form.Control
                  className="soft-input"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  type="password"
                  placeholder="Введите пароль"
                />
              </Form.Group>

              <Button type="submit" className="primary-pill-button w-100" disabled={loading}>
                {loading ? 'Входим...' : 'Войти'}
              </Button>
            </Form>

            <div className="auth-footer">
              Нет аккаунта? <Link to="/register">Зарегистрироваться</Link>
            </div>
          </Card.Body>
        </Card>
      </div>
    </div>
  );
}
