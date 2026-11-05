"""Validaciones puras reutilizables y comprobables sin servidor SQL.

Validan formato y rangos antes de llegar a MySQL. Las reglas que dependen de
otros registros (planteles, fixture, suspensiones, 48 horas) las imponen los
triggers y procedimientos de torneo_ucu_creacion.sql.
"""
from datetime import date, time
import re

TIPOS = frozenset(('grado', 'posgrado', 'docente', 'funcionario'))
ROLES = frozenset(('administrador', 'planillero'))
ESTADOS_TORNEO = ('inscripción', 'en curso', 'finalizado')
ESTADOS_PARTIDO = frozenset(('programado', 'jugado', 'postergado', 'cancelado'))
SUPERFICIES = frozenset(('sintético', 'parquet'))
COLORES = frozenset(('amarilla', 'roja'))
MOTIVOS = frozenset(('roja', 'acumulación de amarillas', 'disciplinaria'))
ORIGENES = frozenset(('manual', 'automatica'))
CORREO = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
HORA = re.compile(r'^([01]\d|2[0-3]):([0-5]\d)(:([0-5]\d))?$')


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


def int_between(value, name, low, high):
    if isinstance(value, bool):
        raise ValidationError(f'{name} debe ser un entero entre {low} y {high}.')
    try:
        result = int(value)
    except (TypeError, ValueError, OverflowError):
        raise ValidationError(f'{name} debe ser un entero entre {low} y {high}.') from None
    if not low <= result <= high or str(value).strip() != str(result):
        raise ValidationError(f'{name} debe ser un entero entre {low} y {high}.')
    return result


def text(payload, field, title, max_len=100):
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > max_len:
        raise ValidationError(f'{title} debe tener entre 1 y {max_len} caracteres.')
    return value.strip()


def iso_date(value):
    try:
        return date.fromisoformat(value) if isinstance(value, str) else None
    except ValueError:
        return None


def required_date(value, title):
    result = iso_date(value)
    if result is None:
        raise ValidationError(f'{title} debe ser una fecha válida (AAAA-MM-DD).')
    return result


def boolean(value, title):
    if value in (True, False, 0, 1) and not isinstance(value, float):
        return bool(value)
    if isinstance(value, str) and value.strip().lower() in ('true', 'false', '0', '1'):
        return value.strip().lower() in ('true', '1')
    raise ValidationError(f'{title} debe ser verdadero o falso.')


def choice(value, options, message):
    if value not in options:
        raise ValidationError(message)
    return value


def hour(value, title):
    match = HORA.fullmatch(value) if isinstance(value, str) else None
    if not match:
        raise ValidationError(f'{title} debe tener formato HH:MM.')
    return time(int(match.group(1)), int(match.group(2)), int(match.group(4) or 0))


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
        result[field] = text(payload, field, title)
    email = payload.get('email')
    if not isinstance(email, str) or not CORREO.fullmatch(email.strip()) or len(email.strip()) > 150:
        raise ValidationError('Ingresá un correo electrónico válido.')
    result['email'] = email.strip().lower()
    born = iso_date(payload.get('fecha_nacimiento'))
    if born is None or born >= date.today():
        raise ValidationError('La fecha de nacimiento debe ser válida y anterior a hoy.')
    result['fecha_nacimiento'] = born.isoformat()
    result['id_facultad'] = positive_int(payload.get('id_facultad'), 'Facultad')
    if payload.get('tipo') not in TIPOS:
        raise ValidationError('El tipo debe ser grado, posgrado, docente o funcionario.')
    result['tipo'] = payload['tipo']
    return result


def validate_facultad(payload):
    return {'nombre': text(payload, 'nombre', 'Nombre de la facultad')}


def validate_turno(payload):
    inicio = hour(payload.get('hora_inicio'), 'Hora de inicio')
    if inicio.minute or inicio.second or not 18 <= inicio.hour <= 22:
        raise ValidationError('Los turnos comienzan en punto, entre las 18:00 y las 22:00.')
    fin = time(inicio.hour + 1)
    if payload.get('hora_fin') not in (None, '') and hour(payload['hora_fin'], 'Hora de fin') != fin:
        raise ValidationError('Cada turno dura exactamente una hora.')
    return {'hora_inicio': inicio.isoformat(), 'hora_fin': fin.isoformat()}


def validate_torneo(payload):
    result = {
        'nombre': text(payload, 'nombre', 'Nombre del torneo', 150),
        'anio': int_between(payload.get('anio'), 'Año', 2000, 2100),
        'semestre': int_between(payload.get('semestre'), 'Semestre', 1, 2),
    }
    inicio = required_date(payload.get('fecha_inicio'), 'Fecha de inicio')
    fin = required_date(payload.get('fecha_fin'), 'Fecha de fin')
    if fin < inicio:
        raise ValidationError('La fecha de fin no puede ser anterior a la de inicio.')
    result['fecha_inicio'], result['fecha_fin'] = inicio.isoformat(), fin.isoformat()
    result['estado'] = choice(payload.get('estado', 'inscripción'), ESTADOS_TORNEO,
                              'El estado debe ser inscripción, en curso o finalizado.')
    return result


def validate_torneo_transition(old, new):
    """Las ediciones solo avanzan: inscripción -> en curso -> finalizado."""
    if ESTADOS_TORNEO.index(new) < ESTADOS_TORNEO.index(old):
        raise ValidationError(f'No se puede volver de «{old}» a «{new}».')


def validate_equipo(payload):
    result = {
        'nombre': text(payload, 'nombre', 'Nombre del equipo'),
        'id_torneo': positive_int(payload.get('id_torneo'), 'Edición'),
        'id_facultad': positive_int(payload.get('id_facultad'), 'Facultad'),
        'ci_capitan': positive_int(payload.get('ci_capitan'), 'Capitán'),
    }
    result['numero_camiseta_capitan'] = int_between(
        payload.get('numero_camiseta_capitan', 1), 'Camiseta del capitán', 1, 99)
    return result


def validate_plantel(payload):
    return {
        'ci_jugador': positive_int(payload.get('ci_jugador'), 'Jugador'),
        'numero_camiseta': int_between(payload.get('numero_camiseta'), 'Número de camiseta', 1, 99),
    }


def validate_complejo(payload):
    return {
        'nombre': text(payload, 'nombre', 'Nombre del complejo'),
        'direccion': text(payload, 'direccion', 'Dirección', 150),
        'departamento': text(payload, 'departamento', 'Departamento'),
    }


def validate_cancha(payload):
    return {
        'nombre_cancha': text(payload, 'nombre_cancha', 'Nombre de la cancha'),
        'superficie': choice(payload.get('superficie'), SUPERFICIES,
                             'La superficie debe ser sintético o parquet.'),
        'techada': boolean(payload.get('techada'), 'Techada'),
    }


def validate_partido(payload):
    result = {
        'id_torneo': positive_int(payload.get('id_torneo'), 'Edición'),
        'numero_fecha': positive_int(payload.get('numero_fecha'), 'Número de fecha', 1000),
        'id_equipo_local': positive_int(payload.get('id_equipo_local'), 'Equipo local'),
        'id_equipo_visitante': positive_int(payload.get('id_equipo_visitante'), 'Equipo visitante'),
        'dia': required_date(payload.get('dia'), 'Día').isoformat(),
        'id_turno': positive_int(payload.get('id_turno'), 'Turno'),
        'nombre_cancha': text(payload, 'nombre_cancha', 'Cancha'),
        'id_complejo': positive_int(payload.get('id_complejo'), 'Complejo'),
        'estado': choice(payload.get('estado', 'programado'), ESTADOS_PARTIDO,
                         'El estado debe ser programado, jugado, postergado o cancelado.'),
    }
    if result['id_equipo_local'] == result['id_equipo_visitante']:
        raise ValidationError('Un equipo no puede jugar contra sí mismo.')
    return result


def validate_planilla(payload):
    participantes = payload.get('participantes')
    if not isinstance(participantes, list) or len(participantes) > 20:
        raise ValidationError('Enviá la lista «participantes» (máximo 20 jugadores).')
    result, vistos = [], set()
    for item in participantes:
        if not isinstance(item, dict):
            raise ValidationError('Cada participante debe indicar ci_jugador e id_equipo.')
        ci = positive_int(item.get('ci_jugador'), 'Jugador')
        if ci in vistos:
            raise ValidationError('Un jugador no puede figurar dos veces en la planilla.')
        vistos.add(ci)
        result.append({'ci_jugador': ci, 'id_equipo': positive_int(item.get('id_equipo'), 'Equipo')})
    return result


def validate_participante(payload):
    return validate_planilla({'participantes': [payload]})[0]


def validate_gol(payload):
    return {
        'ci_jugador': positive_int(payload.get('ci_jugador'), 'Jugador'),
        'minuto': int_between(payload.get('minuto'), 'Minuto', 0, 60),
        'autogol': boolean(payload.get('autogol', False), 'Autogol'),
    }


def validate_tarjeta(payload):
    return {
        'ci_jugador': positive_int(payload.get('ci_jugador'), 'Jugador'),
        'minuto': int_between(payload.get('minuto'), 'Minuto', 0, 60),
        'color': choice(payload.get('color'), COLORES, 'El color debe ser amarilla o roja.'),
    }


def validate_sancion(payload):
    if payload.get('motivo', 'disciplinaria') != 'disciplinaria':
        raise ValidationError('Solo se cargan sanciones disciplinarias: las de tarjetas son automáticas.')
    return {
        'ci_jugador': positive_int(payload.get('ci_jugador'), 'Jugador'),
        'id_torneo': positive_int(payload.get('id_torneo'), 'Edición'),
        'numero_fecha_inicio': positive_int(payload.get('numero_fecha_inicio'), 'Fecha de inicio', 1000),
        'cantidad_fechas': int_between(payload.get('cantidad_fechas'), 'Cantidad de fechas', 1, 50),
    }


def verify_role(role, required):
    if role not in ROLES:
        return False
    return required == 'lectura' or role == 'administrador'
