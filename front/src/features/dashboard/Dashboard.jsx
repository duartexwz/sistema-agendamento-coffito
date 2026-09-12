import { useEffect, useMemo, useState } from 'react';
import './Dashboard.css';
import { PERFIS, STATUS } from '../../shared/constants/domain.js';
import { StatusBadge } from '../../shared/components/StatusBadge.jsx';
import { EmptyState } from '../../shared/components/EmptyState.jsx';
import { compareReservasByStartDateTime, formatDate, isReservaUpcomingOrActive } from '../../shared/utils/date.js';
import { getFriendlyErrorMessage } from '../../shared/utils/errors.js';
import { getFaixa, getQuantidadeParticipantes, getSolicitanteReserva, getSpaceFitMessage } from '../../shared/utils/reservas.js';
import { canAdministrateReservas } from '../../shared/utils/permissions.js';

const EVENT_STATUS_PRIORITY = {
  [STATUS.ANALISE.id]: 0,
  [STATUS.ENVIADA.id]: 1,
  [STATUS.COMPLEMENTACAO.id]: 2,
  [STATUS.REMANEJADA.id]: 3,
  [STATUS.APROVADA.id]: 4,
};

const DASHBOARD_PAGE_SIZE = 6;
const DASHBOARD_CARD_LIMIT = 6;

const URGENCY_LEVELS = [
  { id: 'today', maxDays: 0, label: 'Hoje', legend: 'Proximo evento', color: '#b87500', soft: '#fff4dc' },
  { id: 'critical', maxDays: 2, label: 'Urgente', legend: 'Ate 2 dias', color: '#9a6b13', soft: '#fff7e8' },
  { id: 'soon', maxDays: 7, label: 'Proximo', legend: 'Ate 7 dias', color: '#0f7c8f', soft: '#e8f7fa' },
  { id: 'planned', maxDays: 14, label: 'Planejado', legend: 'Ate 14 dias', color: '#1f5f8b', soft: '#edf6ff' },
  { id: 'normal', maxDays: Infinity, label: 'Programado', legend: 'Mais distante', color: '#2f7d4f', soft: '#edf8f1' },
];

const QUICK_FILTERS = {
  today: { statuses: null },
  pending: {
    statuses: [STATUS.ENVIADA.id, STATUS.ANALISE.id, STATUS.COMPLEMENTACAO.id, STATUS.REMANEJADA.id],
  },
  approved: { statuses: [STATUS.APROVADA.id] },
  rejected: { statuses: [STATUS.REPROVADA.id] },
  cancelled: { statuses: [STATUS.CANCELADA_SOLICITANTE.id, STATUS.CANCELADA_COFFITO.id] },
};

export function Dashboard({
  metrics,
  perfil,
  currentUser,
  reservas,
  espacos,
  onNavigate,
  onAction,
  focusReservaId,
  onFocusHandled,
}) {
  const [filters, setFilters] = useState({ status: 'todos', espaco: 'todos', busca: '' });
  const [quickFilter, setQuickFilter] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedReserva, setSelectedReserva] = useState(null);
  const perfilAtual = PERFIS.find((item) => item.id === perfil);

  const proximosCards = useMemo(() => {
    return reservas
      .filter((reserva) => reserva.status_id === STATUS.APROVADA.id)
      .filter((reserva) => isReservaUpcomingOrActive(reserva))
      .sort(compareReservasByStartDateTime)
      .slice(0, DASHBOARD_CARD_LIMIT);
  }, [reservas]);

  const proximosEventos = useMemo(() => {
    const busca = filters.busca.trim().toLowerCase();

    return reservas
      .filter((reserva) => matchesQuickFilter(reserva, quickFilter))
      .filter((reserva) => filters.status === 'todos' || reserva.status_id === filters.status)
      .filter((reserva) => {
        if (filters.espaco === 'todos') return true;
        return [reserva.espaco_solicitado_id, reserva.espaco_aprovado_id].includes(Number(filters.espaco));
      })
      .filter((reserva) => {
        if (!busca) return true;
        const solicitante = getSolicitanteReserva(reserva);
        return [reserva.nome_evento, reserva.protocolo, solicitante.nome, solicitante.email]
          .filter(Boolean)
          .some((value) => value.toLowerCase().includes(busca));
      })
      .sort((a, b) => {
        const priorityDiff =
          (EVENT_STATUS_PRIORITY[a.status_id] ?? 99) - (EVENT_STATUS_PRIORITY[b.status_id] ?? 99);
        if (priorityDiff !== 0) return priorityDiff;
        return `${a.data_inicio}${a.horario_inicio}`.localeCompare(`${b.data_inicio}${b.horario_inicio}`);
      });
  }, [filters, quickFilter, reservas]);

  const totalEventPages = Math.max(1, Math.ceil(proximosEventos.length / DASHBOARD_PAGE_SIZE));
  const safeEventPage = Math.min(currentPage, totalEventPages);
  const paginatedEventos = proximosEventos.slice(
    (safeEventPage - 1) * DASHBOARD_PAGE_SIZE,
    safeEventPage * DASHBOARD_PAGE_SIZE,
  );

  const selectedEspaco = selectedReserva
    ? findEspaco(espacos, selectedReserva)
    : null;

  useEffect(() => {
    if (!focusReservaId) return;

    const focusedReserva = reservas.find((reserva) => Number(reserva.id) === Number(focusReservaId));
    if (!focusedReserva) return;

    setSelectedReserva(focusedReserva);
    onFocusHandled?.();
  }, [focusReservaId, onFocusHandled, reservas]);

  function updateFilter(field, value) {
    if (field === 'status') setQuickFilter(null);
    setFilters((current) => ({ ...current, [field]: value }));
    setCurrentPage(1);
  }

  function updateQuickFilter(filterId) {
    setQuickFilter((current) => (current === filterId ? null : filterId));
    setFilters((current) => ({ ...current, status: 'todos' }));
    setCurrentPage(1);
  }

  return (
    <section className="view-stack">
      <div className="hero-panel">
        <div>
        
          <h2>Reserva, analise e acompanhamento em um fluxo unico</h2>
          <p>
            Acompanhe disponibilidade, solicitacoes, aprovacao administrativa e necessidades operacionais
            sem depender de planilhas ou formularios soltos.
          </p>
        </div>
        <div className="hero-actions">
          
          <button className="btn btn-light" type="button" onClick={() => onNavigate('nova-reserva')}>
            <i className="bi bi-plus-circle me-2" aria-hidden="true" />
            Nova solicitacao
          </button>
        </div>
      </div>

      <div className="metric-grid">
        <MetricCard
          icon="bi-calendar-day"
          label="Reservas hoje"
          value={metrics?.reservasHoje ?? 0}
          tone="today"
          active={quickFilter === 'today'}
          onClick={() => updateQuickFilter('today')}
        />
        <MetricCard
          icon="bi-hourglass-split"
          label="Pendencias"
          value={metrics?.pendentes ?? 0}
          tone="pending"
          active={quickFilter === 'pending'}
          onClick={() => updateQuickFilter('pending')}
        />
        <MetricCard
          icon="bi-check2-circle"
          label="Aprovadas"
          value={metrics?.aprovadas ?? 0}
          tone="approved"
          active={quickFilter === 'approved'}
          onClick={() => updateQuickFilter('approved')}
        />
        <MetricCard
          icon="bi-x-circle"
          label="Reprovadas"
          value={metrics?.reprovadas ?? 0}
          tone="rejected"
          active={quickFilter === 'rejected'}
          onClick={() => updateQuickFilter('rejected')}
        />
        <MetricCard
          icon="bi-x-octagon"
          label="Canceladas"
          value={metrics?.canceladas ?? 0}
          tone="cancelled"
          active={quickFilter === 'cancelled'}
          onClick={() => updateQuickFilter('cancelled')}
        />
      </div>

      <div className="row g-3 align-items-start">
        <div className="col-12 col-xl-9">
          <div className="panel">
            <div className="panel-header dashboard-panel-header">
              <div>
                <h3>Solicitacoes de eventos</h3>
                <p>Eventos priorizando solicitacoes em analise. {proximosEventos.length} registro(s) no filtro.</p>
              </div>
              <div className="dashboard-filters">
                <input
                  className="form-control form-control-sm"
                  type="search"
                  placeholder="Buscar evento ou protocolo"
                  value={filters.busca}
                  onChange={(event) => updateFilter('busca', event.target.value)}
                />
                <select
                  className="form-select form-select-sm"
                  value={filters.status}
                  onChange={(event) => updateFilter('status', event.target.value)}
                >
                  <option value="todos">Todos os status</option>
                  {Object.values(STATUS).map((status) => (
                    <option key={status.id} value={status.id}>
                      {status.nome}
                    </option>
                  ))}
                </select>
                <select
                  className="form-select form-select-sm"
                  value={filters.espaco}
                  onChange={(event) => updateFilter('espaco', event.target.value)}
                >
                  <option value="todos">Todos os espacos</option>
                  {espacos.map((espaco) => (
                    <option key={espaco.id} value={espaco.id}>
                      {espaco.nome}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {proximosEventos.length === 0 ? (
              <EmptyState title="Sem eventos no filtro atual" description="Altere os filtros para consultar outros eventos." />
            ) : (
              <div className="table-responsive">
                <table className="table align-middle dashboard-events-table">
                  <thead>
                    <tr>
                      <th>Nome do evento</th>
                      <th>Data do evento</th>
                      <th>Tipo de evento</th>
                      <th>Publico / Quantidade de pessoas</th>
                      <th>Status</th>
                      <th>Acoes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedEventos.map((reserva) => (
                      <tr key={reserva.id}>
                        <td>
                          <strong>{reserva.nome_evento}</strong>
                          <span className="table-subtitle">{reserva.protocolo}</span>
                        </td>
                        <td>{getEventDateLabel(reserva)}</td>
                        <td>
                          <span className="origin-badge">{getReservaOriginShortLabel(reserva)}</span>
                        </td>
                        <td>{getPublicoLabel(reserva)}</td>
                        <td>
                          <StatusBadge statusId={reserva.status_id} />
                        </td>
                        <td className="event-action-cell">
                          <button
                            className="btn btn-outline-primary btn-sm"
                            type="button"
                            onClick={() => setSelectedReserva(reserva)}
                          >
                            Ver mais detalhes
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {proximosEventos.length > 0 && (
              <div className="pagination-bar">
                <span>
                  Pagina {safeEventPage} de {totalEventPages}
                </span>
                <div className="btn-group">
                  <button
                    className="btn btn-outline-primary btn-sm"
                    type="button"
                    disabled={safeEventPage === 1}
                    onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
                  >
                    Anterior
                  </button>
                  <button
                    className="btn btn-outline-primary btn-sm"
                    type="button"
                    disabled={safeEventPage === totalEventPages}
                    onClick={() => setCurrentPage((page) => Math.min(totalEventPages, page + 1))}
                  >
                    Proxima
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="col-12 col-xl-3">
          <aside className="dashboard-agenda-panel" aria-label="Eventos por proximidade">
            <ProximityLegend />

            <div className="agenda-side-content dashboard-agenda-content">
              <div className="agenda-side-header">
                <p className="eyebrow">Eventos por proximidade</p>
                <h3>Proximos eventos</h3>
              </div>

              {proximosCards.length === 0 ? (
                <EmptyState title="Sem eventos proximos" description="Eventos aprovados aparecerao aqui." />
              ) : (
                <div className="upcoming-list">
                  {proximosCards.map((reserva) => {
                    const espaco = findEspaco(espacos, reserva);
                    const urgency = getUrgency(reserva.data_inicio);
                    return (
                      <article
                        key={reserva.id}
                        className="upcoming-card"
                        style={{ '--urgency-color': urgency.color, '--urgency-soft': urgency.soft }}
                      >
                        <div className="upcoming-card-date">
                          <strong>{formatDate(reserva.data_inicio)}</strong>
                          <span>{getReservaOriginLabel(reserva)}</span>
                        </div>
                        <div className="upcoming-card-body">
                          <div className="upcoming-card-title">
                            <span className="event-type-pill">{getEventType(espaco, reserva)}</span>
                            <h4>{reserva.nome_evento}</h4>
                          </div>
                          <p>
                            {formatTimeLabel(reserva.horario_inicio)} - {formatTimeLabel(reserva.horario_fim)}
                          </p>
                          <ul>
                            <li>{espaco?.nome ?? 'Espaco a definir'}</li>
                            <li>{getPublicoLabel(reserva)}</li>
                            <li>{reserva.recursos?.length ? reserva.recursos.join(', ') : 'Sem recursos informados'}</li>
                          </ul>
                          <button className="btn btn-sm btn-light" type="button" onClick={() => setSelectedReserva(reserva)}>
                            Ver mais
                          </button>
                        </div>
                      </article>
                    );
                  })}
                </div>
              )}
            </div>
          </aside>
        </div>
      </div>

      {selectedReserva && (
        <DashboardEventModal
          reserva={selectedReserva}
          espaco={selectedEspaco}
          currentUser={currentUser}
          onClose={() => setSelectedReserva(null)}
          onAction={onAction}
        />
      )}
    </section>
  );
}

function MetricCard({ icon, label, value, tone, active = false, onClick }) {
  return (
    <button
      className={`metric-card metric-card-${tone}${active ? ' active' : ''}`}
      type="button"
      onClick={onClick}
      aria-pressed={active}
    >
      <i className={`bi ${icon}`} aria-hidden="true" />
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
    </button>
  );
}

function ProximityLegend() {
  return (
    <div className="legend-row proximity-legend" aria-label="Legenda de proximidade">
      {URGENCY_LEVELS.map((level) => (
        <span key={level.id} className="legend-item">
          <i style={{ background: level.color }} />
          {level.legend}
        </span>
      ))}
    </div>
  );
}

function DashboardEventModal({ reserva, espaco, currentUser, onClose, onAction }) {
  const [motivo, setMotivo] = useState('');
  const [error, setError] = useState('');
  const [submittingAction, setSubmittingAction] = useState('');
  const solicitante = getSolicitanteReserva(reserva);
  const canAdministrate = canAdministrateReservas(currentUser);
  const statusAllowsDecision = [
    STATUS.ENVIADA.id,
    STATUS.ANALISE.id,
    STATUS.COMPLEMENTACAO.id,
    STATUS.REMANEJADA.id,
  ].includes(reserva.status_id);
  const canDecide = statusAllowsDecision && canAdministrate;
  const statusAllowsCancel = ![
    STATUS.CANCELADA_SOLICITANTE.id,
    STATUS.CANCELADA_COFFITO.id,
    STATUS.REPROVADA.id,
    STATUS.REALIZADO.id,
    STATUS.FINALIZADA.id,
  ].includes(reserva.status_id);
  const canCancel = statusAllowsCancel && canAdministrate;
  const canUndoDecision = canAdministrate && [STATUS.APROVADA.id, STATUS.REPROVADA.id].includes(reserva.status_id);
  const requesterName = solicitante.nome || (reserva.solicitante_id ? `Usuario interno #${reserva.solicitante_id}` : 'Nao informado pela API');
  const requesterType = reserva.origem === 'publica' ? 'Solicitacao publica' : 'Reserva interna';
  const contactEmail = valueOrApiFallback(solicitante.email);
  const contactPhone = valueOrApiFallback(solicitante.telefone);
  const requesterDocument = valueOrApiFallback(solicitante.cpf);
  const requesterRole = valueOrApiFallback(solicitante.profissao || reserva.cargo || reserva.cargo_funcao);
  const requestedSpace = espaco?.nome ?? reserva.local ?? reserva.espaco_nome ?? 'A definir pela administracao';
  const approvedSpace = reserva.espaco_aprovado_id ? requestedSpace : 'Ainda nao aprovado';
  const capacityLabel = getCapacityLabel(espaco);
  const fitLabel = getSpaceFitMessage(espaco, reserva.faixa_participantes);
  const eventType = reserva.tipo_evento ?? reserva.evento?.tipo ?? getEventType(espaco, reserva);
  const eventPeriod = getEventPeriodLabel(reserva);
  const eventObjective = reserva.objetivo || reserva.evento?.programacao || 'Nao informado pela API.';
  const observations = reserva.observacao || reserva.observacoes || reserva.recursos_publicos?.observacoes || 'Sem observacoes adicionais.';
  const resourceLabels = getReservationResources(reserva);
  const disclosureItems = getDisclosureItems(reserva);

  async function execute(action) {
    setError('');

    if (action === 'complementacao' && !motivo.trim()) {
      setError('Informe o ajuste que precisa ser solicitado.');
      return;
    }

    if (action === 'reprovar' && !motivo.trim()) {
      setError('Informe a justificativa para reprovar.');
      return;
    }

    if (action === 'cancelar' && !motivo.trim()) {
      setError('Informe a justificativa para cancelar.');
      return;
    }

    const payloadBase = {
      reserva,
      solicitante_nome: solicitante.nome,
      solicitante_email: solicitante.email,
      protocolo: reserva.protocolo,
      nome_evento: reserva.nome_evento,
    };
    const payload =
      action === 'aprovar'
        ? {
            ...payloadBase,
            espaco_aprovado_id: espaco?.id ?? reserva.espaco_solicitado_id,
            observacao: motivo.trim() || 'Aprovado pelo painel.',
          }
        : { ...payloadBase, motivo: motivo.trim(), observacao: motivo.trim() };

    try {
      setSubmittingAction(action);
      const result = await onAction?.(action, reserva.id, payload);
      if (result?.emailWarning) {
        setError(result.emailWarning);
        return;
      }
      onClose();
    } catch (actionError) {
      setError(getFriendlyErrorMessage(actionError, 'acao-admin'));
    } finally {
      setSubmittingAction('');
    }
  }

  return (
    <div className="event-modal-backdrop" role="presentation" onMouseDown={onClose}>
      <div className="event-modal-shell" onMouseDown={(event) => event.stopPropagation()}>
        <button className="event-modal-close-floating" type="button" onClick={onClose} aria-label="Fechar">
          <i className="bi bi-x-lg" aria-hidden="true" />
        </button>
        <section className="event-modal dashboard-event-modal" role="dialog" aria-modal="true">
          <header className="event-modal-header">
            <div>
              <span className="event-type-pill">{requesterType}</span>
              <h3>{reserva.nome_evento}</h3>
              <p>Protocolo {reserva.protocolo || 'nao informado'}</p>
            </div>
          </header>

        <div className="event-modal-section modal-section-highlight">
          <h4>Resumo para decisao</h4>
          <div className="event-modal-grid decision-summary-grid">
            <EventDetail label="Status atual" value={<StatusBadge statusId={reserva.status_id} />} />
            <EventDetail label="Periodo solicitado" value={eventPeriod} />
            <EventDetail label="Publico estimado" value={getPublicoLabel(reserva)} />
            <EventDetail label="Espaco solicitado" value={requestedSpace} />
            <EventDetail label="Capacidade cadastrada" value={capacityLabel} />
            <EventDetail label="Analise de capacidade" value={fitLabel} />
          </div>
        </div>

        <div className="event-modal-section">
          <h4>Solicitante</h4>
          <div className="event-modal-grid">
            <EventDetail label="Nome" value={requesterName} />
            <EventDetail label="Tipo de solicitacao" value={requesterType} />
            <EventDetail label="E-mail" value={contactEmail} />
            <EventDetail label="Telefone" value={contactPhone} />
            <EventDetail label="CPF" value={requesterDocument} />
            <EventDetail label="Profissao / cargo" value={requesterRole} />
          </div>
        </div>

        <div className="event-modal-section">
          <h4>Evento e espaco</h4>
          <div className="event-modal-grid">
            <EventDetail label="Nome do evento" value={reserva.nome_evento} />
            <EventDetail label="Tipo do evento" value={eventType} />
            <EventDetail label="Protocolo" value={reserva.protocolo || 'Nao informado'} />
            <EventDetail label="Espaco aprovado" value={approvedSpace} />
          </div>
        </div>

        <div className="event-modal-section">
          <h4>Objetivo / programacao</h4>
          <p>{eventObjective}</p>
        </div>

        <div className="event-modal-section">
          <h4>Recursos, montagem e apoio</h4>
          <div className="modal-chip-row">
            {resourceLabels.length > 0 ? (
              resourceLabels.map((recurso) => (
                <span key={recurso} className="modal-chip active">
                  {recurso}
                </span>
              ))
            ) : (
              <span className="modal-chip">Nenhum recurso informado</span>
            )}
          </div>
        </div>

        {disclosureItems.length > 0 && (
          <div className="event-modal-section">
            <h4>Divulgacao previa</h4>
            <div className="modal-chip-row">
              {disclosureItems.map((item) => (
                <span key={item} className="modal-chip">
                  {item}
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="event-modal-section">
          <h4>Observacoes da solicitacao</h4>
          <p>{observations}</p>
        </div>

        {Array.isArray(reserva.anexos) && reserva.anexos.length > 0 && (
          <div className="event-modal-section">
            <h4>Anexos</h4>
            <div className="modal-chip-row">
              {reserva.anexos.map((anexo) => (
                <span key={anexo.nome} className="modal-chip">
                  {anexo.nome}
                </span>
              ))}
            </div>
          </div>
        )}

        {canAdministrate && (
          <>
            <div className="dashboard-decision-box">
              <label className="form-label" htmlFor="dashboard-action-motivo">
                Motivo / ajuste / justificativa
              </label>
              <textarea
                id="dashboard-action-motivo"
                className={`form-control ${error ? 'is-invalid' : ''}`}
                rows="3"
                value={motivo}
                onChange={(event) => setMotivo(event.target.value)}
                placeholder="Descreva o ajuste solicitado ou a justificativa da decisao."
              />
              {error && <div className="invalid-feedback d-block">{error}</div>}
              {!statusAllowsDecision && (
                <p className="decision-hint">Este evento nao esta em uma etapa de aprovacao ou reprovacao administrativa.</p>
              )}
              {canUndoDecision && (
                <p className="decision-hint">Use Desfazer para voltar esta reserva para analise quando uma aprovacao ou reprovacao foi feita por engano.</p>
              )}
            </div>

            <footer className="dashboard-modal-actions">
              <button
                className="btn btn-success"
                type="button"
                disabled={!canDecide || Boolean(submittingAction)}
                onClick={() => execute('aprovar')}
              >
                {submittingAction === 'aprovar' ? 'Aprovando...' : 'Aprovar'}
              </button>
              <button
                className="btn btn-warning"
                type="button"
                disabled={!canDecide || Boolean(submittingAction)}
                onClick={() => execute('complementacao')}
              >
                {submittingAction === 'complementacao' ? 'Enviando...' : 'Solicitar ajuste'}
              </button>
              <button
                className="btn btn-danger"
                type="button"
                disabled={!canDecide || Boolean(submittingAction)}
                onClick={() => execute('reprovar')}
              >
                {submittingAction === 'reprovar' ? 'Reprovando...' : 'Reprovar'}
              </button>
              <button
                className="btn btn-secondary"
                type="button"
                disabled={!canCancel || Boolean(submittingAction)}
                onClick={() => execute('cancelar')}
              >
                {submittingAction === 'cancelar' ? 'Cancelando...' : 'Cancelar'}
              </button>
              {canUndoDecision && (
                <button
                  className="btn btn-outline-primary"
                  type="button"
                  disabled={Boolean(submittingAction)}
                  onClick={() => execute('desfazer')}
                >
                  {submittingAction === 'desfazer' ? 'Desfazendo...' : 'Desfazer'}
                </button>
              )}
            </footer>
          </>
        )}
        {!canAdministrate && (
          <div className="dashboard-decision-box">
            <p className="decision-hint mb-0">Visualizacao somente leitura. As acoes administrativas ficam disponiveis para Administrador ou Master.</p>
          </div>
        )}
        </section>
      </div>
    </div>
  );
}

function EventDetail({ label, value }) {
  return (
    <div className="event-detail">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function valueOrApiFallback(value) {
  return value || 'Nao retornado pela API';
}

function findEspaco(espacos, reserva) {
  return espacos.find((item) => item.id === (reserva.espaco_aprovado_id ?? reserva.espaco_solicitado_id));
}

function getUrgency(dateString) {
  const today = new Date();
  const todayOnly = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const eventDate = new Date(`${dateString}T00:00:00`);
  const diffDays = Math.ceil((eventDate - todayOnly) / 86_400_000);
  const normalizedDiff = Math.max(diffDays, 0);
  return URGENCY_LEVELS.find((level) => normalizedDiff <= level.maxDays) ?? URGENCY_LEVELS.at(-1);
}

function getEventType(espaco, reserva) {
  if (reserva.tipo_evento) return reserva.tipo_evento;
  if (espaco?.nome?.toLowerCase().includes('auditorio')) return 'Auditorio';
  if (reserva.faixa_participantes === '110_150') return 'Evento externo';
  if (reserva.nome_evento.toLowerCase().includes('reuniao')) return 'Reuniao';
  return 'Institucional';
}

function getReservaOriginLabel(reserva) {
  return reserva.origem === 'publica' ? 'Evento externo' : 'Solicitacao interna';
}

function getReservaOriginShortLabel(reserva) {
  return reserva.origem === 'publica' ? 'Externo' : 'Interno';
}

function matchesQuickFilter(reserva, filterId) {
  if (!filterId) return true;
  if (filterId === 'today') return reserva.data_inicio === getTodayIso();

  const filter = QUICK_FILTERS[filterId];
  if (!filter?.statuses) return true;
  return filter.statuses.includes(reserva.status_id);
}

function getTodayIso() {
  const today = new Date();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  return `${today.getFullYear()}-${month}-${day}`;
}

function getEventDateLabel(reserva) {
  if (Array.isArray(reserva.datas) && reserva.datas.length > 1) {
    const firstDate = reserva.datas[0].data_inicio ?? reserva.datas[0].data;
    return `${formatDate(firstDate)} as ${formatTimeLabel(reserva.datas[0].horario_inicio)} + ${reserva.datas.length - 1} data(s)`;
  }

  if (!reserva.data_inicio || !reserva.horario_inicio) return '-';
  return `${formatDate(reserva.data_inicio)} as ${formatTimeLabel(reserva.horario_inicio)}`;
}

function getEventPeriodLabel(reserva) {
  if (Array.isArray(reserva.datas) && reserva.datas.length > 1) {
    const firstDate = reserva.datas[0];
    const lastDate = reserva.datas.at(-1);
    const firstLabel = formatDate(firstDate.data_inicio ?? firstDate.data);
    const lastLabel = formatDate(lastDate.data_fim ?? lastDate.data_inicio ?? lastDate.data);
    return `${firstLabel} ate ${lastLabel} (${reserva.datas.length} datas)`;
  }

  const startDate = formatDate(reserva.data_inicio);
  const endDate = formatDate(reserva.data_fim);
  const dateLabel = reserva.data_fim && reserva.data_fim !== reserva.data_inicio ? `${startDate} ate ${endDate}` : startDate;
  return `${dateLabel} - ${formatTimeLabel(reserva.horario_inicio)} as ${formatTimeLabel(reserva.horario_fim)}`;
}

function formatTimeLabel(timeString) {
  if (!timeString) return '--:--';
  return String(timeString).slice(0, 5);
}

function getPublicoLabel(reserva) {
  const faixa = getFaixa(reserva.faixa_participantes).label;
  const quantidade = getQuantidadeParticipantes(reserva);
  return quantidade ? `${quantidade} pessoas (${faixa})` : faixa;
}

function getCapacityLabel(espaco) {
  if (!espaco?.capacidade_minima && !espaco?.capacidade_maxima) return 'Nao retornada pela API';

  if (espaco.capacidade_minima && espaco.capacidade_maxima) {
    return `${espaco.capacidade_minima} a ${espaco.capacidade_maxima} pessoas`;
  }

  return `Ate ${espaco.capacidade_maxima ?? espaco.capacidade_minima} pessoas`;
}

function getReservationResources(reserva) {
  const recursos = (reserva.recursos ?? []).map((recurso) => {
    if (typeof recurso === 'string') return recurso;
    const quantidade = recurso.quantidade ? ` (${recurso.quantidade})` : '';
    return `${recurso.nome ?? recurso.recurso_nome ?? 'Recurso'}${quantidade}`;
  });

  const suporte = Object.entries(reserva.suporte ?? {})
    .filter(([, value]) => value)
    .map(([key]) => formatSupportLabel(key));

  return [...recursos, ...suporte];
}

function getDisclosureItems(reserva) {
  const divulgacao = reserva.divulgacao ?? {};
  const canais = Array.isArray(divulgacao.canais) ? divulgacao.canais : [];
  const items = canais.map((canal) => `Divulgar em ${canal}`);

  if (divulgacao.precisa_inscricao) items.push('Participantes precisam se inscrever');
  if (divulgacao.realizado_anteriormente) items.push(`Ja realizado: ${divulgacao.realizado_anteriormente}`);
  if (divulgacao.material_pronto) items.push('Material de divulgacao pronto');

  return items;
}

function formatSupportLabel(key) {
  const labels = {
    coffee_break: 'Coffee break',
    backdrop: 'Backdrop',
    evento_ornamentado: 'Evento ornamentado',
  };

  return labels[key] ?? key;
}
