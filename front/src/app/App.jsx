import { useCallback, useEffect, useState } from 'react';
import './App.css';
import { Layout } from './Layout.jsx';
import { Agenda } from '../features/agenda/Agenda.jsx';
import { AdminQueue } from '../features/administracao/AdminQueue.jsx';
import { Dashboard } from '../features/dashboard/Dashboard.jsx';
import { EspacosView } from '../features/espacos/EspacosView.jsx';
import { RecursosView } from '../features/recursos/RecursosView.jsx';
import { ReservaForm } from '../features/reservas/ReservaForm.jsx';
import { PublicReservationWizard } from '../features/publicReservation/PublicReservationWizard.jsx';
import { AcompanhamentoView } from '../features/acompanhamento/AcompanhamentoView.jsx';
import { AuditoriaView } from '../features/auditoria/AuditoriaView.jsx';
import { LoginPage } from '../features/auth/LoginPage.jsx';
import { ProtectedRoute } from '../features/auth/ProtectedRoute.jsx';
import { useAuth } from '../features/auth/useAuth.js';
import { LoadingState } from '../shared/components/LoadingState.jsx';
import { ErrorAlert } from '../shared/components/ErrorAlert.jsx';
import { api } from '../services/api.js';
import { STATUS } from '../shared/constants/domain.js';
import { getFriendlyErrorMessage } from '../shared/utils/errors.js';
import { getSolicitanteReserva } from '../shared/utils/reservas.js';
import {
  canAccessView,
  canManageCadastros,
  getDefaultViewForUser,
  isCollaborator,
  isMaster,
} from '../shared/utils/permissions.js';

const actionMap = {
  aprovar: api.approveReserva,
  reprovar: api.rejectReserva,
  complementacao: api.requestComplementacao,
  remanejar: api.remanejarReserva,
  cancelar: api.cancelReserva,
  desfazer: api.undoReservaDecision,
};

const VIEW_PATHS = {
  dashboard: '/app',
  'nova-reserva': '/app/nova-solicitacao',
  acompanhamento: '/app/acompanhamento',
  administracao: '/app/administracao',
  espacos: '/app/espacos',
  recursos: '/app/recursos',
  auditoria: '/app/auditoria',
};

const PATH_VIEWS = Object.fromEntries(Object.entries(VIEW_PATHS).map(([view, path]) => [path, view]));
PATH_VIEWS['/'] = 'dashboard';

function getViewFromPath(path) {
  return PATH_VIEWS[getPathOnly(path)] ?? 'dashboard';
}

function getPathOnly(path) {
  return String(path ?? '').split('?')[0];
}

function isPublicRoute(path) {
  return ['/login', '/solicitar-reserva', '/calendario', '/acompanhar-solicitacao'].includes(getPathOnly(path));
}

function upsertById(list, item) {
  if (!item?.id) return list;
  const exists = list.some((current) => Number(current.id) === Number(item.id));
  if (!exists) return [item, ...list];
  return list.map((current) => (Number(current.id) === Number(item.id) ? { ...current, ...item } : current));
}

function upsertManyById(list, items) {
  return items.reduce((currentList, item) => upsertById(currentList, item), list);
}

function removeById(list, id) {
  return list.filter((item) => Number(item.id) !== Number(id));
}

function getCreatedReservas(created) {
  if (Array.isArray(created?.reservas) && created.reservas.length > 0) return created.reservas;
  return created ? [created] : [];
}

function recalculateDashboardMetrics(reservas) {
  const hoje = new Date().toISOString().slice(0, 10);

  return {
    reservasHoje: reservas.filter((reserva) => reserva.data_inicio === hoje).length,
    pendentes: reservas.filter((reserva) =>
      [STATUS.ENVIADA.id, STATUS.ANALISE.id, STATUS.COMPLEMENTACAO.id].includes(reserva.status_id),
    ).length,
    aprovadas: reservas.filter((reserva) => reserva.status_id === STATUS.APROVADA.id).length,
    reprovadas: reservas.filter((reserva) => reserva.status_id === STATUS.REPROVADA.id).length,
    canceladas: reservas.filter((reserva) => String(reserva.status_id).includes('cancelada')).length,
  };
}

function normalizeText(value) {
  return String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

function getEventDate(reserva, dateField, timeField, fallbackTime) {
  if (!reserva?.[dateField]) return null;
  const time = reserva[timeField] || fallbackTime;
  const date = new Date(`${reserva[dateField]}T${String(time).slice(0, 5)}`);
  return Number.isNaN(date.getTime()) ? null : date;
}

function getEventStartDate(reserva) {
  return getEventDate(reserva, 'data_inicio', 'horario_inicio', '00:00');
}

function getEventEndDate(reserva) {
  return getEventDate(
    {
      ...reserva,
      data_fim: reserva?.data_fim || reserva?.data_inicio,
    },
    'data_fim',
    'horario_fim',
    '23:59',
  );
}

function isApprovedReserva(reserva) {
  const statusId = normalizeText(reserva?.status_id);
  const statusName = normalizeText(reserva?.status ?? reserva?.status_nome);

  return (
    statusId === STATUS.APROVADA.id ||
    statusName === 'aprovada' ||
    statusName === 'aprovado' ||
    Number(reserva?.status_id) === 1
  );
}

function getNextApprovedEvent(reservas) {
  const today = new Date();
  const todayOnly = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const approvedEvents = [...reservas]
    .filter(isApprovedReserva)
    .map((reserva) => ({
      reserva,
      startDate: getEventStartDate(reserva),
      endDate: getEventEndDate(reserva),
    }))
    .filter(({ startDate }) => startDate);

  const futureOrToday = approvedEvents
    .filter(({ startDate, endDate }) => (endDate ?? startDate) >= todayOnly)
    .sort((a, b) => a.startDate - b.startDate);

  return futureOrToday[0]?.reserva ?? null;
}

function formatTime(value) {
  return value ? String(value).slice(0, 5) : '--:--';
}

function findEspaco(espacos, reserva) {
  return espacos.find((espaco) => Number(espaco.id) === Number(reserva?.espaco_aprovado_id ?? reserva?.espaco_solicitado_id));
}

function getDaysUntilEvent(reserva) {
  const startDate = getEventStartDate(reserva);
  if (!startDate) return null;

  const today = new Date();
  const todayOnly = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const eventOnly = new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate());
  return Math.ceil((eventOnly - todayOnly) / 86_400_000);
}

function getCountdownLabel(reserva) {
  const days = getDaysUntilEvent(reserva);
  if (days === null) return 'Data a confirmar';
  if (days === 0) return 'Hoje';
  if (days === 1) return 'Amanha';
  if (days === -1) return 'Ontem';
  if (days < 0) return `Ha ${Math.abs(days)} dias`;
  return `Faltam ${days} dias`;
}

function getWeekdayDateLabel(reserva) {
  if (!reserva?.data_inicio) return 'Data nao informada';

  return new Intl.DateTimeFormat('pt-BR', {
    weekday: 'long',
    day: '2-digit',
    month: 'long',
    timeZone: 'UTC',
  }).format(new Date(`${reserva.data_inicio}T00:00:00`));
}

export function App() {
  const { user, isAuthenticated, isChecking, login, logout } = useAuth();
  const [route, setRoute] = useState(() => window.location.pathname);
  const [activeView, setActiveView] = useState(() => getViewFromPath(window.location.pathname));
  const [perfil, setPerfil] = useState('solicitante');
  const [metrics, setMetrics] = useState(null);
  const [usuarios, setUsuarios] = useState([]);
  const [userCatalogs, setUserCatalogs] = useState(null);
  const [espacos, setEspacos] = useState([]);
  const [recursos, setRecursos] = useState([]);
  const [reservas, setReservas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [nextEventPopup, setNextEventPopup] = useState(null);
  const [focusedReservaId, setFocusedReservaId] = useState(null);

  const updateReservasState = useCallback((updater) => {
    setReservas((current) => {
      const nextReservas = typeof updater === 'function' ? updater(current) : updater;
      setMetrics(recalculateDashboardMetrics(nextReservas));
      return nextReservas;
    });
  }, []);

  const loadData = useCallback(async ({ silent = false, currentUser = user } = {}) => {
    if (!silent) setLoading(true);
    setError(null);
    try {
      const [dashboard, usuariosResult, userCatalogsResult, espacosResult, recursosResult, reservasResult] = await Promise.all([
        isCollaborator(currentUser) ? Promise.resolve(null) : api.getDashboard(),
        isCollaborator(currentUser) ? Promise.resolve([]) : api.getUsuarios(),
        isCollaborator(currentUser) ? Promise.resolve(null) : api.getUserCatalogs(),
        api.getEspacos(),
        api.getRecursos(),
        api.getReservas(),
      ]);
      const nextMetrics = dashboard ?? recalculateDashboardMetrics(reservasResult);
      setMetrics({ ...nextMetrics, ...recalculateDashboardMetrics(reservasResult) });
      setUsuarios(usuariosResult);
      setUserCatalogs(userCatalogsResult);
      setEspacos(espacosResult);
      setRecursos(recursosResult);
      setReservas(reservasResult);
      return {
        dashboard: nextMetrics,
        usuarios: usuariosResult,
        userCatalogs: userCatalogsResult,
        espacos: espacosResult,
        recursos: recursosResult,
        reservas: reservasResult,
      };
    } catch (loadError) {
      setError(getFriendlyErrorMessage(loadError, 'carregamento'));
      return null;
    } finally {
      if (!silent) setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    const publicDataRoute = ['/solicitar-reserva', '/calendario'].includes(route);

    if (isChecking) return;
    if (isAuthenticated || publicDataRoute) {
      loadData();
      return;
    }

    setLoading(false);
  }, [isAuthenticated, isChecking, loadData, route]);

  useEffect(() => {
    function handlePopState() {
      const nextPath = window.location.pathname;
      setRoute(nextPath);
      setActiveView(getViewFromPath(nextPath));
    }

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  useEffect(() => {
    if (!isAuthenticated || isChecking || isPublicRoute(route)) return;
    if (canAccessView(activeView, user)) return;

    const defaultView = getDefaultViewForUser(user);
    window.history.replaceState({}, '', VIEW_PATHS[defaultView]);
    setRoute(VIEW_PATHS[defaultView]);
    setActiveView(defaultView);
  }, [activeView, isAuthenticated, isChecking, route, user]);

  function navigateTo(path) {
    window.history.pushState({}, '', path);
    const nextPath = getPathOnly(path);
    setRoute(nextPath);
    setActiveView(getViewFromPath(nextPath));
  }

  function navigateToView(view) {
    const nextView = canAccessView(view, user) ? view : getDefaultViewForUser(user);
    navigateTo(VIEW_PATHS[nextView] ?? VIEW_PATHS.dashboard);
  }

  function handleOpenNextEventDetails(reservaId) {
    if (!reservaId) return;
    setNextEventPopup(null);
    setFocusedReservaId(reservaId);
    navigateToView('dashboard');
  }

  async function handleLogin(email, password) {
    const authenticatedUser = await login(email, password);
    const loadedData = await loadData({ silent: true, currentUser: authenticatedUser });
    const defaultView = getDefaultViewForUser(authenticatedUser);
    const requestedView = getViewFromPath(route);
    const canRestoreRoute = route && !isPublicRoute(route) && canAccessView(requestedView, authenticatedUser);
    const reservasForPopup = Array.isArray(loadedData?.reservas)
      ? loadedData.reservas
      : await api.getReservas({ limit: 500 }).catch(() => []);
    const nextEvent = getNextApprovedEvent(reservasForPopup);

    navigateTo(canRestoreRoute ? route : VIEW_PATHS[defaultView]);
    window.setTimeout(() => setNextEventPopup(nextEvent), 0);
  }

  async function handleLogout() {
    await logout();
    setNextEventPopup(null);
    navigateTo('/login');
  }

  async function handleCreateReserva(payload) {
    const created = await api.createReserva(payload);
    updateReservasState((current) => upsertManyById(current, getCreatedReservas(created)));
    return created;
  }

  async function handleCreatePublicReservation(payload) {
    const created = await api.createPublicReservation(payload);
    updateReservasState((current) => upsertManyById(current, getCreatedReservas(created)));
    return created;
  }

  async function handleSaveEspaco(payload) {
    const saved = await api.saveEspaco(payload);
    setEspacos((current) => upsertById(current, saved));
    return saved;
  }

  async function handleSaveRecurso(payload) {
    const saved = await api.saveRecurso(payload);
    setRecursos((current) => upsertById(current, saved));
    return saved;
  }

  async function handleCreateUsuario(payload) {
    const created = await api.createUsuario(payload);
    setUsuarios((current) => upsertById(current, created));
    return created;
  }

  async function handleUpdateUsuario(id, payload) {
    const updated = await api.updateUsuario(id, payload);
    setUsuarios((current) => upsertById(current, updated));
    return updated;
  }

  async function handleDeleteUsuario(id) {
    const deleted = await api.deleteUsuario(id);
    setUsuarios((current) => removeById(current, id));
    return deleted;
  }

  async function handleAdminAction(action, id, payload) {
    const handler = actionMap[action];
    if (!handler) return;
    const result = await handler(id, payload);
    updateReservasState((current) => upsertById(current, result));
    return result;
  }

  const getHistorico = useCallback((reservaId) => api.getHistoricoReserva(reservaId), []);

  function renderView() {
    if (loading) return <LoadingState />;
    if (error) return <ErrorAlert message={error} />;

    const views = {
      dashboard: (
        <Dashboard
          metrics={metrics}
          perfil={perfil}
          currentUser={user}
          reservas={reservas}
          espacos={espacos}
          onNavigate={navigateToView}
          onAction={handleAdminAction}
          focusReservaId={focusedReservaId}
          onFocusHandled={() => setFocusedReservaId(null)}
        />
      ),
      'nova-reserva': (
        <ReservaForm
          espacos={espacos}
          recursos={recursos}
          onSubmit={handleCreateReserva}
          onCreated={() => navigateToView(isCollaborator(user) ? 'acompanhamento' : 'dashboard')}
        />
      ),
      acompanhamento: <AcompanhamentoView mode="internal" currentUser={user} />,
      administracao: (
        <AdminQueue
          usuarios={usuarios}
          userCatalogs={userCatalogs}
          canManageUsers={canManageCadastros(user)}
          onCreateUsuario={handleCreateUsuario}
          onUpdateUsuario={handleUpdateUsuario}
          onDeleteUsuario={handleDeleteUsuario}
        />
      ),
      espacos: <EspacosView espacos={espacos} canManage={canManageCadastros(user)} onSave={handleSaveEspaco} />,
      recursos: <RecursosView recursos={recursos} reservas={reservas} canManage={canManageCadastros(user)} onSave={handleSaveRecurso} />,
      auditoria: isMaster(user) ? (
        <AuditoriaView />
      ) : (
        <ErrorAlert message="Apenas usuários MASTER podem acessar a auditoria do sistema." />
      ),
    };

    return views[activeView] ?? views.dashboard;
  }

  if (isChecking && !isPublicRoute(route)) {
    return <LoadingState />;
  }

  const loginPage = (
    <LoginPage
      onLogin={handleLogin}
      onOpenPublic={() => navigateTo('/solicitar-reserva')}
      onOpenPublicCalendar={() => navigateTo('/calendario')}
    />
  );

  if (route === '/login' || (!isAuthenticated && !isPublicRoute(route))) {
    return (
      <ProtectedRoute isAuthenticated={isAuthenticated} isChecking={isChecking} fallback={loginPage}>
        {loginPage}
      </ProtectedRoute>
    );
  }

  if (route === '/solicitar-reserva') {
    if (loading) return <LoadingState />;
    if (error) return <ErrorAlert message={error} />;

    return (
      <PublicReservationWizard
        espacos={espacos}
        recursos={recursos}
        reservas={reservas}
        onSubmit={handleCreatePublicReservation}
        onGoInternal={() => navigateTo(isAuthenticated ? '/app' : '/login')}
        onTrackReservation={(protocolo) => navigateTo(`/acompanhar-solicitacao?protocolo=${encodeURIComponent(protocolo)}`)}
      />
    );
  }

  if (route === '/acompanhar-solicitacao') {
    return (
      <AcompanhamentoView
        mode="public"
        onGoPublic={() => navigateTo('/solicitar-reserva')}
        onGoLogin={() => navigateTo(isAuthenticated ? VIEW_PATHS[getDefaultViewForUser(user)] : '/login')}
      />
    );
  }

  if (route === '/calendario') {
    if (loading) return <LoadingState />;
    if (error) return <ErrorAlert message={error} />;

    return <Agenda reservas={reservas} espacos={espacos} publicMode />;
  }

  return (
    <ProtectedRoute isAuthenticated={isAuthenticated} isChecking={isChecking} fallback={loginPage}>
      <Layout
        activeView={activeView}
        onNavigate={navigateToView}
        perfil={perfil}
        onPerfilChange={setPerfil}
        onOpenPublic={() => navigateTo('/solicitar-reserva')}
        onOpenPublicCalendar={() => navigateTo('/calendario')}
        onLogout={handleLogout}
        currentUser={user}
      >
        {renderView()}
        <NextEventPopup
          reserva={nextEventPopup}
          espaco={findEspaco(espacos, nextEventPopup)}
          onClose={() => setNextEventPopup(null)}
          onOpenDetails={() => handleOpenNextEventDetails(nextEventPopup?.id)}
        />
      </Layout>
    </ProtectedRoute>
  );
}

function NextEventPopup({ reserva, espaco, onClose, onOpenDetails }) {
  if (!reserva) return null;

  const solicitante = getSolicitanteReserva(reserva);
  const eventDateLabel = getWeekdayDateLabel(reserva);
  const eventTimeLabel = `${formatTime(reserva.horario_inicio)} as ${formatTime(reserva.horario_fim)}`;

  function closePopup() {
    onClose();
  }

  return (
    <div className="event-modal-backdrop next-event-backdrop" role="presentation" onMouseDown={closePopup}>
      <div className="event-modal-shell next-event-modal-shell" onMouseDown={(event) => event.stopPropagation()}>
        <button className="event-modal-close-floating next-event-close" type="button" onClick={closePopup} aria-label="Fechar">
          <i className="bi bi-x-lg" aria-hidden="true" />
        </button>
        <article className="event-modal next-event-modal" role="dialog" aria-modal="true" aria-labelledby="nextEventTitle">
          <header className="next-event-header">
            <div>
              <span className="next-event-pill">
                <i className="bi bi-calendar2-check" aria-hidden="true" />
                Proximo evento - aprovado
              </span>
              <h3 id="nextEventTitle">{reserva.nome_evento}</h3>
              <p>Protocolo {reserva.protocolo || 'nao informado'}</p>
            </div>
            <div className="next-event-countdown">
              <i className="bi bi-alarm" aria-hidden="true" />
              <strong>{getCountdownLabel(reserva)}</strong>
            </div>
          </header>

          <div className="next-event-card-wrap">
            <article className="next-event-card">
              <div className="next-event-card-date">
                <strong>{reserva.data_inicio ? reserva.data_inicio.split('-').reverse().join('/') : 'Data nao informada'}</strong>
                <span>Proximo</span>
              </div>
              <div className="next-event-card-body">
                <span className="event-type-pill">Aprovado</span>
                <dl>
                  <div>
                    <dt>Nome do evento</dt>
                    <dd>{reserva.nome_evento}</dd>
                  </div>
                  <div>
                    <dt>Data e hora do evento</dt>
                    <dd>
                      {eventDateLabel} - {eventTimeLabel}
                    </dd>
                  </div>
                  <div>
                    <dt>Espaco do evento</dt>
                    <dd>{espaco?.nome ?? 'Espaco a definir'}</dd>
                  </div>
                  <div>
                    <dt>Solicitante do evento</dt>
                    <dd>{solicitante.nome || 'Nao informado'}</dd>
                  </div>
                </dl>
              </div>
            </article>
          </div>

          <footer className="next-event-actions">
            <button className="btn btn-primary" type="button" onClick={onOpenDetails}>
              Ver detalhes do evento
            </button>
          </footer>
        </article>
      </div>
    </div>
  );
}
