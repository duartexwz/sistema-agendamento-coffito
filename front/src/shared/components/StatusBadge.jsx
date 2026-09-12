import { getStatus } from '../utils/reservas.js';

export function StatusBadge({ statusId }) {
  const status = getStatus(statusId);
  const className = status.tone === 'purple' || status.tone === 'teal'
    ? `badge badge-${status.tone}`
    : `badge text-bg-${status.tone}`;

  return <span className={className}>{status.nome}</span>;
}
