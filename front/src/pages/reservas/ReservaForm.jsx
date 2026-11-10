import { useMemo, useState } from 'react';
import './ReservaForm.css';
import { FAIXAS_PUBLICO, MONTAGEM_OPCOES } from '../../utils/constants/domain.js';
import { ErrorAlert } from '../../components/ErrorAlert.jsx';
import { ResponsibilityTerm } from '../../components/ResponsibilityTerm.jsx';
import { getSpaceFitMessage, validateReservaForm } from '../../utils/reservas.js';
import { formatDate, todayIso } from '../../utils/date.js';
import { getFriendlyErrorMessage } from '../../utils/errors.js';
import { maskPhone, HORARIO_LIMITE } from '../../utils/validation.js';

const initialForm = {
  nome_completo: '',
  cargo: '',
  instituicao: '',
  email: '',
  telefone: '',
  nome_evento: '',
  objetivo: '',
  data_inicio: todayIso(),
  data_fim: todayIso(),
  data_avulsa: '',
  datas: [],
  horario_inicio: '09:00',
  horario_fim: '12:00',
  faixa_participantes: '16_109',
  espaco_solicitado_id: '',
  recursos: [],
  recurso_outros: '',
  suporte: {
    coffee_break: false,
    backdrop: false,
    evento_ornamentado: false,
    outros: '',
  },
  observacao: '',
  aceite_termo: false,
};

export function ReservaForm({ espacos, recursos = [], onSubmit, onCreated }) {
  const [form, setForm] = useState(initialForm);
  const [errors, setErrors] = useState({});
  const [feedback, setFeedback] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const availableSpaces = useMemo(() => espacos.filter((espaco) => espaco.disponivel), [espacos]);
  const availableResources = useMemo(
    () => recursos.filter((recurso) => recurso.disponivel).map((recurso) => recurso.nome),
    [recursos],
  );

  const selectedSpace = useMemo(
    () => availableSpaces.find((espaco) => espaco.id === Number(form.espaco_solicitado_id)),
    [availableSpaces, form.espaco_solicitado_id],
  );

  const publicMessage = selectedSpace
    ? getSpaceFitMessage(selectedSpace, form.faixa_participantes)
    : 'Selecione data, horario e espaco para orientar a analise.';

  function updateField(field, value) {
    let nextValue = value;
    if (field === 'telefone') nextValue = maskPhone(value);
    setForm((current) => ({ ...current, [field]: nextValue }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  }

  function addSpecificDate() {
    if (!form.data_avulsa) return;

    setForm((current) => {
      const dates = [...new Set([...current.datas, current.data_avulsa])].sort();
      return {
        ...current,
        datas: dates,
        data_inicio: dates[0] ?? current.data_inicio,
        data_fim: dates.at(-1) ?? current.data_fim,
        data_avulsa: '',
      };
    });
    setErrors((current) => ({ ...current, datas: undefined, data_inicio: undefined, data_fim: undefined }));
  }

  function removeSpecificDate(date) {
    setForm((current) => {
      const dates = current.datas.filter((item) => item !== date);
      return {
        ...current,
        datas: dates,
        data_inicio: dates[0] ?? current.data_inicio,
        data_fim: dates.at(-1) ?? current.data_fim,
      };
    });
  }

  function toggleRecurso(recurso) {
    setForm((current) => {
      const hasItem = current.recursos.includes(recurso);
      return {
        ...current,
        recursos: hasItem
          ? current.recursos.filter((item) => item !== recurso)
          : [...current.recursos, recurso],
      };
    });
  }

  function toggleMontagem(id) {
    setForm((current) => ({
      ...current,
      suporte: {
        ...current.suporte,
        [id]: !current.suporte[id],
      },
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const nextErrors = validateReservaForm(form);
    setErrors(nextErrors);
    setFeedback(null);

    if (Object.keys(nextErrors).length > 0) {
      setFeedback({ type: 'danger', message: 'Revise os campos destacados antes de enviar.' });
      return;
    }

    setIsSubmitting(true);
    try {
      const created = await onSubmit({
        ...form,
        espaco_solicitado_id: Number(form.espaco_solicitado_id),
        datas: form.datas.map((date) => ({
          data_inicio: date,
          data_fim: date,
          horario_inicio: form.horario_inicio,
          horario_fim: form.horario_fim,
        })),
      });
      const protocolos = created.protocolos?.length ? created.protocolos.join(', ') : created.protocolo;
      setFeedback({
        type: 'success',
        message: `Solicitacao ${protocolos} enviada para analise.`,
      });
      setForm(initialForm);
      onCreated?.(created);
    } catch (error) {
      setFeedback({ type: 'danger', message: getFriendlyErrorMessage(error, 'reserva-interna') });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="view-stack">
      <div className="section-title">
        <div>
          <p className="eyebrow">Formulario baseado no processo atual</p>
          <h2>Nova solicitacao de reserva</h2>
        </div>
      </div>

      <form className="panel form-panel" onSubmit={handleSubmit} noValidate>
        {feedback && <div className={`alert alert-${feedback.type}`}>{feedback.message}</div>}
        {feedback?.type === 'danger' && <ErrorAlert message="Campos obrigatorios ou regras de data/horario precisam ser corrigidos." />}

        <FormSection title="Dados do responsavel" icon="bi-person-vcard">
          <div className="row g-3">
            <TextField label="Nome completo" name="nome_completo" value={form.nome_completo} error={errors.nome_completo} onChange={updateField} />
            <TextField label="Cargo / Funcao" name="cargo" value={form.cargo} error={errors.cargo} onChange={updateField} />
            <TextField label="Orgao / Instituicao solicitante" name="instituicao" value={form.instituicao} error={errors.instituicao} onChange={updateField} />
            <TextField label="E-mail institucional" name="email" type="email" value={form.email} error={errors.email} onChange={updateField} />
            <TextField label="Telefone para contato" name="telefone" value={form.telefone} error={errors.telefone} onChange={updateField} placeholder="(00) 00000-0000" />
          </div>
        </FormSection>

        <FormSection title="Dados do evento" icon="bi-calendar-event">
          <div className="row g-3">
            <TextField label="Nome do evento ou reuniao" name="nome_evento" value={form.nome_evento} error={errors.nome_evento} onChange={updateField} />
            <div className="col-12">
              <label className="form-label" htmlFor="objetivo">
                Objetivo da solicitacao
              </label>
              <textarea
                id="objetivo"
                className={`form-control ${errors.objetivo ? 'is-invalid' : ''}`}
                rows="3"
                value={form.objetivo}
                onChange={(event) => updateField('objetivo', event.target.value)}
              />
              {errors.objetivo && <div className="invalid-feedback">{errors.objetivo}</div>}
            </div>
            <TextField label="Data pretendida (inicio)" name="data_inicio" type="date" value={form.data_inicio} error={errors.data_inicio} onChange={updateField} />
            <TextField label="Data pretendida (final)" name="data_fim" type="date" value={form.data_fim} error={errors.data_fim} onChange={updateField} />
            <TextField label="Horario de inicio" name="horario_inicio" type="time" value={form.horario_inicio} error={errors.horario_inicio} onChange={updateField} min={HORARIO_LIMITE.inicioMin} max={HORARIO_LIMITE.fimMax} />
            <TextField label="Horario de termino" name="horario_fim" type="time" value={form.horario_fim} error={errors.horario_fim} onChange={updateField} min={HORARIO_LIMITE.inicioMin} max={HORARIO_LIMITE.fimMax} />
            <div className="col-12">
              <p className="field-help">Horário permitido: {HORARIO_LIMITE.inicioMin} às {HORARIO_LIMITE.fimMax}.</p>
            </div>
            <div className="col-12">
              <div className="specific-dates-box">
                <div>
                  <label className="form-label" htmlFor="data_avulsa">
                    Datas especificas do mesmo evento
                  </label>
                  <div className="specific-date-input">
                    <input
                      id="data_avulsa"
                      type="date"
                      className="form-control"
                      value={form.data_avulsa}
                      onChange={(event) => updateField('data_avulsa', event.target.value)}
                    />
                    <button className="btn btn-outline-primary" type="button" onClick={addSpecificDate}>
                      Adicionar data
                    </button>
                  </div>
                  <p className="field-help">
                    Use quando o evento ocorrer em dias alternados, como 08/09 e 10/09. Cada data sera enviada como
                    uma reserva individual para analise.
                  </p>
                </div>
                {form.datas.length > 0 && (
                  <div className="selected-date-list" aria-label="Datas especificas selecionadas">
                    {form.datas.map((date) => (
                      <span key={date} className="selected-date-chip">
                        {formatDate(date)}
                        <button type="button" onClick={() => removeSpecificDate(date)} aria-label={`Remover ${formatDate(date)}`}>
                          <i className="bi bi-x" aria-hidden="true" />
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </FormSection>

        <FormSection title="Espaco e publico estimado" icon="bi-people">
          <div className="row g-3">
            <div className="col-12 col-lg-6">
              <label htmlFor="faixa_participantes" className="form-label">
                Quantidade de participantes
              </label>
              <select
                id="faixa_participantes"
                className={`form-select ${errors.faixa_participantes ? 'is-invalid' : ''}`}
                value={form.faixa_participantes}
                onChange={(event) => updateField('faixa_participantes', event.target.value)}
              >
                {FAIXAS_PUBLICO.map((faixa) => (
                  <option key={faixa.id} value={faixa.id}>
                    {faixa.label}
                  </option>
                ))}
              </select>
              {errors.faixa_participantes && <div className="invalid-feedback">{errors.faixa_participantes}</div>}
            </div>

            <div className="col-12 col-lg-6">
              <label htmlFor="espaco_solicitado_id" className="form-label">
                Espaco pretendido
              </label>
              <select
                id="espaco_solicitado_id"
                className={`form-select ${errors.espaco_solicitado_id ? 'is-invalid' : ''}`}
                value={form.espaco_solicitado_id}
                onChange={(event) => updateField('espaco_solicitado_id', event.target.value)}
              >
                <option value="">Selecione</option>
                {availableSpaces.map((espaco) => (
                  <option key={espaco.id} value={espaco.id}>
                    {espaco.nome} - {espaco.capacidade_minima} a {espaco.capacidade_maxima}
                  </option>
                ))}
              </select>
              {errors.espaco_solicitado_id && <div className="invalid-feedback">{errors.espaco_solicitado_id}</div>}
            </div>
          </div>

          <div className="guidance-box mt-3">
            <i className="bi bi-info-circle" aria-hidden="true" />
            <span>{publicMessage}</span>
          </div>
        </FormSection>

        <FormSection title="Suporte e equipamentos" icon="bi-projector">
          <div className="check-grid">
            {availableResources.map((recurso) => (
              <label key={recurso} className="form-check option-check">
                <input
                  className="form-check-input"
                  type="checkbox"
                  checked={form.recursos.includes(recurso)}
                  onChange={() => toggleRecurso(recurso)}
                />
                <span className="form-check-label">{recurso}</span>
              </label>
            ))}
          </div>
          {form.recursos.includes('Outros') && (
            <div className="mt-3">
              <label htmlFor="recurso_outros" className="form-label">
                Descricao de outros recursos
              </label>
              <input
                id="recurso_outros"
                className={`form-control ${errors.recurso_outros ? 'is-invalid' : ''}`}
                value={form.recurso_outros}
                onChange={(event) => updateField('recurso_outros', event.target.value)}
              />
              {errors.recurso_outros && <div className="invalid-feedback">{errors.recurso_outros}</div>}
            </div>
          )}
        </FormSection>

        <FormSection title="Montagem diferenciada" icon="bi-grid-3x3-gap">
          <div className="check-grid">
            {MONTAGEM_OPCOES.map((opcao) => (
              <label key={opcao.id} className="form-check option-check">
                <input
                  className="form-check-input"
                  type="checkbox"
                  checked={form.suporte[opcao.id]}
                  onChange={() => toggleMontagem(opcao.id)}
                />
                <span className="form-check-label">{opcao.label}</span>
              </label>
            ))}
          </div>
          <label htmlFor="observacao" className="form-label mt-3">
            Observacoes adicionais
          </label>
          <textarea
            id="observacao"
            className="form-control"
            rows="3"
            value={form.observacao}
            onChange={(event) => updateField('observacao', event.target.value)}
          />
        </FormSection>

        <FormSection title="Termo de Ciência e Responsabilidade" icon="bi-file-earmark-check">
          <ResponsibilityTerm />
          <label className={`form-check term-check ${errors.aceite_termo ? 'term-error' : ''}`}>
            <input
              className="form-check-input"
              type="checkbox"
              checked={form.aceite_termo}
              onChange={(event) => updateField('aceite_termo', event.target.checked)}
            />
            <span className="form-check-label">
              Declaro que li, compreendi e concordo integralmente com o Termo de Compromisso e Responsabilidade,
              assumindo as responsabilidades decorrentes da utilização do espaço institucional.
            </span>
          </label>
          {errors.aceite_termo && <div className="text-danger small mt-2">{errors.aceite_termo}</div>}
        </FormSection>

        <div className="form-actions">
          <button className="btn btn-primary btn-lg" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Enviando...' : 'Enviar solicitacao'}
          </button>
        </div>
      </form>
    </section>
  );
}

function FormSection({ title, icon, children }) {
  return (
    <fieldset className="form-section">
      <legend>
        <i className={`bi ${icon}`} aria-hidden="true" />
        {title}
      </legend>
      {children}
    </fieldset>
  );
}

function TextField({ label, name, value, onChange, error, type = 'text', placeholder = '', min, max }) {
  return (
    <div className="col-12 col-md-6">
      <label htmlFor={name} className="form-label">
        {label}
      </label>
      <input
        id={name}
        type={type}
        className={`form-control ${error ? 'is-invalid' : ''}`}
        value={value}
        placeholder={placeholder}
        min={min}
        max={max}
        onChange={(event) => onChange(name, event.target.value)}
      />
      {error && <div className="invalid-feedback">{error}</div>}
    </div>
  );
}
