import axios from 'axios';
import { FAIXAS_PUBLICO, STATUS } from '../shared/constants/domain.js';
import { getFriendlyErrorMessage } from '../shared/utils/errors.js';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '/api-local').replace(/\/$/, '');

const COLLECTION_KEYS = {
  '/usuarios/': 'usuarios',
  '/tipos_usuarios/': 'tipos_usuarios',
  '/niveis_acesso/': 'niveis_acesso',
  '/setor_solicitante/': 'setor_solicitante',
  '/cargos/': 'cargos',
  '/espacos/': 'espacos',
  '/recursos/': 'recursos',
  '/reservas/': 'reservas',
  '/status_reservas/': 'status_reservas',
  '/historico_reservas/': 'historico_reservas',
  '/auditoria/': 'logs',
};

const STATUS_NAME_TO_FRONT_ID = {
  pendente: STATUS.ANALISE.id,
  enviada: STATUS.ENVIADA.id,
  'em analise': STATUS.ANALISE.id,
  'em análise': STATUS.ANALISE.id,
  aprovado: STATUS.APROVADA.id,
  aprovada: STATUS.APROVADA.id,
  negado: STATUS.REPROVADA.id,
  reprovado: STATUS.REPROVADA.id,
  reprovada: STATUS.REPROVADA.id,
  'aguardando complementacao': STATUS.COMPLEMENTACAO.id,
  'aguardando complementação': STATUS.COMPLEMENTACAO.id,
  remanejada: STATUS.REMANEJADA.id,
  cancelado: STATUS.CANCELADA_COFFITO.id,
  cancelada: STATUS.CANCELADA_COFFITO.id,
  finalizada: STATUS.FINALIZADA.id,
  realizado: STATUS.REALIZADO.id,
};

let statusCache = null;
let refreshPromise = null;
let unauthorizedHandler = null;

export const http = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  withCredentials: true,
  headers: {
    Accept: 'application/json',
  },
});

export function setUnauthorizedHandler(handler) {
  unauthorizedHandler = handler;
}

function getCookie(name) {
  const cookie = document.cookie
    .split('; ')
    .find((item) => item.startsWith(`${name}=`));

  return cookie ? decodeURIComponent(cookie.split('=').slice(1).join('=')) : null;
}

function normalizeText(value = '') {
  return String(value)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

function onlyDigits(value = '') {
  return String(value).replace(/\D/g, '');
}

function isAuthEndpoint(url = '') {
  return ['/login/', '/auth/refresh', '/logout/'].some((endpoint) => String(url).includes(endpoint));
}

http.interceptors.request.use((config) => {
  const method = String(config.method ?? 'get').toUpperCase();
  const unsafeMethods = ['POST', 'PUT', 'PATCH', 'DELETE'];
  const csrfToken = getCookie('csrf_token');

  if (unsafeMethods.includes(method) && csrfToken) {
    if (typeof config.headers?.set === 'function') {
      config.headers.set('X-CSRF-Token', csrfToken);
    } else {
      config.headers = {
        ...config.headers,
        'X-CSRF-Token': csrfToken,
      };
    }
  }

  return config;
});

function detailToMessage(detail) {
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg ?? JSON.stringify(item)).join(' ');
  }

  if (typeof detail === 'object' && detail !== null) {
    return detail.message ?? detail.detail ?? JSON.stringify(detail);
  }

  return detail;
}

function normalizeAxiosError(error) {
  if (error?.status) return error;

  const status = error.response?.status;
  const url = error.config?.url ?? '';
  const detail = error.response?.data?.detail ?? error.response?.data?.message ?? error.response?.data;
  const apiMessage = detailToMessage(detail);
  const context = String(url).includes('/login/') ? 'login' : 'default';
  const messageByStatus = {
    401: context === 'login'
      ? 'E-mail ou senha invalidos. Verifique os dados e tente novamente.'
      : 'Sua sessao expirou. Faca login novamente.',
    403: 'Voce nao tem permissao para realizar esta acao.',
    422: getFriendlyErrorMessage({ status, data: error.response?.data, message: apiMessage }, context),
    500: 'Nao foi possivel concluir a operacao agora. Tente novamente em instantes.',
  };

  const message =
    messageByStatus[status] ??
    getFriendlyErrorMessage({ status, data: error.response?.data, code: error.code, message: apiMessage }, context) ??
    (error.code === 'ECONNABORTED'
      ? 'A operacao demorou demais. Tente novamente.'
      : 'Nao foi possivel comunicar com a API.');

  const normalized = new Error(message);
  normalized.status = status;
  normalized.data = error.response?.data;
  normalized.originalError = error;

  return normalized;
}

http.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config ?? {};
    const status = error.response?.status;

    if (
      status === 401 &&
      !originalRequest._retry &&
      !originalRequest._skipAuthRefresh &&
      !isAuthEndpoint(originalRequest.url)
    ) {
      originalRequest._retry = true;

      try {
        refreshPromise =
          refreshPromise ??
          http.post('/auth/refresh', null, {
            _skipAuthRefresh: true,
          });
        await refreshPromise;
        refreshPromise = null;
        return http(originalRequest);
      } catch (refreshError) {
        refreshPromise = null;
        unauthorizedHandler?.();
        throw normalizeAxiosError(refreshError);
      }
    }

    if (status === 401 && !isAuthEndpoint(originalRequest.url)) {
      unauthorizedHandler?.();
    }

    throw normalizeAxiosError(error);
  },
);

async function request(path, options = {}) {
  const { query, body, headers, method = 'GET', ...axiosOptions } = options;
  const isFormData = body instanceof FormData;

  const response = await http.request({
    url: path,
    method,
    params: query,
    data: body,
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...headers,
    },
    ...axiosOptions,
  });

  return response.data;
}

async function requestCollection(path, key, query = {}) {
  try {
    const data = await request(path, { method: 'GET', query });
    return data[key] ?? data[COLLECTION_KEYS[path]] ?? data ?? [];
  } catch (error) {
    if (error.status === 404) return [];
    throw error;
  }
}

async function getStatusReservas() {
  if (statusCache) return statusCache;

  const statuses = await requestCollection('/status_reservas/', 'status_reservas');
  statusCache = statuses.map((status) => ({
    ...status,
    front_id: STATUS_NAME_TO_FRONT_ID[normalizeText(status.nome)] ?? STATUS.ANALISE.id,
  }));

  return statusCache;
}

async function resolveStatusId(...possibleNames) {
  const statuses = await getStatusReservas();
  const normalizedNames = possibleNames.map(normalizeText);
  const status = statuses.find((item) => normalizedNames.includes(normalizeText(item.nome)));

  if (!status) {
    throw new Error(`Status nao encontrado na API: ${possibleNames.join(' ou ')}.`);
  }

  return status.id;
}

async function resolveStatusIdWithFallback(primaryNames, fallbackNames = []) {
  try {
    return await resolveStatusId(...primaryNames);
  } catch (error) {
    if (fallbackNames.length === 0) throw error;
    return resolveStatusId(...fallbackNames);
  }
}

function normalizeStatusId(statusId, statuses = []) {
  if (!statusId) return STATUS.ANALISE.id;
  if (typeof statusId === 'string' && Object.values(STATUS).some((status) => status.id === statusId)) return statusId;

  const status = statuses.find((item) => Number(item.id) === Number(statusId));
  return status?.front_id ?? STATUS.ANALISE.id;
}

function calculateFaixaId(total) {
  const quantity = Number(total) || 0;
  return FAIXAS_PUBLICO.find((faixa) => quantity >= faixa.min && quantity <= faixa.max)?.id ?? FAIXAS_PUBLICO[0].id;
}

function quantityFromFaixa(faixaId) {
  if (faixaId === '110_150') return 130;
  if (faixaId === 'ate_15') return 15;
  return 50;
}

function normalizeUsuario(usuario) {
  return {
    ...usuario,
    nivel_acesso_id: usuario.nivel_acesso_id ?? usuario.niveis_acesso_id,
    criado_em: usuario.criado_em ?? usuario.created_at,
    atualizado_em: usuario.atualizado_em ?? usuario.updated_at,
  };
}

function normalizeCatalogItem(item) {
  return {
    id: Number(item.id),
    nome: item.nome,
  };
}

function normalizeEspaco(espaco) {
  return {
    ...espaco,
    disponivel: espaco.disponivel ?? espaco.ativo ?? true,
    ativo: espaco.ativo ?? espaco.disponivel ?? true,
    criado_em: espaco.criado_em ?? espaco.created_at,
    atualizado_em: espaco.atualizado_em ?? espaco.updated_at,
  };
}

function normalizeRecurso(recurso) {
  return {
    ...recurso,
    disponivel: recurso.disponivel ?? true,
  };
}

function normalizeReserva(reserva, statuses = []) {
  const quantidade = Number(reserva.quantidade_participantes ?? reserva.publico_estimado ?? 0);
  const solicitanteNome = reserva.solicitante_nome ?? reserva.nome_solicitante ?? reserva.profissional?.nome ?? '';
  const solicitanteCpf = reserva.solicitante_cpf ?? reserva.cpf ?? reserva.profissional?.cpf ?? '';
  const solicitanteEmail = reserva.solicitante_email ?? reserva.email ?? reserva.email_solicitante ?? reserva.profissional?.email ?? '';
  const solicitanteTelefone =
    reserva.solicitante_telefone ?? reserva.telefone ?? reserva.profissional?.celular ?? reserva.profissional?.telefone ?? '';
  const solicitanteProfissao = reserva.solicitante_profissao ?? reserva.profissao ?? reserva.profissional?.profissao ?? '';

  return {
    ...reserva,
    status_id: normalizeStatusId(reserva.status_id, statuses),
    espaco_aprovado_id: reserva.espaco_aprovado_id || null,
    observacao: reserva.observacao ?? reserva.observacoes ?? '',
    observacoes: reserva.observacoes ?? reserva.observacao ?? '',
    recursos: reserva.recursos ?? [],
    quantidade_participantes: quantidade,
    publico_estimado: quantidade,
    faixa_participantes: reserva.faixa_participantes ?? calculateFaixaId(quantidade),
    solicitante_nome: solicitanteNome,
    solicitante_cpf: solicitanteCpf,
    solicitante_email: solicitanteEmail,
    solicitante_telefone: solicitanteTelefone,
    solicitante_profissao: solicitanteProfissao,
    email: reserva.email ?? solicitanteEmail,
    criado_em: reserva.criado_em ?? reserva.created_at,
    atualizado_em: reserva.atualizado_em ?? reserva.updated_at,
  };
}

function toEspacoPayload(espaco) {
  return {
    nome: espaco.nome,
    descricao: espaco.descricao,
    localizacao: espaco.localizacao,
    capacidade_minima: Number(espaco.capacidade_minima),
    capacidade_maxima: Number(espaco.capacidade_maxima),
    ativo: espaco.ativo ?? espaco.disponivel ?? true,
  };
}

function toRecursoPayload(recurso) {
  return {
    nome: recurso.nome,
    quantidade: Number(recurso.quantidade),
    disponivel: recurso.disponivel ?? true,
  };
}

function toUsuarioPayload(usuario) {
  return {
    nome: usuario.nome,
    tipo_usuario_id: Number(usuario.tipo_usuario_id),
    niveis_acesso_id: Number(usuario.niveis_acesso_id ?? usuario.nivel_acesso_id),
    matricula: usuario.matricula,
    setor_solicitante_id: Number(usuario.setor_solicitante_id),
    cargo_id: Number(usuario.cargo_id),
    cpf: onlyDigits(usuario.cpf),
    email: usuario.email,
    telefone: usuario.telefone,
    password: usuario.password,
    ativo: usuario.ativo ?? true,
    updated_by: Number(usuario.updated_by ?? 1),
  };
}

function toUsuarioUpdatePayload(usuario) {
  const payload = toUsuarioPayload(usuario);

  delete payload.password;

  return payload;
}

function toReservaPayload(reserva) {
  const espacoSolicitadoId = Number(reserva.espaco_solicitado_id);
  const participantes = Number(
    reserva.quantidade_participantes ??
      reserva.publico_estimado ??
      quantityFromFaixa(reserva.faixa_participantes),
  );
  const solicitanteNome = reserva.solicitante_nome ?? reserva.nome_completo ?? '';
  const solicitanteCpf = onlyDigits(reserva.solicitante_cpf ?? reserva.cpf ?? '');
  const solicitanteEmail = reserva.solicitante_email ?? reserva.email ?? '';
  const solicitanteTelefone = reserva.solicitante_telefone ?? reserva.telefone ?? '';
  const solicitanteProfissao = reserva.solicitante_profissao ?? reserva.cargo ?? '';

  const payload = {
    solicitante_id: reserva.solicitante_id ? Number(reserva.solicitante_id) : null,
    espaco_solicitado_id: espacoSolicitadoId,
    espaco_aprovado_id: reserva.espaco_aprovado_id ? Number(reserva.espaco_aprovado_id) : espacoSolicitadoId,
    nome_evento: reserva.nome_evento,
    objetivo: reserva.objetivo ?? reserva.programacao ?? '',
    data_inicio: reserva.data_inicio,
    data_fim: reserva.data_fim,
    horario_inicio: reserva.horario_inicio,
    horario_fim: reserva.horario_fim,
    quantidade_participantes: participantes,
    observacoes: reserva.observacoes ?? reserva.observacao ?? '',
    analisado_por: reserva.analisado_por ? Number(reserva.analisado_por) : null,
  };

  if (solicitanteNome) payload.solicitante_nome = solicitanteNome;
  if (solicitanteCpf) payload.solicitante_cpf = solicitanteCpf;
  if (solicitanteEmail) payload.solicitante_email = solicitanteEmail;
  if (solicitanteTelefone) payload.solicitante_telefone = solicitanteTelefone;
  if (solicitanteProfissao) payload.solicitante_profissao = solicitanteProfissao;

  return payload;
}

function getSpecificDateItems(payload = {}) {
  return [...(payload.datas ?? [])]
    .map((item) => ({
      data_inicio: item.data_inicio ?? item.data,
      data_fim: item.data_fim ?? item.data_inicio ?? item.data,
      horario_inicio: item.horario_inicio ?? payload.horario_inicio ?? payload.periodo?.horario_inicio,
      horario_fim: item.horario_fim ?? payload.horario_fim ?? payload.periodo?.horario_fim,
    }))
    .filter((item) => item.data_inicio)
    .sort((a, b) => a.data_inicio.localeCompare(b.data_inicio));
}

function withSpecificReservationDate(payload, dateItem) {
  return {
    ...payload,
    data_inicio: dateItem.data_inicio,
    data_fim: dateItem.data_fim ?? dateItem.data_inicio,
    horario_inicio: dateItem.horario_inicio,
    horario_fim: dateItem.horario_fim,
  };
}

function normalizeAcompanhamentoResponse(data, statuses = []) {
  return {
    reserva: data?.reserva ? normalizeReserva(data.reserva, statuses) : null,
    historico: data?.historico ?? [],
  };
}

function withSpecificPublicReservationDate(payload, dateItem) {
  return {
    ...payload,
    periodo: {
      ...(payload.periodo ?? {}),
      data_inicio: dateItem.data_inicio,
      data_fim: dateItem.data_fim ?? dateItem.data_inicio,
      horario_inicio: dateItem.horario_inicio,
      horario_fim: dateItem.horario_fim,
    },
    datas: [],
  };
}

function combineCreatedReservations(reservas) {
  const firstReserva = reservas[0] ?? {};
  return {
    ...firstReserva,
    reservas,
    protocolos: reservas.map((reserva) => reserva.protocolo).filter(Boolean),
  };
}

function publicReservationToApiPayload(payload) {
  const periodo = payload.periodo ?? {};
  if (!payload.espaco_solicitado_id) {
    throw new Error('Cadastre ao menos um espaco compativel antes de enviar a solicitacao publica.');
  }

  const sortedDates = [...(payload.datas ?? [])].sort((a, b) =>
    (a.data_inicio ?? a.data).localeCompare(b.data_inicio ?? b.data),
  );
  const firstDate = sortedDates[0] ?? {};
  const lastDate = sortedDates.at(-1) ?? firstDate;
  const participants = Number(payload.evento.publico_estimado);

  const reservaPayload = toReservaPayload({
    solicitante_id: null,
    espaco_solicitado_id: payload.espaco_solicitado_id,
    espaco_aprovado_id: payload.espaco_solicitado_id,
    nome_evento: payload.evento.nome,
    objetivo: payload.evento.programacao || payload.evento.nome,
    data_inicio: periodo.data_inicio || firstDate.data_inicio || firstDate.data,
    data_fim: periodo.data_fim || lastDate.data_fim || lastDate.data || firstDate.data_inicio || firstDate.data,
    horario_inicio: periodo.horario_inicio || firstDate.horario_inicio,
    horario_fim: periodo.horario_fim || lastDate.horario_fim || firstDate.horario_fim,
    quantidade_participantes: participants,
    observacoes: payload.recursos.observacoes,
  });

  return {
    ...reservaPayload,
    solicitante_nome: payload.profissional.nome,
    solicitante_cpf: onlyDigits(payload.profissional.cpf),
    solicitante_email: payload.profissional.email,
    solicitante_telefone: payload.profissional.celular,
    solicitante_profissao: payload.profissional.profissao,
  };
}

function isSnapshotUnsupported(error) {
  const details = `${error.message ?? ''} ${JSON.stringify(error.data ?? '')}`;
  return error.status === 422 && /extra|solicitante_|email|not permitted|forbidden/i.test(details);
}

async function postPublicReservationPayload(apiPayload) {
  try {
    return await request('/reservas/', {
      method: 'POST',
      body: apiPayload,
    });
  } catch (error) {
    if (!isSnapshotUnsupported(error)) throw error;

    return request('/reservas/', {
      method: 'POST',
      body: toReservaPayload(apiPayload),
    });
  }
}

function escapeHtml(value = '') {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function getReservaNotificationTarget(reserva = {}, payload = {}) {
  return {
    email:
      payload.solicitante_email ??
      reserva.solicitante_email ??
      reserva.email ??
      reserva.email_solicitante ??
      reserva.profissional?.email ??
      '',
    nome:
      payload.solicitante_nome ??
      reserva.solicitante_nome ??
      reserva.nome_solicitante ??
      reserva.profissional?.nome ??
      'Solicitante',
  };
}

function getDecisionEmailContent(action, reserva, payload = {}) {
  const motivo = payload.motivo || payload.observacao || '';
  const protocolo = reserva.protocolo || 'sem protocolo';
  const nomeEvento = reserva.nome_evento || 'evento solicitado';
  const acompanhamentoUrl = `${window.location.origin}/acompanhar-solicitacao?protocolo=${encodeURIComponent(protocolo)}`;
  const statusLabels = {
    aprovar: {
      assunto: `Reserva ${protocolo} - Aprovada`,
      titulo: 'sua solicitacao foi aprovada',
      detalhe: 'A reserva foi aprovada pela administracao do COFFITO.',
    },
    complementacao: {
      assunto: `Reserva ${protocolo} - Solicitacao de ajuste`,
      titulo: 'sua solicitacao precisa de ajuste',
      detalhe: 'A administracao do COFFITO solicitou ajustes para continuar a analise.',
    },
    reprovar: {
      assunto: `Reserva ${protocolo} - Reprovada`,
      titulo: 'sua solicitacao foi reprovada',
      detalhe: 'A reserva foi reprovada pela administracao do COFFITO.',
    },
  };
  const labels = statusLabels[action];

  if (!labels) return null;

  return {
    assunto: labels.assunto,
    corpo_html: `
      <html>
        <body>
          <p>Ola, ${escapeHtml(getReservaNotificationTarget(reserva, payload).nome)}.</p>
          <p>Informamos que ${labels.titulo}.</p>
          <p>
            Evento: <strong>${escapeHtml(nomeEvento)}</strong><br/>
            Protocolo: <strong>${escapeHtml(protocolo)}</strong>
          </p>
          <p>${escapeHtml(labels.detalhe)}</p>
          ${motivo ? `<p><strong>Observacao:</strong> ${escapeHtml(motivo)}</p>` : ''}
          <p>
            Acompanhe a solicitação pelo link:<br/>
            <a href="${acompanhamentoUrl}">${acompanhamentoUrl}</a>
          </p>
          <p>Atenciosamente,<br/>Equipe COFFITO</p>
        </body>
      </html>
    `,
  };
}

async function notifyReservationDecision(action, reserva, payload = {}) {
  if (action === 'aprovar') return null;

  const target = getReservaNotificationTarget(reserva, payload);
  const content = getDecisionEmailContent(action, reserva, payload);

  if (!content || !reserva.id) return null;

  try {
    await request('/email/', {
      method: 'POST',
      body: {
        reserva_id: Number(reserva.id),
        assunto: content.assunto,
        corpo_html: content.corpo_html,
      },
    });
    return null;
  } catch (error) {
    const reason = getFriendlyErrorMessage(error, 'acao-admin');
    return `Status atualizado, mas nao foi possivel enviar o e-mail para ${target.email || 'o solicitante'}: ${reason}`;
  }
}

async function patchReservaStatus(id, statusNames, payload = {}, options = {}) {
  const statusId = await resolveStatusIdWithFallback(statusNames, options.fallbackStatusNames ?? []);
  const updated = await request(`/reservas/${id}`, {
    method: 'PATCH',
    body: {
      status_id: statusId,
      ...(payload.espaco_aprovado_id ? { espaco_aprovado_id: Number(payload.espaco_aprovado_id) } : {}),
      ...(payload.observacao || payload.motivo ? { observacoes: payload.observacao ?? payload.motivo } : {}),
    },
  });

  const normalized = normalizeReserva({ ...(payload.reserva ?? {}), id: Number(id), ...updated }, await getStatusReservas());
  const emailWarning = await notifyReservationDecision(options.action, normalized, payload);

  return emailWarning ? { ...normalized, emailWarning } : normalized;
}

export const api = {
  async getCurrentUser() {
    const data = await request('/auth/me', { method: 'GET' });
    return data.user;
  },

  async logout() {
    try {
      await request('/logout/', { method: 'POST' });
    } catch (error) {
      if (error.status !== 401) throw error;
    }
  },

  async login(username, password) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    const data = await request('/login/', {
      method: 'POST',
      body: formData,
    });

    return data.user;
  },

  async getDashboard() {
    const reservas = await this.getReservas();
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
  },

  async getUsuarios() {
    try {
      const usuarios = await requestCollection('/usuarios/', 'usuarios');
      return usuarios.map(normalizeUsuario);
    } catch (error) {
      console.warn('Nao foi possivel carregar usuarios da API local.', error);
      return [];
    }
  },

  async getTiposUsuarios() {
    const tiposUsuarios = await requestCollection('/tipos_usuarios/', 'tipos_usuarios');
    return tiposUsuarios.map(normalizeCatalogItem);
  },

  async getNiveisAcesso() {
    const niveisAcesso = await requestCollection('/niveis_acesso/', 'niveis_acesso');
    return niveisAcesso.map(normalizeCatalogItem);
  },

  async getSetoresSolicitantes() {
    const setoresSolicitantes = await requestCollection('/setor_solicitante/', 'setor_solicitante');
    return setoresSolicitantes.map(normalizeCatalogItem);
  },

  async getCargos() {
    const cargos = await requestCollection('/cargos/', 'cargos');
    return cargos.map(normalizeCatalogItem);
  },

  async getUserCatalogs() {
    const [tiposUsuarios, niveisAcesso, setoresSolicitantes, cargos] = await Promise.all([
      this.getTiposUsuarios(),
      this.getNiveisAcesso(),
      this.getSetoresSolicitantes(),
      this.getCargos(),
    ]);

    return {
      tiposUsuarios,
      niveisAcesso,
      setoresSolicitantes,
      cargos,
    };
  },

  async createUsuario(payload) {
    const usuario = await request('/usuarios/', {
      method: 'POST',
      body: toUsuarioPayload(payload),
    });
    return normalizeUsuario(usuario);
  },

  async updateUsuario(id, payload) {
    const usuario = await request(`/usuarios/${id}`, {
      method: 'PATCH',
      body: toUsuarioUpdatePayload(payload),
    });
    return normalizeUsuario(usuario);
  },

  async deleteUsuario(id) {
    return request(`/usuarios/${id}`, {
      method: 'DELETE',
    });
  },

  async getEspacos() {
    const espacos = await requestCollection('/espacos/', 'espacos');
    return espacos.map(normalizeEspaco);
  },

  async saveEspaco(espaco) {
    const method = espaco.id ? 'PATCH' : 'POST';
    const path = espaco.id ? `/espacos/${espaco.id}` : '/espacos/';
    const saved = await request(path, {
      method,
      body: toEspacoPayload(espaco),
    });

    return normalizeEspaco(saved);
  },

  async getRecursos() {
    const recursos = await requestCollection('/recursos/', 'recursos');
    return recursos.map(normalizeRecurso);
  },

  async saveRecurso(recurso) {
    const method = recurso.id ? 'PATCH' : 'POST';
    const path = recurso.id ? `/recursos/${recurso.id}` : '/recursos/';
    const saved = await request(path, {
      method,
      body: toRecursoPayload(recurso),
    });

    return normalizeRecurso(saved);
  },

  async getReservas(filters = {}) {
    const statuses = await getStatusReservas();
    const query = {
      protocolo: filters.protocolo,
      nome_evento: filters.nome_evento,
      status_id: filters.status_id,
      espaco_solicitado_id: filters.espaco_id,
      offset: filters.offset,
      limit: filters.limit ?? 100,
    };

    const reservas = await requestCollection('/reservas/', 'reservas', query);
    return reservas.map((reserva) => normalizeReserva(reserva, statuses));
  },

  async createReserva(payload) {
    const specificDates = getSpecificDateItems(payload);
    if (specificDates.length > 0) {
      const statuses = await getStatusReservas();
      const createdReservas = [];

      for (const dateItem of specificDates) {
        const reservaPayload = toReservaPayload(withSpecificReservationDate(payload, dateItem));
        const created = await request('/reservas/', {
          method: 'POST',
          body: reservaPayload,
        });
        createdReservas.push(normalizeReserva({ ...reservaPayload, ...created }, statuses));
      }

      return combineCreatedReservations(createdReservas);
    }

    const created = await request('/reservas/', {
      method: 'POST',
      body: toReservaPayload(payload),
    });

    return normalizeReserva(created, await getStatusReservas());
  },

  async createPublicReservation(payload) {
    const specificDates = getSpecificDateItems(payload);
    if (specificDates.length > 0) {
      const statuses = await getStatusReservas();
      const createdReservas = [];

      for (const dateItem of specificDates) {
        const apiPayload = publicReservationToApiPayload(withSpecificPublicReservationDate(payload, dateItem));
        const created = await postPublicReservationPayload(apiPayload);
        createdReservas.push(normalizeReserva({ ...apiPayload, ...created }, statuses));
      }

      return combineCreatedReservations(createdReservas);
    }

    const apiPayload = publicReservationToApiPayload(payload);
    const created = await postPublicReservationPayload(apiPayload);

    return normalizeReserva({ ...apiPayload, ...created }, await getStatusReservas());
  },

  async trackPublicReservation(payload) {
    const statuses = await getStatusReservas();
    const data = await request('/acompanhamento/consulta', {
      method: 'POST',
      body: {
        protocolo: payload.protocolo,
        email: payload.email,
      },
    });

    return normalizeAcompanhamentoResponse(data, statuses);
  },

  async getInternalTracking() {
    const statuses = await getStatusReservas();
    const reservas = await requestCollection('/acompanhamento/interno', 'reservas');
    return reservas.map((reserva) => normalizeReserva(reserva, statuses));
  },

  async updateReserva(id, payload) {
    const updated = await request(`/reservas/${id}`, {
      method: 'PATCH',
      body: toReservaPayload(payload),
    });

    return normalizeReserva({ id: Number(id), ...updated }, await getStatusReservas());
  },

  async approveReserva(id, payload) {
    return patchReservaStatus(id, ['Aprovada', 'Aprovado'], payload, { action: 'aprovar' });
  },

  async rejectReserva(id, payload) {
    return patchReservaStatus(id, ['Reprovada', 'Reprovado', 'Negado'], payload, { action: 'reprovar' });
  },

  async requestComplementacao(id, payload) {
    return patchReservaStatus(id, ['Aguardando complementacao', 'Complementacao solicitada'], payload, {
      action: 'complementacao',
      fallbackStatusNames: ['Pendente', 'Em analise', 'Em análise'],
    });
  },

  async remanejarReserva(id, payload) {
    return patchReservaStatus(id, ['Remanejada'], payload);
  },

  async cancelReserva(id, payload) {
    const updated = await request(`/reservas/${id}/cancelar`, {
      method: 'PATCH',
      body: {
        observacoes: payload.observacao ?? payload.motivo ?? 'Cancelado pelo painel.',
      },
    });

    return normalizeReserva({ ...(payload.reserva ?? {}), id: Number(id), ...updated }, await getStatusReservas());
  },

  async undoReservaDecision(id, payload) {
    const statusName = payload.reserva?.status_id === STATUS.APROVADA.id ? 'Aprovado' : 'Negado';
    const updated = await request(`/reservas_status_historico/${id}/status`, {
      method: 'PATCH',
      body: {
        status: statusName,
      },
    });

    return normalizeReserva({ ...(payload.reserva ?? {}), id: Number(id), ...updated }, await getStatusReservas());
  },

  async getHistoricoReserva(id) {
    const historico = await requestCollection('/historico_reservas/', 'historico_reservas', {
      reserva_id: id,
      limit: 100,
    });

    return historico;
  },

  async getAuditoria(filters = {}) {
    const data = await request('/auditoria/', {
      method: 'GET',
      query: {
        data_inicio: filters.data_inicio || undefined,
        data_fim: filters.data_fim || undefined,
        ator_usuario_id: filters.ator_usuario_id || undefined,
        entidade_tipo: filters.entidade_tipo || undefined,
        entidade_id: filters.entidade_id || undefined,
        acao: filters.acao || undefined,
        busca: filters.busca || undefined,
        offset: filters.offset,
        limit: filters.limit ?? 50,
      },
    });

    return {
      logs: data.logs ?? [],
      total: data.total ?? 0,
    };
  },
};
