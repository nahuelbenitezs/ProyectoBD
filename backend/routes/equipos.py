"""ABM de equipos y de sus planteles (equipo_jugador_torneo)."""
from flask import Blueprint, g, jsonify

from core import APIError, admin_required, api_login_required, found, json_body, query_int
from database import connection, execute, fetch_all, fetch_one, to_json_value
from logic import ValidationError, int_between, validate_equipo, validate_plantel

bp = Blueprint('equipos', __name__)

EQUIPO = '''SELECT e.id_equipo, e.nombre, e.id_torneo, e.id_facultad, f.nombre AS facultad, e.ci_capitan,
                   (SELECT COUNT(*) FROM equipo_jugador_torneo ejt
                     WHERE ejt.id_equipo = e.id_equipo AND ejt.id_torneo = e.id_torneo) AS cantidad_jugadores
              FROM equipo e JOIN facultad f ON f.id_facultad = e.id_facultad'''
PLANTEL = '''SELECT ejt.id_equipo, ejt.id_torneo, ejt.ci_jugador, j.nombre, j.apellido, j.tipo,
                    ejt.numero_camiseta
               FROM equipo_jugador_torneo ejt JOIN jugador j ON j.ci = ejt.ci_jugador'''


def load_equipo(db, id_equipo):
    return found(fetch_one(db, EQUIPO + ' WHERE e.id_equipo = %s', (id_equipo,)), 'Equipo no encontrado.')


def load_plantel(db, id_equipo):
    return fetch_all(db, PLANTEL + ' WHERE ejt.id_equipo = %s ORDER BY ejt.numero_camiseta', (id_equipo,))


@bp.get('/equipos')
@api_login_required
def equipos_list():
    torneo = query_int('id_torneo', 'Edición')
    facultad = query_int('id_facultad', 'Facultad')
    with connection(g.db_role) as db:
        rows = fetch_all(db, EQUIPO + '''
             WHERE (%s IS NULL OR e.id_torneo = %s) AND (%s IS NULL OR e.id_facultad = %s)
             ORDER BY e.id_torneo, e.nombre''', (torneo, torneo, facultad, facultad))
    return jsonify(rows)


@bp.get('/equipos/<int:id_equipo>')
@api_login_required
def equipo_detail(id_equipo):
    with connection(g.db_role) as db:
        row = load_equipo(db, id_equipo)
        row['plantel'] = load_plantel(db, id_equipo)
    return jsonify(to_json_value(row))


@bp.post('/equipos')
@admin_required
def equipo_create():
    data = validate_equipo(json_body())
    with connection('administrador') as db:
        # Equipo y capitán se insertan en la misma transacción: si falla el plantel, ROLLBACK.
        new_id, _ = execute(db, '''INSERT INTO equipo (nombre, id_torneo, id_facultad, ci_capitan)
                                   VALUES (%s, %s, %s, %s)''',
                            (data['nombre'], data['id_torneo'], data['id_facultad'], data['ci_capitan']))
        execute(db, '''INSERT INTO equipo_jugador_torneo (id_equipo, ci_jugador, id_torneo, numero_camiseta)
                       VALUES (%s, %s, %s, %s)''',
                (new_id, data['ci_capitan'], data['id_torneo'], data['numero_camiseta_capitan']))
        db.commit()
        row = load_equipo(db, new_id)
    return jsonify(row), 201


@bp.patch('/equipos/<int:id_equipo>')
@admin_required
def equipo_update(id_equipo):
    payload = json_body()
    with connection('administrador') as db:
        current = load_equipo(db, id_equipo)
        data = validate_equipo({**current, **payload})
        if data['id_torneo'] != current['id_torneo'] or data['id_facultad'] != current['id_facultad']:
            raise ValidationError('No se puede cambiar la edición o la facultad de un equipo.')
        # bu_equipo exige que el nuevo capitán ya integre el plantel.
        execute(db, 'UPDATE equipo SET nombre = %s, ci_capitan = %s WHERE id_equipo = %s',
                (data['nombre'], data['ci_capitan'], id_equipo))
        db.commit()
        row = load_equipo(db, id_equipo)
    return jsonify(row)


@bp.delete('/equipos/<int:id_equipo>')
@admin_required
def equipo_delete(id_equipo):
    with connection('administrador') as db:
        _, affected = execute(db, 'DELETE FROM equipo WHERE id_equipo = %s', (id_equipo,))
        if not affected:
            raise APIError('Equipo no encontrado.', 404)
        db.commit()
    return ('', 204)


@bp.get('/equipos/<int:id_equipo>/plantel')
@api_login_required
def plantel_list(id_equipo):
    with connection(g.db_role) as db:
        load_equipo(db, id_equipo)
        rows = load_plantel(db, id_equipo)
    return jsonify(rows)


@bp.post('/equipos/<int:id_equipo>/plantel')
@admin_required
def plantel_add(id_equipo):
    data = validate_plantel(json_body())
    with connection('administrador') as db:
        equipo = load_equipo(db, id_equipo)
        # validar_alta_plantel (trigger) controla inscripción, facultad, 10 jugadores y 2 docentes/funcionarios.
        execute(db, '''INSERT INTO equipo_jugador_torneo (id_equipo, ci_jugador, id_torneo, numero_camiseta)
                       VALUES (%s, %s, %s, %s)''',
                (id_equipo, data['ci_jugador'], equipo['id_torneo'], data['numero_camiseta']))
        db.commit()
        row = fetch_one(db, PLANTEL + ' WHERE ejt.id_equipo = %s AND ejt.ci_jugador = %s',
                        (id_equipo, data['ci_jugador']))
    return jsonify(row), 201


@bp.patch('/equipos/<int:id_equipo>/plantel/<int:ci>')
@admin_required
def plantel_update(id_equipo, ci):
    numero = int_between(json_body().get('numero_camiseta'), 'Número de camiseta', 1, 99)
    with connection('administrador') as db:
        found(fetch_one(db, PLANTEL + ' WHERE ejt.id_equipo = %s AND ejt.ci_jugador = %s', (id_equipo, ci)),
              'El jugador no integra ese plantel.')
        execute(db, '''UPDATE equipo_jugador_torneo SET numero_camiseta = %s
                        WHERE id_equipo = %s AND ci_jugador = %s''', (numero, id_equipo, ci))
        db.commit()
        row = fetch_one(db, PLANTEL + ' WHERE ejt.id_equipo = %s AND ejt.ci_jugador = %s', (id_equipo, ci))
    return jsonify(row)


@bp.delete('/equipos/<int:id_equipo>/plantel/<int:ci>')
@admin_required
def plantel_remove(id_equipo, ci):
    with connection('administrador') as db:
        _, affected = execute(db, 'DELETE FROM equipo_jugador_torneo WHERE id_equipo = %s AND ci_jugador = %s',
                              (id_equipo, ci))
        if not affected:
            raise APIError('El jugador no integra ese plantel.', 404)
        db.commit()
    return ('', 204)
