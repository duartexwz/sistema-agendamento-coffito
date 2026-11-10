import coffitoLogo from '../../assets/logo.png';
import './PublicReservation.css';

export function PublicFormShell({ children, showGuidance = true }) {
  return (
    <main className="public-shell">
      <section className="public-container">
        <header className="public-brand">
          <img className="public-brand-logo" src={coffitoLogo} alt="COFFITO" />
          <div className="public-title-band">EVENTO COM UTILIZACAO DE ESPACO INSTITUCIONAL DO COFFITO</div>
        </header>

        {showGuidance && (
          <div className="public-guidance">
            <strong>Prezado profissional, leia com atencao estas observacoes:</strong>
            <ul>
              <li>A confirmacao de envio sera exibida ao final do preenchimento do formulario.</li>
              <li>A solicitacao sera analisada conforme disponibilidade, volume e prioridade das demandas.</li>
              <li>Dias ja ocupados poderao receber alerta visual para apoiar a escolha da data.</li>
              <li>Solicitacoes com menos de 30 dias de antecedencia geram aviso, mas seguem para analise.</li>
            </ul>
          </div>
        )}

        {children}
      </section>
    </main>
  );
}
