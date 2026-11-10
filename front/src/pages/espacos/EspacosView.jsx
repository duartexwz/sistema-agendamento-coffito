import { useMemo, useState } from 'react';
import './EspacosView.css';
import { EmptyState } from '../../components/EmptyState.jsx';
import { getFriendlyErrorMessage } from '../../utils/errors.js';

const emptySpace = {
  nome: '',
  descricao: '',
  localizacao: 'Sede COFFITO',
  capacidade_minima: 16,
  capacidade_maxima: 109,
  disponivel: true,
};

const locationSuggestions = ['Sede COFFITO', 'CREFITO Sao Paulo', 'CREFITO Rio de Janeiro', 'CREFITO Minas Gerais'];

export function EspacosView({ espacos, canManage = false, onSave }) {
  const [form, setForm] = useState(emptySpace);
  const [showModal, setShowModal] = useState(false);
  const [createdSpace, setCreatedSpace] = useState(null);
  const [feedback, setFeedback] = useState(null);

  const groupedSpaces = useMemo(() => {
    return espacos.reduce((groups, espaco) => {
      const key = espaco.localizacao?.trim() || 'Sem localizacao informada';
      groups[key] = [...(groups[key] ?? []), espaco];
      return groups;
    }, {});
  }, [espacos]);

  function openCreateModal() {
    setForm(emptySpace);
    setFeedback(null);
    setShowModal(true);
  }

  function openEditModal(espaco) {
    setForm(espaco);
    setFeedback(null);
    setShowModal(true);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const minCapacity = Number(form.capacidade_minima);
    const maxCapacity = Number(form.capacidade_maxima);

    if (!form.nome.trim() || !form.descricao.trim() || !form.localizacao.trim()) {
      setFeedback({ type: 'danger', message: 'Informe nome, descricao e localizacao do espaco.' });
      return;
    }

    if (!Number.isInteger(minCapacity) || !Number.isInteger(maxCapacity) || minCapacity < 1 || maxCapacity < 1) {
      setFeedback({ type: 'danger', message: 'Informe capacidades validas para o espaco.' });
      return;
    }

    if (maxCapacity < minCapacity) {
      setFeedback({ type: 'danger', message: 'A capacidade maxima nao pode ser menor que a minima.' });
      return;
    }

    const isCreating = !form.id;
    const payload = {
      ...form,
      capacidade_minima: minCapacity,
      capacidade_maxima: maxCapacity,
    };
    try {
      const savedSpace = await onSave(payload);

      setShowModal(false);
      setForm(emptySpace);
      if (isCreating) setCreatedSpace(savedSpace ?? payload);
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
          <p className="eyebrow">Cadastro de ambientes</p>
          <h2>Espaços por unidade</h2>
          <p>Organize os lugares disponiveis por sede, regional ou unidade institucional.</p>
        </div>
        {canManage && (
          <button className="btn btn-primary" type="button" onClick={openCreateModal}>
            <i className="bi bi-plus-lg me-2" aria-hidden="true" />
            Novo espaço
          </button>
        )}
      </div>

      {espacos.length === 0 ? (
        <div className="panel">
          <EmptyState
            title="Nenhum espaco cadastrado"
            description={canManage ? 'Cadastre o primeiro ambiente institucional.' : 'Nenhum ambiente disponivel para consulta.'}
          />
        </div>
      ) : (
        <div className="space-module-stack">
          {Object.entries(groupedSpaces).map(([localizacao, spaces]) => (
            <section className="panel space-module" key={localizacao}>
              <div className="panel-header">
                <div>
                  <p className="eyebrow">Modulo de espacos</p>
                  <h3>{formatModuleTitle(localizacao)}</h3>
                </div>
                <span className="space-count">{spaces.length} espaco(s)</span>
              </div>

              <div className="space-card-grid">
                {spaces.map((espaco) => (
                  <article key={espaco.id} className="space-card">
                    <div className="space-card-header">
                      <h3>{espaco.nome}</h3>
                    </div>
                    <p>{espaco.descricao}</p>
                    <dl>
                      <div>
                        <dt>Capacidade</dt>
                        <dd>
                          {espaco.capacidade_minima} a {espaco.capacidade_maxima} pessoas
                        </dd>
                      </div>
                    </dl>
                    {canManage && (
                      <button type="button" className="btn btn-outline-primary btn-sm" onClick={() => openEditModal(espaco)}>
                        Editar
                      </button>
                    )}
                  </article>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}

      {canManage && showModal && (
        <div className="event-modal-backdrop" role="presentation" onMouseDown={() => setShowModal(false)}>
          <section className="event-modal user-modal" role="dialog" aria-modal="true" onMouseDown={(event) => event.stopPropagation()}>
            <header className="event-modal-header">
              <div>
                <h3>{form.id ? 'Editar espaço' : 'Novo espaço'}</h3>
                <p>Cadastre ambientes como Auditorio COFFITO, Sala Multiuso 1, Sala Multiuso 2 ou unidades regionais.</p>
              </div>
              <button className="btn btn-light btn-sm" type="button" onClick={() => setShowModal(false)} aria-label="Fechar">
                <i className="bi bi-x-lg" aria-hidden="true" />
              </button>
            </header>

            <form onSubmit={handleSubmit}>
              <div className="user-form-grid space-form-grid">
                {feedback && <div className={`alert alert-${feedback.type} grid-column-full`}>{feedback.message}</div>}

                <label className="form-label">
                  Nome do espaço *
                  <input
                    className="form-control"
                    value={form.nome}
                    maxLength={150}
                    placeholder="Ex: Auditorio COFFITO"
                    onChange={(event) => setForm((current) => ({ ...current, nome: event.target.value }))}
                  />
                </label>

                <label className="form-label">
                  Unidade / localizacao *
                  <input
                    className="form-control"
                    list="spaceLocationOptions"
                    value={form.localizacao}
                    maxLength={255}
                    placeholder="Ex: Sede COFFITO"
                    onChange={(event) => setForm((current) => ({ ...current, localizacao: event.target.value }))}
                  />
                  <datalist id="spaceLocationOptions">
                    {locationSuggestions.map((location) => (
                      <option value={location} key={location} />
                    ))}
                  </datalist>
                </label>

                <label className="form-label grid-column-full">
                  Descricao *
                  <textarea
                    className="form-control"
                    rows="3"
                    value={form.descricao}
                    placeholder="Descreva o uso do espaco e observacoes importantes."
                    onChange={(event) => setForm((current) => ({ ...current, descricao: event.target.value }))}
                  />
                </label>

                <label className="form-label">
                  Capacidade minima *
                  <input
                    type="number"
                    min="1"
                    className="form-control"
                    value={form.capacidade_minima}
                    onChange={(event) => setForm((current) => ({ ...current, capacidade_minima: event.target.value }))}
                  />
                </label>

                <label className="form-label">
                  Capacidade maxima *
                  <input
                    type="number"
                    min="1"
                    className="form-control"
                    value={form.capacidade_maxima}
                    onChange={(event) => setForm((current) => ({ ...current, capacidade_maxima: event.target.value }))}
                  />
                </label>

                <label className="form-check user-active-check grid-column-full">
                  <input
                    className="form-check-input"
                    type="checkbox"
                    checked={form.disponivel}
                    onChange={(event) => setForm((current) => ({ ...current, disponivel: event.target.checked }))}
                  />
                  <span className="form-check-label">Disponivel para novas solicitacoes</span>
                </label>
              </div>

              <footer className="user-modal-actions">
                <button className="btn btn-outline-secondary" type="button" onClick={() => setShowModal(false)}>
                  Cancelar
                </button>
                <button className="btn btn-primary" type="submit">
                  Salvar espaço
                </button>
              </footer>
            </form>
          </section>
        </div>
      )}
      {createdSpace && (
        <CreatedSpaceConfirmationModal
          espaco={createdSpace}
          onClose={() => setCreatedSpace(null)}
        />
      )}
    </section>
  );
}

function formatModuleTitle(localizacao) {
  return `Espaços ${localizacao}`;
}

function CreatedSpaceConfirmationModal({ espaco, onClose }) {
  return (
    <div className="event-modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section className="event-modal user-modal" role="dialog" aria-modal="true" onMouseDown={(event) => event.stopPropagation()}>
        <header className="event-modal-header">
          <div>
            <h3>Espaço criado</h3>
            <p>O ambiente foi cadastrado com sucesso e já pode ser usado nas solicitações.</p>
          </div>
          <button className="btn btn-light btn-sm" type="button" onClick={onClose} aria-label="Fechar">
            <i className="bi bi-x-lg" aria-hidden="true" />
          </button>
        </header>

        <div className="user-created-summary">
          <div>
            <strong>{espaco.nome}</strong>
            <span>
              {espaco.localizacao} · {espaco.capacidade_minima} a {espaco.capacidade_maxima} pessoas
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
