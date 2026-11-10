import re

VALID_DDDS = {
    '11','12','13','14','15','16','17','18','19','21','22','24','27','28','31','32','33','34','35','37','38',
    '41','42','43','44','45','46','47','48','49','51','53','54','55','61','62','63','64','65','66','67','68','69',
    '71','73','74','75','77','79','81','82','83','84','85','86','87','88','89','91','92','93','94','95','96','97','98','99',
}

def only_digits(value: str = '') -> str:
    return re.sub(r'\D', '', str(value or ''))

def is_valid_cpf(cpf: str = '') -> bool:
    digits = only_digits(cpf)
    if len(digits) != 11:
        return False
    if re.match(r'^(\d)\1{10}$', digits):
        return False
    def calc_digit(base: str, factor: int) -> int:
        s = sum(int(d) * (factor - i) for i, d in enumerate(base))
        r = (s * 10) % 11
        return 0 if r == 10 else r
    d1 = calc_digit(digits[:9], 10)
    d2 = calc_digit(digits[:10], 11)
    return d1 == int(digits[9]) and d2 == int(digits[10])

def is_valid_phone(phone: str = '') -> bool:
    digits = only_digits(phone)
    if len(digits) not in (10, 11):
        return False
    ddd = digits[:2]
    if ddd not in VALID_DDDS:
        return False
    if len(digits) == 11 and digits[2] != '9':
        return False
    if re.match(r'^(\d)\1+$', digits):
        return False
    return True

def is_valid_name(name: str = '') -> bool:
    trimmed = str(name or '').strip()
    if len(trimmed) < 3:
        return False
    parts = [p for p in re.split(r'\s+', trimmed) if p]
    if len(parts) < 2:
        return False
    if any(len(p) < 2 for p in parts):
        return False
    if not re.match(r"^[A-Za-zÀ-ÿ\s'-]+$", trimmed):
        return False
    lower = trimmed.lower()
    fake_patterns = [
        r'^([a-z])\1+$',
        r'^(abc|qwerty|asdf|zxcv|teste|test|fulano|anonimo|anônimo)',
    ]
    for pat in fake_patterns:
        if re.match(pat, lower):
            return False
    vowels = len(re.findall(r'[aeiouáéíóúãõâêôà]', lower))
    letters = len(re.findall(r'[a-zà-ÿ]', lower))
    ratio = (vowels / letters) if letters else 0
    if ratio < 0.15 or ratio > 0.85:
        return False
    if re.search(r'[bcdfghjklmnpqrstvwxyz]{5,}', trimmed, re.IGNORECASE):
        return False
    unique = len(set(lower.replace(' ', '')))
    if unique < 3:
        return False
    if len(set(p.lower() for p in parts)) == 1 and len(parts) > 1:
        return False
    if any(not re.search(r'[aeiouáéíóúãõâêôà]', p, re.IGNORECASE) for p in parts):
        return False
    return True

def is_valid_email(email: str = '') -> bool:
    return bool(re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]{2,}$', str(email or '').strip()))

HORARIO_MIN = '07:00'
HORARIO_MAX = '20:00'

def is_valid_horario(horario) -> bool:
    if not horario:
        return False
    # horario pode ser datetime.time ou str
    if hasattr(horario, 'strftime'):
        horario = horario.strftime('%H:%M')
    horario = str(horario)[:5]
    return HORARIO_MIN <= horario <= HORARIO_MAX
