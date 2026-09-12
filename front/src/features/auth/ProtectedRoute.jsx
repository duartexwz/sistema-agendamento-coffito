import { LoadingState } from '../../shared/components/LoadingState.jsx';

export function ProtectedRoute({ isAuthenticated, isChecking, children, fallback }) {
  if (isChecking) return <LoadingState />;
  if (!isAuthenticated) return fallback;

  return children;
}
