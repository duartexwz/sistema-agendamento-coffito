export function WizardStepper({ steps, currentStep }) {
  return (
    <ol className="wizard-stepper" aria-label="Etapas do formulario">
      {steps.map((step, index) => (
        <li key={step.id} className={index === currentStep ? 'active' : index < currentStep ? 'done' : ''}>
          <span>{index + 1}</span>
          <strong>{step.label}</strong>
        </li>
      ))}
    </ol>
  );
}
