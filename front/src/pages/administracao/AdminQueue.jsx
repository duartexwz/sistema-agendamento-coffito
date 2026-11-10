import { useMemo, useState } from 'react';
import './AdminQueue.css';
import {
  CARGOS,
  NIVEIS_ACESSO,
  SETORES_SOLICITANTES,
  TIPOS_USUARIOS,
} from '../../utils/constants/domain.js';
import { EmptyState } from '../../components/EmptyState.jsx';
import { getFriendlyErrorMessage } from '../../utils/errors.js';
import { AlertTriangle, Edit, Trash2 } from 'lucide-react';

const PAGE_SIZE = 6;

const initialUserForm = {
  nome: '',
  email: '',
  cpf: '',
  telefone: '',
  matricula: '',
  tipo_usuario_id: '',
  nivel_acesso_id: '',
  setor_solicitante_id: '',
  cargo_id: '',
  password: '',
  passwordConfirmation: '',
  ativo: true,
};

export function AdminQueue({
  usuarios = [],
  userCatalogs,
  canManageUsers = false,
  onCreateUsuario,
  onUpdateUsuario,
  onDeleteUsuario,
}) {
  const [filters, setFilters] = useState({ search: '', status: 'todos', setor: 'todos' });
  const [currentPage, setCurrentPage] = useState(1);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [pendingDeleteUser, setPendingDeleteUser] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [actionConfirmation, setActionConfirmation] = useState(null);
  const [actionError, setActionError] = useState('');
  const catalogs = useMemo(
    () => ({
      tiposUsuarios: pickCatalog(userCatalogs?.tiposUsuarios, TIPOS_USUARIOS),
      niveisAcesso: pickCatalog(userCatalogs?.niveisAcesso, NIVEIS_ACESSO),
      setoresSolicitantes: pickCatalog(userCatalogs?.setoresSolicitantes, SETORES_SOLICITANTES),
      cargos: pickCatalog(userCatalogs?.cargos, CARGOS),
    }),
    [userCatalogs],
  );

  const filteredUsers = useMemo(() => {
    const search = filters.search.trim().toLowerCase();

    return usuarios
      .filter((usuario) => {
        if (filters.status === 'ativo') return usuario.ativo;
        if (filters.status === 'inativo') return !usuario.ativo;
        return true;
      })
      .filter((usuario) => filters.setor === 'todos' || usuario.setor_solicitante_id === Number(filters.setor))
      .filter((usuario) => {
        if (!search) return true;
        return [usuario.nome, usuario.email, usuario.matricula, usuario.cpf]
          .filter(Boolean)
          .some((value) => value.toLowerCase().includes(search));
      })
      .sort((a, b) => a.nome.localeCompare(b.nome));
  }, [filters, usuarios]);

  const totalPages = Math.max(1, Math.ceil(filteredUsers.length / PAGE_SIZE));
  const safePage = Math.min(currentPage, totalPages);
  const paginatedUsers = filteredUsers.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);

  function updateFilter(field, value) {
    setFilters((current) => ({ ...current, [field]: value }));
    setCurrentPage(1);
  }

  function handleRequestDelete(usuario) {
    setActionError('');
    setPendingDeleteUser(usuario);
  }

  async function handleConfirmDelete() {
    if (!pendingDeleteUser) return;
    setIsDeleting(true);
    setActionError('');
    try {
      await onDeleteUsuario(pendingDeleteUser.id);
      setActionConfirmation({
        title: 'Usuário excluído',
        description: 'O cadastro interno foi removido com sucesso.',
        usuario: pendingDeleteUser,
      });
      setPendingDeleteUser(null);
    } catch (deleteError) {
      setActionError(getFriendlyErrorMessage(deleteError, 'cadastro'));
    } finally {
      setIsDeleting(false);
    }
  }

  function handleCancelDelete() {
    if (isDeleting) return;
    setPendingDeleteUser(null);
  }

  return (
    <section className="view-stack">
      <div className="section-title admin-users-title">
        <div>
          <p className="eyebrow">Administração do sistema</p>
          <h2>Usuários cadastrados</h2>
          <p>{filteredUsers.length} usuário(s) encontrado(s)</p>
        </div>
        {canManageUsers && (
          <button className="btn btn-primary" type="button" onClick={() => setShowCreateModal(true)}>
            <i className="bi bi-plus-lg me-2" aria-hidden="true" />
            Criar novo usuário
          </button>
        )}
      </div>

      {actionError && (
        <div className="alert alert-danger user-form-alert" role="alert">
          {actionError}
        </div>
      )}

      <div className="panel admin-users-filter-panel">
        <div className="admin-users-filters">
          <label className="form-label">
            Busca
            <input
              className="form-control"
              type="search"
              placeholder="Pesquisar por nome, e-mail, matrícula ou CPF"
              value={filters.search}
              onChange={(event) => updateFilter('search', event.target.value)}
            />
          </label>
          <label className="form-label">
            Status
            <select
              className="form-select"
              value={filters.status}
              onChange={(event) => updateFilter('status', event.target.value)}
            >
              <option value="todos">Todos</option>
              <option value="ativo">Ativos</option>
              <option value="inativo">Inativos</option>
            </select>
          </label>
          <label className="form-label">
            Setor
            <select
              className="form-select"
              value={filters.setor}
              onChange={(event) => updateFilter('setor', event.target.value)}
            >
              <option value="todos">Todos</option>
              {catalogs.setoresSolicitantes.map((setor) => (
                <option key={setor.id} value={setor.id}>
                  {setor.nome}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <div className="panel admin-users-panel">
        {paginatedUsers.length === 0 ? (
          <EmptyState
            icon="bi-people"
            title="Nenhum usuário encontrado"
            description={canManageUsers ? 'Altere os filtros ou cadastre um novo usuário interno.' : 'Altere os filtros para consultar outros usuários.'}
          />
        ) : (
          <>
            <div className="table-responsive">
              <table className="table align-middle admin-users-table">
                <thead>
                  <tr>
                    <th>Nome</th>
                    <th>Setor</th>
                    <th>Cargo</th>
                    <th>Perfil</th>
                    <th>Matrícula</th>
                    <th>Status</th>
                    {canManageUsers && <th>Ações</th>}
                  </tr>
                </thead>
                <tbody>
                  {paginatedUsers.map((usuario) => (
                    <tr key={usuario.id}>
                      <td>
                        <div className="user-cell">

                          <div>
                            <strong>{usuario.nome}</strong>
                            <span>{usuario.email}</span>
                          </div>
                        </div>
                      </td>
                      <td>{catalogName(catalogs.setoresSolicitantes, usuario.setor_solicitante_id)}</td>
                      <td>{catalogName(catalogs.cargos, usuario.cargo_id)}</td>
                      <td>{catalogName(catalogs.tiposUsuarios, usuario.tipo_usuario_id)}</td>
                      <td>{usuario.matricula}</td>
                      <td>
                        <span className={`badge ${usuario.ativo ? 'text-bg-success' : 'text-bg-secondary'}`}>
                          {usuario.ativo ? 'Ativo' : 'Inativo'}
                        </span>
                      </td>
                      {canManageUsers && (
                        <td>
                          <div className="d-flex justify-content-start gap-2">
                            <button
                              className="btn btn-outline-warning btn-sm"
                              type="button"
                              title="Editar colaborador"
                              onClick={() => {
                                setActionError('');
                                setEditingUser(usuario);
                              }}
                            >
                              <Edit size={14} />
                            </button>
                            <button
                              className="btn btn-outline-danger btn-sm"
                              type="button"
                              title="Excluir colaborador"
                              onClick={() => handleRequestDelete(usuario)}
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="pagination-bar">
              <span>
                Página {safePage} de {totalPages}
              </span>
              <div className="btn-group">
                <button
                  className="btn btn-outline-primary btn-sm"
                  type="button"
                  disabled={safePage === 1}
                  onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
                >
                  Anterior
                </button>
                <button
                  className="btn btn-outline-primary btn-sm"
                  type="button"
                  disabled={safePage === totalPages}
                  onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}
                >
                  Próxima
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {canManageUsers && showCreateModal && (
        <UserFormModal
          mode="create"
          catalogs={catalogs}
          existingUsers={usuarios}
          onClose={() => setShowCreateModal(false)}
          onSubmit={async (payload) => {
            const usuario = await onCreateUsuario(payload);
            setShowCreateModal(false);
            setActionConfirmation({
              title: 'Usuário criado',
              description: 'O cadastro interno foi registrado com sucesso.',
              usuario: usuario ?? payload,
            });
          }}
        />
      )}
      {canManageUsers && editingUser && (
        <UserFormModal
          mode="edit"
          usuario={editingUser}
          catalogs={catalogs}
          existingUsers={usuarios}
          onClose={() => setEditingUser(null)}
          onSubmit={async (payload) => {
            const usuario = await onUpdateUsuario(editingUser.id, payload);
            setEditingUser(null);
            setActionConfirmation({
              title: 'Usuário atualizado',
              description: 'As alterações foram salvas com sucesso.',
              usuario: usuario ?? payload,
            });
          }}
        />
      )}
      {pendingDeleteUser && (
        <UserDeleteConfirmationModal
          usuario={pendingDeleteUser}
          isDeleting={isDeleting}
          onClose={handleCancelDelete}
          onConfirm={handleConfirmDelete}
        />
      )}
      {actionConfirmation && (
        <UserActionConfirmationModal
          title={actionConfirmation.title}
          description={actionConfirmation.description}
          usuario={actionConfirmation.usuario}
          onClose={() => setActionConfirmation(null)}
        />
      )}
    </section>
  );
}

function UserDeleteConfirmationModal({ usuario, isDeleting, onClose, onConfirm }) {
  return (
    <div className="event-modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        className="event-modal user-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="deleteUserTitle"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="event-modal-header">
          <div>
            <h3 id="deleteUserTitle">Excluir usuário</h3>
            <p>Essa ação não poderá ser desfeita.</p>
          </div>
          <button className="btn btn-light btn-sm" type="button" onClick={onClose} aria-label="Fechar" disabled={isDeleting}>
            <i className="bi bi-x-lg" aria-hidden="true" />
          </button>
        </header>

        <div
          style={{
            margin: '18px 22px 0',
            padding: '16px',
            border: '1px solid #fecaca',
            borderLeft: '4px solid #dc3545',
            borderRadius: '8px',
            background: '#fef2f2',
            display: 'flex',
            gap: '12px',
            alignItems: 'flex-start',
          }}
        >
          <span
            style={{
              display: 'inline-grid',
              placeItems: 'center',
              width: 36,
              height: 36,
              borderRadius: 999,
              background: '#fff',
              border: '1px solid #fecaca',
              color: '#dc3545',
              flexShrink: 0,
            }}
          >
            <AlertTriangle size={18} />
          </span>
          <div>
            <strong style={{ display: 'block', color: 'var(--ink)' }}>Deseja excluir &quot;{usuario.nome}&quot;?</strong>
            <span style={{ display: 'block', marginTop: 4, color: 'var(--muted)', fontSize: '0.9rem', lineHeight: 1.4 }}>
              O cadastro interno será removido permanentemente. O usuário perderá o acesso ao sistema.
            </span>
          </div>
        </div>

        <div className="user-created-summary" style={{ marginTop: 16 }}>
          <div>
            <strong>{usuario.nome}</strong>
            <span>{usuario.email}</span>
            {usuario.matricula && <span style={{ fontSize: '0.82rem', color: 'var(--muted)' }}>Matrícula: {usuario.matricula}</span>}
          </div>
        </div>

        <footer className="user-modal-actions">
          <button className="btn btn-outline-secondary" type="button" onClick={onClose} disabled={isDeleting}>
            Cancelar
          </button>
          <button className="btn btn-danger" type="button" onClick={onConfirm} disabled={isDeleting}>
            {isDeleting ? 'Excluindo...' : 'Excluir usuário'}
          </button>
        </footer>
      </section>
    </div>
  );
}

function UserFormModal({ mode = 'create', usuario, catalogs, existingUsers = [], onClose, onSubmit }) {
  const isEditing = mode === 'edit';
  const [form, setForm] = useState(() => getInitialUserForm(usuario));
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
    setFormError('');
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (saving) return;
    const validationErrors = validateUserForm(form, existingUsers, {
      currentUserId: usuario?.id,
      requirePassword: !isEditing,
    });

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      setFormError('Revise os campos destacados antes de salvar o usuário.');
      return;
    }

    setSaving(true);
    try {
      const { passwordConfirmation, ...payload } = form;
      if (isEditing && !payload.password) delete payload.password;
      await onSubmit(payload);
    } catch (submitError) {
      const conflictErrors = getUserConflictErrors(submitError);
      if (Object.keys(conflictErrors).length > 0) {
        setErrors((current) => ({ ...current, ...conflictErrors }));
      }
      setFormError(getFriendlyErrorMessage(submitError, 'cadastro'));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="event-modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section className="event-modal user-modal" role="dialog" aria-modal="true" onMouseDown={(event) => event.stopPropagation()}>
        <header className="event-modal-header">
          <div>
            <h3>{isEditing ? 'Editar usuário' : 'Criar novo usuário'}</h3>
            <p>
              {isEditing
                ? 'Atualize os dados do cadastro interno.'
                : 'Cadastro interno para acesso ao sistema de reservas.'}
            </p>
          </div>
          <button className="btn btn-light btn-sm" type="button" onClick={onClose} aria-label="Fechar">
            <i className="bi bi-x-lg" aria-hidden="true" />
          </button>
        </header>

        <form onSubmit={handleSubmit}>
          {formError && (
            <div className="alert alert-danger user-form-alert" role="alert">
              {formError}
            </div>
          )}

          <div className="user-form-grid">
            <TextInput label="Nome" field="nome" value={form.nome} error={errors.nome} onChange={updateField} />
            <TextInput label="E-mail" field="email" type="email" value={form.email} error={errors.email} onChange={updateField} />
            <TextInput
              label="CPF"
              field="cpf"
              value={form.cpf}
              error={errors.cpf}
              placeholder="000.000.000-00"
              inputMode="numeric"
              maxLength={14}
              formatValue={formatCpf}
              onChange={updateField}
            />
            <TextInput label="Telefone" field="telefone" value={form.telefone} error={errors.telefone} placeholder="(00) 00000-0000" onChange={updateField} />
            <TextInput label="Matrícula" field="matricula" value={form.matricula} error={errors.matricula} onChange={updateField} />
            {!isEditing && (
              <TextInput
                label="Senha inicial"
                field="password"
                type="password"
                autoComplete="new-password"
                value={form.password}
                error={errors.password}
                placeholder="Mínimo 6 caracteres"
                onChange={updateField}
              />
            )}
            <SelectInput
              label="Tipo de usuário"
              field="tipo_usuario_id"
              value={form.tipo_usuario_id}
              error={errors.tipo_usuario_id}
              options={catalogs.tiposUsuarios}
              onChange={updateField}
            />
            <SelectInput
              label="Nível de acesso"
              field="nivel_acesso_id"
              value={form.nivel_acesso_id}
              error={errors.nivel_acesso_id}
              options={catalogs.niveisAcesso}
              onChange={updateField}
            />
            <SelectInput
              label="Setor solicitante"
              field="setor_solicitante_id"
              value={form.setor_solicitante_id}
              error={errors.setor_solicitante_id}
              options={catalogs.setoresSolicitantes}
              onChange={updateField}
            />
            <SelectInput
              label="Cargo"
              field="cargo_id"
              value={form.cargo_id}
              error={errors.cargo_id}
              options={catalogs.cargos}
              onChange={updateField}
            />
            <label className="form-check user-active-check">
              <input
                className="form-check-input"
                type="checkbox"
                checked={form.ativo}
                onChange={(event) => updateField('ativo', event.target.checked)}
              />
              <span className="form-check-label">Usuário ativo</span>
            </label>
            {isEditing && (
              <>
                <TextInput
                  label="Nova senha (opcional)"
                  field="password"
                  type="password"
                  autoComplete="new-password"
                  value={form.password}
                  error={errors.password}
                  placeholder="Em branco mantém a senha atual"
                  required={false}
                  onChange={updateField}
                />
                <TextInput
                  label="Confirmar nova senha"
                  field="passwordConfirmation"
                  type="password"
                  autoComplete="new-password"
                  value={form.passwordConfirmation}
                  error={errors.passwordConfirmation}
                  required={Boolean(form.password)}
                  onChange={updateField}
                />
              </>
            )}
          </div>

          <footer className="user-modal-actions">
            <button className="btn btn-outline-secondary" type="button" onClick={onClose}>
              Cancelar
            </button>
            <button className="btn btn-primary" type="submit" disabled={saving}>
              {saving ? 'Salvando...' : isEditing ? 'Salvar alterações' : 'Salvar usuário'}
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}

function UserActionConfirmationModal({ title, description, usuario, onClose }) {
  return (
    <div className="event-modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section className="event-modal user-modal" role="dialog" aria-modal="true" onMouseDown={(event) => event.stopPropagation()}>
        <header className="event-modal-header">
          <div>
            <h3>{title}</h3>
            <p>{description}</p>
          </div>
          <button className="btn btn-light btn-sm" type="button" onClick={onClose} aria-label="Fechar">
            <i className="bi bi-x-lg" aria-hidden="true" />
          </button>
        </header>

        <div className="user-created-summary">
          <div>
            <strong>{usuario.nome}</strong>
            <span>{usuario.email}</span>
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

function TextInput({
  label,
  field,
  value,
  error,
  onChange,
  type = 'text',
  placeholder = '',
  inputMode,
  maxLength,
  autoComplete,
  formatValue = (inputValue) => inputValue,
  required = true,
}) {
  return (
    <label className="form-label">
      {label} {required ? '*' : ''}
      <input
        className={`form-control ${error ? 'is-invalid' : ''}`}
        type={type}
        inputMode={inputMode}
        maxLength={maxLength}
        autoComplete={autoComplete}
        aria-invalid={Boolean(error)}
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(field, formatValue(event.target.value))}
      />
      {error && <span className="invalid-feedback d-block">{error}</span>}
    </label>
  );
}

function SelectInput({ label, field, value, error, options = [], onChange }) {
  return (
    <label className="form-label">
      {label} *
      <select
        className={`form-select ${error ? 'is-invalid' : ''}`}
        value={value}
        onChange={(event) => onChange(field, event.target.value)}
      >
        <option value="">Selecione</option>
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.nome}
          </option>
        ))}
      </select>
      {error && <span className="invalid-feedback d-block">{error}</span>}
    </label>
  );
}

function getInitialUserForm(usuario) {
  if (!usuario) return { ...initialUserForm };

  return {
    nome: usuario.nome ?? '',
    email: usuario.email ?? '',
    cpf: formatCpf(usuario.cpf ?? ''),
    telefone: usuario.telefone ?? '',
    matricula: usuario.matricula ?? '',
    tipo_usuario_id: stringifyId(usuario.tipo_usuario_id),
    nivel_acesso_id: stringifyId(usuario.nivel_acesso_id ?? usuario.niveis_acesso_id),
    setor_solicitante_id: stringifyId(usuario.setor_solicitante_id),
    cargo_id: stringifyId(usuario.cargo_id),
    password: '',
    passwordConfirmation: '',
    ativo: usuario.ativo ?? true,
  };
}

function stringifyId(value) {
  return value ? String(value) : '';
}

function validateUserForm(form, existingUsers = [], options = {}) {
  const errors = {};
  const requiredFields = [
    'nome',
    'email',
    'cpf',
    'telefone',
    'matricula',
    'tipo_usuario_id',
    'nivel_acesso_id',
    'setor_solicitante_id',
    'cargo_id',
  ];

  if (options.requirePassword) {
    requiredFields.push('password');
  }

  requiredFields.forEach((field) => {
    if (!String(form[field] ?? '').trim()) {
      errors[field] = 'Campo obrigatório.';
    }
  });

  if (form.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    errors.email = 'Informe um e-mail válido.';
  }

  if (form.cpf && onlyDigits(form.cpf).length !== 11) {
    errors.cpf = 'Informe um CPF com 11 dígitos.';
  }

  if (form.password && (form.password.length < 6 || !form.password.trim())) {
    errors.password = 'A senha deve ter no mínimo 6 caracteres.';
  }

  if (!options.requirePassword && form.password !== form.passwordConfirmation) {
    errors.passwordConfirmation = 'As senhas não coincidem.';
  }

  const duplicateErrors = findDuplicateUserFields(form, existingUsers, options);
  Object.assign(errors, duplicateErrors);

  return errors;
}

function findDuplicateUserFields(form, existingUsers = [], options = {}) {
  const errors = {};
  const normalizedForm = {
    nome: normalizeComparable(form.nome),
    email: normalizeComparable(form.email),
    cpf: onlyDigits(form.cpf),
    matricula: normalizeComparable(form.matricula),
  };

  existingUsers.forEach((usuario) => {
    if (Number(usuario.id) === Number(options.currentUserId)) return;

    if (normalizedForm.nome && normalizeComparable(usuario.nome) === normalizedForm.nome) {
      errors.nome = 'Já existe um usuário com este nome.';
    }

    if (normalizedForm.email && normalizeComparable(usuario.email) === normalizedForm.email) {
      errors.email = 'Já existe um usuário com este e-mail.';
    }

    if (normalizedForm.cpf && onlyDigits(usuario.cpf) === normalizedForm.cpf) {
      errors.cpf = 'Já existe um usuário com este CPF.';
    }

    if (normalizedForm.matricula && normalizeComparable(usuario.matricula) === normalizedForm.matricula) {
      errors.matricula = 'Já existe um usuário com esta matrícula.';
    }
  });

  return errors;
}

function getUserConflictErrors(error) {
  if (error.status !== 409) return {};

  const message = normalizeComparable(`${error.message ?? ''} ${JSON.stringify(error.data ?? '')}`);

  if (message.includes('matricula')) {
    return { matricula: 'Já existe um usuário com esta matrícula.' };
  }

  if (message.includes('email') || message.includes('e-mail')) {
    return { email: 'Já existe um usuário com este e-mail.' };
  }

  if (message.includes('cpf')) {
    return { cpf: 'Já existe um usuário com este CPF.' };
  }

  if (message.includes('nome')) {
    return { nome: 'Já existe um usuário com este nome.' };
  }

  return {};
}

function catalogName(catalog, id) {
  return catalog.find((item) => item.id === Number(id))?.nome ?? '-';
}

function pickCatalog(apiCatalog, fallbackCatalog) {
  return Array.isArray(apiCatalog) && apiCatalog.length > 0 ? apiCatalog : fallbackCatalog;
}

function onlyDigits(value = '') {
  return String(value).replace(/\D/g, '');
}

function normalizeComparable(value = '') {
  return String(value)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

function formatCpf(value = '') {
  return onlyDigits(value)
    .slice(0, 11)
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
}
