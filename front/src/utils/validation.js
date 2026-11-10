/**
 * Validações e máscaras centralizadas (CPF, telefone, nome, horário).
 */

export function onlyDigits(value = '') {
  return String(value ?? '').replace(/\D/g, '');
}

// ---- CPF ----
export function isValidCPF(cpf = '') {
  const digits = onlyDigits(cpf);
  if (digits.length !== 11) return false;
  if (/^(\d)\1{10}$/.test(digits)) return false;

  const calcDigit = (base, factor) => {
    let sum = 0;
    for (let i = 0; i < base.length; i += 1) {
      sum += Number(base[i]) * (factor - i);
    }
    const rest = (sum * 10) % 11;
    return rest === 10 ? 0 : rest;
  };

  const d1 = calcDigit(digits.slice(0, 9), 10);
  const d2 = calcDigit(digits.slice(0, 10), 11);
  return d1 === Number(digits[9]) && d2 === Number(digits[10]);
}

export function maskCPF(value = '') {
  const digits = onlyDigits(value).slice(0, 11);
  if (digits.length <= 3) return digits;
  if (digits.length <= 6) return `${digits.slice(0, 3)}.${digits.slice(3)}`;
  if (digits.length <= 9) return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6)}`;
  return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6, 9)}-${digits.slice(9, 11)}`;
}

// ---- Telefone (BR) ----
const VALID_DDDS = new Set([
  '11','12','13','14','15','16','17','18','19','21','22','24','27','28','31','32','33','34','35','37','38',
  '41','42','43','44','45','46','47','48','49','51','53','54','55','61','62','63','64','65','66','67','68','69',
  '71','73','74','75','77','79','81','82','83','84','85','86','87','88','89','91','92','93','94','95','96','97','98','99',
]);

export function isValidPhone(phone = '') {
  const digits = onlyDigits(phone);
  if (!(digits.length === 10 || digits.length === 11)) return false;
  const ddd = digits.slice(0, 2);
  if (!VALID_DDDS.has(ddd)) return false;
  if (digits.length === 11 && digits[2] !== '9') return false;
  if (/^(\d)\1+$/.test(digits)) return false;
  return true;
}

export function maskPhone(value = '') {
  const digits = onlyDigits(value).slice(0, 11);
  if (digits.length <= 2) return digits;
  if (digits.length <= 6) return `(${digits.slice(0, 2)}) ${digits.slice(2)}`;
  if (digits.length <= 10) return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`;
  return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7, 11)}`;
}

// ---- Nome ----
const FAKE_PATTERNS = [
  /^([a-z])\1+$/i,
  /^(abc|qwerty|asdf|zxcv|teste|test|fulano|anonimo|anônimo)/i,
];

export function isValidName(name = '') {
  const trimmed = String(name ?? '').trim();
  if (trimmed.length < 3) return false;
  const parts = trimmed.split(/\s+/).filter(Boolean);
  if (parts.length < 2) return false;
  if (parts.some((p) => p.length < 2)) return false;
  if (!/^[A-Za-zÀ-ÿ\s'-]+$/.test(trimmed)) return false;
  const withoutSpaces = trimmed.replace(/\s+/g, '');
  if (withoutSpaces.length < 3) return false;
  const lower = trimmed.toLowerCase();
  if (FAKE_PATTERNS.some((re) => re.test(lower))) return false;
  // repetição sequencial tipo "aksdaoskdnaskjdnsakjsn" -> baixa razão vogal/consoante e sem padrão silábico
  const vowels = (lower.match(/[aeiouáéíóúãõâêôà]/g) || []).length;
  const letters = (lower.match(/[a-zà-ÿ]/g) || []).length;
  const ratio = letters ? vowels / letters : 0;
  if (ratio < 0.15 || ratio > 0.85) return false;
  // sequencia sem vogais em bloco grande
  if (/[bcdfghjklmnpqrstvwxyz]{5,}/i.test(trimmed)) return false;
  // entropia muito baixa (muitas repetições de char)
  const unique = new Set(lower.replace(/\s/g, '')).size;
  if (unique < 3) return false;
  // palavras repetidas
  if (new Set(parts.map((p) => p.toLowerCase())).size === 1 && parts.length > 1) return false;
  // avalia cada palavra: deve ter ao menos uma vogal
  if (parts.some((p) => !/[aeiouáéíóúãõâêôà]/i.test(p))) return false;
  return true;
}

// ---- Email ----
export function isValidEmail(email = '') {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(String(email).trim());
}

// ---- Horário evento 07:00 .. 20:00 ----
export const HORARIO_LIMITE = { inicioMin: '07:00', fimMax: '20:00' };

export function isValidHorario(horario) {
  if (!horario) return false;
  return horario >= HORARIO_LIMITE.inicioMin && horario <= HORARIO_LIMITE.fimMax;
}

export function validateHorarioIntervalo(horarioInicio, horarioFim) {
  if (!horarioInicio || !horarioFim) return null;
  if (!isValidHorario(horarioInicio)) return 'horário de solicitação não permitido';
  if (!isValidHorario(horarioFim)) return 'horário de solicitação não permitido';
  if (horarioFim <= horarioInicio) return 'Horário final deve ser posterior ao inicial.';
  return null;
}
