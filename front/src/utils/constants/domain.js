export const PERFIS = [
  { id: 'solicitante', nome: 'Solicitante', icon: 'bi-person-check' },
  { id: 'administracao', nome: 'Administracao', icon: 'bi-kanban' },
  { id: 'infra', nome: 'Infra', icon: 'bi-tools' },
  { id: 'ti', nome: 'TI', icon: 'bi-router' },
  { id: 'operacional', nome: 'Operacional', icon: 'bi-shield-check' },
];

export const STATUS = {
  RASCUNHO: { id: 'rascunho', nome: 'Rascunho', tone: 'secondary' },
  ENVIADA: { id: 'enviada', nome: 'Enviada', tone: 'primary' },
  ANALISE: { id: 'analise', nome: 'Em analise', tone: 'warning' },
  COMPLEMENTACAO: { id: 'complementacao', nome: 'Aguardando complementacao', tone: 'info' },
  APROVADA: { id: 'aprovada', nome: 'Aprovada', tone: 'success' },
  REPROVADA: { id: 'reprovada', nome: 'Reprovada', tone: 'danger' },
  CANCELADA_SOLICITANTE: {
    id: 'cancelada_solicitante',
    nome: 'Cancelada pelo solicitante',
    tone: 'dark',
  },
  CANCELADA_COFFITO: { id: 'cancelada_coffito', nome: 'Cancelada pelo COFFITO', tone: 'dark' },
  REMANEJADA: { id: 'remanejada', nome: 'Remanejada', tone: 'purple' },
  REALIZADO: { id: 'realizado', nome: 'Evento realizado', tone: 'teal' },
  FINALIZADA: { id: 'finalizada', nome: 'Finalizada', tone: 'secondary' },
};

export const STATUS_LIST = Object.values(STATUS);

export const FAIXAS_PUBLICO = [
  {
    id: 'ate_15',
    label: 'Ate 15 participantes',
    min: 1,
    max: 15,
    orientacao: 'Indicado para reunioes pequenas e atendimento interno.',
  },
  {
    id: '16_109',
    label: '16 a 109 participantes',
    min: 16,
    max: 109,
    orientacao: 'Indicado para salas e ambientes de medio porte.',
  },
  {
    id: '110_150',
    label: '110 a 150 participantes',
    min: 110,
    max: 150,
    orientacao: 'Indicado prioritariamente para o Auditorio.',
  },
];

export const RECURSOS_BASE = [
  'Emprestimo de macas portateis',
  'Impressos gerais',
  'Notebook',
  'Televisor',
  'Projetor',
  'Sonorizacao',
  'Internet / Wi-Fi',
  'Suporte da TI',
  'Datashow',
  'Outros',
];

export const PROFISSOES = ['Fisioterapeuta', 'Terapeuta Ocupacional', 'Representante institucional', 'Outro'];

export const TIPOS_EVENTO = [
  'Curso',
  'Congresso',
  'Reuniao',
  'Plenaria',
  'Capacitacao',
  'Encontro',
  'Outro',
];

export const MONTAGEM_OPCOES = [
  { id: 'coffee_break', label: 'Espaco para Coffee Break' },
  { id: 'backdrop', label: 'Espaco para Backdrop' },
  { id: 'evento_ornamentado', label: 'Evento ornamentado' },
];

export const STATUS_EVENT_COLORS = {
  rascunho: '#6c757d',
  enviada: '#0d6efd',
  analise: '#f59f00',
  complementacao: '#0dcaf0',
  aprovada: '#198754',
  reprovada: '#dc3545',
  cancelada_solicitante: '#343a40',
  cancelada_coffito: '#343a40',
  remanejada: '#7952b3',
  realizado: '#087f5b',
  finalizada: '#6c757d',
};

export const TIPOS_USUARIOS = [
  { id: 5, nome: 'Externo' },
  { id: 6, nome: 'Interno' },
];

export const NIVEIS_ACESSO = [
  { id: 1, nome: 'ADMINISTRADOR' },
  { id: 2, nome: 'COLABORADOR' },
  { id: 3, nome: 'MASTER' },
  { id: 4, nome: 'OPERADOR' },
];

export const SETORES_SOLICITANTES = [
  { id: 1, nome: 'SETIN' },
  { id: 2, nome: 'DAGEP' },
];

export const CARGOS = [
  { id: 1, nome: 'Estagiario' },
  { id: 2, nome: 'MENOR APRENDIZ' },
  { id: 3, nome: 'Chefe de Setor' },
];
