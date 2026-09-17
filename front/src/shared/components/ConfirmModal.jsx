import { useEffect, useRef } from 'react';
import { AlertTriangle, Trash2, Info } from 'lucide-react';
import './ConfirmModal.css';

const ICON_BY_VARIANT = {
  danger: Trash2,
  warning: AlertTriangle,
  primary: Info,
};

export function ConfirmModal({
  open = false,
  variant = 'danger',
  title,
  description,
  confirmLabel = 'Confirmar',
  cancelLabel = 'Cancelar',
  onConfirm,
  onClose,
  loading = false,
  children,
  icon: CustomIcon,
}) {
  const confirmButtonRef = useRef(null);
  const Icon = CustomIcon ?? ICON_BY_VARIANT[variant] ?? Trash2;

  useEffect(() => {
    if (!open) return undefined;

    function handleKeyDown(event) {
      if (event.key === 'Escape' && !loading) onClose?.();
    }

    document.addEventListener('keydown', handleKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [open, loading, onClose]);

  if (!open) return null;

  return (
    <div className="event-modal-backdrop" role="presentation" onMouseDown={loading ? undefined : onClose}>
      <section
        className="event-modal confirm-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirmModalTitle"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="event-modal-header confirm-modal-header">
          <div className="confirm-modal-title-group">
            <span className={`confirm-icon confirm-icon--${variant}`} aria-hidden="true">
              <Icon size={20} />
            </span>
            <div>
              <h3 id="confirmModalTitle">{title}</h3>
              {description && <p>{description}</p>}
            </div>
          </div>
          <button
            className="btn btn-light btn-sm"
            type="button"
            onClick={onClose}
            disabled={loading}
            aria-label="Fechar"
          >
            <i className="bi bi-x-lg" aria-hidden="true" />
          </button>
        </header>

        {children && <div className="confirm-modal-body">{children}</div>}

        <footer className="user-modal-actions">
          <button className="btn btn-outline-secondary" type="button" onClick={onClose} disabled={loading}>
            {cancelLabel}
          </button>
          <button
            ref={confirmButtonRef}
            className={`btn ${variant === 'danger' ? 'btn-danger' : variant === 'warning' ? 'btn-warning' : 'btn-primary'}`}
            type="button"
            onClick={onConfirm}
            disabled={loading}
          >
            {loading ? 'Processando...' : confirmLabel}
          </button>
        </footer>
      </section>
    </div>
  );
}
