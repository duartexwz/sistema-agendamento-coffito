import { LoadingState } from './LoadingState.jsx';

export function ProtectedRoute({ isAuthenticated, isChecking, children, fallback }) {
  if (isChecking) return <LoadingState />;
  if (!isAuthenticated) return fallback;

  return children;
}
