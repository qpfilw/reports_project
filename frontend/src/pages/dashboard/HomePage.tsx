import { Col, Row } from 'react-bootstrap';
import { ContentCard } from '../../shared/ui/ContentCard';

export default function HomePage() {
  return (
    <ContentCard
      header={
        <div className="section-header">
          <h2 className="section-title">Главная</h2>
        </div>
      }
    >
      <Row className="g-3">
        <Col md={4}>
          <div className="metric-card">
            <div className="metric-label">Отчетов в работе</div>
            <div className="metric-value">12</div>
          </div>
        </Col>
        <Col md={4}>
          <div className="metric-card">
            <div className="metric-label">Задач в очереди</div>
            <div className="metric-value">3</div>
          </div>
        </Col>
        <Col md={4}>
          <div className="metric-card">
            <div className="metric-label">Ошибок за сутки</div>
            <div className="metric-value">1</div>
          </div>
        </Col>
      </Row>
    </ContentCard>
  );
}