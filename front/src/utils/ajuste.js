/**
 * Regras da caixa "Ajuste solicitado pela administração".
 *
 * O motivo só aparece quando a operação de solicitar ajuste foi
 * realmente a última ação relevante do histórico. Uma observação
 * qualquer gravada pelo painel (ex.: motivo de cancelamento) nunca
 * deve aparecer como ajuste solicitado.
 */

function normalizeText(value) {
  return String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

function isAjusteEntry(item = {}) {
  const text = normalizeText(`${item.acao ?? ''} ${item.status ?? ''}`);
  return text.includes('ajuste') || text.includes('complement');
}

function isAjusteRespondidoEntry(item = {}) {
  return normalizeText(item.acao ?? '').includes('ajuste_respondido');
}

export function getMotivoAjuste(reserva = {}, historico = []) {
  const entries = [...(historico ?? [])].filter(
    (item) => String(item?.acao ?? '').trim() || String(item?.status ?? '').trim(),
  );

  // Última ação relevante manda: só mostra a caixa se ela for um
  // pedido de ajuste ainda não superado por outra decisão/resposta.
  const lastRelevant = entries.at(-1);
  if (lastRelevant && isAjusteEntry(lastRelevant) && !isAjusteRespondidoEntry(lastRelevant)) {
    const motivo = String(lastRelevant.observacao ?? '').trim()
      || String(reserva.observacoes ?? reserva.observacao ?? '').trim();
    return motivo;
  }

  // Legado: reservas já paradas em status de complementação, sem
  // histórico novo de ajuste (ação genérica antiga).
  const statusText = normalizeText(`${reserva.status ?? ''} ${reserva.status_id ?? ''}`);
  if (statusText.includes('complement') || statusText.includes('ajuste')) {
    return String(reserva.observacoes ?? reserva.observacao ?? '').trim();
  }

  return '';
}
