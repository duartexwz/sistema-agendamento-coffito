export const ACCESS_LEVELS = {
  ADMINISTRADOR: 1,
  COLABORADOR: 2,
  MASTER: 3,
  OPERADOR: 4,
};

export function getAccessLevel(user) {
  return Number(user?.niveis_acesso_id ?? user?.nivel_acesso_id);
}

export function isAdmin(user) {
  return getAccessLevel(user) === ACCESS_LEVELS.ADMINISTRADOR;
}

export function isCollaborator(user) {
  return getAccessLevel(user) === ACCESS_LEVELS.COLABORADOR;
}

export function isMaster(user) {
  return getAccessLevel(user) === ACCESS_LEVELS.MASTER;
}

export function isOperator(user) {
  return getAccessLevel(user) === ACCESS_LEVELS.OPERADOR;
}

export function canAdministrateReservas(user) {
  return isAdmin(user) || isMaster(user);
}

export function canManageCadastros(user) {
  return isAdmin(user) || isMaster(user);
}

export function getDefaultViewForUser(user) {
  return isCollaborator(user) ? 'acompanhamento' : 'dashboard';
}

export function canAccessView(view, user) {
  if (isCollaborator(user)) {
    return ['nova-reserva', 'acompanhamento'].includes(view);
  }

  if (view === 'auditoria') return isMaster(user);

  return true;
}
