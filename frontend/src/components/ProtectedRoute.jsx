import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Spinner } from './ui';

export default function ProtectedRoute({ children }) {
  const { status } = useAuth();
  const location = useLocation();
  if (status === 'checking') {
    return (
      <div className="full-page-center">
        <Spinner label="Loading your workspace…" />
      </div>
    );
  }
  if (status !== 'authenticated') {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return children;
}

export function GuestRoute({ children }) {
  const { status } = useAuth();
  if (status === 'checking') {
    return (
      <div className="full-page-center">
        <Spinner />
      </div>
    );
  }
  if (status === 'authenticated') return <Navigate to="/app" replace />;
  return children;
}
