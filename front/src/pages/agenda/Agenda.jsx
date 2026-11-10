import { useMemo, useState } from 'react';
import './Agenda.css';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import listPlugin from '@fullcalendar/list';
import bootstrap5Plugin from '@fullcalendar/bootstrap5';
import { STATUS, STATUS_EVENT_COLORS } from '../../utils/constants/domain.js';
import {
  getFaixa,
  getQuantidadeParticipantes,
  getSolicitanteReserva,
  getSpaceFitMessage,
  getStatus,
} from '../../utils/reservas.js';
import { compareReservasByStartDateTime, formatDate, isReservaUpcomingOrActive } from '../../utils/date.js';

export function Agenda({ reservas, espacos, publicMode = false }) {
  const [filters, setFilters] = useState({ espaco_id: '' });
  const [selectedReserva, setSelectedReserva] = useState(null);

  const filteredReservas = useMemo(() => {
    return reservas
      .filter((reserva) => reserva.status_id === STATUS.APROVADA.id)
      .filter((reserva) => {
        const espacoOk =
          !filters.espaco_id ||
          reserva.espaco_solicitado_id === Number(filters.espaco_id) ||
          reserva.espaco_aprovado_id === Number(filters.espaco_id);
        return espacoOk;
      });
  }, [filters, reservas]);

  const upcomingReservas = useMemo(() => {
    return [...filteredReservas]
      .filter((reserva) => isReservaUpcomingOrActive(reserva))
      .sort(compareReservasByStartDateTime);
  }, [filteredReservas]);

  const events = filteredReservas.map((reserva) => {
    const espaco = espacos.find((item) => item.id === (reserva.espaco_aprovado_id ?? reserva.espaco_solicitado_id));
    const color = getUrgency(reserva.data_inicio).color ?? STATUS_EVENT_COLORS[reserva.status_id] ?? '#0d6efd';
    const start = buildCalendarDate(reserva.data_inicio, reserva.horario_inicio);
    const end = getCalendarEventEnd(reserva, start);

    return {
      id: String(reserva.id),
      title: reserva.nome_evento,
      start,
      end,
      backgroundColor: color,
      borderColor: color,
      extendedProps: {
        protocolo: reserva.protocolo,
        espaco: espaco?.nome ?? 'Espaco a definir',
        status: getStatus(reserva.status_id).nome,
        faixa: getFaixa(reserva.faixa_participantes).label,
        horario: `${formatTimeLabel(reserva.horario_inicio)} - ${formatTimeLabel(reserva.horario_fim)}`,
        tipo: getEventType(espaco, reserva),
        recursos: reserva.recursos,
        reserva,
      },
    };
  });

  const firstEventDate = upcomingReservas[0]?.data_inicio;
  const publicInitialDate = publicMode ? firstEventDate ?? new Date().toISOString().slice(0, 10) : undefined;
  const monthViewName = publicMode ? 'dayGridEventWindow' : 'dayGridMonth';

  return (
    <section className={publicMode ? 'public-agenda-shell' : 'view-stack'}>
      {!publicMode && (
        <div className="section-title">
          <div>
            <p className="eyebrow">Agenda institucional</p>
            <h2>Eventos aprovados</h2>
          </div>
          <div className="filters-row">
            <select
              className="form-select"
              value={filters.espaco_id}
              onChange={(event) => setFilters((current) => ({ ...current, espaco_id: event.target.value }))}
              aria-label="Filtrar por espaco"
            >
              <option value="">Todos os espacos</option>
              {espacos.map((espaco) => (
                <option key={espaco.id} value={espaco.id}>
                  {espaco.nome}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      <div className={publicMode ? 'agenda-board public-agenda-board' : 'agenda-board'}>
        <aside className="agenda-side-panel" aria-label="Proximos eventos">
          <ProximityLegend />

          <div className="agenda-side-content">
            <div className="agenda-side-header">
              <p className="eyebrow">Eventos por proximidade</p>
              <h3>Proximos eventos aprovados</h3>
            </div>

            <div className="upcoming-list">
              {upcomingReservas.map((reserva) => {
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
                        <li>{getFaixa(reserva.faixa_participantes).label}</li>
                        <li>{reserva.recursos.length ? reserva.recursos.join(', ') : 'Sem recursos informados'}</li>
                      </ul>
                      <button className="btn btn-sm btn-light" type="button" onClick={() => setSelectedReserva(reserva)}>
                        Ver mais
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
          </div>
        </aside>

        <div className="panel calendar-panel colorful-calendar-panel">
          <FullCalendar
            key={publicMode ? `public-calendar-${publicInitialDate}` : 'internal-calendar'}
            plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin, listPlugin, bootstrap5Plugin]}
            themeSystem="bootstrap5"
            initialView={monthViewName}
            initialDate={publicInitialDate}
            locale="pt-br"
            height={publicMode ? 'calc(100vh - 86px)' : 'auto'}
            nowIndicator
            eventDisplay="block"
            eventMinHeight={52}
            eventShortHeight={42}
            dayMaxEvents={2}
            fixedWeekCount={false}
            slotEventOverlap={false}
            slotMinTime="07:00:00"
            slotMaxTime="21:00:00"
            headerToolbar={{
              left: 'prev,next today',
              center: 'title',
              right: `${monthViewName},timeGridWeek,listMonth`,
            }}
            views={{
              dayGridEventWindow: {
                type: 'dayGrid',
                duration: { weeks: 4 },
                dateAlignment: 'week',
                dateIncrement: { weeks: 4 },
                buttonText: 'Mês',
              },
              listMonth: {
                buttonText: 'Lista',
              },
            }}
            buttonText={{
              today: 'Hoje',
              month: 'Mês',
              week: 'Semana',
              list: 'Lista',
            }}
            events={events}
            eventClick={(info) => setSelectedReserva(info.event.extendedProps.reserva)}
            eventContent={renderEventContent}
          />
        </div>
      </div>

      {selectedReserva && (
        <ReservaModal
          reserva={selectedReserva}
          espaco={findEspaco(espacos, selectedReserva)}
          publicMode={publicMode}
          onClose={() => setSelectedReserva(null)}
        />
      )}
    </section>
  );
}

function renderEventContent(info) {
  const props = info.event.extendedProps;

  if (info.view.type.startsWith('list')) {
    return (
      <div className="calendar-list-event">
        <div>
          <strong>{info.event.title}</strong>
          <span>{props.espaco}</span>
        </div>
        <div className="calendar-list-meta">
          <span>{props.horario}</span>
          <span>{props.faixa}</span>
          <span>{props.tipo}</span>
          {props.recursos?.length > 0 && <span>{props.recursos.slice(0, 3).join(', ')}</span>}
        </div>
      </div>
    );
  }

  if (info.view.type.startsWith('timeGrid')) {
    return (
      <div className="calendar-event calendar-event-week">
        <strong title={info.event.title}>{info.event.title}</strong>
        <span>{props.horario}</span>
        <small>{props.espaco}</small>
      </div>
    );
  }

  return (
    <div className="calendar-event calendar-event-rich">
      <strong>{info.event.title}</strong>
      <span>
        {info.event.start?.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })} -{' '}
        {info.event.end?.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
      </span>
      <span>{props.espaco}</span>
    </div>
  );
}

const URGENCY_LEVELS = [
  { id: 'today', maxDays: 0, label: 'Hoje', legend: 'Proximo evento', color: '#b87500', soft: '#fff4dc' },
  { id: 'critical', maxDays: 2, label: 'Urgente', legend: 'Ate 2 dias', color: '#9a6b13', soft: '#fff7e8' },
  { id: 'soon', maxDays: 7, label: 'Proximo', legend: 'Ate 7 dias', color: '#0f7c8f', soft: '#e8f7fa' },
  { id: 'planned', maxDays: 14, label: 'Planejado', legend: 'Ate 14 dias', color: '#1f5f8b', soft: '#edf6ff' },
  { id: 'normal', maxDays: Infinity, label: 'Programado', legend: 'Mais distante', color: '#2f7d4f', soft: '#edf8f1' },
];

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

function formatTimeLabel(timeString) {
  if (!timeString) return '--:--';
  return String(timeString).slice(0, 5);
}

function buildCalendarDate(dateString, timeString) {
  const safeTime = timeString ? String(timeString).slice(0, 8) : '00:00:00';
  return new Date(`${dateString}T${safeTime}`);
}

function getCalendarEventEnd(reserva, start) {
  const end = buildCalendarDate(reserva.data_fim ?? reserva.data_inicio, reserva.horario_fim ?? reserva.horario_inicio);

  if (Number.isNaN(end.getTime()) || end <= start) {
    return new Date(start.getTime() + 60 * 60 * 1000);
  }

  return end;
}

function formatDateTimeLabel(dateString, timeString) {
  if (!dateString || !timeString) return '-';
  return `${formatDate(dateString)} as ${formatTimeLabel(timeString)}`;
}

function getCapacityLabel(espaco) {
  if (!espaco?.capacidade_minima && !espaco?.capacidade_maxima) return 'Nao retornada pela API';

  if (espaco.capacidade_minima && espaco.capacidade_maxima) {
    return `${espaco.capacidade_minima} a ${espaco.capacidade_maxima} pessoas`;
  }

  return `Ate ${espaco.capacidade_maxima ?? espaco.capacidade_minima} pessoas`;
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

function ReservaModal({ reserva, espaco, publicMode, onClose }) {
  const status = getStatus(reserva.status_id);
  const solicitante = getSolicitanteReserva(reserva);
  const quantidadeParticipantes = getQuantidadeParticipantes(reserva);
  const requesterType = reserva.origem === 'publica' ? 'Solicitacao publica' : 'Reserva interna';
  const eventType = reserva.tipo_evento ?? reserva.evento?.tipo ?? getEventType(espaco, reserva);
  const requestedSpace = espaco?.nome ?? reserva.local ?? reserva.espaco_nome ?? 'A definir';
  const approvedSpace = reserva.espaco_aprovado_id ? requestedSpace : 'Aguardando definicao';
  const capacityLabel = getCapacityLabel(espaco);
  const fitLabel = getSpaceFitMessage(espaco, reserva.faixa_participantes);
  const eventPeriod = getEventPeriodLabel(reserva);
  const eventObjective = reserva.objetivo || reserva.evento?.programacao || 'Nao informado pela API.';
  const observations = reserva.observacao || reserva.observacoes || reserva.recursos_publicos?.observacoes || 'Sem observacoes adicionais.';
  const resourceLabels = getReservationResources(reserva);
  const disclosureItems = getDisclosureItems(reserva);
  const requesterName =
    solicitante.nome || reserva.organizador || reserva.evento?.organizador || (reserva.solicitante_id ? `Usuario interno #${reserva.solicitante_id}` : 'Nao informado pela API');

  return (
    <div className="event-modal-backdrop" role="presentation" onMouseDown={onClose}>
      <div className="event-modal-shell" onMouseDown={(event) => event.stopPropagation()}>
        <button className="event-modal-close-floating" type="button" onClick={onClose} aria-label="Fechar popup">
          <i className="bi bi-x-lg" aria-hidden="true" />
        </button>
        <section
          className="event-modal dashboard-event-modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby="eventModalTitle"
        >
          <header className="event-modal-header">
            <div>
              <span className="event-type-pill">{eventType}</span>
              <h3 id="eventModalTitle">{reserva.nome_evento}</h3>
              <p>Protocolo {reserva.protocolo || 'nao informado'}</p>
            </div>
          </header>

        <div className="event-modal-section modal-section-highlight">
          <h4>Resumo do evento</h4>
          <div className="event-modal-grid decision-summary-grid">
            <Detail label="Status" value={status.nome} />
            <Detail label="Periodo" value={eventPeriod} />
            <Detail
              label="Publico estimado"
              value={quantidadeParticipantes ? `${quantidadeParticipantes} pessoas (${getFaixa(reserva.faixa_participantes).label})` : getFaixa(reserva.faixa_participantes).label}
            />
            <Detail label="Espaco" value={requestedSpace} />
            <Detail label="Capacidade cadastrada" value={capacityLabel} />
            <Detail label="Compatibilidade" value={fitLabel} />
          </div>
        </div>

        <div className="event-modal-section">
          <h4>Evento e espaco</h4>
          <div className="event-modal-grid">
            <Detail label="Nome do evento" value={reserva.nome_evento} />
            <Detail label="Tipo do evento" value={eventType} />
            <Detail label="Origem" value={requesterType} />
            <Detail label="Espaco aprovado" value={approvedSpace} />
            <Detail label="Protocolo" value={reserva.protocolo || 'Nao informado'} />
            <Detail label="Responsavel pelo evento" value={requesterName} />
          </div>
        </div>

        {!publicMode && (
          <div className="event-modal-section">
            <h4>Contato administrativo</h4>
            <div className="event-modal-grid">
              <Detail label="E-mail" value={solicitante.email || 'Nao retornado pela API'} />
              <Detail label="Telefone" value={solicitante.telefone || 'Nao retornado pela API'} />
              <Detail label="CPF" value={solicitante.cpf || 'Nao retornado pela API'} />
              <Detail label="Profissao / cargo" value={solicitante.profissao || reserva.cargo || 'Nao retornado pela API'} />
            </div>
          </div>
        )}

        <div className="event-modal-section">
          <h4>Objetivo / programacao</h4>
          <p>{eventObjective}</p>
        </div>

        {Array.isArray(reserva.datas) && reserva.datas.length > 0 && (
          <div className="event-modal-section">
            <h4>Datas solicitadas</h4>
            <div className="modal-chip-row">
              {reserva.datas.map((item) => (
                <span key={item.id ?? item.data_inicio ?? item.data} className="modal-chip active">
                  {formatPeriod(item)} - {formatTimeLabel(item.horario_inicio)} as {formatTimeLabel(item.horario_fim)}
                </span>
              ))}
            </div>
          </div>
        )}

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
          <h4>Observacoes do evento</h4>
          <p>{observations}</p>
        </div>

        {!publicMode && Array.isArray(reserva.anexos) && reserva.anexos.length > 0 && (
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
        </section>
      </div>
    </div>
  );
}

function Detail({ label, value }) {
  return (
    <div className="event-detail">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatPeriod(item) {
  const startDate = item.data_inicio ?? item.data;
  const endDate = item.data_fim ?? item.data ?? startDate;

  if (!startDate) return '-';
  if (!endDate || endDate === startDate) return formatDate(startDate);

  return `${formatDate(startDate)} ate ${formatDate(endDate)}`;
}
