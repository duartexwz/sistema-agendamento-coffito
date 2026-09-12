import { formatDate } from '../../shared/utils/date.js';

export function DateRangeSelector({
  periodo,
  selectedDates = [],
  occupiedDates,
  onChange,
  onAddDate = () => {},
  onRemoveDate = () => {},
}) {
  const warnings = getDateWarnings(periodo.data_inicio, periodo.data_fim, occupiedDates, selectedDates);

  return (
    <div className="date-range-list">
      <div className="date-range-row">
        <div className="date-range-grid">
          <div>
            <label className="form-label" htmlFor="data-inicio-evento">
              Data de inicio do evento *
            </label>
            <input
              id="data-inicio-evento"
              type="date"
              className="form-control"
              value={periodo.data_inicio}
              onChange={(event) => onChange('data_inicio', event.target.value)}
            />
          </div>

          <div>
            <label className="form-label" htmlFor="data-fim-evento">
              Data final do evento *
            </label>
            <input
              id="data-fim-evento"
              type="date"
              className="form-control"
              value={periodo.data_fim}
              onChange={(event) => onChange('data_fim', event.target.value)}
            />
          </div>

          <div>
            <label className="form-label" htmlFor="horario-inicio-evento">
              Horario inicial *
            </label>
            <input
              id="horario-inicio-evento"
              type="time"
              className="form-control"
              value={periodo.horario_inicio}
              onChange={(event) => onChange('horario_inicio', event.target.value)}
            />
          </div>

          <div>
            <label className="form-label" htmlFor="horario-fim-evento">
              Horario final *
            </label>
            <input
              id="horario-fim-evento"
              type="time"
              className="form-control"
              value={periodo.horario_fim}
              onChange={(event) => onChange('horario_fim', event.target.value)}
            />
          </div>
        </div>

        <div className="specific-dates-box">
          <div>
            <label className="form-label" htmlFor="data-avulsa-evento">
              Datas especificas do mesmo evento
            </label>
            <div className="specific-date-input">
              <input
                id="data-avulsa-evento"
                type="date"
                className="form-control"
                value={periodo.data_avulsa ?? ''}
                onChange={(event) => onChange('data_avulsa', event.target.value)}
              />
              <button type="button" className="btn btn-outline-primary" onClick={onAddDate}>
                Adicionar data
              </button>
            </div>
            <p className="field-help">
              Use para eventos em dias alternados. Se nenhuma data especifica for adicionada, sera usado o periodo
              continuo informado acima.
            </p>
          </div>
          {selectedDates.length > 0 && (
            <div className="selected-date-list" aria-label="Datas especificas selecionadas">
              {selectedDates.map((date) => (
                <span key={date} className="selected-date-chip">
                  {formatDate(date)}
                  <button type="button" onClick={() => onRemoveDate(date)} aria-label={`Remover ${formatDate(date)}`}>
                    <i className="bi bi-x" aria-hidden="true" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {warnings.length > 0 && (
          <div className="date-warning-list">
            {warnings.map((warning) => (
              <span key={warning}>{warning}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function getDateWarnings(startDate, endDate, occupiedDates, selectedDates = []) {
  const datesToCheck = selectedDates.length > 0 ? selectedDates : [startDate].filter(Boolean);
  if (datesToCheck.length === 0) return [];

  const warnings = [];
  const selected = new Date(`${datesToCheck[0]}T00:00:00`);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const diffDays = Math.ceil((selected - today) / 86_400_000);

  if (diffDays < 30) warnings.push('Atencao: data com menos de 30 dias de antecedencia.');
  const hasConflict =
    selectedDates.length > 0
      ? selectedDates.some((date) => occupiedDates.has(date))
      : hasOccupiedDate(startDate, endDate, occupiedDates);

  if (hasConflict) {
    warnings.push('Atencao: existe reserva ou bloqueio no periodo informado.');
  }

  return warnings;
}

function hasOccupiedDate(startDate, endDate, occupiedDates) {
  if (!startDate) return false;
  const start = new Date(`${startDate}T00:00:00`);
  const end = new Date(`${endDate || startDate}T00:00:00`);

  for (let current = start; current <= end; current.setDate(current.getDate() + 1)) {
    if (occupiedDates.has(current.toISOString().slice(0, 10))) return true;
  }

  return false;
}
