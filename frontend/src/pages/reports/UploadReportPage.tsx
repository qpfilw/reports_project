import { useEffect, useMemo, useState, type ChangeEvent } from 'react';
import { Alert, Button, Col, Form, Row, Spinner } from 'react-bootstrap';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthProvider';
import { mlApi } from '../../shared/api/ml';
import { processingApi } from '../../shared/api/processing';
import { reportsApi } from '../../shared/api/reports';
import { uploadsApi } from '../../shared/api/uploads';
import type { Report } from '../../shared/types/report';
import type { TemplatePredictionResult } from '../../shared/types/ml-pipeline';
import type { MlTemplate } from '../../shared/types/template';
import type { ReportUpload } from '../../shared/types/upload';
import { ContentCard } from '../../shared/ui/ContentCard';

function formatDate(value?: string | null) {
  if (!value) return '-';

  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('ru-RU');
}

function formatBytes(value: number) {
  if (value < 1024) return `${value} Б`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} КБ`;
  return `${(value / (1024 * 1024)).toFixed(2)} МБ`;
}

export default function UploadReportPage() {
  const { reportId } = useParams<{ reportId: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();

  const numericReportId = Number(reportId);

  const [report, setReport] = useState<Report | null>(null);
  const [existingUploads, setExistingUploads] = useState<ReportUpload[]>([]);
  const [templates, setTemplates] = useState<MlTemplate[]>([]);
  const [prediction, setPrediction] = useState<TemplatePredictionResult | null>(null);

  const [file, setFile] = useState<File | null>(null);
  const [comment, setComment] = useState('');
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('');
  const [priority, setPriority] = useState('5');

  const [createdUploadId, setCreatedUploadId] = useState<number | null>(null);

  const [isBootLoading, setIsBootLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isLaunching, setIsLaunching] = useState(false);
  const [isPredictionLoading, setIsPredictionLoading] = useState(false);

  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    if (!reportId || Number.isNaN(numericReportId)) {
      setError('Некорректный идентификатор отчета.');
      setIsBootLoading(false);
      return;
    }

    (async () => {
      try {
        setIsBootLoading(true);
        setError('');

        const [reportData, uploadsData] = await Promise.all([
          reportsApi.getById(numericReportId),
          uploadsApi.list(),
        ]);

        setReport(reportData);

        const filteredUploads = uploadsData
          .filter((item) => item.report_id === numericReportId)
          .sort((a, b) => b.upload_version - a.upload_version);

        setExistingUploads(filteredUploads);

        if (reportData.ml_template_id) {
          setSelectedTemplateId(String(reportData.ml_template_id));
        }

        const templatesData = await mlApi.listTemplates(reportData.report_type_id);
        setTemplates(templatesData);
      } catch {
        setError('Не удалось загрузить данные отчета и загрузок.');
      } finally {
        setIsBootLoading(false);
      }
    })();
  }, [reportId, numericReportId]);

  const latestUpload = useMemo<ReportUpload | null>(() => {
    return existingUploads.find((item) => item.is_latest) ?? existingUploads[0] ?? null;
  }, [existingUploads]);

  const displayedUpload = useMemo<ReportUpload | null>(() => {
    if (createdUploadId == null) {
      return latestUpload;
    }

    return existingUploads.find((item) => item.id === createdUploadId) ?? latestUpload;
  }, [createdUploadId, existingUploads, latestUpload]);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const nextFile = event.currentTarget.files?.[0] ?? null;
    setFile(nextFile);
  };

  const handleUpload = async () => {
    if (!file || !report) {
      setError('Сначала выбери файл для загрузки.');
      return;
    }

    try {
      setError('');
      setSuccessMessage('');
      setIsUploading(true);

      const upload = await reportsApi.uploadFile(report.id, file, comment);

      setCreatedUploadId(upload.id);

      setExistingUploads((prev) =>
        [upload, ...prev.map((item) => ({ ...item, is_latest: false }))].sort(
          (a, b) => b.upload_version - a.upload_version,
        ),
      );

      setSuccessMessage(`Файл "${upload.original_filename}" успешно загружен.`);

      try {
        setIsPredictionLoading(true);
        const predictionResult = await mlApi.predictTemplateForUpload(upload.id);
        setPrediction(predictionResult);

        if (!selectedTemplateId && predictionResult.best_match?.template_id) {
          setSelectedTemplateId(String(predictionResult.best_match.template_id));
        }
      } finally {
        setIsPredictionLoading(false);
      }
    } catch {
      setError('Не удалось загрузить файл. Проверь формат и права доступа.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleLaunch = async () => {
    if (!report || !user) {
      setError('Не удалось определить контекст пользователя или отчета.');
      return;
    }

    const uploadId = createdUploadId ?? latestUpload?.id;

    if (!uploadId) {
      setError('Сначала загрузи файл отчета.');
      return;
    }

    try {
      setError('');
      setSuccessMessage('');
      setIsLaunching(true);

      const task = await processingApi.launchTask({
        report_id: report.id,
        report_upload_id: uploadId,
        ml_template_id: selectedTemplateId ? Number(selectedTemplateId) : null,
        created_by: user.id,
        priority: Number(priority),
        params_json: {},
      });

      navigate(`/tasks/${task.id}`);
    } catch {
      setError('Не удалось запустить задачу обработки.');
    } finally {
      setIsLaunching(false);
    }
  };

  if (isBootLoading) {
    return (
      <ContentCard
        header={
          <div className="section-header">
            <h2 className="section-title">Загрузка файла отчета</h2>
          </div>
        }
      >
        <div className="py-5 text-center">
          <Spinner animation="border" />
        </div>
      </ContentCard>
    );
  }

  if (!report) {
    return (
      <ContentCard
        header={
          <div className="section-header">
            <h2 className="section-title">Загрузка файла отчета</h2>
          </div>
        }
      >
        <Alert variant="danger" className="mb-0">
          {error || 'Отчет не найден.'}
        </Alert>
      </ContentCard>
    );
  }

  return (
    <ContentCard
      header={
        <div className="toolbar-row">
          <div className="toolbar-left">
            <h2 className="section-title mb-0">Загрузка файла отчета</h2>
          </div>

          <Button
            className="secondary-pill-button"
            onClick={() => navigate('/reports')}
          >
            Назад к отчетам
          </Button>
        </div>
      }
    >
      <div className="form-shell">
        {error ? <Alert variant="danger">{error}</Alert> : null}
        {successMessage ? <Alert variant="success">{successMessage}</Alert> : null}

        <div className="form-meta-grid mb-4">
          <div className="form-meta-card">
            <div className="form-meta-label">Отчет</div>
            <div className="form-meta-value">{report.title}</div>
          </div>

          <div className="form-meta-card">
            <div className="form-meta-label">Период</div>
            <div className="form-meta-value">
              {report.report_period_start} - {report.report_period_end}
            </div>
          </div>

          <div className="form-meta-card">
            <div className="form-meta-label">Статус</div>
            <div className="form-meta-value">{report.status}</div>
          </div>
        </div>

        <Row className="g-4">
          <Col lg={7}>
            <div className="upload-panel">
              <Form.Group className="mb-3">
                <Form.Label>Файл отчетности</Form.Label>
                <Form.Control
                  type="file"
                  className="soft-input"
                  accept=".xlsx,.xls,.csv"
                  onChange={handleFileChange}
                />
              </Form.Group>

              <Form.Group className="mb-3">
                <Form.Label>Комментарий к загрузке</Form.Label>
                <Form.Control
                  as="textarea"
                  rows={4}
                  className="soft-input soft-textarea"
                  value={comment}
                  onChange={(event) => setComment(event.target.value)}
                  placeholder="Например: Исправленная версия отчета за период"
                />
              </Form.Group>

              <Form.Group className="mb-3">
                <Form.Label>ML-шаблон обработки</Form.Label>
                <Form.Select
                  className="soft-input"
                  value={selectedTemplateId}
                  onChange={(event) => setSelectedTemplateId(event.target.value)}
                >
                  <option value="">Без шаблона</option>
                  {templates.map((template) => (
                    <option key={template.id} value={template.id}>
                      {template.name} ({template.version})
                      {template.is_default ? ' • по умолчанию' : ''}
                    </option>
                  ))}
                </Form.Select>
              </Form.Group>

              <Form.Group className="mb-0">
                <Form.Label>Приоритет задачи</Form.Label>
                <Form.Select
                  className="soft-input"
                  value={priority}
                  onChange={(event) => setPriority(event.target.value)}
                >
                  <option value="1">1 - минимальный</option>
                  <option value="3">3</option>
                  <option value="5">5 - стандартный</option>
                  <option value="7">7</option>
                  <option value="10">10 - максимальный</option>
                </Form.Select>
              </Form.Group>

              <div className="action-dock action-dock-inline mt-4">
                <Button
                  className="secondary-pill-button"
                  onClick={handleUpload}
                  disabled={!file || isUploading}
                >
                  {isUploading ? 'Загрузка...' : 'Загрузить файл'}
                </Button>

                <Button
                  className="primary-pill-button"
                  onClick={handleLaunch}
                  disabled={isLaunching || (!createdUploadId && !latestUpload)}
                >
                  {isLaunching ? 'Запуск...' : 'Запустить обработку'}
                </Button>
              </div>
            </div>
          </Col>

          <Col lg={5}>
            <div className="upload-side-stack">
              <div className="form-meta-card">
                <div className="form-meta-label">Текущий файл</div>
                <div className="form-meta-value">
                  {displayedUpload?.original_filename ?? 'Файл еще не загружен'}
                </div>
              </div>

              <div className="form-meta-card">
                <div className="form-meta-label">Последняя загрузка</div>
                <div className="form-meta-value">
                  {latestUpload ? formatDate(latestUpload.uploaded_at) : '-'}
                </div>
              </div>

              <div className="form-meta-card">
                <div className="form-meta-label">Размер файла</div>
                <div className="form-meta-value">
                  {displayedUpload
                    ? formatBytes(displayedUpload.file_size)
                    : file
                      ? formatBytes(file.size)
                      : '-'}
                </div>
              </div>

              <div className="form-meta-card">
                <div className="form-meta-label">Прогноз ML-шаблона</div>
                <div className="form-meta-value">
                  {isPredictionLoading
                    ? 'Выполняется анализ...'
                    : prediction?.best_match
                      ? `${prediction.best_match.template_code ?? 'template'} • ${Math.round(prediction.best_match.confidence * 100)}%`
                      : 'Нет прогноза'}
                </div>
              </div>
            </div>
          </Col>
        </Row>
      </div>
    </ContentCard>
  );
}