import { useState } from 'react';
import { PROFISSOES } from '../../utils/constants/domain.js';
import { formatDate } from '../../utils/date.js';
import { getFriendlyErrorMessage } from '../../utils/errors.js';
import { getMotivoAjuste } from '../../utils/ajuste.js';
import { isValidCPF, isValidEmail, isValidName, isValidPhone, maskCPF, maskPhone } from '../../utils/validation.js';
import { api } from '../../services/api.js';

const STEPS = [
  { id: 'profissional', label: 'Profissional' },
  { id: 'evento', label: 'Evento' },
  { id: 'datas', label: 'Datas' },
  { id: 'observacoes', label: 'Observações' },
  { id: 'revisao', label: 'Revisão' },
];

function toInputDate(value) {
  if (!value) return '';
  return String(value).slice(0, 10);
}

function toInputTime(value) {
  if (!value) return '';
  return String(value).slice(0, 5);
}

function buildEditForm(reserva = {}) {
  return {
    solicitante_nome: reserva.solicitante_nome ?? '',
    solicitante_cpf: maskCPF(reserva.solicitante_cpf ?? ''),
    solicitante_email: reserva.solicitante_email ?? reserva.email ?? '',
    solicitante_telefone: maskPhone(reserva.solicitante_telefone ?? ''),
    solicitante_profissao: reserva.solicitante_profissao ?? '',
    nome_evento: reserva.nome_evento ?? '',
    objetivo: reserva.objetivo ?? '',
    espaco_solicitado_id: reserva.espaco_solicitado_id ?? '',
    data_inicio: toInputDate(reserva.data_inicio),
    data_fim: toInputDate(reserva.data_fim ?? reserva.data_inicio),
    horario_inicio: toInputTime(reserva.horario_inicio),
    horario_fim: toInputTime(reserva.horario_fim),
    quantidade_participantes: reserva.quantidade_participantes ?? reserva.publico_estimado ?? '',
    observacoes: reserva.observacoes ?? reserva.observacao ?? '',
  };
}

const MSG_REQUIRED = 'Preencha todos os campos corretamente.';
const MSG_NOME_INVALIDO = 'Nome inválido.';
const MSG_CPF_INVALIDO = 'CPF inválido.';
const MSG_NUMERO_INVALIDO = 'Número inválido.';
const MSG_EMAIL_INVALIDO = 'E-mail inválido.';

function validateProfissional(form) {
  if (!String(form.solicitante_nome ?? '').trim()) return MSG_REQUIRED;
  if (!isValidName(form.solicitante_nome)) return MSG_NOME_INVALIDO;
  if (String(form.solicitante_cpf ?? '').trim() && !isValidCPF(form.solicitante_cpf)) return MSG_CPF_INVALIDO;
  if (String(form.solicitante_telefone ?? '').trim() && !isValidPhone(form.solicitante_telefone)) {
    return MSG_NUMERO_INVALIDO;
  }
  if (String(form.solicitante_email ?? '').trim() && !isValidEmail(form.solicitante_email)) return MSG_EMAIL_INVALIDO;
  return '';
}

function validateEvento(form) {
  if (!String(form.nome_evento ?? '').trim() || !form.espaco_solicitado_id || !String(form.quantidade_participantes ?? '').trim()) {
    return MSG_REQUIRED;
  }
  if (!Number(form.quantidade_participantes) || Number(form.quantidade_participantes) <= 0) {
    return MSG_NUMERO_INVALIDO;
  }
  return '';
}

function validateDatas(form) {
  if (!form.data_inicio || !form.data_fim || !form.horario_inicio || !form.horario_fim) return MSG_REQUIRED;
  if (form.data_fim < form.data_inicio) return 'A data final não pode ser anterior à data inicial.';
  if (form.data_inicio === form.data_fim && form.horario_fim <= form.horario_inicio) {
    return 'O horário final deve ser posterior ao inicial no mesmo dia.';
  }
  return '';
}

function validateAll(form) {
  return validateProfissional(form) || validateEvento(form) || validateDatas(form);
}

export function AjusteEditor({ reserva, historico = [], authProtocolo, authEmail, espacos = [], onSaved }) {
  const [isEditing, setIsEditing] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);
  const [draft, setDraft] = useState(() => buildEditForm(reserva));
  const [stepError, setStepError] = useState('');
  const [saveError, setSaveError] = useState('');
  const [saveSuccess, setSaveSuccess] = useState('');
  const [saving, setSaving] = useState(false);

  const motivoAjuste = getMotivoAjuste(reserva, historico);
  const espacoNome = espacos.find((espaco) => Number(espaco.id) === Number(draft.espaco_solicitado_id))?.nome
    ?? reserva.espaco_solicitado
    ?? reserva.espaco
    ?? '-';

  function updateField(field, value) {
    let nextValue = value;
    if (field === 'solicitante_cpf') nextValue = maskCPF(value);
    if (field === 'solicitante_telefone') nextValue = maskPhone(value);
    setDraft((current) => ({ ...current, [field]: nextValue }));
    setStepError('');
    setSaveError('');
  }

  function handleStartEdit() {
    setDraft(buildEditForm(reserva));
    setStepError('');
    setSaveError('');
    setSaveSuccess('');
    setStepIndex(0);
    setIsEditing(true);
  }

  function handleCancelEdit() {
    setDraft(buildEditForm(reserva));
    setStepError('');
    setSaveError('');
    setIsEditing(false);
    setStepIndex(0);
  }

  function validateStep(index) {
    const stepId = STEPS[index].id;
    if (stepId === 'profissional') return validateProfissional(draft);
    if (stepId === 'evento') return validateEvento(draft);
    if (stepId === 'datas') return validateDatas(draft);
    return '';
  }

  function goNext() {
    const message = validateStep(stepIndex);
    if (message) {
      setStepError(message);
      return;
    }
    setStepError('');
    setStepIndex((current) => Math.min(current + 1, STEPS.length - 1));
  }

  function goBack() {
    setStepError('');
    setStepIndex((current) => Math.max(current - 1, 0));
  }

  async function handleSave(event) {
    event?.preventDefault();
    if (!isEditing || saving) return;

    const message = validateAll(draft);
    if (message) {
      setSaveError(message);
      const badIndex = STEPS.findIndex((step) => validateStep(STEPS.indexOf(step)));
      if (badIndex >= 0) setStepIndex(badIndex);
      return;
    }

    setSaving(true);
    setSaveError('');
    setSaveSuccess('');
    try {
      const payload = {
        protocolo: String(authProtocolo ?? '').trim(),
        email: String(authEmail ?? '').trim(),
        nome_evento: String(draft.nome_evento).trim(),
        objetivo: String(draft.objetivo ?? '').trim() || null,
        espaco_solicitado_id: Number(draft.espaco_solicitado_id),
        data_inicio: draft.data_inicio,
        data_fim: draft.data_fim,
        horario_inicio: draft.horario_inicio,
        horario_fim: draft.horario_fim,
        quantidade_participantes: Number(draft.quantidade_participantes),
        solicitante_nome: String(draft.solicitante_nome ?? '').trim() || null,
        solicitante_cpf: String(draft.solicitante_cpf ?? '').trim() || null,
        solicitante_email: String(draft.solicitante_email ?? '').trim() || null,
        solicitante_telefone: String(draft.solicitante_telefone ?? '').trim() || null,
        solicitante_profissao: String(draft.solicitante_profissao ?? '').trim() || null,
        observacoes: String(draft.observacoes ?? '').trim() || null,
      };
      const updated = await api.submitPublicAjuste(reserva.id, payload);
      onSaved?.(updated);
      // Após salvar, nada mais fica alterável até clicar em editar novamente.
      setIsEditing(false);
      setStepIndex(0);
      setSaveSuccess('Ajuste salvo com sucesso. A solicitação voltou para análise do COFFITO.');
    } catch (requestError) {
      setSaveError(getFriendlyErrorMessage(requestError, 'reserva-publica'));
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="ajuste-editor" aria-label="Ajuste da solicitação">
      {motivoAjuste && (
        <div className="ajuste-motivo-box" role="note" aria-label="Motivo do ajuste solicitado">
          <h3>
            <i className="bi bi-exclamation-triangle" aria-hidden="true" />
            Ajuste solicitado pela administração
          </h3>
          <p>{motivoAjuste}</p>
        </div>
      )}

      {saveSuccess && <div className="alert alert-success">{saveSuccess}</div>}

      {!isEditing ? (
        <>
          <div className="ajuste-locked-banner">
            <i className="bi bi-lock" aria-hidden="true" />
            <span>Os dados estão bloqueados. Clique em editar para alterar sua solicitação por seção.</span>
          </div>
          <div className="ajuste-editor-actions">
            <button className="btn btn-warning" type="button" onClick={handleStartEdit}>
              <i className="bi bi-pencil-square me-2" aria-hidden="true" />
              Editar solicitação
            </button>
          </div>
        </>
      ) : (
        <>
          <ol className="wizard-stepper" aria-label="Seções do ajuste">
            {STEPS.map((step, index) => (
              <li key={step.id} className={index === stepIndex ? 'active' : index < stepIndex ? 'done' : ''}>
                <button type="button" className="wizard-step-button" onClick={() => { setStepError(''); setStepIndex(index); }} aria-current={index === stepIndex ? 'step' : undefined}>
                  <span>{index + 1}</span>
                  <strong>{step.label}</strong>
                </button>
              </li>
            ))}
          </ol>

          {stepError && <div className="alert alert-danger">{stepError}</div>}

          <div className="public-step">
            {STEPS[stepIndex].id === 'profissional' && (
              <>
                <h2>Dados do profissional</h2>
                <div className="row g-3">
                  <EditorSelect
                    label="Profissão"
                    value={draft.solicitante_profissao}
                    options={PROFISSOES}
                    onChange={(value) => updateField('solicitante_profissao', value)}
                  />
                  <EditorInput label="Nome completo" value={draft.solicitante_nome} onChange={(value) => updateField('solicitante_nome', value)} />
                  <EditorInput label="Celular" value={draft.solicitante_telefone} onChange={(value) => updateField('solicitante_telefone', value)} placeholder="(00) 00000-0000" />
                  <EditorInput label="E-mail" type="email" value={draft.solicitante_email} onChange={(value) => updateField('solicitante_email', value)} placeholder="email@email.com.br" />
                  <EditorInput label="CPF" value={draft.solicitante_cpf} onChange={(value) => updateField('solicitante_cpf', value)} placeholder="000.000.000-00" />
                </div>
              </>
            )}

            {STEPS[stepIndex].id === 'evento' && (
              <>
                <h2>Dados do evento</h2>
                <div className="row g-3">
                  <EditorInput label="Nome do evento" value={draft.nome_evento} onChange={(value) => updateField('nome_evento', value)} />
                  <EditorInput label="Número de participantes" type="number" value={draft.quantidade_participantes} onChange={(value) => updateField('quantidade_participantes', value)} />
                  <div className="col-12">
                    <label className="form-label" htmlFor="ajuste-objetivo">Programação / objetivo</label>
                    <textarea
                      id="ajuste-objetivo"
                      className="form-control"
                      rows="4"
                      value={draft.objetivo}
                      onChange={(event) => updateField('objetivo', event.target.value)}
                    />
                  </div>
                  <div className="col-12">
                    <label className="form-label" htmlFor="ajuste-espaco">Espaço pretendido</label>
                    <select
                      id="ajuste-espaco"
                      className="form-select"
                      value={draft.espaco_solicitado_id}
                      onChange={(event) => updateField('espaco_solicitado_id', event.target.value)}
                    >
                      <option value="">Selecione</option>
                      {espacos.map((espaco) => (
                        <option key={espaco.id} value={espaco.id}>
                          {espaco.nome}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </>
            )}

            {STEPS[stepIndex].id === 'datas' && (
              <>
                <h2>Período do evento</h2>
                <div className="row g-3">
                  <EditorInput label="Data de início" type="date" value={draft.data_inicio} onChange={(value) => updateField('data_inicio', value)} />
                  <EditorInput label="Data final" type="date" value={draft.data_fim} onChange={(value) => updateField('data_fim', value)} />
                  <EditorInput label="Horário de início" type="time" value={draft.horario_inicio} onChange={(value) => updateField('horario_inicio', value)} />
                  <EditorInput label="Horário de término" type="time" value={draft.horario_fim} onChange={(value) => updateField('horario_fim', value)} />
                </div>
              </>
            )}

            {STEPS[stepIndex].id === 'observacoes' && (
              <>
                <h2>Observações</h2>
                <label className="form-label" htmlFor="ajuste-observacoes">Observações do ajuste</label>
                <textarea
                  id="ajuste-observacoes"
                  className="form-control"
                  rows="5"
                  value={draft.observacoes}
                  onChange={(event) => updateField('observacoes', event.target.value)}
                  placeholder="Detalhe aqui o que foi corrigido..."
                />
              </>
            )}

            {STEPS[stepIndex].id === 'revisao' && (
              <>
                <h2>Revisão</h2>
                <p>Confira os dados antes de salvar o ajuste.</p>
                <dl className="ajuste-readonly-list">
                  <ReviewRow label="Solicitante" value={draft.solicitante_nome} />
                  <ReviewRow label="E-mail" value={draft.solicitante_email} />
                  <ReviewRow label="Telefone" value={draft.solicitante_telefone} />
                  <ReviewRow label="Evento" value={draft.nome_evento} />
                  <ReviewRow label="Espaço" value={espacoNome} />
                  <ReviewRow label="Participantes" value={draft.quantidade_participantes} />
                  <ReviewRow label="Período" value={`${formatDate(draft.data_inicio)} até ${formatDate(draft.data_fim)}`} />
                  <ReviewRow
                    label="Horário"
                    value={`${String(draft.horario_inicio).slice(0, 5)} às ${String(draft.horario_fim).slice(0, 5)}`}
                  />
                </dl>
              </>
            )}
          </div>

          {saveError && <div className="alert alert-danger">{saveError}</div>}

          <div className="public-form-actions ajuste-editor-footer">
            <button type="button" className="btn btn-secondary" onClick={goBack} disabled={stepIndex === 0}>
              Voltar
            </button>
            <div className="ajuste-edit-actions">
              <button type="button" className="btn btn-outline-secondary" onClick={handleCancelEdit} disabled={saving}>
                Cancelar
              </button>
              {stepIndex < STEPS.length - 1 ? (
                <button type="button" className="btn btn-primary" onClick={goNext}>
                  Próximo
                </button>
              ) : null}
              <button type="button" className="btn btn-success" onClick={handleSave} disabled={saving}>
                {saving ? 'Salvando...' : 'Salvar ajuste'}
              </button>
            </div>
          </div>
        </>
      )}
    </section>
  );
}

function ReviewRow({ label, value }) {
  return (
    <div className="ajuste-readonly-row">
      <dt>{label}</dt>
      <dd>{value ? String(value) : '-'}</dd>
    </div>
  );
}

function EditorInput({ label, value, onChange, type = 'text', placeholder = '' }) {
  return (
    <div className="col-12 col-lg-6">
      <label className="form-label">
        {label}
        <input
          type={type}
          className="form-control"
          value={value ?? ''}
          placeholder={placeholder}
          onChange={(event) => onChange(event.target.value)}
        />
      </label>
    </div>
  );
}

function EditorSelect({ label, value, options, onChange }) {
  const normalized = [...new Set([...options, value].filter(Boolean))];
  return (
    <div className="col-12 col-lg-6">
      <label className="form-label">
        {label}
        <select className="form-select" value={value ?? ''} onChange={(event) => onChange(event.target.value)}>
          <option value="">Selecione</option>
          {normalized.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
