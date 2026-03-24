import { Outlet } from 'react-router-dom';
import { AppSidebar } from '../../shared/ui/AppSidebar';
import { TopSearchBar } from '../../shared/ui/TopSearchBar';

export default function AppLayout() {
  return (
    <div className="app-shell">
      <AppSidebar />

      <main className="app-main">
        <TopSearchBar />
        <Outlet />
      </main>
    </div>
  );
}