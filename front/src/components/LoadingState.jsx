export function LoadingState({ label = 'Carregando dados...' }) {
  return (
    <div className="loading-state" role="status" aria-live="polite">
      <div className="spinner-border text-primary" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
