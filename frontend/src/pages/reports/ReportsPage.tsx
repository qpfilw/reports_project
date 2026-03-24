import { useEffect, useMemo, useState } from 'react';
import { Alert, Button, Form, Spinner, Table } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { reportsApi } from '../../shared/api/reports';
import { getReportStatusClassName, getReportStatusLabel, reportStatusOptions } from '../../shared/lib/reportStatus';
import type { Report } from '../../shared/types/report';
import { ContentCard } from '../../shared/ui/ContentCard';

function formatDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString('ru-RU');
}

export default function ReportsPage() {
  const navigate = useNavigate();

  const [reports, setReports] = useState<Report[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        setIsLoading(true);
        setError('');
        const data = await reportsApi.list();
        setReports(data);
      } catch {
        setError('Не удалось загрузить список отчетов.');
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  const filteredReports = useMemo(() => {
    if (statusFilter === 'all') {
      return reports;
    }
    return reports.filter((report) => report.status === statusFilter);
  }, [reports, statusFilter]);

  const toggleOne = (reportId: number) => {
    setSelectedIds((prev) =>
      prev.includes(reportId) ? prev.filter((id) => id !== reportId) : [...prev, reportId],
    );
  };

  const toggleAll = () => {
    if (filteredReports.length === 0) {
      return;
    }

    const visibleIds = filteredReports.map((report) => report.id);
    const allSelected = visibleIds.every((id) => selectedIds.includes(id));

    setSelectedIds((prev) => {
      if (allSelected) {
        return prev.filter((id) => !visibleIds.includes(id));
      }

      return Array.from(new Set([...prev, ...visibleIds]));
    });
  };

  return (
    <ContentCard
      header={
        <div className="toolbar-row">
          <div className="toolbar-left">
            <h2 className="section-title mb-0">Отфильтровать по...</h2>

            <Form.Select
              className="soft-select"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              {reportStatusOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Form.Select>
          </div>

          <Button className="primary-pill-button" onClick={() => navigate('/reports/create')}>
            Создать отчет
          </Button>
        </div>
      }
    >
      {isLoading ? (
        <div className="py-5 text-center">
          <Spinner animation="border" />
        </div>
      ) : null}

      {!isLoading && error ? <Alert variant="danger">{error}</Alert> : null}

      {!isLoading && !error ? (
        <>
          <div className="table-wrap">
            <Table borderless responsive className="prototype-table">
              <thead>
                <tr>
                  <th className="checkbox-col">
                    <Form.Check
                      checked={
                        filteredReports.length > 0 &&
                        filteredReports.every((report) => selectedIds.includes(report.id))
                      }
                      onChange={toggleAll}
                    />
                  </th>
                  <th>ID</th>
                  <th>Название</th>
                  <th>Статус</th>
                  <th>Период начала</th>
                  <th>Период конца</th>
                  <th>Версия</th>
                </tr>
              </thead>
              <tbody>
                {filteredReports.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-4">
                      Отчеты не найдены
                    </td>
                  </tr>
                ) : (
                  filteredReports.map((report) => (
                    <tr
                      key={report.id}
                      className="table-row-clickable"
                      onClick={() => navigate(`/reports/${report.id}/result`)}
                    >
                      <td
                        className="checkbox-col"
                        onClick={(event) => event.stopPropagation()}
                      >
                        <Form.Check
                          checked={selectedIds.includes(report.id)}
                          onChange={() => toggleOne(report.id)}
                        />
                      </td>
                      <td>{report.id}</td>
                      <td>{report.title}</td>
                      <td>
                        <span className={getReportStatusClassName(report.status)}>
                          {getReportStatusLabel(report.status)}
                        </span>
                      </td>
                      <td>{formatDate(report.report_period_start)}</td>
                      <td>{formatDate(report.report_period_end)}</td>
                      <td>{report.version}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </Table>
          </div>

          <div className="action-dock">
            <Button className="primary-pill-button" disabled={selectedIds.length !== 1}>
              Редактировать
            </Button>
            <Button className="primary-pill-button" disabled={selectedIds.length === 0}>
              Удалить
            </Button>
            <Button className="primary-pill-button" disabled={selectedIds.length !== 1}>
              Сохранить как
            </Button>
          </div>
        </>
      ) : null}
    </ContentCard>
  );
}