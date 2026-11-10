import { useMemo, useState } from 'react';
import { PROFISSOES, TIPOS_EVENTO } from '../../utils/constants/domain.js';
import { calculateFaixaByParticipants, getFaixa } from '../../utils/reservas.js';
import { getFriendlyErrorMessage } from '../../utils/errors.js';
import { isValidCPF, isValidEmail, isValidName, isValidPhone, maskCPF, maskPhone, HORARIO_LIMITE, validateHorarioIntervalo } from '../../utils/validation.js';
import { PublicFormShell } from './PublicFormShell.jsx';
import { WizardStepper } from './WizardStepper.jsx';
import { DateRangeSelector } from './DateRangeSelector.jsx';
import { ResourceChecklist } from './ResourceChecklist.jsx';
import { FileUploadField } from './FileUploadField.jsx';
import { ReviewSummary } from './ReviewSummary.jsx';
import { ResponsibilityTerm } from '../../components/ResponsibilityTerm.jsx';

const steps = [
  { id: 'profissional', label: 'Profissional' },
  { id: 'evento', label: 'Evento' },
  { id: 'datas', label: 'Datas' },
  { id: 'divulgacao', label: 'Divulgacao' },
  { id: 'recursos', label: 'Recursos' },
  { id: 'revisao', label: 'Revisao' },
];

const initialForm = {
  profissional: {
    profissao: 'Fisioterapeuta',
    nome: '',
    celular: '',
    email: '',
    cpf: '',
  },
  solicitante_nome: '',
  solicitante_cpf: '',
  solicitante_email: '',
  solicitante_telefone: '',
  solicitante_profissao: 'Fisioterapeuta',
  evento: {
    tipo: '',
    nome: '',
    organizador: '',
    programacao: '',
    link: '',
    pago: 'nao',
    valor: '',
    publico_estimado: '',
    faixa_calculada: 'ate_15',
  },
  espaco_solicitado_id: '',
  periodo: {
    data_inicio: '',
    data_fim: '',
    data_avulsa: '',
    horario_inicio: '',
    horario_fim: '',
  },
  datas: [],
  divulgacao: {
    canais: [],
    precisa_inscricao: 'nao',
    realizado_anteriormente: '',
    material_pronto: 'nao',
  },
  recursos: {
    itens: [],
    outros_apoiadores: '',
    observacoes: '',
  },
  anexos: [],
  aceite_termo: false,
};

export function PublicReservationWizard({ espacos, recursos = [], reservas, onSubmit, onGoInternal, onTrackReservation }) {
  const [stepIndex, setStepIndex] = useState(0);
  const [editingFromReview, setEditingFromReview] = useState(false);
  const [reviewConfirmed, setReviewConfirmed] = useState(false);
  const [form, setForm] = useState(initialForm);
  const [errors, setErrors] = useState({});
  const [submitState, setSubmitState] = useState({ status: 'idle', reserva: null, message: '' });
  const availableSpaces = useMemo(() => espacos.filter((espaco) => espaco.disponivel), [espacos]);
  const availableResources = useMemo(
    () => recursos.filter((recurso) => recurso.disponivel).map((recurso) => recurso.nome),
    [recursos],
  );

  const occupiedDates = useMemo(() => {
    return new Set(
      reservas
        .filter((reserva) => !reserva.status_id.includes('cancelada'))
        .flatMap((reserva) => {
          if (Array.isArray(reserva.datas) && reserva.datas.length > 0) {
            return reserva.datas.flatMap((item) => [item.data_inicio ?? item.data, item.data_fim ?? item.data]);
          }
          return [reserva.data_inicio, reserva.data_fim];
        }),
    );
  }, [reservas]);

  const suggestedSpace = useMemo(() => {
    const selectedSpace = availableSpaces.find((espaco) => espaco.id === Number(form.espaco_solicitado_id));
    if (selectedSpace) return selectedSpace;

    const total = Number(form.evento.publico_estimado) || 0;
    if (!total || availableSpaces.length === 0) return null;

    const compatibleSpaces = availableSpaces.filter(
      (espaco) => total >= Number(espaco.capacidade_minima) && total <= Number(espaco.capacidade_maxima),
    );
    const orderedCompatibleSpaces = [...compatibleSpaces].sort((a, b) => {
      const auditoriumPriority = Number(isAuditorium(b)) - Number(isAuditorium(a));
      if (total >= 110 && auditoriumPriority !== 0) return auditoriumPriority;
      return Number(a.capacidade_maxima) - Number(b.capacidade_maxima);
    });

    return orderedCompatibleSpaces[0] ?? findClosestSpaceByCapacity(availableSpaces, total);
  }, [availableSpaces, form.espaco_solicitado_id, form.evento.publico_estimado]);

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
    setErrors({});
  }

  function updateSection(section, field, value) {
    let maskedValue = value;
    if (section === 'profissional' && field === 'cpf') maskedValue = maskCPF(value);
    if (section === 'profissional' && field === 'celular') maskedValue = maskPhone(value);
    setForm((current) => {
      const next = {
        ...current,
        [section]: {
          ...current[section],
          [field]: maskedValue,
        },
      };

      if (section === 'evento' && field === 'publico_estimado') {
        next.evento.faixa_calculada = calculateFaixaByParticipants(value).id;
      }

      if (section === 'profissional') {
        const solicitanteFieldMap = {
          nome: 'solicitante_nome',
          cpf: 'solicitante_cpf',
          email: 'solicitante_email',
          celular: 'solicitante_telefone',
          profissao: 'solicitante_profissao',
        };
        if (solicitanteFieldMap[field]) next[solicitanteFieldMap[field]] = maskedValue;
      }

      return next;
    });
    setErrors({});
  }

  function updatePeriodo(field, value) {
    setForm((current) => ({
      ...current,
      periodo: {
        ...current.periodo,
        [field]: value,
      },
    }));
    setErrors({});
  }

  function addSpecificDate() {
    if (!form.periodo.data_avulsa) return;

    setForm((current) => {
      const dates = [...new Set([...current.datas, current.periodo.data_avulsa])].sort();
      return {
        ...current,
        datas: dates,
        periodo: {
          ...current.periodo,
          data_inicio: dates[0] ?? current.periodo.data_inicio,
          data_fim: dates.at(-1) ?? current.periodo.data_fim,
          data_avulsa: '',
        },
      };
    });
    setErrors({});
  }

  function removeSpecificDate(date) {
    setForm((current) => {
      const dates = current.datas.filter((item) => item !== date);
      return {
        ...current,
        datas: dates,
        periodo: {
          ...current.periodo,
          data_inicio: dates[0] ?? current.periodo.data_inicio,
          data_fim: dates.at(-1) ?? current.periodo.data_fim,
        },
      };
    });
  }

  function toggleArray(section, field, value) {
    setForm((current) => {
      const list = current[section][field];
      const exists = list.includes(value);
      return {
        ...current,
        [section]: {
          ...current[section],
          [field]: exists ? list.filter((item) => item !== value) : [...list, value],
        },
      };
    });
  }

  function validateStep(index) {
    const step = steps[index].id;
    const nextErrors = {};

    if (step === 'profissional') {
      if (!form.profissional.profissao) nextErrors.profissao = 'Selecione a profissao.';
      if (!form.profissional.nome.trim()) nextErrors.nome = 'Informe o nome completo.';
      else if (!isValidName(form.profissional.nome)) nextErrors.nome = 'Nome inválido (use nome completo real, ex: João Silva).';
      if (!form.profissional.celular.trim()) nextErrors.celular = 'Informe o celular.';
      else if (!isValidPhone(form.profissional.celular)) nextErrors.celular = 'Celular inválido (use DDD + 10 ou 11 dígitos).';
      if (!form.profissional.email.trim()) nextErrors.email = 'Informe o e-mail.';
      else if (!isValidEmail(form.profissional.email)) nextErrors.email = 'E-mail inválido.';
      if (!form.profissional.cpf.trim()) nextErrors.cpf = 'Informe o CPF.';
      else if (!isValidCPF(form.profissional.cpf)) nextErrors.cpf = 'CPF inválido.';
    }

    if (step === 'evento') {
      if (!form.evento.tipo) nextErrors.tipo = 'Selecione o tipo do evento.';
      if (!form.evento.nome.trim()) nextErrors.nome_evento = 'Informe o nome do evento.';
      if (!form.evento.organizador.trim()) nextErrors.organizador = 'Informe o organizador.';
      if (!form.evento.publico_estimado || Number(form.evento.publico_estimado) <= 0) {
        nextErrors.publico_estimado = 'Informe o numero estimado de participantes.';
      }
      if (!form.espaco_solicitado_id) nextErrors.espaco_solicitado_id = 'Selecione o espaco pretendido.';
    }

    if (step === 'datas') {
      const hasSpecificDates = form.datas.length > 0;
      if (!hasSpecificDates && !form.periodo.data_inicio) nextErrors.data_inicio = 'Informe a data de inicio do evento.';
      if (!hasSpecificDates && !form.periodo.data_fim) nextErrors.data_fim = 'Informe a data final do evento.';
      if (!form.periodo.horario_inicio) nextErrors.horario_inicio = 'Informe o horario inicial do evento.';
      else if (form.periodo.horario_inicio < HORARIO_LIMITE.inicioMin || form.periodo.horario_inicio > HORARIO_LIMITE.fimMax) {
        nextErrors.horario_inicio = 'horário de solicitação não permitido';
      }
      if (!form.periodo.horario_fim) nextErrors.horario_fim = 'Informe o horario final do evento.';
      else if (form.periodo.horario_fim < HORARIO_LIMITE.inicioMin || form.periodo.horario_fim > HORARIO_LIMITE.fimMax) {
        nextErrors.horario_fim = 'horário de solicitação não permitido';
      }
      if (form.periodo.horario_inicio && form.periodo.horario_fim) {
        const msg = validateHorarioIntervalo(form.periodo.horario_inicio, form.periodo.horario_fim);
        if (msg && !nextErrors.horario_inicio && !nextErrors.horario_fim) nextErrors.intervalo = msg;
      }
      if (!hasSpecificDates && form.periodo.data_inicio && form.periodo.data_fim && form.periodo.data_fim < form.periodo.data_inicio) {
        nextErrors.periodo = 'Data final deve ser igual ou posterior a data de inicio.';
      }
      if (
        !hasSpecificDates &&
        form.periodo.data_inicio &&
        form.periodo.data_fim &&
        form.periodo.data_inicio === form.periodo.data_fim &&
        form.periodo.horario_inicio &&
        form.periodo.horario_fim &&
        form.periodo.horario_fim <= form.periodo.horario_inicio
      ) {
        nextErrors.intervalo = 'Horario final deve ser posterior ao inicial quando o evento ocorre no mesmo dia.';
      }
    }

    if (step === 'recursos') {
      if (!form.aceite_termo) nextErrors.aceite_termo = 'Confirme a ciencia das regras do edital.';
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  function goNext() {
    if (!validateStep(stepIndex)) return;
    setStepIndex((current) => editingFromReview ? steps.length - 1 : Math.min(current + 1, steps.length - 1));
    setEditingFromReview(false);
    setReviewConfirmed(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function goBack() {
    setEditingFromReview(false);
    setReviewConfirmed(false);
    setStepIndex((current) => Math.max(current - 1, 0));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function editReviewSection(section) {
    const index = steps.findIndex((step) => step.id === section);
    if (index < 0 || submitState.status === 'loading') return;
    setErrors({});
    setSubmitState({ status: 'idle', reserva: null, message: '' });
    setReviewConfirmed(false);
    setEditingFromReview(true);
    setStepIndex(index);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function restartWizard() {
    setForm(initialForm);
    setErrors({});
    setSubmitState({ status: 'idle', reserva: null, message: '' });
    setStepIndex(0);
    setEditingFromReview(false);
    setReviewConfirmed(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  async function submit() {
    if (!reviewConfirmed || submitState.status === 'loading') return;
    for (let index = 0; index < steps.length - 1; index += 1) {
      if (!validateStep(index)) {
        setStepIndex(index);
        setEditingFromReview(true);
        setReviewConfirmed(false);
        window.scrollTo({ top: 0, behavior: 'smooth' });
        return;
      }
    }

    setSubmitState({ status: 'loading', reserva: null, message: '' });
    try {
      const created = await onSubmit({
        ...form,
        espaco_solicitado_id: Number(form.espaco_solicitado_id),
        datas: form.datas.map((date) => ({
          data_inicio: date,
          data_fim: date,
          horario_inicio: form.periodo.horario_inicio,
          horario_fim: form.periodo.horario_fim,
        })),
      });
      const protocolos = created.protocolos?.length ? created.protocolos.join(', ') : created.protocolo;
      setSubmitState({
        status: 'success',
        reserva: created,
        message: `Solicitacao ${protocolos} enviada para analise.`,
      });
    } catch (error) {
      setSubmitState({
        status: 'error',
        reserva: null,
        message: getFriendlyErrorMessage(error, 'reserva-publica'),
      });
    }
  }

  if (submitState.status === 'success') {
    const trackingProtocol = submitState.reserva?.protocolos?.[0] ?? submitState.reserva?.protocolo;

    return (
      <PublicFormShell>
        <section className="public-card public-success">
          <i className="bi bi-check2-circle" aria-hidden="true" />
          <h2>Solicitacao enviada</h2>
          <p>{submitState.message}</p>
          <p>
            O COFFITO analisara a disponibilidade e retornara pelo e-mail informado. Guarde o numero do protocolo
            para acompanhamento.
          </p>
          <div className="public-actions">
            <button type="button" className="btn btn-outline-secondary" onClick={restartWizard}>
              Nova solicitacao
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => (trackingProtocol ? onTrackReservation?.(trackingProtocol) : onGoInternal?.())}
            >
              Acompanhar solicitacao
            </button>
          </div>
        </section>
      </PublicFormShell>
    );
  }

  return (
    <PublicFormShell>
      <WizardStepper steps={steps} currentStep={stepIndex} />
      <form className={`public-card${stepIndex === 5 ? ' public-card--review' : ''}`} onSubmit={(event) => event.preventDefault()} noValidate>
        {Object.keys(errors).length > 0 && (
          <div className="alert alert-danger">Revise os campos obrigatorios antes de continuar.</div>
        )}
        {submitState.status === 'error' && <div className="alert alert-danger" role="alert">{submitState.message}</div>}

        {stepIndex === 0 && (
          <StepProfissional form={form} errors={errors} updateSection={updateSection} />
        )}
        {stepIndex === 1 && (
          <StepEvento
            form={form}
            errors={errors}
            suggestedSpace={suggestedSpace}
            availableSpaces={availableSpaces}
            updateSection={updateSection}
            updateField={updateField}
          />
        )}
        {stepIndex === 2 && (
          <StepDatas
            form={form}
            errors={errors}
            occupiedDates={occupiedDates}
            updatePeriodo={updatePeriodo}
            addSpecificDate={addSpecificDate}
            removeSpecificDate={removeSpecificDate}
          />
        )}
        {stepIndex === 3 && <StepDivulgacao form={form} updateSection={updateSection} toggleArray={toggleArray} />}
        {stepIndex === 4 && (
          <StepRecursos
            form={form}
            errors={errors}
            resourceOptions={availableResources}
            updateSection={updateSection}
            toggleArray={toggleArray}
            setForm={setForm}
          />
        )}
        {stepIndex === 5 && (
          <ReviewSummary
            form={form}
            suggestedSpace={suggestedSpace}
            confirmed={reviewConfirmed}
            onConfirm={setReviewConfirmed}
            onEdit={editReviewSection}
            onBack={goBack}
            onSubmit={submit}
            submitting={submitState.status === 'loading'}
          />
        )}

        {stepIndex < steps.length - 1 && <div className="public-form-actions">
          <button type="button" className="btn btn-secondary" onClick={goBack} disabled={stepIndex === 0}>
            Voltar
          </button>
          <button type="button" className="btn btn-primary" onClick={goNext}>
            {editingFromReview ? 'Voltar à revisão' : 'Proximo'}
          </button>
        </div>}
      </form>
    </PublicFormShell>
  );
}

function StepProfissional({ form, errors, updateSection }) {
  return (
    <div className="public-step">
      <h2>Dados do profissional</h2>
      <div className="row g-3">
        <SelectField
          label="Profissao"
          value={form.profissional.profissao}
          error={errors.profissao}
          options={PROFISSOES}
          onChange={(value) => updateSection('profissional', 'profissao', value)}
        />
        <InputField label="Nome completo" value={form.profissional.nome} error={errors.nome} onChange={(value) => updateSection('profissional', 'nome', value)} />
        <InputField label="Celular" value={form.profissional.celular} error={errors.celular} onChange={(value) => updateSection('profissional', 'celular', value)} placeholder="(00) 00000-0000" />
        <InputField label="E-mail" type="email" value={form.profissional.email} error={errors.email} onChange={(value) => updateSection('profissional', 'email', value)} placeholder="email@email.com.br" />
        <InputField label="CPF" value={form.profissional.cpf} error={errors.cpf} onChange={(value) => updateSection('profissional', 'cpf', value)} placeholder="000.000.000-00" />
      </div>
    </div>
  );
}

function StepEvento({ form, errors, suggestedSpace, availableSpaces, updateSection, updateField }) {
  const faixa = getFaixa(form.evento.faixa_calculada);
  return (
    <div className="public-step">
      <h2>Dados do evento</h2>
      <div className="row g-3">
        <SelectField label="Tipo do evento" value={form.evento.tipo} error={errors.tipo} options={TIPOS_EVENTO} onChange={(value) => updateSection('evento', 'tipo', value)} />
        <InputField label="Nome do evento" value={form.evento.nome} error={errors.nome_evento} onChange={(value) => updateSection('evento', 'nome', value)} />
        <InputField label="Instituicao ou profissional organizador" value={form.evento.organizador} error={errors.organizador} onChange={(value) => updateSection('evento', 'organizador', value)} />
        <div className="col-12">
          <label className="form-label" htmlFor="programacao">
            Programacao preliminar
          </label>
          <textarea
            id="programacao"
            className="form-control"
            rows="5"
            value={form.evento.programacao}
            onChange={(event) => updateSection('evento', 'programacao', event.target.value)}
            placeholder="Ex: conteudo programatico, palestrante(s)..."
          />
          <p className="field-help">Preencha somente se houver.</p>
        </div>
        <InputField label="Pagina do evento (link)" value={form.evento.link} onChange={(value) => updateSection('evento', 'link', value)} />
        <InputField label="Numero de participantes" type="number" value={form.evento.publico_estimado} error={errors.publico_estimado} onChange={(value) => updateSection('evento', 'publico_estimado', value)} />
        <SpaceSelectField
          label="Espaco pretendido"
          value={form.espaco_solicitado_id}
          error={errors.espaco_solicitado_id}
          spaces={availableSpaces}
          onChange={(value) => updateField('espaco_solicitado_id', value)}
        />
        <SelectField label="Evento pago?" value={form.evento.pago} options={['nao', 'sim']} onChange={(value) => updateSection('evento', 'pago', value)} />
        {form.evento.pago === 'sim' && (
          <InputField label="Valor do evento" value={form.evento.valor} onChange={(value) => updateSection('evento', 'valor', value)} />
        )}
      </div>
      <div className="public-hint mt-3">
        <strong>Faixa calculada:</strong> {faixa.label}.{' '}
        <SpaceSuggestionText
          selectedSpaceId={form.espaco_solicitado_id}
          suggestedSpace={suggestedSpace}
          total={Number(form.evento.publico_estimado) || 0}
        />
      </div>
    </div>
  );
}

function StepDatas({ form, errors, occupiedDates, updatePeriodo, addSpecificDate, removeSpecificDate }) {
  return (
    <div className="public-step">
      <h2>Periodo do evento</h2>
      <p>
        Informe a data de inicio, data final e horarios correspondentes. Datas com menos de 30 dias ou ja ocupadas
        geram aviso visual, mas podem ser enviadas para analise.
      </p>
      <DateRangeSelector
        periodo={form.periodo}
        selectedDates={form.datas}
        occupiedDates={occupiedDates}
        onChange={updatePeriodo}
        onAddDate={addSpecificDate}
        onRemoveDate={removeSpecificDate}
      />
      {Object.entries(errors)
        .filter(([key]) => ['data_inicio', 'data_fim', 'horario_inicio', 'horario_fim', 'periodo', 'intervalo'].includes(key))
        .map(([key, value]) => (
          <div className="text-danger small mt-2" key={key}>
            {value}
          </div>
        ))}
    </div>
  );
}

function StepDivulgacao({ form, updateSection, toggleArray }) {
  return (
    <div className="public-step">
      <h2>Divulgacao previa</h2>
      <p>Preencha somente se solicitar divulgacao do evento antes da realizacao.</p>

      <div className="public-checkbox-stack">
        <label className="form-check">
          <input
            className="form-check-input"
            type="checkbox"
            checked={form.divulgacao.canais.includes('site')}
            onChange={() => toggleArray('divulgacao', 'canais', 'site')}
          />
          <span className="form-check-label">Site oficial da autarquia</span>
        </label>
        <label className="form-check">
          <input
            className="form-check-input"
            type="checkbox"
            checked={form.divulgacao.canais.includes('redes_sociais')}
            onChange={() => toggleArray('divulgacao', 'canais', 'redes_sociais')}
          />
          <span className="form-check-label">Redes sociais</span>
        </label>
      </div>

      <div className="row g-3 mt-1">
        <SelectField label="Os participantes precisam se inscrever?" value={form.divulgacao.precisa_inscricao} options={['nao', 'sim']} onChange={(value) => updateSection('divulgacao', 'precisa_inscricao', value)} />
        <SelectField label="Possui material de divulgacao pronto?" value={form.divulgacao.material_pronto} options={['nao', 'sim']} onChange={(value) => updateSection('divulgacao', 'material_pronto', value)} />
        <InputField label="O evento ja foi realizado anteriormente?" value={form.divulgacao.realizado_anteriormente} onChange={(value) => updateSection('divulgacao', 'realizado_anteriormente', value)} placeholder="Se sim, onde?" />
      </div>
    </div>
  );
}

function StepRecursos({ form, errors, resourceOptions, updateSection, toggleArray, setForm }) {
  return (
    <div className="public-step">
      <h2>Recursos, anexos e ciencia</h2>
      <ResourceChecklist
        resourceOptions={resourceOptions}
        selectedItems={form.recursos.itens}
        onToggle={(item) => toggleArray('recursos', 'itens', item)}
      />

      <label className="form-label mt-3" htmlFor="apoiadores">
        Havera outros apoiadores?
      </label>
      <input
        id="apoiadores"
        className="form-control"
        value={form.recursos.outros_apoiadores}
        onChange={(event) => updateSection('recursos', 'outros_apoiadores', event.target.value)}
        placeholder="Se sim, quais?"
      />

      <label className="form-label mt-3" htmlFor="publicObservacoes">
        Observacoes
      </label>
      <textarea
        id="publicObservacoes"
        className="form-control"
        rows="4"
        value={form.recursos.observacoes}
        onChange={(event) => updateSection('recursos', 'observacoes', event.target.value)}
      />

      <div className="mt-3">
        <FileUploadField files={form.anexos} onChange={(files) => setForm((current) => ({ ...current, anexos: files }))} />
      </div>

      <div className="public-counterpart">
        <strong>Contrapartidas para o COFFITO</strong>
        <ul>
          <li>Disponibilizacao de vagas para sorteio quando aplicavel.</li>
          <li>Inclusao de fala institucional breve na programacao.</li>
          <li>Logo do Conselho em materiais de divulgacao, quando houver.</li>
        </ul>
      </div>

      <ResponsibilityTerm />

      <label className={`form-check public-term ${errors.aceite_termo ? 'term-error' : ''}`}>
        <input
          className="form-check-input"
          type="checkbox"
          checked={form.aceite_termo}
          onChange={(event) => setForm((current) => ({ ...current, aceite_termo: event.target.checked }))}
        />
        <span className="form-check-label">
          Declaro que li, compreendi e concordo integralmente com o Termo de Compromisso e Responsabilidade,
          assumindo as responsabilidades decorrentes da utilização do espaço institucional.
        </span>
      </label>
      {errors.aceite_termo && <div className="text-danger small mt-2">{errors.aceite_termo}</div>}
    </div>
  );
}

function InputField({ label, value, onChange, error, type = 'text', placeholder = '' }) {
  return (
    <div className="col-12 col-lg-6">
      <label className="form-label">
        {label} {error !== undefined && '*'}
        <input
          type={type}
          className={`form-control ${error ? 'is-invalid' : ''}`}
          value={value}
          placeholder={placeholder}
          onChange={(event) => onChange(event.target.value)}
        />
      </label>
      {error && <div className="invalid-feedback d-block">{error}</div>}
    </div>
  );
}

function SelectField({ label, value, options, onChange, error }) {
  return (
    <div className="col-12 col-lg-6">
      <label className="form-label">
        {label} {error !== undefined && '*'}
        <select className={`form-select ${error ? 'is-invalid' : ''}`} value={value} onChange={(event) => onChange(event.target.value)}>
          <option value="">Selecione</option>
          {options.map((option) => (
            <option key={option} value={option}>
              {option === 'sim' ? 'Sim' : option === 'nao' ? 'Nao' : option}
            </option>
          ))}
        </select>
      </label>
      {error && <div className="invalid-feedback d-block">{error}</div>}
    </div>
  );
}

function SpaceSelectField({ label, value, spaces, onChange, error }) {
  return (
    <div className="col-12 col-lg-6">
      <label className="form-label">
        {label} {error !== undefined && '*'}
        <select className={`form-select ${error ? 'is-invalid' : ''}`} value={value} onChange={(event) => onChange(event.target.value)}>
          <option value="">Selecione</option>
          {spaces.map((space) => (
            <option key={space.id} value={space.id}>
              {space.nome} - {space.capacidade_minima} a {space.capacidade_maxima} pessoas
            </option>
          ))}
        </select>
      </label>
      {spaces.length === 0 && <p className="field-help">Nenhum espaco disponivel foi retornado pela API.</p>}
      {error && <div className="invalid-feedback d-block">{error}</div>}
    </div>
  );
}

function SpaceSuggestionText({ selectedSpaceId, suggestedSpace, total }) {
  if (!suggestedSpace) return 'Cadastre ao menos um espaco para que a solicitacao possa ser enviada para analise.';

  if (!selectedSpaceId) {
    return `Sugestao automatica: ${suggestedSpace.nome}. Selecione o espaco pretendido para continuar.`;
  }

  const minimum = Number(suggestedSpace.capacidade_minima);
  const maximum = Number(suggestedSpace.capacidade_maxima);
  const compatible = total >= minimum && total <= maximum;

  if (compatible) {
    return `Espaco pretendido compativel para analise: ${suggestedSpace.nome}.`;
  }

  return `Espaco pretendido fora da faixa informada: ${suggestedSpace.nome}. A administracao podera remanejar por capacidade.`;
}

function findClosestSpaceByCapacity(spaces, total) {
  return [...spaces].sort((a, b) => {
    const aMax = Number(a.capacidade_maxima);
    const bMax = Number(b.capacidade_maxima);
    const aDiff = Math.abs(aMax - total);
    const bDiff = Math.abs(bMax - total);

    if (aDiff !== bDiff) return aDiff - bDiff;
    return bMax - aMax;
  })[0] ?? null;
}

function isAuditorium(space) {
  return space.nome?.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().includes('auditorio');
}
