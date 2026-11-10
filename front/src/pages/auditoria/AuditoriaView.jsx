import { useEffect, useMemo, useState } from 'react';
import './Auditoria.css';
import { EmptyState } from '../../components/EmptyState.jsx';
import { getFriendlyErrorMessage } from '../../utils/errors.js';
import { api } from '../../services/api.js';

const PAGE_SIZE = 50;

const ENTITY_OPTIONS = [
  { value: '', label: 'Todas' },
  { value: 'reserva', label: 'Reservas' },
  { value: 'usuario', label: 'Usuários' },
  { value: 'espaco', label: 'Espaços' },
  { value: 'recurso', label: 'Recursos' },
  { value: 'auth', label: 'Autenticação' },
];

const ACTION_OPTIONS = [
  { value: '', label: 'Todas as ações' },
  { value: 'reserva.criada', label: 'Reserva criada' },
  { value: 'reserva.aprovada', label: 'Reserva aprovada' },
  { value: 'reserva.reprovada', label: 'Reserva reprovada' },
  { value: 'reserva.ajuste_solicitado', label: 'Ajuste solicitado' },
  { value: 'reserva.cancelada', label: 'Reserva cancelada' },
  { value: 'usuario.criado', label: 'Usuário criado' },
  { value: 'usuario.atualizado', label: 'Usuário atualizado' },
  { value: 'usuario.deletado', label: 'Usuário deletado' },
  { value: 'espaco.criado', label: 'Espaço criado' },
  { value: 'espaco.atualizado', label: 'Espaço atualizado' },
  { value: 'recurso.criado', label: 'Recurso criado' },
  { value: 'recurso.atualizado', label: 'Recurso atualizado' },
  { value: 'auth.login_realizado', label: 'Login realizado' },
  { value: 'auth.login_invalido', label: 'Login inválido' },
];

const ACTION_LABELS = Object.fromEntries(ACTION_OPTIONS.filter((item) => item.value).map((item) => [item.value, item.label]));
const ENTITY_LABELS = Object.fromEntries(ENTITY_OPTIONS.filter((item) => item.value).map((item) => [item.value, item.label]));

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function addDays(days) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 10);
}

function formatDateTime(value) {
  if (!value) return '-';
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(value));
}

function getEventInfo(log) {
  const metadata = log.metadata ?? {};
  return metadata.protocolo || metadata.nome_evento
    ? [metadata.protocolo, metadata.nome_evento].filter(Boolean).join(' - ')
    : '-';
}

function compactUserAgent(value) {
  if (!value) return 'Não informado';
  return value.length > 140 ? `${value.slice(0, 140)}...` : value;
}

function formatJson(value) {
  if (!value) return 'Sem dados';
  return JSON.stringify(value, null, 2);
}

function MetadataList({ metadata }) {
  const entries = Object.entries(metadata ?? {}).filter(([, value]) => value !== null && value !== undefined && value !== '');

  if (entries.length === 0) {
    return <p className="audit-muted">Nenhum dado contextual registrado.</p>;
  }

  return (
    <dl className="audit-metadata-list">
      {entries.map(([key, value]) => (
        <div key={key}>
          <dt>{key.replaceAll('_', ' ')}</dt>
          <dd>{String(value)}</dd>
        </div>
      ))}
    </dl>
  );
}

function AuditDetailsModal({ log, onClose }) {
  if (!log) return null;

  return (
    <div className="event-modal-backdrop" role="presentation" onMouseDown={onClose}>
      <div className="event-modal-shell audit-modal-shell" onMouseDown={(event) => event.stopPropagation()}>
        <button className="event-modal-close-floating" type="button" onClick={onClose} aria-label="Fechar">
          <i className="bi bi-x-lg" aria-hidden="true" />
        </button>
        <article className="event-modal audit-modal" role="dialog" aria-modal="true" aria-labelledby="auditDetailsTitle">
          <header className="event-modal-header">
            <div>
              <span className="event-type-pill audit-action-pill">{ACTION_LABELS[log.acao] ?? log.acao}</span>
              <h3 id="auditDetailsTitle">Detalhes da auditoria</h3>
              <p>{formatDateTime(log.created_at)}</p>
            </div>
          </header>

          <div className="event-modal-grid">
            <div className="event-detail">
              <span>Usuário</span>
              <strong>{log.ator_nome || 'Ação pública ou sistema'}</strong>
            </div>
            <div className="event-detail">
              <span>E-mail</span>
              <strong>{log.ator_email || 'Não informado'}</strong>
            </div>
            <div className="event-detail">
              <span>Entidade</span>
              <strong>{ENTITY_LABELS[log.entidade_tipo] ?? log.entidade_tipo}</strong>
            </div>
            <div className="event-detail">
              <span>Registro</span>
              <strong>{log.entidade_id ?? '-'}</strong>
            </div>
          </div>

          <section className="event-modal-section">
            <h4>Resumo</h4>
            <p>{log.descricao}</p>
          </section>

          <section className="event-modal-section">
            <h4>Dados principais</h4>
            <MetadataList metadata={log.metadata} />
          </section>

          <section className="event-modal-section audit-technical-section">
            <h4>Informação técnica</h4>
            <div className="audit-tech-grid">
              <span>IP: {log.ip_address || 'Não informado'}</span>
              <span>Navegador: {compactUserAgent(log.user_agent)}</span>
            </div>
          </section>

          <section className="event-modal-section">
            <h4>Antes e depois</h4>
            <div className="audit-json-grid">
              <pre className="audit-json-box">{formatJson(log.dados_antes)}</pre>
              <pre className="audit-json-box">{formatJson(log.dados_depois)}</pre>
            </div>
          </section>
        </article>
      </div>
    </div>
  );
}

export function AuditoriaView() {
  const [filters, setFilters] = useState({
    data_inicio: addDays(-30),
    data_fim: todayIso(),
    entidade_tipo: '',
    acao: '',
    busca: '',
  });
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedLog, setSelectedLog] = useState(null);

  const metrics = useMemo(() => {
    const today = todayIso();
    return {
      hoje: logs.filter((log) => String(log.created_at).startsWith(today)).length,
      reservas: logs.filter((log) => log.entidade_tipo === 'reserva').length,
      usuarios: logs.filter((log) => log.entidade_tipo === 'usuario').length,
      falhasLogin: logs.filter((log) => log.acao === 'auth.login_invalido').length,
    };
  }, [logs]);

  async function loadAuditoria(nextFilters = filters) {
    setLoading(true);
    setError('');

    try {
      const result = await api.getAuditoria({
        ...nextFilters,
        offset: 0,
        limit: PAGE_SIZE,
      });
      setLogs(result.logs);
      setTotal(result.total);
    } catch (loadError) {
      setError(getFriendlyErrorMessage(loadError, 'auditoria'));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAuditoria();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function updateFilter(field, value) {
    setFilters((current) => ({ ...current, [field]: value }));
  }

  function submitFilters(event) {
    event.preventDefault();
    loadAuditoria(filters);
  }

  return (
    <section className="view-stack">
      <div className="section-title admin-users-title">
        <div>
          <p className="eyebrow">Auditoria do sistema</p>
          <h2>Logs de atividades</h2>
          <p>{total} registro(s) encontrado(s)</p>
        </div>
        <button className="btn btn-outline-primary" type="button" onClick={() => loadAuditoria(filters)}>
          <i className="bi bi-arrow-clockwise me-2" aria-hidden="true" />
          Atualizar
        </button>
      </div>

      <div className="metric-grid audit-metric-grid">
        <article className="metric-card metric-card-today">
          <i className="bi bi-calendar2-check" aria-hidden="true" />
          <span>Ações hoje</span>
          <strong>{metrics.hoje}</strong>
        </article>
        <article className="metric-card metric-card-pending">
          <i className="bi bi-journal-check" aria-hidden="true" />
          <span>Reservas alteradas</span>
          <strong>{metrics.reservas}</strong>
        </article>
        <article className="metric-card metric-card-approved">
          <i className="bi bi-people" aria-hidden="true" />
          <span>Usuários alterados</span>
          <strong>{metrics.usuarios}</strong>
        </article>
        <article className="metric-card metric-card-cancelled">
          <i className="bi bi-shield-exclamation" aria-hidden="true" />
          <span>Falhas de login</span>
          <strong>{metrics.falhasLogin}</strong>
        </article>
      </div>

      <form className="panel audit-filters" onSubmit={submitFilters}>
        <label className="form-label">
          Data inicial
          <input
            className="form-control"
            type="date"
            value={filters.data_inicio}
            onChange={(event) => updateFilter('data_inicio', event.target.value)}
          />
        </label>
        <label className="form-label">
          Data final
          <input
            className="form-control"
            type="date"
            value={filters.data_fim}
            onChange={(event) => updateFilter('data_fim', event.target.value)}
          />
        </label>
        <label className="form-label">
          Entidade
          <select
            className="form-select"
            value={filters.entidade_tipo}
            onChange={(event) => updateFilter('entidade_tipo', event.target.value)}
          >
            {ENTITY_OPTIONS.map((item) => (
              <option key={item.value || 'all'} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        <label className="form-label">
          Ação
          <select className="form-select" value={filters.acao} onChange={(event) => updateFilter('acao', event.target.value)}>
            {ACTION_OPTIONS.map((item) => (
              <option key={item.value || 'all'} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        <label className="form-label audit-search-label">
          Busca
          <input
            className="form-control"
            type="search"
            placeholder="Protocolo, evento, usuário ou descrição"
            value={filters.busca}
            onChange={(event) => updateFilter('busca', event.target.value)}
          />
        </label>
        <button className="btn btn-primary" type="submit">
          Filtrar
        </button>
      </form>

      {error && (
        <div className="alert alert-danger user-form-alert" role="alert">
          {error}
        </div>
      )}

      <div className="panel admin-users-panel">
        {loading ? (
          <div className="loading-state">Carregando auditoria...</div>
        ) : logs.length === 0 ? (
          <EmptyState
            icon="bi-clock-history"
            title="Nenhum log encontrado"
            description="Altere os filtros ou gere uma nova ação no sistema para consultar a trilha de auditoria."
          />
        ) : (
          <div className="table-responsive">
            <table className="table align-middle admin-users-table audit-table">
              <thead>
                <tr>
                  <th>Data/hora</th>
                  <th>Usuário</th>
                  <th>Ação</th>
                  <th>Entidade</th>
                  <th>Protocolo / evento</th>
                  <th>Resumo</th>
                  <th>Detalhes</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td>{formatDateTime(log.created_at)}</td>
                    <td>
                      <div className="user-cell audit-user-cell">
                        <div>
                          <strong>{log.ator_nome || 'Público / sistema'}</strong>
                          <span>{log.ator_email || 'Sem usuário autenticado'}</span>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className="badge text-bg-primary">{ACTION_LABELS[log.acao] ?? log.acao}</span>
                    </td>
                    <td>{ENTITY_LABELS[log.entidade_tipo] ?? log.entidade_tipo}</td>
                    <td>{getEventInfo(log)}</td>
                    <td>{log.descricao}</td>
                    <td>
                      <button className="btn btn-outline-primary btn-sm" type="button" onClick={() => setSelectedLog(log)}>
                        Ver detalhes
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <AuditDetailsModal log={selectedLog} onClose={() => setSelectedLog(null)} />
    </section>
  );
}
