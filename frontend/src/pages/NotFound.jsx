import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { EmptyState } from '../components/ui';

export default function NotFound() {
  const { isAuthenticated } = useAuth();
  return (
    <div className="full-page-center">
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
