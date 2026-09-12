export function formatDate(dateString) {
  if (!dateString) return '-';
  return new Intl.DateTimeFormat('pt-BR', { timeZone: 'UTC' }).format(new Date(`${dateString}T00:00:00`));
}

export function formatDateTime(dateString, timeString) {
  if (!dateString || !timeString) return '-';
  return `${formatDate(dateString)} as ${timeString}`;
}

export function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

export function isSameDay(startDate, endDate) {
  return startDate && endDate && startDate === endDate;
}

export function buildLocalDateTime(dateString, timeString = '00:00') {
  if (!dateString) return null;

  const safeTime = String(timeString || '00:00').slice(0, 5);
  const date = new Date(`${dateString}T${safeTime}`);

  return Number.isNaN(date.getTime()) ? null : date;
}

export function getReservaStartDateTime(reserva) {
  return buildLocalDateTime(reserva?.data_inicio, reserva?.horario_inicio || '00:00');
}

export function getReservaEndDateTime(reserva) {
  return buildLocalDateTime(
    reserva?.data_fim || reserva?.data_inicio,
    reserva?.horario_fim || reserva?.horario_inicio || '23:59',
  );
}

export function isReservaUpcomingOrActive(reserva, referenceDate = new Date()) {
  const startDate = getReservaStartDateTime(reserva);
  const endDate = getReservaEndDateTime(reserva) ?? startDate;

  if (!startDate && !endDate) return false;

  return (endDate ?? startDate) >= referenceDate;
}

export function compareReservasByStartDateTime(a, b) {
  const first = getReservaStartDateTime(a);
  const second = getReservaStartDateTime(b);

  if (!first && !second) return 0;
  if (!first) return 1;
  if (!second) return -1;

  return first.getTime() - second.getTime();
}
