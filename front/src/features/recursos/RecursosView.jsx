import { useMemo, useState } from 'react';
import './RecursosView.css';
import { STATUS } from '../../shared/constants/domain.js';
import { EmptyState } from '../../shared/components/EmptyState.jsx';
import { formatDateTime } from '../../shared/utils/date.js';
import { getFriendlyErrorMessage } from '../../shared/utils/errors.js';

const initialResourceForm = {
  nome: '',
  quantidade: 1,
  disponivel: true,
};

export function RecursosView({ recursos, reservas, canManage = false, onSave }) {
  const [filters, setFilters] = useState({ search: '', disponibilidade: 'todos' });
  const [form, setForm] = useState(initialResourceForm);
  const [showModal, setShowModal] = useState(false);
  const [createdResource, setCreatedResource] = useState(null);
  const [feedback, setFeedback] = useState(null);

  const recursosFiltrados = useMemo(() => {
    const search = filters.search.trim().toLowerCase();

    return recursos
      .filter((recurso) => {
        if (filters.disponibilidade === 'disponivel') return recurso.disponivel;
        if (filters.disponibilidade === 'indisponivel') return !recurso.disponivel;
        return true;
      })
      .filter((recurso) => !search || recurso.nome.toLowerCase().includes(search))
      .sort((a, b) => a.nome.localeCompare(b.nome));
  }, [filters, recursos]);

  const reservasAprovadas = useMemo(() => {
    const today = new Date().toISOString().slice(0, 10);

    return reservas
      .filter((reserva) => reserva.status_id === STATUS.APROVADA.id)
      .filter((reserva) => reserva.data_fim >= today)
      .sort((a, b) => `${a.data_inicio}T${a.horario_inicio}`.localeCompare(`${b.data_inicio}T${b.horario_inicio}`));
  }, [reservas]);

  const recursosReservados = useMemo(() => {
    return reservasAprovadas.flatMap((reserva) =>
      (reserva.recursos ?? []).map((nomeRecurso) => {
        const recurso = recursos.find((item) => normalize(item.nome) === normalize(nomeRecurso));
        return {
          id: `${reserva.id}-${nomeRecurso}`,
          reserva,
          recurso,
          nome: nomeRecurso,
          quantidade: 1,
        };
      }),
    );
  }, [recursos, reservasAprovadas]);

  const resumoUso = useMemo(() => {
    return recursos.map((recurso) => {
      const reservado = recursosReservados
        .filter((item) => item.recurso?.id === recurso.id || normalize(item.nome) === normalize(recurso.nome))
        .reduce((total, item) => total + item.quantidade, 0);

      return {
        ...recurso,
        reservado,
        saldo: Math.max(Number(recurso.quantidade) - reservado, 0),
      };
    });
  }, [recursos, recursosReservados]);

  function openCreateModal() {
    setForm(initialResourceForm);
    setFeedback(null);
    setShowModal(true);
  }

  function openEditModal(recurso) {
    setForm(recurso);
    setFeedback(null);
    setShowModal(true);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const quantidade = Number(form.quantidade);

    if (!form.nome.trim()) {
      setFeedback({ type: 'danger', message: 'Informe o nome do recurso.' });
      return;
    }

    if (!Number.isInteger(quantidade) || quantidade < 0) {
      setFeedback({ type: 'danger', message: 'Informe uma quantidade valida.' });
      return;
    }

    const isCreating = !form.id;
    const payload = {
      ...form,
      quantidade,
    };
    try {
      const savedResource = await onSave(payload);
      setShowModal(false);
      setForm(initialResourceForm);
      if (isCreating) setCreatedResource(savedResource ?? payload);
    } catch (error) {
      setFeedback({
        type: 'danger',
        message: getFriendlyErrorMessage(error, 'cadastro'),
      });
    }
  }

  return (
    <section className="view-stack">
      <div className="section-title admin-users-title">
        <div>
          <p className="eyebrow">Recursos e suporte</p>
          <h2>Gestão de recursos</h2>
          <p>Catálogo usado nas solicitações internas e públicas.</p>
        </div>
        {canManage && (
          <button className="btn btn-primary" type="button" onClick={openCreateModal}>
            <i className="bi bi-plus-lg me-2" aria-hidden="true" />
            Cadastrar recurso
          </button>
        )}
      </div>

      <div className="resource-summary-grid">
        <SummaryCard icon="bi-box-seam" label="Recursos cadastrados" value={recursos.length} />
        <SummaryCard icon="bi-check2-circle" label="Disponíveis" value={recursos.filter((recurso) => recurso.disponivel).length} />
        <SummaryCard icon="bi-calendar-check" label="Reservados em eventos" value={recursosReservados.length} />
      </div>

      <div className="panel admin-users-filter-panel">
        <div className="admin-users-filters resource-filters">
          <label className="form-label">
            Busca
            <input
              className="form-control"
              type="search"
              placeholder="Pesquisar recurso"
              value={filters.search}
              onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value }))}
            />
          </label>
          <label className="form-label">
            Disponibilidade
            <select
              className="form-select"
              value={filters.disponibilidade}
              onChange={(event) => setFilters((current) => ({ ...current, disponibilidade: event.target.value }))}
            >
              <option value="todos">Todos</option>
              <option value="disponivel">Disponíveis</option>
              <option value="indisponivel">Indisponíveis</option>
            </select>
          </label>
        </div>
      </div>

      <div className="row g-3 align-items-start">
        <div className="col-12 col-xl-7">
          <div className="panel admin-users-panel">
            <div className="resource-table-header">
              <div>
                <h3>Recursos cadastrados</h3>
                <p>Representa a tabela recursos: nome, quantidade e disponibilidade.</p>
              </div>
            </div>
            {recursosFiltrados.length === 0 ? (
              <EmptyState
                title="Nenhum recurso encontrado"
                description={canManage ? 'Altere os filtros ou cadastre um novo recurso.' : 'Altere os filtros para consultar outros recursos.'}
              />
            ) : (
              <div className="table-responsive">
                <table className="table align-middle admin-users-table">
                  <thead>
                    <tr>
                      <th>Nome</th>
                      <th>Quantidade</th>
                      <th>Reservado</th>
                      <th>Saldo previsto</th>
                      <th>Disponível</th>
                      {canManage && <th>Ações</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {recursosFiltrados.map((recurso) => {
                      const resumo = resumoUso.find((item) => item.id === recurso.id);
                      return (
                        <tr key={recurso.id}>
                          <td>
                            <strong>{recurso.nome}</strong>
                            <span className="table-subtitle">ID {recurso.id}</span>
                          </td>
                          <td>{recurso.quantidade}</td>
                          <td>{resumo?.reservado ?? 0}</td>
                          <td>{resumo?.saldo ?? recurso.quantidade}</td>
                          <td>
                            <span className={`badge ${recurso.disponivel ? 'text-bg-success' : 'text-bg-secondary'}`}>
                              {recurso.disponivel ? 'Sim' : 'Não'}
                            </span>
                          </td>
                          {canManage && (
                            <td>
                              <button className="btn btn-outline-primary btn-sm" type="button" onClick={() => openEditModal(recurso)}>
                                Editar
                              </button>
                            </td>
                          )}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        <div className="col-12 col-xl-5">
          <div className="panel admin-users-panel">
            <div className="resource-table-header">
              <div>
                <h3>Recursos reservados</h3>
                <p>Próximos eventos aprovados que já solicitaram itens do catálogo.</p>
              </div>
            </div>
            {recursosReservados.length === 0 ? (
              <EmptyState title="Nenhum recurso reservado" description="Eventos aprovados com recursos aparecerão aqui." />
            ) : (
              <div className="table-responsive">
                <table className="table align-middle admin-users-table resource-booking-table">
                  <thead>
                    <tr>
                      <th>Recurso</th>
                      <th>Qtd.</th>
                      <th>Evento</th>
                      <th>Data</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recursosReservados.map((item) => (
                      <tr key={item.id}>
                        <td>
                          <strong>{item.nome}</strong>
                          <span className="table-subtitle">{item.recurso ? `ID ${item.recurso.id}` : 'Fora do catálogo'}</span>
                        </td>
                        <td>{item.quantidade}</td>
                        <td>{item.reserva.nome_evento}</td>
                        <td>{formatDateTime(item.reserva.data_inicio, item.reserva.horario_inicio)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>

      {canManage && showModal && (
        <div className="event-modal-backdrop" role="presentation" onMouseDown={() => setShowModal(false)}>
          <section className="event-modal resource-modal" role="dialog" aria-modal="true" onMouseDown={(event) => event.stopPropagation()}>
            <header className="event-modal-header">
              <div>
                <h3>{form.id ? 'Editar recurso' : 'Cadastrar recurso'}</h3>
                <p>Campos alinhados à tabela recursos.</p>
              </div>
              <button className="btn btn-light btn-sm" type="button" onClick={() => setShowModal(false)} aria-label="Fechar">
                <i className="bi bi-x-lg" aria-hidden="true" />
              </button>
            </header>

            <form onSubmit={handleSubmit}>
              <div className="user-form-grid resource-form-grid">
                {feedback && <div className={`alert alert-${feedback.type} grid-column-full`}>{feedback.message}</div>}
                <label className="form-label">
                  Nome *
                  <input
                    className="form-control"
                    value={form.nome}
                    maxLength={150}
                    onChange={(event) => setForm((current) => ({ ...current, nome: event.target.value }))}
                  />
                </label>
                <label className="form-label">
                  Quantidade *
                  <input
                    className="form-control"
                    type="number"
                    min="0"
                    value={form.quantidade}
                    onChange={(event) => setForm((current) => ({ ...current, quantidade: event.target.value }))}
                  />
                </label>
                <label className="form-check user-active-check">
                  <input
                    className="form-check-input"
                    type="checkbox"
                    checked={form.disponivel}
                    onChange={(event) => setForm((current) => ({ ...current, disponivel: event.target.checked }))}
                  />
                  <span className="form-check-label">Disponível para novas solicitações</span>
                </label>
              </div>

              <footer className="user-modal-actions">
                <button className="btn btn-outline-secondary" type="button" onClick={() => setShowModal(false)}>
                  Cancelar
                </button>
                <button className="btn btn-primary" type="submit">
                  Salvar recurso
                </button>
              </footer>
            </form>
          </section>
        </div>
      )}
      {createdResource && (
        <CreatedResourceConfirmationModal
          recurso={createdResource}
          onClose={() => setCreatedResource(null)}
        />
      )}
    </section>
  );
}

function SummaryCard({ icon, label, value }) {
  return (
    <article className="metric-card">
      <i className={`bi ${icon}`} aria-hidden="true" />
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
    </article>
  );
}

function normalize(value) {
  return String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

function CreatedResourceConfirmationModal({ recurso, onClose }) {
  return (
    <div className="event-modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section className="event-modal user-modal" role="dialog" aria-modal="true" onMouseDown={(event) => event.stopPropagation()}>
        <header className="event-modal-header">
          <div>
            <h3>Recurso criado</h3>
            <p>O item foi cadastrado com sucesso e já pode aparecer nas solicitações.</p>
          </div>
          <button className="btn btn-light btn-sm" type="button" onClick={onClose} aria-label="Fechar">
            <i className="bi bi-x-lg" aria-hidden="true" />
          </button>
        </header>

        <div className="user-created-summary">
          <div>
            <strong>{recurso.nome}</strong>
            <span>
              Quantidade: {recurso.quantidade} · {recurso.disponivel ? 'Disponível para solicitação' : 'Indisponível para solicitação'}
            </span>
          </div>
        </div>

        <footer className="user-modal-actions">
          <button className="btn btn-primary" type="button" onClick={onClose}>
            Entendi
          </button>
        </footer>
      </section>
    </div>
  );
}
