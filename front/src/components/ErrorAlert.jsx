export function ErrorAlert({ message }) {
  if (!message) return null;

  return (
    <div className="alert alert-danger d-flex align-items-start gap-2" role="alert">
      <i className="bi bi-exclamation-triangle-fill mt-1" aria-hidden="true" />
      <div>{message}</div>
    </div>
  );
}
