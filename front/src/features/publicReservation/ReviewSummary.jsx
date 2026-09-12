import { getFaixa } from '../../shared/utils/reservas.js';
import { formatDate } from '../../shared/utils/date.js';

export function ReviewSummary({ form, suggestedSpace }) {
  const faixa = getFaixa(form.evento.faixa_calculada);
  const total = Number(form.evento.publico_estimado) || 0;
  const isCompatible =
    suggestedSpace &&
    total >= Number(suggestedSpace.capacidade_minima) &&
    total <= Number(suggestedSpace.capacidade_maxima);

  return (
    <div className="review-grid">
      <ReviewBlock title="Profissional">
        <p>{form.profissional.nome || '-'}</p>
        <p>{form.profissional.profissao || '-'}</p>
        <p>{form.profissional.email || '-'}</p>
      </ReviewBlock>

      <ReviewBlock title="Evento">
        <p>{form.evento.nome || '-'}</p>
        <p>{form.evento.tipo || '-'}</p>
        <p>
          {form.evento.publico_estimado || 0} participantes - {faixa.label}
        </p>
      </ReviewBlock>

      <ReviewBlock title="Espaço pretendido">
        <p>{suggestedSpace?.nome ?? 'A definir pela administracao'}</p>
        <p>{suggestedSpace ? `${suggestedSpace.capacidade_minima} a ${suggestedSpace.capacidade_maxima} pessoas` : '-'}</p>
        {suggestedSpace && !isCompatible && <p>Cadastro usado para triagem. A administracao podera remanejar.</p>}
      </ReviewBlock>

      <ReviewBlock title="Periodo">
        {form.datas.length > 0 ? (
          <>
            <p>{form.datas.length} data(s) especifica(s)</p>
            <p>{form.datas.map(formatDate).join(', ')}</p>
            <p>
              {form.periodo.horario_inicio || '--:--'} as {form.periodo.horario_fim || '--:--'}
            </p>
          </>
        ) : (
          <p>
            {form.periodo.data_inicio || '-'} ate {form.periodo.data_fim || '-'} -{' '}
            {form.periodo.horario_inicio || '--:--'} as {form.periodo.horario_fim || '--:--'}
          </p>
        )}
      </ReviewBlock>

      <ReviewBlock title="Recursos">
        <p>{form.recursos.itens.length ? form.recursos.itens.join(', ') : 'Nenhum recurso selecionado'}</p>
      </ReviewBlock>

      <ReviewBlock title="Anexos">
        <p>{form.anexos.length ? `${form.anexos.length} arquivo(s) selecionado(s)` : 'Nenhum anexo'}</p>
      </ReviewBlock>
    </div>
  );
}

function ReviewBlock({ title, children }) {
  return (
    <article className="review-block">
      <h4>{title}</h4>
      {children}
    </article>
  );
}
