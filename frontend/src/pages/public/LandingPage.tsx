import { Alert, Button, Card, Col, Container, Row, Spinner } from 'react-bootstrap';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthProvider';

const featureItems = [
  {
    title: 'Централизованная отчётность',
    text: 'Загрузка файлов, контроль статусов, хранение результатов обработки и единый доступ в рамках проекта.',
  },
  {
    title: 'Автоматизированная обработка',
    text: 'Фоновая обработка, нормализация данных, повторный запуск и мониторинг задач без ручного переключения между сервисами.',
  },
  {
    title: 'Согласование и аналитика',
    text: 'Маршруты рассмотрения и утверждения, экспорт результатов, дашборды и сводные показатели по отчётным данным.',
  },
];

const helpItems = [
  'Зарегистрируйтесь с корпоративным email и дождитесь подтверждения администратора.',
  'После одобрения выберите или создайте проект и загрузите отчётный файл.',
  'Запустите обработку, проверьте результат, затем отправьте отчёт на рассмотрение и утверждение.',
];

export default function LandingPage() {
  const { user, isAuthenticated, isLoading, logout } = useAuth();

  if (isLoading) {
    return (
      <div className="app-loader">
        <Spinner animation="border" />
      </div>
    );
  }

  if (isAuthenticated && user?.role.code !== 'pending') {
    return <Navigate to="/dashboard" replace />;
  }

  const isPending = user?.role.code === 'pending';

  return (
    <div className="landing-page-shell">
      <Container className="py-5">
        <div className="landing-hero">
          <h1 className="landing-title">Автоматизированная обработка отчётности на предприятиях</h1>
          <p className="landing-subtitle">
            Единая веб-платформа для загрузки отчётных файлов, их обработки, согласования,
            анализа и экспорта результатов.
          </p>

          <div className="landing-actions">
            {isPending ? (
              <>
                <Link to="/dashboard" className="btn primary-pill-button">
                  Перейти в кабинет
                </Link>
                <Link to="/profile" className="btn secondary-pill-button">
                  Профиль
                </Link>
                <Button className="secondary-pill-button" onClick={logout}>
                  Выйти
                </Button>
              </>
            ) : (
              <>
                <Link to="/login" className="btn primary-pill-button">
                  Войти в систему
                </Link>
                <Link to="/register" className="btn secondary-pill-button">
                  Зарегистрироваться
                </Link>
              </>
            )}
          </div>
        </div>

        {isPending ? (
          <Alert variant="info" className="landing-alert">
            Ваша учётная запись ещё не подтверждена администратором. Пока доступен только
            справочный контур, профиль и базовые настройки.
          </Alert>
        ) : null}

        <Row className="g-3 mb-4">
          {featureItems.map((item) => (
            <Col md={4} key={item.title}>
              <Card className="landing-card h-100">
                <Card.Body>
                  <div className="landing-card-title">{item.title}</div>
                  <div className="landing-card-text">{item.text}</div>
                </Card.Body>
              </Card>
            </Col>
          ))}
        </Row>

        <Row className="g-3">
          <Col lg={7}>
            <Card className="landing-card h-100">
              <Card.Body>
                <div className="landing-card-title">Как начать работу</div>
                <ol className="landing-help-list mb-0">
                  {helpItems.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ol>
              </Card.Body>
            </Card>
          </Col>

          <Col lg={5}>
            <Card className="landing-card h-100">
              <Card.Body>
                <div className="landing-card-title">Справка по доступу</div>
                <div className="landing-card-text mb-3">
                  Гость может ознакомиться с назначением платформы и пройти регистрацию.
                  Подтверждённый пользователь получает доступ к проектам, отчётам, задачам,
                  аналитике и уведомлениям в соответствии со своей ролью.
                </div>
                <div className="landing-mini-note">
                  Поддерживаемые роли: администратор, менеджер, оператор, наблюдатель.
                </div>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    </div>
  );
}
