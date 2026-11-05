"""ABM de jugadores y consulta de suspensiones."""
from flask import Blueprint, g, jsonify

from core import APIError, admin_required, api_login_required, found, json_body, query_choice, query_int
from database import connection, execute, fetch_all, fetch_one, to_json_value
from logic import TIPOS, validate_player

bp = Blueprint('jugadores', __name__)

JUGADOR = '''SELECT ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo
               FROM jugador'''


@bp.get('/jugadores')
@api_login_required
def players_list():
    facultad = query_int('id_facultad', 'Facultad')
    tipo = query_choice('tipo', TIPOS, 'Tipo de jugador')
    with connection(g.db_role) as db:
        rows = fetch_all(db, JUGADOR + '''
             WHERE (%s IS NULL OR id_facultad = %s) AND (%s IS NULL OR tipo = %s)
             ORDER BY ci''', (facultad, facultad, tipo, tipo))
    return jsonify(to_json_value(rows))


@bp.get('/jugadores/<int:ci>')
@api_login_required
def player_detail(ci):
    with connection(g.db_role) as db:
        row = found(fetch_one(db, JUGADOR + ' WHERE ci = %s', (ci,)), 'Jugador no encontrado.')
        row['equipos'] = fetch_all(db, '''
            SELECT ejt.id_torneo, ejt.id_equipo, e.nombre AS equipo, ejt.numero_camiseta
              FROM equipo_jugador_torneo ejt JOIN equipo e ON e.id_equipo = ejt.id_equipo
             WHERE ejt.ci_jugador = %s ORDER BY ejt.id_torneo''', (ci,))
    return jsonify(to_json_value(row))


@bp.get('/jugadores/<int:ci>/suspension')
@api_login_required
def player_suspension(ci):
    """¿Está suspendido el jugador en la fecha N de una edición? (manuales + automáticas)."""
    torneo = query_int('id_torneo', 'Edición')
    fecha = query_int('numero_fecha', 'Número de fecha')
    if torneo is None or fecha is None:
        raise APIError('Indicá id_torneo y numero_fecha.', 400)
    with connection(g.db_role) as db:
        rows = fetch_all(db, '''
            SELECT id_sancion, motivo, numero_fecha_inicio, cantidad_fechas, origen
              FROM v_sanciones
             WHERE ci_jugador = %s AND id_torneo = %s
               AND %s >= numero_fecha_inicio AND %s < numero_fecha_inicio + cantidad_fechas
        ''', (ci, torneo, fecha, fecha))
    return jsonify({'ci_jugador': ci, 'id_torneo': torneo, 'numero_fecha': fecha,
                    'suspendido': bool(rows), 'sanciones': rows})


@bp.post('/jugadores')
@admin_required
def player_create():
    player = validate_player(json_body())
    with connection('administrador') as db:
        execute(db, '''INSERT INTO jugador
            (ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo)
            VALUES (%s, %s, %s, %s, %s, %s, %s)''', tuple(player.values()))
        db.commit()
    return jsonify(player), 201


@bp.patch('/jugadores/<int:ci>')
@admin_required
def player_update(ci):
    payload = json_body()
    # El frontend manda todos los campos; para PATCH parcial recuperamos los restantes.
    with connection('administrador') as db:
        current = found(fetch_one(db, JUGADOR + ' WHERE ci = %s', (ci,)), 'Jugador no encontrado.')
        merged = {**to_json_value(current), **payload, 'ci': ci}
        player = validate_player(merged, expected_ci=ci)
        execute(db, '''UPDATE jugador SET nombre=%s, apellido=%s, email=%s,
                       fecha_nacimiento=%s, id_facultad=%s, tipo=%s WHERE ci=%s''',
                (player['nombre'], player['apellido'], player['email'], player['fecha_nacimiento'],
                 player['id_facultad'], player['tipo'], ci))
        db.commit()
    return jsonify(player)


@bp.delete('/jugadores/<int:ci>')
@admin_required
def player_delete(ci):
    with connection('administrador') as db:
        _, affected = execute(db, 'DELETE FROM jugador WHERE ci=%s', (ci,))
        if not affected:
            raise APIError('Jugador no encontrado.', 404)
        db.commit()
    return ('', 204)
