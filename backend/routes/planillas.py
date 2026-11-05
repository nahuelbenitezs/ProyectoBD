"""Planilla de partido, goles y tarjetas: operaciones del administrador y del planillero.

Usan la cuenta MySQL del rol autenticado, de modo que el planillero opera con
permisos limitados a planilla_partido, gol y tarjeta. Los triggers controlan el
plazo de 48 horas, el plantel y las suspensiones.
"""
from flask import Blueprint, g, jsonify

from core import APIError, api_login_required, found, json_body
from database import connection, execute, fetch_all, fetch_one, to_json_value
from logic import validate_gol, validate_participante, validate_planilla, validate_tarjeta

bp = Blueprint('planillas', __name__)

PLANILLA = '''SELECT pp.id_partido, pp.ci_jugador, j.nombre, j.apellido, pp.id_equipo, e.nombre AS equipo
                FROM planilla_partido pp
                JOIN jugador j ON j.ci = pp.ci_jugador
                JOIN equipo e ON e.id_equipo = pp.id_equipo'''
GOL = '''SELECT g.id_gol, g.id_partido, g.ci_jugador, j.nombre, j.apellido, pp.id_equipo, g.minuto, g.autogol
           FROM gol g
           JOIN jugador j ON j.ci = g.ci_jugador
           JOIN planilla_partido pp ON pp.id_partido = g.id_partido AND pp.ci_jugador = g.ci_jugador'''
TARJETA = '''SELECT t.id_tarjeta, t.id_partido, t.ci_jugador, j.nombre, j.apellido, pp.id_equipo, t.minuto, t.color
               FROM tarjeta t
               JOIN jugador j ON j.ci = t.ci_jugador
               JOIN planilla_partido pp ON pp.id_partido = t.id_partido AND pp.ci_jugador = t.ci_jugador'''


def load_partido(db, id_partido):
    return found(fetch_one(db, '''SELECT id_partido, id_torneo, numero_fecha, id_equipo_local,
                                         id_equipo_visitante, estado FROM partido WHERE id_partido = %s''',
                           (id_partido,)), 'Partido no encontrado.')


def load_planilla(db, id_partido):
    return fetch_all(db, PLANILLA + ' WHERE pp.id_partido = %s ORDER BY e.nombre, j.apellido', (id_partido,))


@bp.get('/partidos/<int:id_partido>/habilitados')
@api_login_required
def habilitados(id_partido):
    """Planteles de ambos equipos indicando quién está suspendido para esa fecha."""
    with connection(g.db_role) as db:
        load_partido(db, id_partido)
        rows = fetch_all(db, '''
            SELECT ejt.id_equipo, e.nombre AS equipo, j.ci AS ci_jugador, j.nombre, j.apellido,
                   ejt.numero_camiseta,
                   EXISTS (SELECT 1 FROM v_sanciones s
                            WHERE s.ci_jugador = j.ci AND s.id_torneo = p.id_torneo
                              AND p.numero_fecha >= s.numero_fecha_inicio
                              AND p.numero_fecha < s.numero_fecha_inicio + s.cantidad_fechas) AS suspendido,
                   EXISTS (SELECT 1 FROM planilla_partido pp
                            WHERE pp.id_partido = p.id_partido AND pp.ci_jugador = j.ci) AS en_planilla
              FROM partido p
              JOIN equipo_jugador_torneo ejt
                ON ejt.id_torneo = p.id_torneo AND ejt.id_equipo IN (p.id_equipo_local, p.id_equipo_visitante)
              JOIN equipo e ON e.id_equipo = ejt.id_equipo
              JOIN jugador j ON j.ci = ejt.ci_jugador
             WHERE p.id_partido = %s
             ORDER BY e.nombre, ejt.numero_camiseta''', (id_partido,))
    return jsonify([{**r, 'suspendido': bool(r['suspendido']), 'en_planilla': bool(r['en_planilla'])}
                    for r in rows])


@bp.get('/partidos/<int:id_partido>/planilla')
@api_login_required
def planilla_list(id_partido):
    with connection(g.db_role) as db:
        load_partido(db, id_partido)
        rows = load_planilla(db, id_partido)
    return jsonify(rows)


@bp.put('/partidos/<int:id_partido>/planilla')
@api_login_required
def planilla_replace(id_partido):
    """Reemplaza la planilla completa en una única transacción (ROLLBACK ante cualquier rechazo)."""
    nuevos = {p['ci_jugador']: p['id_equipo'] for p in validate_planilla(json_body())}
    with connection(g.db_role) as db:
        load_partido(db, id_partido)
        actuales = {r['ci_jugador']: r['id_equipo'] for r in fetch_all(
            db, 'SELECT ci_jugador, id_equipo FROM planilla_partido WHERE id_partido = %s', (id_partido,))}
        quitar = [ci for ci in actuales if ci not in nuevos or nuevos[ci] != actuales[ci]]
        if quitar:
            con_eventos = fetch_all(db, f'''
                SELECT ci_jugador FROM gol WHERE id_partido = %s AND ci_jugador IN ({', '.join(['%s'] * len(quitar))})
                UNION
                SELECT ci_jugador FROM tarjeta WHERE id_partido = %s AND ci_jugador IN ({', '.join(['%s'] * len(quitar))})
            ''', (id_partido, *quitar, id_partido, *quitar))
            if con_eventos:
                raise APIError('No se puede quitar de la planilla a un jugador con goles o tarjetas registrados.', 409)
        for ci in quitar:
            execute(db, 'DELETE FROM planilla_partido WHERE id_partido = %s AND ci_jugador = %s', (id_partido, ci))
        for ci, equipo in nuevos.items():
            if ci not in actuales or ci in quitar:
                execute(db, 'INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES (%s, %s, %s)',
                        (id_partido, ci, equipo))
        db.commit()
        rows = load_planilla(db, id_partido)
    return jsonify(rows)


@bp.post('/partidos/<int:id_partido>/planilla')
@api_login_required
def planilla_add(id_partido):
    data = validate_participante(json_body())
    with connection(g.db_role) as db:
        load_partido(db, id_partido)
        execute(db, 'INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES (%s, %s, %s)',
                (id_partido, data['ci_jugador'], data['id_equipo']))
        db.commit()
        row = fetch_one(db, PLANILLA + ' WHERE pp.id_partido = %s AND pp.ci_jugador = %s',
                        (id_partido, data['ci_jugador']))
    return jsonify(row), 201


@bp.delete('/partidos/<int:id_partido>/planilla/<int:ci>')
@api_login_required
def planilla_remove(id_partido, ci):
    with connection(g.db_role) as db:
        _, affected = execute(db, 'DELETE FROM planilla_partido WHERE id_partido = %s AND ci_jugador = %s',
                              (id_partido, ci))
        if not affected:
            raise APIError('El jugador no figura en la planilla de ese partido.', 404)
        db.commit()
    return ('', 204)


@bp.get('/partidos/<int:id_partido>/goles')
@api_login_required
def goles_list(id_partido):
    with connection(g.db_role) as db:
        load_partido(db, id_partido)
        rows = fetch_all(db, GOL + ' WHERE g.id_partido = %s ORDER BY g.minuto, g.id_gol', (id_partido,))
    return jsonify([{**r, 'autogol': bool(r['autogol'])} for r in rows])


@bp.post('/partidos/<int:id_partido>/goles')
@api_login_required
def gol_create(id_partido):
    data = validate_gol(json_body())
    with connection(g.db_role) as db:
        load_partido(db, id_partido)
        # La FK a planilla_partido impide goles de jugadores fuera de la planilla.
        new_id, _ = execute(db, 'INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES (%s, %s, %s, %s)',
                            (id_partido, data['ci_jugador'], data['minuto'], data['autogol']))
        db.commit()
    return jsonify({'id_gol': new_id, 'id_partido': id_partido, **data}), 201


@bp.patch('/partidos/<int:id_partido>/goles/<int:id_gol>')
@api_login_required
def gol_update(id_partido, id_gol):
    payload = json_body()
    with connection(g.db_role) as db:
        current = found(fetch_one(db, 'SELECT ci_jugador, minuto, autogol FROM gol WHERE id_gol = %s AND id_partido = %s',
                                  (id_gol, id_partido)), 'Gol no encontrado en ese partido.')
        data = validate_gol({**current, **payload})
        execute(db, 'UPDATE gol SET ci_jugador = %s, minuto = %s, autogol = %s WHERE id_gol = %s',
                (data['ci_jugador'], data['minuto'], data['autogol'], id_gol))
        db.commit()
    return jsonify({'id_gol': id_gol, 'id_partido': id_partido, **data})


@bp.delete('/partidos/<int:id_partido>/goles/<int:id_gol>')
@api_login_required
def gol_delete(id_partido, id_gol):
    with connection(g.db_role) as db:
        _, affected = execute(db, 'DELETE FROM gol WHERE id_gol = %s AND id_partido = %s', (id_gol, id_partido))
        if not affected:
            raise APIError('Gol no encontrado en ese partido.', 404)
        db.commit()
    return ('', 204)


@bp.get('/partidos/<int:id_partido>/tarjetas')
@api_login_required
def tarjetas_list(id_partido):
    with connection(g.db_role) as db:
        load_partido(db, id_partido)
        rows = fetch_all(db, TARJETA + ' WHERE t.id_partido = %s ORDER BY t.minuto, t.id_tarjeta', (id_partido,))
    return jsonify(rows)


@bp.post('/partidos/<int:id_partido>/tarjetas')
@api_login_required
def tarjeta_create(id_partido):
    data = validate_tarjeta(json_body())
    with connection(g.db_role) as db:
        load_partido(db, id_partido)
        # La sanción automática (roja o 3.ª amarilla) aparece sola en v_sanciones.
        new_id, _ = execute(db, 'INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES (%s, %s, %s, %s)',
                            (id_partido, data['ci_jugador'], data['minuto'], data['color']))
        db.commit()
    return jsonify({'id_tarjeta': new_id, 'id_partido': id_partido, **data}), 201


@bp.patch('/partidos/<int:id_partido>/tarjetas/<int:id_tarjeta>')
@api_login_required
def tarjeta_update(id_partido, id_tarjeta):
    payload = json_body()
    with connection(g.db_role) as db:
        current = found(fetch_one(db, '''SELECT ci_jugador, minuto, color FROM tarjeta
                                          WHERE id_tarjeta = %s AND id_partido = %s''', (id_tarjeta, id_partido)),
                        'Tarjeta no encontrada en ese partido.')
        data = validate_tarjeta({**current, **payload})
        execute(db, 'UPDATE tarjeta SET ci_jugador = %s, minuto = %s, color = %s WHERE id_tarjeta = %s',
                (data['ci_jugador'], data['minuto'], data['color'], id_tarjeta))
        db.commit()
    return jsonify({'id_tarjeta': id_tarjeta, 'id_partido': id_partido, **data})


@bp.delete('/partidos/<int:id_partido>/tarjetas/<int:id_tarjeta>')
@api_login_required
def tarjeta_delete(id_partido, id_tarjeta):
    with connection(g.db_role) as db:
        _, affected = execute(db, 'DELETE FROM tarjeta WHERE id_tarjeta = %s AND id_partido = %s',
                              (id_tarjeta, id_partido))
        if not affected:
            raise APIError('Tarjeta no encontrada en ese partido.', 404)
        db.commit()
    return ('', 204)


@bp.get('/partidos/<int:id_partido>/eventos')
@api_login_required
def eventos(id_partido):
    """Planilla, goles y tarjetas de un partido en una sola llamada."""
    with connection(g.db_role) as db:
        partido = load_partido(db, id_partido)
        data = {
            'partido': partido,
            'planilla': load_planilla(db, id_partido),
            'goles': fetch_all(db, GOL + ' WHERE g.id_partido = %s ORDER BY g.minuto', (id_partido,)),
            'tarjetas': fetch_all(db, TARJETA + ' WHERE t.id_partido = %s ORDER BY t.minuto', (id_partido,)),
        }
    return jsonify(to_json_value(data))
