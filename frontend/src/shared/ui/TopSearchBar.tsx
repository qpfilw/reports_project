import { Form } from 'react-bootstrap';
import { NotificationsBell } from './NotificationsBell';

export function TopSearchBar() {
  return (
    <div className="top-search-wrap">
      <div className="top-search-row">
        <Form.Control
          type="search"
          placeholder="Найти"
          className="top-search-input"
        />

        <NotificationsBell />
      </div>
    </div>
  );
}