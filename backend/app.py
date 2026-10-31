"""API REST UCU League — Flask + MySQL, sin ORM.

Endpoints iniciales: autenticación, bootstrap, 12 reportes y ABM de jugadores.
Los otros ABM se incorporarán en commits posteriores.
"""
import hashlib
import hmac
import os
import re
import secrets
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, g, jsonify, request
from mysql.connector import Error as MySQLError
from werkzeug.security import check_password_hash, generate_password_hash

from database import connection, execute, fetch_all, fetch_one, to_json_value
from logic import ValidationError, positive_int, validate_player, verify_role
from reports import REPORTS, get_report

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
app = Flask(__name__)
app.json.ensure_ascii = False
SESSION_TTL = max(60, min(86400, int(os.getenv('SESSION_TTL_SECONDS', '43200'))))
ALLOWED_ORIGINS = {origin.strip() for origin in os.getenv(
    'CORS_ORIGINS', 'http://localhost:5500,http://127.0.0.1:5500'
).split(',') if origin.strip()}


class APIError(Exception):
    def __init__(self, message, status):
        super().__init__(message)
        self.status = status


@app.after_request
def add_headers(response):
    origin = request.headers.get('Origin')
    if origin in ALLOWED_ORIGINS:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Vary'] = 'Origin'
        response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type, Accept'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, DELETE, OPTIONS'
    response.headers['Cache-Control'] = 'no-store'
    return response


@app.errorhandler(APIError)
def http_error(err):
    return jsonify({'error': str(err)}), err.status


@app.errorhandler(ValidationError)
def validation_error(err):
    return jsonify({'error': str(err)}), 400


@app.errorhandler(MySQLError)
def sql_error(err):
    if err.errno in (1062, 1451, 1452):
        return jsonify({'error': 'Registro duplicado o vinculado a otros datos. Revisá las referencias.'}), 409
    if err.sqlstate == '45000':
        # Mensajes de negocio definidos por los triggers de nuestro esquema.
        return jsonify({'error': err.msg}), 409
    if err.errno in (1044, 1045, 1146, 2003, 2005, 2013):
        app.logger.exception('Error de configuración/conexión MySQL')
        return jsonify({'error': 'No se pudo acceder a MySQL. Revisá el esquema, la tabla sesion_api y las cuentas técnicas.'}), 503
    app.logger.exception('Error inesperado de MySQL')
    return jsonify({'error': 'Error interno al consultar la base de datos.'}), 500


@app.errorhandler(404)
def route_missing(_):
    return jsonify({'error': 'Ruta no implementada en esta etapa del backend.'}), 404


@app.errorhandler(405)
def method_not_allowed(_):
    return jsonify({'error': 'Método HTTP no permitido en esta ruta.'}), 405


def json_body():
    if not request.is_json:
        raise APIError('Enviá los datos como application/json.', 415)
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise APIError('El cuerpo debe ser un objeto JSON.', 400)
    return body


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


@app.get('/api/health')
def health():
    with connection('administrador') as db:
        fetch_one(db, 'SELECT 1 AS ok')
    return jsonify({'status': 'ok', 'database': 'connected'})


@app.post('/api/auth/login')
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


@app.post('/api/auth/logout')
@api_login_required
def logout():
    with connection('administrador') as db:
        execute(db, 'DELETE FROM sesion_api WHERE token_hash = %s', (g.token_hash,))
        db.commit()
    return jsonify({'ok': True})


# Importante: NO incluir contraseñas ni cuentas login en /bootstrap.
# En sancion_jugador se devuelve SOLO la sanción manual (la UI calcula
# las automáticas desde las tarjetas; incluirlas aquí duplicaría conteos).
BOOTSTRAP_QUERIES = {
    'facultad': 'SELECT id_facultad, nombre FROM facultad ORDER BY id_facultad',
    'torneo': 'SELECT id_torneo, nombre, anio, semestre, fecha_inicio, fecha_fin, estado FROM torneo ORDER BY id_torneo',
    'jugador': 'SELECT ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo FROM jugador ORDER BY ci',
    'equipo': 'SELECT id_equipo, nombre, id_torneo, id_facultad, ci_capitan FROM equipo ORDER BY id_equipo',
    'equipo_jugador_torneo': 'SELECT id_equipo, ci_jugador, id_torneo, numero_camiseta FROM equipo_jugador_torneo ORDER BY id_equipo, ci_jugador',
    'complejo': 'SELECT id_complejo, nombre, direccion, departamento FROM complejo ORDER BY id_complejo',
    'cancha': 'SELECT nombre_cancha, id_complejo, superficie, techada FROM cancha ORDER BY id_complejo, nombre_cancha',
    'turno': 'SELECT id_turno, hora_inicio, hora_fin FROM turno ORDER BY id_turno',
    'partido': '''SELECT id_partido, id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante,
                        dia, id_turno, nombre_cancha, id_complejo, estado FROM partido ORDER BY id_partido''',
    'planilla_partido': 'SELECT id_partido, ci_jugador, id_equipo FROM planilla_partido ORDER BY id_partido, ci_jugador',
    'gol': 'SELECT id_gol, id_partido, ci_jugador, minuto, autogol FROM gol ORDER BY id_gol',
    'tarjeta': 'SELECT id_tarjeta, id_partido, ci_jugador, minuto, color FROM tarjeta ORDER BY id_tarjeta',
    'sancion_jugador': '''SELECT id_sancion, ci_jugador, id_torneo, motivo, numero_fecha_inicio,
                                cantidad_fechas, origen FROM v_sanciones WHERE origen = 'manual' ORDER BY id_sancion''',
}


@app.get('/api/bootstrap')
@api_login_required
def bootstrap():
    # Leer con los permisos SQL del rol real, no siempre como administrador.
    with connection(g.db_role) as db:
        data = {key: fetch_all(db, sql) for key, sql in BOOTSTRAP_QUERIES.items()}
    return jsonify(to_json_value(data))


@app.get('/api/reportes/<slug>')
@api_login_required
def reports(slug):
    if slug not in REPORTS:
        raise APIError('Reporte no encontrado.', 404)
    torneo = positive_int(request.args.get('id_torneo'), 'Edición')
    with connection(g.db_role) as db:
        rows = get_report(db, slug, torneo)
    return jsonify(to_json_value(rows))


@app.get('/api/jugadores')
@api_login_required
def players_list():
    with connection(g.db_role) as db:
        rows = fetch_all(db, BOOTSTRAP_QUERIES['jugador'])
    return jsonify(to_json_value(rows))


@app.get('/api/jugadores/<int:ci>')
@api_login_required
def player_detail(ci):
    with connection(g.db_role) as db:
        row = fetch_one(db, '''SELECT ci, nombre, apellido, email, fecha_nacimiento,
                                      id_facultad, tipo FROM jugador WHERE ci = %s''', (ci,))
    if row is None:
        raise APIError('Jugador no encontrado.', 404)
    return jsonify(to_json_value(row))


@app.post('/api/jugadores')
@admin_required
def player_create():
    player = validate_player(json_body())
    with connection('administrador') as db:
        execute(db, '''INSERT INTO jugador
            (ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo)
            VALUES (%s, %s, %s, %s, %s, %s, %s)''', tuple(player.values()))
        db.commit()
    return jsonify(player), 201


@app.patch('/api/jugadores/<int:ci>')
@admin_required
def player_update(ci):
    payload = json_body()
    # El frontend manda todos los campos; para PATCH parcial recuperamos los restantes.
    with connection('administrador') as db:
        current = fetch_one(db, '''SELECT ci, nombre, apellido, email, fecha_nacimiento,
                                          id_facultad, tipo FROM jugador WHERE ci = %s''', (ci,))
        if not current:
            raise APIError('Jugador no encontrado.', 404)
        merged = {**to_json_value(current), **payload, 'ci': ci}
        player = validate_player(merged, expected_ci=ci)
        execute(db, '''UPDATE jugador SET nombre=%s, apellido=%s, email=%s,
                       fecha_nacimiento=%s, id_facultad=%s, tipo=%s WHERE ci=%s''',
                (player['nombre'], player['apellido'], player['email'], player['fecha_nacimiento'],
                 player['id_facultad'], player['tipo'], ci))
        db.commit()
    return jsonify(player)


@app.delete('/api/jugadores/<int:ci>')
@admin_required
def player_delete(ci):
    with connection('administrador') as db:
        _, affected = execute(db, 'DELETE FROM jugador WHERE ci=%s', (ci,))
        if not affected:
            raise APIError('Jugador no encontrado.', 404)
        db.commit()
    return ('', 204)


if __name__ == '__main__':
    # Debug deshabilitado: no publicar contraseñas ni información de MySQL.
    app.run(host='127.0.0.1', port=int(os.getenv('PORT', '5000')), debug=False)
