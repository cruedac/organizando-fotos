"""
Utilidades comunes para parseo de fechas y carpetas.

Consolida lógica repetida para extracción de año/mes desde nombres de carpetas.
"""
import re
from typing import Optional, Tuple

# Patrón para años válidos
_YEAR_PATTERN = re.compile(r'(19|20)\d{2}')

# Variantes de nombres de meses (español e inglés)
_MONTH_VARIANTS = {
    1: ['enero', 'ene', 'january', 'jan'],
    2: ['febrero', 'feb', 'february'],
    3: ['marzo', 'mar', 'march'],
    4: ['abril', 'abr', 'april', 'apr'],
    5: ['mayo', 'may'],
    6: ['junio', 'jun', 'june'],
    7: ['julio', 'jul', 'july'],
    8: ['agosto', 'ago', 'august', 'aug'],
    9: ['septiembre', 'setiembre', 'sep', 'sept', 'september'],
    10: ['octubre', 'oct', 'october'],
    11: ['noviembre', 'nov', 'november'],
    12: ['diciembre', 'dic', 'december', 'dec'],
}

_MONTH_CANONICAL = {num: variants[0].capitalize() for num, variants in _MONTH_VARIANTS.items()}
_MONTH_LOOKUP = {alias: num for num, variants in _MONTH_VARIANTS.items() for alias in variants}
for number in range(1, 13):
    _MONTH_LOOKUP[str(number)] = number
    _MONTH_LOOKUP[f'{number:02d}'] = number


def parse_year_from_name(name: str) -> Optional[int]:
    """Extrae un año de 4 dígitos (1900-2100) desde un string."""
    if not name:
        return None
    match = _YEAR_PATTERN.search(name)
    if match:
        value = int(match.group())
        if 1900 <= value <= 2100:
            return value
    return None


def parse_month_from_name(name: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Extrae número de mes (1-12) y su texto canónico desde un string.
    
    Returns:
        (month_number, month_text): Tupla con número y texto del mes, o (None, None)
    """
    if not name:
        return None, None

    month_number: Optional[int] = None
    month_text: Optional[str] = None
    cleaned = name.strip()
    if not cleaned:
        return None, None

    # Buscar prefijo numérico (ej: "01-Enero" → 1)
    prefix_match = re.match(r'(?P<num>\d{1,2})\D*(?P<rest>.*)$', cleaned)
    if prefix_match:
        try:
            candidate = int(prefix_match.group('num'))
            if 1 <= candidate <= 12:
                month_number = candidate
        except ValueError:
            pass
        remainder = prefix_match.group('rest').strip(" -_.")
        if remainder and any(char.isalpha() for char in remainder):
            month_text = remainder

    # Buscar nombres de meses en tokens
    tokens = re.split(r'[\s\-_/.,]+', cleaned.lower())
    for token in tokens:
        if token in _MONTH_LOOKUP:
            resolved = _MONTH_LOOKUP[token]
            if month_number is None:
                month_number = resolved
            if not month_text:
                month_text = _MONTH_CANONICAL.get(resolved)
            break

    # Normalizar texto del mes
    if month_number and not month_text:
        month_text = _MONTH_CANONICAL.get(month_number)

    if month_text:
        month_text = ' '.join(part.capitalize() for part in month_text.strip().split())

    return month_number, month_text


def normalize_date_value(val: str) -> Optional[str]:
    """
    Normaliza una fecha en formato ISO (YYYY-MM-DD) desde diferentes formatos.
    
    Args:
        val: String con fecha en formato DD/MM/YYYY o YYYY-MM-DD
        
    Returns:
        Fecha normalizada en formato ISO o None si no es válida
    """
    if not val or not isinstance(val, str):
        return None
    
    val = val.strip()
    if not val or val in ('NULL', '0000-00-00'):
        return None
    
    # Ya está en formato ISO
    if re.match(r'^\d{4}-\d{2}-\d{2}$', val):
        return val
    
    # Convertir DD/MM/YYYY a YYYY-MM-DD
    match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', val)
    if match:
        day, month, year = match.groups()
        return f'{year}-{month.zfill(2)}-{day.zfill(2)}'
    
    return None
