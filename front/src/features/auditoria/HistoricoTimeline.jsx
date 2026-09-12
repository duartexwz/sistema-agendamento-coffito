import { useEffect, useState } from 'react';
import { LoadingState } from '../../shared/components/LoadingState.jsx';
import { StatusBadge } from '../../shared/components/StatusBadge.jsx';

export function HistoricoTimeline({ reservaId, getHistorico }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let ignore = false;
    setLoading(true);
    getHistorico(reservaId)
      .then((result) => {
        if (!ignore) setItems(result);
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });

    return () => {
      ignore = true;
    };
  }, [getHistorico, reservaId]);

  if (loading) return <LoadingState label="Carregando historico..." />;

  return (
    <div className="timeline">
      <h4>Historico</h4>
      {items.length === 0 ? (
        <p className="text-muted mb-0">Nenhum historico registrado.</p>
      ) : (
        items.map((item) => (
          <article key={item.id} className="timeline-item">
            <span className="timeline-dot" />
            <div>
              <strong>{item.acao}</strong>
              <small>{new Date(item.criado_em).toLocaleString('pt-BR')}</small>
              <p>{item.observacao}</p>
              {item.status_novo_id && <StatusBadge statusId={item.status_novo_id} />}
            </div>
          </article>
        ))
      )}
    </div>
  );
}
