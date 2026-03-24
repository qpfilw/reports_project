import { useState } from 'react';
import { Alert, Button, Card, Form } from 'react-bootstrap';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthProvider';

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

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      await register(form);
      navigate('/');
    } catch {
      setError('Не удалось зарегистрироваться.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <Card className="auth-card">
        <Card.Body>
          <h1 className="auth-title">Регистрация</h1>
          <p className="auth-subtitle">Создание учетной записи сотрудника</p>

          {error ? <Alert variant="danger">{error}</Alert> : null}

          <Form onSubmit={handleSubmit}>
            <Form.Group className="mb-3">
              <Form.Label>ФИО</Form.Label>
              <Form.Control
                value={form.full_name}
                onChange={(e) => updateField('full_name', e.target.value)}
                placeholder="Иванов Иван Иванович"
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Email</Form.Label>
              <Form.Control
                value={form.email}
                onChange={(e) => updateField('email', e.target.value)}
                type="email"
                placeholder="name@company.ru"
              />
            </Form.Group>

            <Form.Group className="mb-4">
              <Form.Label>Пароль</Form.Label>
              <Form.Control
                value={form.password}
                onChange={(e) => updateField('password', e.target.value)}
                type="password"
                placeholder="Введите пароль"
              />
            </Form.Group>

            <Button type="submit" className="primary-pill-button w-100" disabled={loading}>
              {loading ? 'Создаем...' : 'Создать аккаунт'}
            </Button>
          </Form>

          <div className="auth-footer">
            Уже есть аккаунт? <Link to="/login">Войти</Link>
          </div>
        </Card.Body>
      </Card>
    </div>
  );
}