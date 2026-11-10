import { useState } from 'react';
import './LoginPage.css';
import coffitoLogo from '../../assets/logo.png';
import { getFriendlyErrorMessage } from '../../utils/errors.js';

export function LoginPage({ onLogin, onOpenPublic, onOpenPublicCalendar }) {
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
    setError('');
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (!form.email.trim() || !form.password.trim()) {
      setError('Informe e-mail e senha para acessar.');
      return;
    }

    setLoading(true);
    try {
      await onLogin(form.email, form.password);
    } catch (loginError) {
      setError(getFriendlyErrorMessage(loginError, 'login'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-shell">
      <section className="login-card" aria-labelledby="loginTitle">
        <div className="login-brand">
          <img src={coffitoLogo} alt="COFFITO" />
          <h1 id="loginTitle">Acesso interno</h1>
        </div>

        <p className="login-description">
          Entre com seu usuario interno para acompanhar reservas, recursos e administracao do sistema.
        </p>

        {error && <div className="alert alert-danger">{error}</div>}

        <form onSubmit={handleSubmit} noValidate>
          <label className="form-label" htmlFor="loginEmail">
            E-mail
            <input
              id="loginEmail"
              className="form-control"
              type="email"
              autoComplete="username"
              value={form.email}
              onChange={(event) => updateField('email', event.target.value)}
              placeholder="admin@coffito.gov.br"
            />
          </label>

          <label className="form-label" htmlFor="loginPassword">
            Senha
            <input
              id="loginPassword"
              className="form-control"
              type="password"
              autoComplete="current-password"
              value={form.password}
              onChange={(event) => updateField('password', event.target.value)}
              placeholder="Informe sua senha"
            />
          </label>

          <button className="btn btn-primary login-submit" type="submit" disabled={loading}>
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>

        <div className="login-links" aria-label="Links publicos">
          <button className="btn btn-link" type="button" onClick={onOpenPublic}>
            Solicitar reserva sem login
          </button>
          <button className="btn btn-link" type="button" onClick={onOpenPublicCalendar}>
            Ver calendario publico
          </button>
        </div>
      </section>
    </main>
  );
}
