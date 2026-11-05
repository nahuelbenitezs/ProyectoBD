"""Piezas comunes de la API: errores HTTP, autenticación por token y helpers de request."""
import hashlib
import hmac
import re
from functools import wraps

from flask import g, request
from werkzeug.security import check_password_hash

from database import connection, fetch_one
from logic import positive_int, verify_role


class APIError(Exception):
    def __init__(self, message, status):
        super().__init__(message)
        self.status = status


def json_body():
    if not request.is_json:
        raise APIError('Enviá los datos como application/json.', 415)
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise APIError('El cuerpo debe ser un objeto JSON.', 400)
    return body


def query_int(name, title):
    """Filtro entero opcional de la query string (?id_torneo=1)."""
    value = request.args.get(name)
    return None if value in (None, '') else positive_int(value, title)


def query_choice(name, options, title):
    value = request.args.get(name)
    if value in (None, ''):
        return None
    if value not in options:
        raise APIError(f'{title} no válido.', 400)
    return value


def found(row, message):
    if row is None:
        raise APIError(message, 404)
    return row


def token_hash(raw_token):
    return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()


def api_login_required(view):
    @wraps(view)
    def inner(*args, **kwargs):
        header = request.headers.get('Authorization', '')
        if not header.startswith('Bearer '):
            raise APIError('Tenés que iniciar sesión.', 401)
        token = header[7:]
        if not re.fullmatch(r'[A-Za-z0-9_\-]{30,256}', token):
            raise APIError('Token de sesión no válido.', 401)
        with connection('administrador') as db:
            user = fetch_one(db, '''
                SELECT l.correo, l.rol
                  FROM sesion_api s JOIN login l ON l.correo = s.correo
                 WHERE s.token_hash = %s AND s.expira_en > UTC_TIMESTAMP()
            ''', (token_hash(token),))
        if not user or user['rol'] not in ('administrador', 'planillero'):
            raise APIError('Sesión vencida. Volvé a iniciar sesión.', 401)
        g.user = user
        # Cada rol de la aplicación usa su propia cuenta técnica de MySQL.
        g.db_role = user['rol']
        g.token_hash = token_hash(token)
        return view(*args, **kwargs)
    return inner


def admin_required(view):
    @wraps(view)
    @api_login_required
    def inner(*args, **kwargs):
        if not verify_role(g.user['rol'], 'administracion'):
            raise APIError('No tenés permisos para esta operación.', 403)
        return view(*args, **kwargs)
    return inner


def matches_password(typed, stored):
    """Permite migrar las claves SHA2 de la demo al hash scrypt sin romper la semilla."""
    if not isinstance(stored, str):
        return False, False
    if re.fullmatch(r'[a-fA-F0-9]{64}', stored):
        digest = hashlib.sha256(typed.encode('utf-8')).hexdigest()
        return hmac.compare_digest(digest, stored.lower()), True
    try:
        return check_password_hash(stored, typed), False
    except (ValueError, TypeError):
        return False, False
