"""Validaciones puras reutilizables y comprobables sin servidor SQL."""
from datetime import date
import re

TIPOS = frozenset(('grado', 'posgrado', 'docente', 'funcionario'))
ROLES = frozenset(('administrador', 'planillero'))
CORREO = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


class ValidationError(ValueError):
    pass


def positive_int(value, name, limit=2147483647):
    if isinstance(value, bool):
        raise ValidationError(f'{name} debe ser un entero positivo.')
    try:
        result = int(value)
    except (TypeError, ValueError, OverflowError):
        raise ValidationError(f'{name} debe ser un entero positivo.') from None
    if result < 1 or result > limit or str(value).strip() != str(result):
        raise ValidationError(f'{name} debe ser un entero positivo.')
    return result


def validate_player(payload, *, expected_ci=None):
    if not isinstance(payload, dict):
        raise ValidationError('Enviá un objeto JSON con los datos del jugador.')
    ci = positive_int(payload.get('ci', expected_ci), 'Cédula')
    if len(str(ci)) not in (6, 7, 8, 9, 10):
        raise ValidationError('La cédula debe tener entre 6 y 10 dígitos.')
    if expected_ci is not None and ci != expected_ci:
        raise ValidationError('No se puede cambiar la cédula de un jugador.')
    result = {'ci': ci}
    for field, title in (('nombre', 'Nombre'), ('apellido', 'Apellido')):
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > 100:
            raise ValidationError(f'{title} debe tener entre 1 y 100 caracteres.')
        result[field] = value.strip()
    email = payload.get('email')
    if not isinstance(email, str) or not CORREO.fullmatch(email.strip()) or len(email.strip()) > 150:
        raise ValidationError('Ingresá un correo electrónico válido.')
    result['email'] = email.strip().lower()
    raw_date = payload.get('fecha_nacimiento')
    try:
        born = date.fromisoformat(raw_date) if isinstance(raw_date, str) else None
    except ValueError:
        born = None
    if born is None or born >= date.today():
        raise ValidationError('La fecha de nacimiento debe ser válida y anterior a hoy.')
    result['fecha_nacimiento'] = born.isoformat()
    result['id_facultad'] = positive_int(payload.get('id_facultad'), 'Facultad')
    if payload.get('tipo') not in TIPOS:
        raise ValidationError('El tipo debe ser grado, posgrado, docente o funcionario.')
    result['tipo'] = payload['tipo']
    return result


def verify_role(role, required):
    if role not in ROLES:
        return False
    return required == 'lectura' or role == 'administrador'
