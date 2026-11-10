import { FAIXAS_PUBLICO, STATUS, STATUS_LIST } from './constants/domain.js';
import { isValidCPF, isValidEmail, isValidName, isValidPhone, HORARIO_LIMITE, validateHorarioIntervalo, onlyDigits } from './validation.js';

export function getStatus(statusId) {
  return STATUS_LIST.find((status) => status.id === statusId) ?? STATUS.RASCUNHO;
}

export function getFaixa(faixaId) {
  return FAIXAS_PUBLICO.find((faixa) => faixa.id === faixaId) ?? FAIXAS_PUBLICO[0];
}

export function calculateFaixaByParticipants(total) {
  const participants = Number(total);
  if (!Number.isFinite(participants) || participants <= 0) return FAIXAS_PUBLICO[0];
  return FAIXAS_PUBLICO.find((faixa) => participants >= faixa.min && participants <= faixa.max) ?? FAIXAS_PUBLICO.at(-1);
}

export function getSolicitanteReserva(reserva = {}) {
  return {
    nome: reserva.solicitante_nome ?? reserva.nome_solicitante ?? reserva.profissional?.nome ?? '',
    cpf: reserva.solicitante_cpf ?? reserva.cpf ?? reserva.profissional?.cpf ?? '',
    email: reserva.solicitante_email ?? reserva.email ?? reserva.email_solicitante ?? reserva.profissional?.email ?? '',
    telefone: reserva.solicitante_telefone ?? reserva.telefone ?? reserva.profissional?.celular ?? '',
    profissao: reserva.solicitante_profissao ?? reserva.profissao ?? reserva.profissional?.profissao ?? '',
    possui_bloqueio: Boolean(reserva.possui_bloqueio ?? reserva.profissional?.possui_bloqueio ?? false),
    obs_bloqueio: reserva.obs_bloqueio ?? reserva.profissional?.obs_bloqueio ?? '',
  };
}

export function checkCpfBloqueio(cpf, reservas = [], currentReserva = null) {
  const digits = onlyDigits(cpf);

  if (currentReserva && Boolean(currentReserva.possui_bloqueio)) {
    return {
      isBlocked: true,
      obsBloqueio: currentReserva.obs_bloqueio || '',
      blockedReserva: currentReserva,
    };
  }

  if (digits && Array.isArray(reservas)) {
    const matching = reservas.find((r) => {
      const rCpf = onlyDigits(r.solicitante_cpf ?? r.cpf);
      return rCpf === digits && Boolean(r.possui_bloqueio);
    });

    if (matching) {
      return {
        isBlocked: true,
        obsBloqueio: matching.obs_bloqueio || '',
        blockedReserva: matching,
      };
    }
  }

  return {
    isBlocked: false,
    obsBloqueio: '',
    blockedReserva: null,
  };
}

export function getQuantidadeParticipantes(reserva = {}) {
  return reserva.quantidade_participantes ?? reserva.publico_estimado ?? null;
}

export function isAuditorio(spaceName = '') {
  return spaceName.toLowerCase().includes('auditorio');
}

export function getSpaceFitMessage(space, faixaId) {
  if (!space) return 'Selecione um espaco para validar a compatibilidade.';
  const faixa = getFaixa(faixaId);

  if (faixa.id === '110_150' && isAuditorio(space.nome)) {
    return 'Boa aderencia: o auditorio e priorizado para eventos de maior porte.';
  }

  if (faixa.id === '110_150' && !isAuditorio(space.nome)) {
    return 'Atencao: essa faixa costuma exigir o Auditorio ou um espaco equivalente.';
  }

  if (faixa.id === '16_109' && isAuditorio(space.nome)) {
    return 'O COFFITO podera sugerir outro espaco compativel para essa faixa.';
  }

  return 'Espaco compativel para analise administrativa.';
}

export function validateReservaForm(form) {
  const errors = {};

  if (!form.nome_completo?.trim()) errors.nome_completo = 'Informe o nome completo.';
  else if (!isValidName(form.nome_completo)) errors.nome_completo = 'Informe um nome completo válido (ex: João Silva).';
  if (!form.cargo?.trim()) errors.cargo = 'Informe o cargo ou funcao.';
  if (!form.instituicao?.trim()) errors.instituicao = 'Informe o orgao ou instituicao.';
  if (!form.email?.trim()) errors.email = 'Informe o e-mail institucional.';
  else if (!isValidEmail(form.email)) errors.email = 'Informe um e-mail válido.';
  if (!form.telefone?.trim()) errors.telefone = 'Informe o telefone.';
  else if (!isValidPhone(form.telefone)) errors.telefone = 'Informe um telefone válido com DDD (10 ou 11 dígitos).';
  if (!form.nome_evento?.trim()) errors.nome_evento = 'Informe o nome do evento.';
  if (!form.objetivo?.trim()) errors.objetivo = 'Descreva o objetivo da solicitacao.';
  const hasSpecificDates = Array.isArray(form.datas) && form.datas.length > 0;
  if (!hasSpecificDates && !form.data_inicio) errors.data_inicio = 'Informe a data inicial.';
  if (!hasSpecificDates && !form.data_fim) errors.data_fim = 'Informe a data final.';
  if (!form.horario_inicio) errors.horario_inicio = 'Informe o horario inicial.';
  else if (form.horario_inicio < HORARIO_LIMITE.inicioMin || form.horario_inicio > HORARIO_LIMITE.fimMax) {
    errors.horario_inicio = 'horário de solicitação não permitido';
  }
  if (!form.horario_fim) errors.horario_fim = 'Informe o horario final.';
  else if (form.horario_fim < HORARIO_LIMITE.inicioMin || form.horario_fim > HORARIO_LIMITE.fimMax) {
    errors.horario_fim = 'horário de solicitação não permitido';
  }
  if (form.horario_inicio && form.horario_fim) {
    const intervaloMsg = validateHorarioIntervalo(form.horario_inicio, form.horario_fim);
    if (intervaloMsg && !errors.horario_fim && !errors.horario_inicio) errors.horario_fim = intervaloMsg;
  }
  if (!form.espaco_solicitado_id) errors.espaco_solicitado_id = 'Selecione o espaco pretendido.';
  if (!form.faixa_participantes) errors.faixa_participantes = 'Selecione a faixa de participantes.';
  if (!form.aceite_termo) errors.aceite_termo = 'O termo precisa ser aceito para enviar.';

  if (!hasSpecificDates && form.data_inicio && form.data_fim && form.data_fim < form.data_inicio) {
    errors.data_fim = 'A data final nao pode ser anterior a data inicial.';
  }

  if (
    !hasSpecificDates &&
    form.data_inicio &&
    form.data_fim &&
    form.data_inicio === form.data_fim &&
    form.horario_inicio &&
    form.horario_fim &&
    form.horario_fim <= form.horario_inicio
  ) {
    errors.horario_fim = 'O horario final deve ser posterior ao horario inicial.';
  }

  if (form.recursos?.includes('Outros') && !form.recurso_outros?.trim()) {
    errors.recurso_outros = 'Descreva o recurso adicional solicitado.';
  }

  // CPF se preenchido (campo opcional em form interno, pode vir de integração)
  if (form.cpf?.trim() && !isValidCPF(form.cpf)) errors.cpf = 'CPF inválido.';

  return errors;
}
