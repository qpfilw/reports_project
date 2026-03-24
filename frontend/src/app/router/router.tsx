import { createBrowserRouter } from 'react-router-dom';
import AppLayout from '../layouts/AppLayout';
import { ProtectedRoute } from '../../features/auth/ProtectedRoute';
import { RoleGuard } from '../../features/auth/RoleGuard';
import LoginPage from '../../pages/auth/LoginPage';
import RegisterPage from '../../pages/auth/RegisterPage';
import HomePage from '../../pages/dashboard/HomePage';
import ReportsPage from '../../pages/reports/ReportsPage';
import AnalyticsPage from '../../pages/analytics/AnalyticsPage';
import AdminPage from '../../pages/admin/AdminPage';
import ProfilePage from '../../pages/profile/ProfilePage';
import CreateReportPage from '../../pages/reports/CreateReportPage';
import UploadReportPage from '../../pages/reports/UploadReportPage';
import TaskDetailsPage from '../../pages/tasks/TaskDetailsPage';
import ReportResultPage from '../../pages/reports/ReportResultPage';
import AdminTemplatesPage from '../../pages/admin/AdminTemplatesPage';
import NotificationsPage from '../../pages/notifications/NotificationsPage';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/register',
    element: <RegisterPage />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: 'reports',
        element: <ReportsPage />,
      },
      {
        path: 'reports/create',
        element: <CreateReportPage />,
      },
      {
        path: 'reports/:reportId/upload',
        element: <UploadReportPage />,
      },
      {
        path: 'reports/:reportId/result',
        element: <ReportResultPage />,
      },
      {
        path: 'tasks/:taskId',
        element: <TaskDetailsPage />,
      },
      {
        path: 'analytics',
        element: (
          <RoleGuard roles={['admin', 'manager', 'operator', 'viewer']}>
            <AnalyticsPage />
          </RoleGuard>
        ),
      },
      {
        path: 'admin',
        element: (
          <RoleGuard roles={['admin']}>
            <AdminPage />
          </RoleGuard>
        ),
      },
      {
        path: 'admin/templates',
        element: (
            <RoleGuard roles={['admin']}>
            <AdminTemplatesPage />
            </RoleGuard>
        ),
      },
      {
        path: 'profile',
        element: <ProfilePage />,
      },
      {
        path: 'notifications',
        element: <NotificationsPage />,
      },
    ],
  },
]);