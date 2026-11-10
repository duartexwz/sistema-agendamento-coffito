import {
  CalendarDays, CheckCircle2, Clock3, FileText, Info, Layers,
  LockKeyhole, MapPin, Monitor, Pencil, Send, ShieldCheck, TriangleAlert, UserRound, UsersRound,
} from 'lucide-react';
import { formatDate } from '../../utils/date.js';
import './ReviewSummary.css';

export function ReviewSummary({
  form, suggestedSpace, confirmed, onConfirm, onEdit, onBack, onSubmit, submitting = false,
}) {
  const total = Number(form.evento.publico_estimado) || 0;
  const capacity = Number(suggestedSpace?.capacidade_maxima);
  const exceedsCapacity = suggestedSpace && Number.isFinite(capacity) && capacity > 0 && total > capacity;
  const dates = [...new Set(form.datas ?? [])].sort();
  const period = dates.length
    ? dates.map(formatDate).join(', ')
    : formatPeriod(form.periodo.data_inicio, form.periodo.data_fim);
  const hours = `${form.periodo.horario_inicio || '--:--'} às ${form.periodo.horario_fim || '--:--'}`;
  const participants = `${total} ${total === 1 ? 'participante' : 'participantes'}`;
  const spaceName = suggestedSpace?.nome ?? 'A definir pela administração';
  const canSubmit = confirmed && !submitting;

  return (
    <div className="reservation-review" aria-busy={submitting}>
      <div className="review-notice" role="note">
        <Info size={24} aria-hidden="true" />
        <p>Após o envio, a solicitação será analisada conforme disponibilidade e prioridade. Você poderá acompanhar o status pelo sistema.</p>
      </div>
      <div className="review-layout">
        <section className="review-details" aria-labelledby="review-details-title">
          <h2 id="review-details-title">Dados da solicitação</h2>
          <ReviewRow title="Profissional" icon={UserRound} onEdit={() => onEdit('profissional')} disabled={submitting}>
            <strong>{form.profissional.nome || '-'}</strong>
            <p>{form.profissional.profissao || '-'}</p>
            <p>{form.profissional.email || '-'}</p>
          </ReviewRow>
          <ReviewRow title="Evento" icon={CalendarDays} onEdit={() => onEdit('evento')} disabled={submitting}>
            <strong>{form.evento.nome || '-'}</strong>
            <p>{form.evento.tipo || '-'}</p>
            <p>{participants}</p>
            {exceedsCapacity && (
              <div className="review-capacity-alert" role="note">
                <TriangleAlert size={23} aria-hidden="true" />
                <div>
                  <p>A quantidade de participantes excede a capacidade do espaço selecionado.</p>
                  <button type="button" className="review-correction-link" disabled={submitting} onClick={() => onEdit('evento')}>
                    Alterar espaço ou participantes
                  </button>
                </div>
              </div>
            )}
          </ReviewRow>
          <ReviewRow title="Data e horário" icon={CalendarDays} onEdit={() => onEdit('datas')} disabled={submitting}>
            {dates.length > 0 && <strong>{dates.length} {dates.length === 1 ? 'data específica' : 'datas específicas'}</strong>}
            <p>{period}</p>
            <p>{hours}</p>
          </ReviewRow>
          <ReviewRow title="Espaço pretendido" icon={MapPin} onEdit={() => onEdit('evento')} disabled={submitting}>
            <strong>{spaceName}</strong>
            {suggestedSpace && <p>{suggestedSpace.capacidade_minima} a {suggestedSpace.capacidade_maxima} pessoas</p>}
            <p className="review-muted">Sujeito à confirmação da administração.</p>
          </ReviewRow>
          <ReviewRow title="Recursos" icon={Monitor} onEdit={() => onEdit('recursos')} disabled={submitting}>
            {form.recursos.itens.length ? (
              <ul className="review-resource-list" aria-label="Recursos selecionados">
                {form.recursos.itens.map((item) => <li key={item}>{item}</li>)}
              </ul>
            ) : <p>Nenhum recurso selecionado.</p>}
          </ReviewRow>
          <ReviewRow title="Anexos" icon={FileText} onEdit={() => onEdit('recursos')} disabled={submitting}>
            {form.anexos.length ? (
              <ul className="review-attachment-list">
                {form.anexos.map((file, index) => <li key={`${file.name}-${index}`}>{file.name}</li>)}
              </ul>
            ) : <p>Nenhum anexo selecionado.</p>}
          </ReviewRow>
        </section>
        <aside className="review-summary" aria-labelledby="review-summary-title">
          <h2 id="review-summary-title">Resumo</h2>
          {exceedsCapacity ? (
            <div className="review-capacity-alert review-status" role="status">
              <TriangleAlert size={28} aria-hidden="true" />
              <div>
                <strong>Confira a capacidade</strong>
                <p>O público excede a capacidade cadastrada. A administração poderá remanejar o espaço.</p>
              </div>
            </div>
          ) : (
            <div className="review-ready" role="status">
              <CheckCircle2 size={22} aria-hidden="true" />
              <p>{confirmed ? 'Dados confirmados para envio.' : 'Confira os dados antes de enviar.'}</p>
            </div>
          )}
          <dl className="review-summary-list">
            <SummaryItem title="Evento" icon={FileText}>{form.evento.nome || '-'}</SummaryItem>
            <SummaryItem title={dates.length ? 'Datas' : 'Período'} icon={CalendarDays}>{period}</SummaryItem>
            <SummaryItem title="Horário" icon={Clock3}>{hours}</SummaryItem>
            <SummaryItem title="Espaço" icon={MapPin}>{spaceName}</SummaryItem>
            <SummaryItem title="Participantes" icon={UsersRound}>
              {participants}
              {exceedsCapacity && (
                <span className="review-capacity-note"><TriangleAlert size={17} aria-hidden="true" />Excede a capacidade do espaço selecionado.</span>
              )}
            </SummaryItem>
            <SummaryItem title="Recursos" icon={Layers}>{form.recursos.itens.join(', ') || 'Nenhum recurso selecionado'}</SummaryItem>
          </dl>
          <div className="review-submit-area">
            <label className="review-confirmation">
              <input type="checkbox" checked={confirmed} disabled={submitting} onChange={(event) => onConfirm(event.target.checked)} />
              <span>Li e confirmei que os dados estão corretos.</span>
            </label>
            <button className="btn review-send" type="button" disabled={!canSubmit} onClick={onSubmit}>
              {submitting ? <span className="spinner-border spinner-border-sm" aria-hidden="true" /> : canSubmit ? <Send size={18} aria-hidden="true" /> : <LockKeyhole size={18} aria-hidden="true" />}
              {submitting ? 'Enviando solicitação...' : 'Enviar solicitação'}
            </button>
            <button className="btn review-back" type="button" disabled={submitting} onClick={onBack}>Voltar e corrigir</button>
          </div>
          <p className="review-privacy"><ShieldCheck size={26} aria-hidden="true" />Seus dados são tratados conforme a LGPD.</p>
        </aside>
      </div>
    </div>
  );
}

function ReviewRow({ title, icon: Icon, onEdit, disabled, children }) {
  return (
    <div className="review-row">
      <span className="review-row-icon"><Icon size={23} aria-hidden="true" /></span>
      <h3>{title}</h3>
      <div className="review-row-content">{children}</div>
      <button className="review-edit" type="button" onClick={onEdit} disabled={disabled} aria-label={`Editar: ${title}`}>
        <Pencil size={18} aria-hidden="true" /><span>Editar</span>
      </button>
    </div>
  );
}

function SummaryItem({ title, icon: Icon, children }) {
  return (
    <div className="review-summary-item">
      <dt><Icon size={20} aria-hidden="true" />{title}</dt>
      <dd>{children}</dd>
    </div>
  );
}

function formatPeriod(start, end) {
  if (!start) return '-';
  const formatter = new Intl.DateTimeFormat('pt-BR', { day: 'numeric', month: 'short', year: 'numeric' });
  const first = new Date(`${start}T12:00:00`);
  const last = new Date(`${end || start}T12:00:00`);
  if (Number.isNaN(first.getTime()) || Number.isNaN(last.getTime())) return '-';
  return start === end || !end ? formatter.format(first) : formatter.formatRange(first, last);
}
