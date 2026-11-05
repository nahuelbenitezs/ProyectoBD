"""Gestión de ediciones del torneo y sus estados."""
from flask import Blueprint, g, jsonify

from core import APIError, admin_required, api_login_required, found, json_body, query_choice
from database import connection, execute, fetch_all, fetch_one, to_json_value
from logic import ESTADOS_TORNEO, ValidationError, validate_torneo, validate_torneo_transition

bp = Blueprint('torneos', __name__)

TORNEO = '''SELECT id_torneo, nombre, anio, semestre, fecha_inicio, fecha_fin, estado
              FROM torneo'''


@bp.get('/torneos')
@api_login_required
def torneos_list():
    estado = query_choice('estado', ESTADOS_TORNEO, 'Estado')
    with connection(g.db_role) as db:
        rows = fetch_all(db, TORNEO + ' WHERE (%s IS NULL OR estado = %s) ORDER BY anio DESC, semestre DESC',
                         (estado, estado))
    return jsonify(to_json_value(rows))


@bp.get('/torneos/<int:id_torneo>')
@api_login_required
def torneo_detail(id_torneo):
    with connection(g.db_role) as db:
        row = fetch_one(db, TORNEO + ' WHERE id_torneo = %s', (id_torneo,))
    return jsonify(to_json_value(found(row, 'Edición no encontrada.')))


@bp.get('/torneos/<int:id_torneo>/equipos')
@api_login_required
def torneo_equipos(id_torneo):
    with connection(g.db_role) as db:
        found(fetch_one(db, TORNEO + ' WHERE id_torneo = %s', (id_torneo,)), 'Edición no encontrada.')
        rows = fetch_all(db, '''
            SELECT e.id_equipo, e.nombre, e.id_facultad, f.nombre AS facultad, e.ci_capitan,
                   (SELECT COUNT(*) FROM equipo_jugador_torneo ejt
                     WHERE ejt.id_equipo = e.id_equipo AND ejt.id_torneo = e.id_torneo) AS cantidad_jugadores
              FROM equipo e JOIN facultad f ON f.id_facultad = e.id_facultad
             WHERE e.id_torneo = %s ORDER BY e.nombre''', (id_torneo,))
    return jsonify(rows)


@bp.get('/torneos/<int:id_torneo>/fechas')
@api_login_required
def torneo_fechas(id_torneo):
    with connection(g.db_role) as db:
        found(fetch_one(db, TORNEO + ' WHERE id_torneo = %s', (id_torneo,)), 'Edición no encontrada.')
        rows = fetch_all(db, '''
            SELECT numero_fecha, MIN(dia) AS primer_dia, MAX(dia) AS ultimo_dia,
                   COUNT(*) AS partidos,
                   SUM(estado = 'jugado') AS jugados, SUM(estado = 'programado') AS programados,
                   SUM(estado = 'postergado') AS postergados, SUM(estado = 'cancelado') AS cancelados
              FROM partido WHERE id_torneo = %s
             GROUP BY numero_fecha ORDER BY numero_fecha''', (id_torneo,))
    return jsonify(to_json_value(rows))


@bp.post('/torneos')
@admin_required
def torneo_create():
    data = validate_torneo(json_body())
    if data['estado'] != 'inscripción':
        raise ValidationError('Una edición nueva debe comenzar en inscripción.')
    with connection('administrador') as db:
        new_id, _ = execute(db, '''INSERT INTO torneo
            (nombre, anio, semestre, fecha_inicio, fecha_fin, estado) VALUES (%s, %s, %s, %s, %s, %s)''',
            tuple(data.values()))
        db.commit()
    return jsonify({'id_torneo': new_id, **data}), 201


@bp.patch('/torneos/<int:id_torneo>')
@admin_required
def torneo_update(id_torneo):
    payload = json_body()
    with connection('administrador') as db:
        current = found(fetch_one(db, TORNEO + ' WHERE id_torneo = %s', (id_torneo,)), 'Edición no encontrada.')
        data = validate_torneo({**to_json_value(current), **payload})
        validate_torneo_transition(current['estado'], data['estado'])
        # El trigger bu_torneo verifica planteles completos al salir de inscripción.
        execute(db, '''UPDATE torneo SET nombre=%s, anio=%s, semestre=%s, fecha_inicio=%s,
                       fecha_fin=%s, estado=%s WHERE id_torneo=%s''', (*data.values(), id_torneo))
        db.commit()
    return jsonify({'id_torneo': id_torneo, **data})


@bp.delete('/torneos/<int:id_torneo>')
@admin_required
def torneo_delete(id_torneo):
    with connection('administrador') as db:
        _, affected = execute(db, 'DELETE FROM torneo WHERE id_torneo = %s', (id_torneo,))
        if not affected:
            raise APIError('Edición no encontrada.', 404)
        db.commit()
    return ('', 204)
