"""ABM de sanciones disciplinarias y consulta de todas las sanciones (v_sanciones).

Las sanciones por tarjetas no se guardan: v_sanciones_automaticas las deriva de
las tarjetas (id negativo = id de la tarjeta que las originó).
"""
from flask import Blueprint, g, jsonify

from core import APIError, admin_required, api_login_required, found, json_body, query_choice, query_int
from database import connection, execute, fetch_all, fetch_one
from logic import MOTIVOS, ORIGENES, validate_sancion

bp = Blueprint('sanciones', __name__)

SANCION = '''SELECT s.id_sancion, s.ci_jugador, j.nombre, j.apellido, s.id_torneo,
                    ejt.id_equipo, e.nombre AS equipo, s.motivo,
                    s.numero_fecha_inicio, s.cantidad_fechas, s.origen
               FROM v_sanciones s
               JOIN jugador j ON j.ci = s.ci_jugador
               LEFT JOIN equipo_jugador_torneo ejt ON ejt.ci_jugador = s.ci_jugador AND ejt.id_torneo = s.id_torneo
               LEFT JOIN equipo e ON e.id_equipo = ejt.id_equipo'''


def load_manual(db, id_sancion):
    if id_sancion < 0:
        raise APIError('Las sanciones automáticas se derivan de las tarjetas: corregí la tarjeta.', 409)
    return found(fetch_one(db, SANCION + ' WHERE s.id_sancion = %s', (id_sancion,)), 'Sanción no encontrada.')


@bp.get('/sanciones')
@api_login_required
def sanciones_list():
    torneo = query_int('id_torneo', 'Edición')
    ci = query_int('ci_jugador', 'Jugador')
    equipo = query_int('id_equipo', 'Equipo')
    motivo = query_choice('motivo', MOTIVOS, 'Motivo')
    origen = query_choice('origen', ORIGENES, 'Origen')
    with connection(g.db_role) as db:
        rows = fetch_all(db, SANCION + '''
             WHERE (%s IS NULL OR s.id_torneo = %s) AND (%s IS NULL OR s.ci_jugador = %s)
               AND (%s IS NULL OR ejt.id_equipo = %s) AND (%s IS NULL OR s.motivo = %s)
               AND (%s IS NULL OR s.origen = %s)
             ORDER BY s.id_torneo, s.numero_fecha_inicio, j.apellido''',
            (torneo, torneo, ci, ci, equipo, equipo, motivo, motivo, origen, origen))
    return jsonify(rows)


@bp.get('/sanciones/<int(signed=True):id_sancion>')
@api_login_required
def sancion_detail(id_sancion):
    with connection(g.db_role) as db:
        row = fetch_one(db, SANCION + ' WHERE s.id_sancion = %s', (id_sancion,))
    return jsonify(found(row, 'Sanción no encontrada.'))


@bp.post('/sanciones')
@admin_required
def sancion_create():
    data = validate_sancion(json_body())
    with connection('administrador') as db:
        # bi_sancion -> validar_sancion: jugador inscripto y sin planillas en las fechas sancionadas.
        new_id, _ = execute(db, '''INSERT INTO sancion_jugador
            (ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas, origen)
            VALUES (%s, %s, 'disciplinaria', %s, %s, 'manual')''',
            (data['ci_jugador'], data['id_torneo'], data['numero_fecha_inicio'], data['cantidad_fechas']))
        db.commit()
        row = load_manual(db, new_id)
    return jsonify(row), 201


@bp.patch('/sanciones/<int(signed=True):id_sancion>')
@admin_required
def sancion_update(id_sancion):
    payload = json_body()
    with connection('administrador') as db:
        data = validate_sancion({**load_manual(db, id_sancion), **payload})
        execute(db, '''UPDATE sancion_jugador SET ci_jugador = %s, id_torneo = %s,
                              numero_fecha_inicio = %s, cantidad_fechas = %s
                        WHERE id_sancion = %s''',
                (data['ci_jugador'], data['id_torneo'], data['numero_fecha_inicio'],
                 data['cantidad_fechas'], id_sancion))
        db.commit()
        row = load_manual(db, id_sancion)
    return jsonify(row)


@bp.delete('/sanciones/<int(signed=True):id_sancion>')
@admin_required
def sancion_delete(id_sancion):
    with connection('administrador') as db:
        load_manual(db, id_sancion)
        execute(db, 'DELETE FROM sancion_jugador WHERE id_sancion = %s', (id_sancion,))
        db.commit()
    return ('', 204)
