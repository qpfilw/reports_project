import { Form } from 'react-bootstrap';
import { NotificationsBell } from './NotificationsBell';
import { ProjectSwitcher } from './ProjectSwitcher';

export function TopSearchBar() {
  return (
    <div className="top-search-wrap">
      <div className="top-search-row">
        <Form.Control
          type="search"
          placeholder="Найти"
          className="top-search-input"
        />

        <div className="top-bar-actions">
          <ProjectSwitcher />
          <NotificationsBell />
        </div>
      </div>
    </div>
  );
}