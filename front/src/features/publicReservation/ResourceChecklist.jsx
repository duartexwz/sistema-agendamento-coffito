export function ResourceChecklist({ resourceOptions, selectedItems, onToggle }) {
  return (
    <div className="public-resource-grid">
      {resourceOptions.map((item) => (
        <label key={item} className="form-check public-resource-option">
          <input
            className="form-check-input"
            type="checkbox"
            checked={selectedItems.includes(item)}
            onChange={() => onToggle(item)}
          />
          <span className="form-check-label">{item}</span>
          {requiresQuantity(item) && <small>Atencao: informe quantidade nas observacoes.</small>}
        </label>
      ))}
    </div>
  );
}

function requiresQuantity(item) {
  return ['Emprestimo de macas portateis', 'Impressos gerais', 'Sonorizacao', 'Notebook', 'Televisor', 'Datashow'].includes(item);
}
