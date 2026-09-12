const DEFAULT_MESSAGES = {
  default: 'Nao foi possivel concluir a operacao. Tente novamente.',
  login: 'Nao foi possivel realizar o login. Tente novamente.',
  carregamento: 'Nao foi possivel carregar os dados. Atualize a tela e tente novamente.',
  'reserva-interna': 'Nao foi possivel enviar a solicitacao interna. Revise os dados e tente novamente.',
  'reserva-publica': 'Nao foi possivel enviar a solicitacao. Revise os dados e tente novamente.',
  acompanhamento: 'Nao foi possivel localizar a solicitacao. Confira o protocolo e o e-mail informado.',
  'acompanhamento-interno': 'Nao foi possivel carregar o acompanhamento. Tente novamente.',
  cadastro: 'Nao foi possivel salvar o cadastro. Revise os dados e tente novamente.',
  'acao-admin': 'Nao foi possivel concluir a acao administrativa. Tente novamente.',
  auditoria: 'Nao foi possivel carregar a auditoria. Tente novamente.',
};

const STATUS_MESSAGES = {
  400: 'Revise os dados informados e tente novamente.',
  401: 'Sua sessao expirou. Faca login novamente.',
  403: 'Voce nao tem permissao para realizar esta acao.',
  404: 'Registro nao encontrado. Atualize a tela e tente novamente.',
  409: 'Ja existe um registro com essas informacoes.',
  422: 'Revise os campos informados. Algum dado esta invalido ou incompleto.',
  500: 'Nao foi possivel concluir a operacao agora. Tente novamente em instantes.',
};

const TECHNICAL_PATTERNS = [
  /request failed with status code/i,
  /status code\s+\d+/i,
  /extra_forbidden/i,
  /validation error/i,
  /traceback/i,
  /\bloc\b/i,
  /\bbody\b/i,
  /\binput\b/i,
  /not permitted/i,
  /forbidden/i,
  /^\[?\{.*\}\]?$/,
];

function extractDetailMessage(detail) {
  if (!detail) return '';

  if (Array.isArray(detail)) {
    return detail.map((item) => extractDetailMessage(item)).filter(Boolean).join(' ');
  }

  if (typeof detail === 'object') {
    return detail.message ?? detail.detail ?? detail.msg ?? '';
  }

  return String(detail);
}

function isTechnicalMessage(message = '') {
  const normalized = String(message).trim();
  if (!normalized) return true;

  return TECHNICAL_PATTERNS.some((pattern) => pattern.test(normalized));
}

function getContextDefault(context) {
  return DEFAULT_MESSAGES[context] ?? DEFAULT_MESSAGES.default;
}

export function getFriendlyErrorMessage(error, context = 'default') {
  const status = Number(error?.status ?? error?.response?.status);
  const code = error?.code ?? error?.originalError?.code;
  const data = error?.data ?? error?.response?.data;
  const rawMessage = typeof error === 'string' ? error : error?.message;
  const apiMessage = extractDetailMessage(data?.detail ?? data?.message ?? data);

  if (context === 'login' && status === 401) {
    return 'E-mail ou senha invalidos. Verifique os dados e tente novamente.';
  }

  if (code === 'ECONNABORTED') {
    return 'A operacao demorou demais. Tente novamente.';
  }

  if (code === 'ERR_NETWORK' || (!status && error?.request && !error?.response)) {
    return 'Nao foi possivel conectar ao servidor. Verifique sua conexao ou tente novamente.';
  }

  if (status === 422) {
    if (apiMessage && !isTechnicalMessage(apiMessage)) return apiMessage;
    return STATUS_MESSAGES[422];
  }

  if (status && STATUS_MESSAGES[status]) {
    return STATUS_MESSAGES[status];
  }

  if (apiMessage && !isTechnicalMessage(apiMessage)) {
    return apiMessage;
  }

  if (rawMessage && !isTechnicalMessage(rawMessage)) {
    return rawMessage;
  }

  return getContextDefault(context);
}
