"""Salud del servicio, inicio y cierre de sesión."""
import os
import secrets

from flask import Blueprint, g, jsonify
from werkzeug.security import generate_password_hash

from core import APIError, api_login_required, json_body, matches_password, token_hash
from database import connection, execute, fetch_one

bp = Blueprint('auth', __name__)
SESSION_TTL = max(60, min(86400, int(os.getenv('SESSION_TTL_SECONDS', '43200'))))


@bp.get('/health')
def health():
    with connection('administrador') as db:
        fetch_one(db, 'SELECT 1 AS ok')
    return jsonify({'status': 'ok', 'database': 'connected'})


@bp.post('/auth/login')
def login():
    body = json_body()
    correo, password = body.get('correo'), body.get('contrasena')
    if not isinstance(correo, str) or not 3 <= len(correo) <= 150 or '@' not in correo:
        raise APIError('Ingresá un correo válido.', 400)
    if not isinstance(password, str) or not 1 <= len(password) <= 256:
        raise APIError('Ingresá la contraseña.', 400)
    correo = correo.strip().lower()
    with connection('administrador') as db:
        row = fetch_one(db, 'SELECT correo, contrasena, rol FROM login WHERE correo = %s', (correo,))
        valid, is_legacy = matches_password(password, row['contrasena'] if row else None)
        if not valid or row['rol'] not in ('administrador', 'planillero'):
            raise APIError('Correo o contraseña incorrectos.', 401)
        if is_legacy:
            execute(db, 'UPDATE login SET contrasena = %s WHERE correo = %s',
                    (generate_password_hash(password, method='scrypt'), row['correo']))
        raw = secrets.token_urlsafe(32)
        execute(db, '''
            INSERT INTO sesion_api (token_hash, correo, expira_en)
            VALUES (%s, %s, DATE_ADD(UTC_TIMESTAMP(), INTERVAL %s SECOND))
        ''', (token_hash(raw), row['correo'], SESSION_TTL))
        db.commit()
    return jsonify({'token': raw, 'user': {'correo': row['correo'], 'rol': row['rol']}})


@bp.post('/auth/logout')
@api_login_required
def logout():
    with connection('administrador') as db:
        execute(db, 'DELETE FROM sesion_api WHERE token_hash = %s', (g.token_hash,))
        db.commit()
    return jsonify({'ok': True})


@bp.get('/auth/me')
@api_login_required
def me():
    return jsonify({'correo': g.user['correo'], 'rol': g.user['rol']})
