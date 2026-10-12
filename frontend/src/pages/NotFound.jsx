import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Brand } from '../components/Logo';
import { EmptyState } from '../components/ui';

export default function NotFound() {
  const { isAuthenticated } = useAuth();
  useEffect(() => {
    document.title = 'Page not found · Nextrung';
  }, []);
  return (
    <div className="full-page-center not-found">
      <Link to="/" className="not-found-brand" aria-label="Nextrung home"><Brand /></Link>
      <EmptyState
        icon="search"
        title="Page not found"
        action={<Link to={isAuthenticated ? '/app' : '/login'} className="btn btn-primary">Go to {isAuthenticated ? 'dashboard' : 'log in'}</Link>}
      >
        The page you’re looking for doesn’t exist or has moved.
      </EmptyState>
    </div>
  );
}
