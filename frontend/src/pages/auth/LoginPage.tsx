import { useState } from 'react';
import { Alert, Button, Card, Form } from 'react-bootstrap';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthProvider';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('admin@gmail.com');
  const [password, setPassword] = useState('adminpasswd123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login({ email, password });
      navigate('/');
    } catch {
      setError('Не удалось выполнить вход. Проверь email и пароль.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <Card className="auth-card">
        <Card.Body>
          <h1 className="auth-title">Вход в систему</h1>
          <p className="auth-subtitle">Платформа обработки отчетности</p>

          {error ? <Alert variant="danger">{error}</Alert> : null}

          <Form onSubmit={handleSubmit}>
            <Form.Group className="mb-3">
              <Form.Label>Email</Form.Label>
              <Form.Control
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                type="email"
                placeholder="Введите email"
              />
            </Form.Group>

            <Form.Group className="mb-4">
              <Form.Label>Пароль</Form.Label>
              <Form.Control
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
  );
}