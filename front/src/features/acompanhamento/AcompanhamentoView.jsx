import { useEffect, useMemo, useState } from 'react';
import './Acompanhamento.css';
import { EmptyState } from '../../shared/components/EmptyState.jsx';
import { StatusBadge } from '../../shared/components/StatusBadge.jsx';
import { formatDate } from '../../shared/utils/date.js';
import { getFriendlyErrorMessage } from '../../shared/utils/errors.js';
import { getFaixa, getQuantidadeParticipantes, getSolicitanteReserva } from '../../shared/utils/reservas.js';
import { STATUS_LIST } from '../../shared/constants/domain.js';
import { isCollaborator } from '../../shared/utils/permissions.js';
import { api } from '../../services/api.js';
import { PublicFormShell } from '../publicReservation/PublicFormShell.jsx';

const STATUS_OPTIONS = [{ id: 'todos', nome: 'Todos os status' }, ...STATUS_LIST];

function getInitialProtocol() {
  return new URLSearchParams(window.location.search).get('protocolo') ?? '';
}

function formatTime(value) {
  return value ? String(value).slice(0, 5) : '--:--';
}

function formatPeriod(reserva) {
  if (!reserva) return '-';
  const sameDay = reserva.data_inicio === reserva.data_fim;
  const dates = sameDay
    ? formatDate(reserva.data_inicio)
    : `${formatDate(reserva.data_inicio)} ate ${formatDate(reserva.data_fim)}`;

  return `${dates} - ${formatTime(reserva.horario_inicio)} as ${formatTime(reserva.horario_fim)}`;
}

function formatDateTime(value) {
  if (!value) return '-';
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(value));
}

function getPublicoLabel(reserva) {
  const quantidade = getQuantidadeParticipantes(reserva);
  if (quantidade) {
    return `${quantidade} pessoas (${getFaixa(reserva.faixa_participantes).label})`;
  }
  return getFaixa(reserva?.faixa_participantes).label;
}

function getEspacoLabel(reserva) {
  return reserva?.espaco_aprovado ?? reserva?.espaco ?? reserva?.espaco_solicitado ?? 'Espaco em analise';
}

function normalizeText(value) {
  return String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

export function AcompanhamentoView({ mode = 'internal', currentUser, onGoPublic, onGoLogin }) {
  if (mode === 'public') {
    return <PublicAcompanhamento onGoPublic={onGoPublic} onGoLogin={onGoLogin} />;
  }

  return <InternalAcompanhamento currentUser={currentUser} />;
}

function PublicAcompanhamento({ onGoPublic, onGoLogin }) {
  const [form, setForm] = useState({ protocolo: getInitialProtocol(), email: '' });
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setResult(null);

    if (!form.protocolo.trim() || !form.email.trim()) {
      setError('Informe o protocolo e o e-mail usado na solicitação.');
      return;
    }

    setLoading(true);
    try {
      const data = await api.trackPublicReservation(form);
      setResult(data);
    } catch (requestError) {
      setError(getFriendlyErrorMessage(requestError, 'acompanhamento'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <PublicFormShell showGuidance={false}>
      <section className="public-card tracking-public-card">
        <div className="tracking-page-header">
          <div>
            <p className="eyebrow">Acompanhamento de solicitação</p>
            <h2>Consulte o andamento da sua reserva</h2>
            <p>Informe o protocolo recebido e o e-mail usado no formulário.</p>
          </div>
          <button className="btn btn-outline-secondary" type="button" onClick={onGoLogin}>
            Area interna
          </button>
        </div>

        <form className="tracking-query-form" onSubmit={handleSubmit} noValidate>
          <label className="form-field">
            <span>Protocolo</span>
            <input
              className="form-control"
              value={form.protocolo}
              onChange={(event) => setForm((current) => ({ ...current, protocolo: event.target.value }))}
              placeholder="Ex.: 08 2026 1"
            />
          </label>
          <label className="form-field">
            <span>E-mail usado na solicitação</span>
            <input
              className="form-control"
              type="email"
              value={form.email}
              onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
              placeholder="seuemail@exemplo.com"
            />
          </label>
          <button className="btn btn-primary" type="submit" disabled={loading}>
            {loading ? 'Consultando...' : 'Consultar solicitação'}
          </button>
        </form>

        {error && <div className="alert alert-danger">{error}</div>}
        {result?.reserva && <TrackingResult reserva={result.reserva} historico={result.historico} />}

        {!result && (
          <div className="tracking-empty-callout">
            <i className="bi bi-search" aria-hidden="true" />
            <div>
              <strong>A consulta é protegida por protocolo e e-mail.</strong>
              <span>Esses dados ajudam a evitar que terceiros vejam informações da sua solicitação.</span>
            </div>
          </div>
        )}

        <div className="public-actions">
          <button type="button" className="btn btn-outline-secondary" onClick={onGoPublic}>
            Nova solicitação
          </button>
        </div>
      </section>
    </PublicFormShell>
  );
}

function InternalAcompanhamento({ currentUser }) {
  const [reservas, setReservas] = useState([]);
  const [filters, setFilters] = useState({ busca: '', status: 'todos' });
  const [selectedReserva, setSelectedReserva] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const collaborator = isCollaborator(currentUser);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError('');
      try {
        const data = await api.getInternalTracking();
        if (active) setReservas(data);
      } catch (requestError) {
        if (active) setError(getFriendlyErrorMessage(requestError, 'acompanhamento-interno'));
      } finally {
        if (active) setLoading(false);
      }
    }

    load();
    return () => {
      active = false;
    };
  }, []);

  const filteredReservas = useMemo(() => {
    const busca = normalizeText(filters.busca);
    return reservas
      .filter((reserva) => filters.status === 'todos' || String(reserva.status_id) === String(filters.status))
      .filter((reserva) => {
        if (!busca) return true;
        const solicitante = getSolicitanteReserva(reserva);
        return [
          reserva.protocolo,
          reserva.nome_evento,
          solicitante.nome,
          solicitante.email,
          getEspacoLabel(reserva),
          reserva.setor_solicitante,
        ].some((value) => normalizeText(value).includes(busca));
      });
  }, [filters, reservas]);

  return (
    <section className="view-stack tracking-internal-view">
      <div className="tracking-hero">
        <div>
          <p className="eyebrow">Acompanhamento</p>
          <h2>{collaborator ? 'Acompanhamento do meu setor' : 'Acompanhamento de reservas internas'}</h2>
          <p>
            {collaborator
              ? 'Acompanhe suas solicitações e as reservas registradas por usuários do mesmo setor.'
              : 'Acompanhe status, período, espaço e solicitante das reservas registradas internamente.'}
          </p>
        </div>
      </div>

      <div className="panel">
        <div className="panel-header dashboard-panel-header">
          <div>
            <h3>Solicitações internas</h3>
            <p>{filteredReservas.length} registro(s) encontrado(s).</p>
          </div>
          <div className="dashboard-filters tracking-filters">
            <input
              className="form-control form-control-sm"
              type="search"
              placeholder="Buscar protocolo, evento, solicitante ou espaço"
              value={filters.busca}
              onChange={(event) => setFilters((current) => ({ ...current, busca: event.target.value }))}
            />
            <select
              className="form-select form-select-sm"
              value={filters.status}
              onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value }))}
            >
              {STATUS_OPTIONS.map((status) => (
                <option key={status.id} value={status.id}>
                  {status.nome}
                </option>
              ))}
            </select>
          </div>
        </div>

        {loading && <p className="tracking-muted">Carregando solicitações...</p>}
        {error && <div className="alert alert-danger">{error}</div>}
        {!loading && !error && filteredReservas.length === 0 && (
          <EmptyState title="Nenhuma solicitação encontrada" description="Altere os filtros ou crie uma nova solicitação." />
        )}

        {!loading && !error && filteredReservas.length > 0 && (
          <div className="table-responsive">
            <table className="table align-middle dashboard-events-table tracking-table">
              <thead>
                <tr>
                  <th>Evento</th>
                  <th>Período</th>
                  <th>Espaço</th>
                  <th>Solicitante</th>
                  <th>Status</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {filteredReservas.map((reserva) => {
                  const solicitante = getSolicitanteReserva(reserva);
                  return (
                    <tr key={reserva.id}>
                      <td>
                        <strong>{reserva.nome_evento}</strong>
                        <span className="table-subtitle">{reserva.protocolo}</span>
                      </td>
                      <td>{formatPeriod(reserva)}</td>
                      <td>{getEspacoLabel(reserva)}</td>
                      <td>
                        {solicitante.nome || 'Não informado'}
                        {reserva.setor_solicitante && (
                          <span className="table-subtitle">Setor: {reserva.setor_solicitante}</span>
                        )}
                      </td>
                      <td>
                        <StatusBadge statusId={reserva.status_id} />
                      </td>
                      <td>
                        <button className="btn btn-outline-primary btn-sm" type="button" onClick={() => setSelectedReserva(reserva)}>
                          Ver detalhes
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedReserva && (
        <TrackingDetailsModal reserva={selectedReserva} onClose={() => setSelectedReserva(null)} />
      )}
    </section>
  );
}

function TrackingResult({ reserva, historico = [] }) {
  const solicitante = getSolicitanteReserva(reserva);

  return (
    <section className="tracking-result">
      <div className="tracking-status-card">
        <div>
          <span>Status atual</span>
          <StatusBadge statusId={reserva.status_id} />
        </div>
        <strong>{reserva.status}</strong>
      </div>

      <div className="tracking-detail-grid">
        <DetailItem label="Protocolo" value={reserva.protocolo} />
        <DetailItem label="Evento" value={reserva.nome_evento} />
        <DetailItem label="Data e horário" value={formatPeriod(reserva)} />
        <DetailItem label="Espaço" value={getEspacoLabel(reserva)} />
        <DetailItem label="Público estimado" value={getPublicoLabel(reserva)} />
        <DetailItem label="Solicitante" value={solicitante.nome || 'Não informado'} />
      </div>

      {(reserva.objetivo || reserva.observacoes) && (
        <div className="tracking-notes">
          {reserva.objetivo && (
            <div>
              <h3>Objetivo</h3>
              <p>{reserva.objetivo}</p>
            </div>
          )}
          {reserva.observacoes && (
            <div>
              <h3>Observações / ajuste solicitado</h3>
              <p>{reserva.observacoes}</p>
            </div>
          )}
        </div>
      )}

      <Timeline historico={historico} />
    </section>
  );
}

function TrackingDetailsModal({ reserva, onClose }) {
  const solicitante = getSolicitanteReserva(reserva);
  const statusName = getStatusName(reserva);

  return (
    <div className="event-modal-backdrop" role="presentation" onMouseDown={onClose}>
      <div className="event-modal-shell" onMouseDown={(event) => event.stopPropagation()}>
        <button className="event-modal-close-floating" type="button" onClick={onClose} aria-label="Fechar">
          <i className="bi bi-x-lg" aria-hidden="true" />
        </button>
        <article className="event-modal tracking-details-modal" role="dialog" aria-modal="true" aria-labelledby="trackingDetailsTitle">
          <header className="tracking-details-header">
            <div>
              <span className="event-type-pill">
                <i className="bi bi-clipboard-check me-1" aria-hidden="true" />
                Acompanhamento
              </span>
              <h3 id="trackingDetailsTitle">{reserva.nome_evento}</h3>
              <p>Protocolo {reserva.protocolo}</p>
            </div>
            <div className="tracking-details-status">
              <span>Status atual</span>
              <StatusBadge statusId={reserva.status_id} />
            </div>
          </header>

          <div className="tracking-details-body">
            <section className="tracking-details-summary" aria-label="Resumo da solicitação">
              <div>
                <span>Situação da solicitação</span>
                <strong>{statusName}</strong>
              </div>
              <p>
                Consulte abaixo os dados registrados para esta reserva. Esta tela é somente leitura.
              </p>
            </section>

            <section className="tracking-details-list" aria-label="Dados principais da reserva">
              <TrackingInfo icon="bi-hash" label="Protocolo" value={reserva.protocolo} />
              <TrackingInfo icon="bi-calendar-event" label="Data e horário" value={formatPeriod(reserva)} />
              <TrackingInfo icon="bi-building" label="Espaço" value={getEspacoLabel(reserva)} />
              <TrackingInfo icon="bi-people" label="Público estimado" value={getPublicoLabel(reserva)} />
              <TrackingInfo icon="bi-person" label="Solicitante" value={solicitante.nome || 'Não informado'} />
              {reserva.setor_solicitante && (
                <TrackingInfo icon="bi-diagram-3" label="Setor" value={reserva.setor_solicitante} />
              )}
              <TrackingInfo icon="bi-envelope" label="E-mail" value={solicitante.email || 'Não informado'} />
            </section>

            {(reserva.objetivo || reserva.observacoes) && (
              <section className="tracking-details-notes">
                {reserva.objetivo && (
                  <div>
                    <h4>Objetivo</h4>
                    <p>{reserva.objetivo}</p>
                  </div>
                )}
                {reserva.observacoes && (
                  <div>
                    <h4>Observações / ajuste solicitado</h4>
                    <p>{reserva.observacoes}</p>
                  </div>
                )}
              </section>
            )}
          </div>
        </article>
      </div>
    </div>
  );
}

function TrackingInfo({ icon, label, value }) {
  return (
    <div className="tracking-info-row">
      <i className={`bi ${icon}`} aria-hidden="true" />
      <div>
        <span>{label}</span>
        <strong>{value || '-'}</strong>
      </div>
    </div>
  );
}

function getStatusName(reserva) {
  return reserva.status ?? STATUS_LIST.find((status) => status.id === reserva.status_id)?.nome ?? 'Status não informado';
}

function DetailItem({ label, value }) {
  return (
    <div className="event-detail">
      <span>{label}</span>
      <strong>{value || '-'}</strong>
    </div>
  );
}

function Timeline({ historico = [] }) {
  if (historico.length === 0) {
    return null;
  }

  return (
    <div className="tracking-timeline">
      <h3>Linha do tempo</h3>
      <ol>
        {historico.map((item, index) => (
          <li key={`${item.acao}-${item.created_at}-${index}`}>
            <span>{formatDateTime(item.created_at)}</span>
            <strong>{item.status || item.acao}</strong>
            {item.observacao && <p>{item.observacao}</p>}
          </li>
        ))}
      </ol>
    </div>
  );
}
