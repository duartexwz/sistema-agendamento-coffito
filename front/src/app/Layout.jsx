import { useState } from 'react';
import './Layout.css';
import { PERFIS } from '../shared/constants/domain.js';
import { canAccessView, isCollaborator, isOperator } from '../shared/utils/permissions.js';

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Painel', icon: 'bi-speedometer2' },
  { id: 'nova-reserva', label: 'Nova solicitacao', icon: 'bi-plus-circle' },
  { id: 'acompanhamento', label: 'Acompanhamento', icon: 'bi-clipboard-check' },
  { id: 'administracao', label: 'Administracao', icon: 'bi-kanban' },
  { id: 'espacos', label: 'Espacos', icon: 'bi-buildings' },
  { id: 'recursos', label: 'Recursos', icon: 'bi-projector' },
  { id: 'auditoria', label: 'Auditoria', icon: 'bi-shield-check', masterOnly: true },
];

const TOPBAR_TITLES = {
  'nova-reserva': 'Nova solicitacao de reserva',
  acompanhamento: 'Acompanhamento de solicitações',
  administracao: 'Administracao de usuarios',
  espacos: 'Cadastro de Espaços Coffito',
  recursos: 'Gestao de recursos',
  auditoria: 'Auditoria do sistema',
};

function getInitials(nome = '') {
  const parts = String(nome).trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return '?';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function getRoleLabel(user) {
  const level = Number(user?.niveis_acesso_id);
  if (level === 3) return 'MASTER';
  if (level === 4) return 'OPERADOR';
  if (level === 2) return 'COLABORADOR';
  if (level === 1) return 'ADMINISTRADOR';
  return 'Usuario';
}

function getNavItems(perfil, currentUser) {
  if (perfil === 'operacional') {
    return [{ id: 'dashboard', label: 'Painel', icon: 'bi-speedometer2' }];
  }

  return NAV_ITEMS.filter((item) => canAccessView(item.id, currentUser));
}

export function Layout({
  activeView,
  onNavigate,
  perfil,
  onPerfilChange,
  onOpenPublic,
  onOpenPublicCalendar,
  onLogout,
  currentUser,
  children,
}) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const navItems = getNavItems(perfil, currentUser);
  const collaborator = isCollaborator(currentUser);
  const operator = isOperator(currentUser);
  const showPublicReservationShortcut = !collaborator && !operator;
  const showPublicCalendarShortcut = true;
  const hideTopbar = ['dashboard', 'nova-reserva', 'acompanhamento', 'administracao', 'espacos', 'recursos', 'auditoria'].includes(activeView);

  return (
    <div className={`app-shell ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand-block">
            <div className="brand-mark">CO</div>
            <div className="brand-copy">
              <strong>Reservas COFFITO</strong>
              <span>Espacos institucionais</span>
            </div>
          </div>

          <button
            type="button"
            className="sidebar-toggle"
            onClick={() => setSidebarCollapsed((current) => !current)}
            aria-label={sidebarCollapsed ? 'Abrir menu lateral' : 'Fechar menu lateral'}
            title={sidebarCollapsed ? 'Abrir menu' : 'Fechar menu'}
          >
            <i className={`bi ${sidebarCollapsed ? 'bi-layout-sidebar-inset' : 'bi-layout-sidebar-inset-reverse'}`} aria-hidden="true" />
          </button>
        </div>

        <div className="brand-block mobile-brand-block">
          <div className="brand-mark">CO</div>
          <div className="brand-copy">
            <strong>Reservas COFFITO</strong>
            <span>Espacos institucionais</span>
          </div>
        </div>

        {currentUser && (
          <div className="sidebar-user-card" title={`${currentUser.nome ?? ''} ${currentUser.email ?? ''}`}>
            <div className="sidebar-user-avatar" aria-hidden="true">
              {getInitials(currentUser.nome)}
            </div>
            <div className="sidebar-user-info">
              <strong className="sidebar-user-name">{currentUser.nome}</strong>
              <span className="sidebar-user-email">{currentUser.email}</span>
              <span className="sidebar-user-role">{getRoleLabel(currentUser)}</span>
            </div>
          </div>
        )}

        <nav className="nav flex-column app-nav" aria-label="Navegacao principal">
          {navItems.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`nav-link ${activeView === item.id ? 'active' : ''}`}
              onClick={() => onNavigate(item.id)}
              title={item.label}
              aria-label={item.label}
            >
              <i className={`bi ${item.icon}`} aria-hidden="true" />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        {showPublicReservationShortcut && (
          <>
            <button type="button" className="public-link-button" onClick={onOpenPublic} title="Solicitação pública">
              <i className="bi bi-box-arrow-up-right" aria-hidden="true" />
              <span>Solicitação pública</span>
            </button>
          </>
        )}

        {showPublicCalendarShortcut && (
          <button type="button" className="public-link-button" onClick={onOpenPublicCalendar} title="Calendário público">
            <i className="bi bi-display" aria-hidden="true" />
            <span>Calendário público</span>
          </button>
        )}

        <button type="button" className="logout-button" onClick={onLogout} title="Sair">
          <i className="bi bi-box-arrow-left" aria-hidden="true" />
          <span>Sair</span>
        </button>
      </aside>

      <div className="main-shell">
        {!hideTopbar && (
          <header className="topbar">
            <div>
              <p className="eyebrow">Sistema de Reservas Institucionais</p>
              <h1>{TOPBAR_TITLES[activeView] ?? 'Agendamento de espacos'}</h1>
            </div>

            <div className="profile-switcher">
              <label htmlFor="perfilAtual" className="form-label">
                Perfil simulado
              </label>
              <select
                id="perfilAtual"
                className="form-select"
                value={perfil}
                onChange={(event) => onPerfilChange(event.target.value)}
              >
                {PERFIS.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.nome}
                  </option>
                ))}
              </select>
            </div>
          </header>
        )}

        <main className="content-area">{children}</main>
      </div>
    </div>
  );
}
