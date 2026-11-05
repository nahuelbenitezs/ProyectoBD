"""ABM de facultades y turnos, y disponibilidad de canchas por día."""
from flask import Blueprint, g, jsonify, request

from core import APIError, admin_required, api_login_required, found, json_body, query_int
from database import connection, execute, fetch_all, fetch_one, to_json_value
from logic import required_date, validate_facultad, validate_turno

bp = Blueprint('catalogos', __name__)

FACULTAD = 'SELECT id_facultad, nombre FROM facultad'
TURNO = 'SELECT id_turno, hora_inicio, hora_fin FROM turno'


@bp.get('/facultades')
@api_login_required
def facultades_list():
    with connection(g.db_role) as db:
        rows = fetch_all(db, FACULTAD + ' ORDER BY nombre')
    return jsonify(rows)


@bp.get('/facultades/<int:id_facultad>')
@api_login_required
def facultad_detail(id_facultad):
    with connection(g.db_role) as db:
        row = fetch_one(db, FACULTAD + ' WHERE id_facultad = %s', (id_facultad,))
    return jsonify(found(row, 'Facultad no encontrada.'))


@bp.post('/facultades')
@admin_required
def facultad_create():
    data = validate_facultad(json_body())
    with connection('administrador') as db:
        new_id, _ = execute(db, 'INSERT INTO facultad (nombre) VALUES (%s)', (data['nombre'],))
        db.commit()
    return jsonify({'id_facultad': new_id, **data}), 201


@bp.patch('/facultades/<int:id_facultad>')
@admin_required
def facultad_update(id_facultad):
    data = validate_facultad(json_body())
    with connection('administrador') as db:
        found(fetch_one(db, FACULTAD + ' WHERE id_facultad = %s', (id_facultad,)), 'Facultad no encontrada.')
        execute(db, 'UPDATE facultad SET nombre = %s WHERE id_facultad = %s', (data['nombre'], id_facultad))
        db.commit()
    return jsonify({'id_facultad': id_facultad, **data})


@bp.delete('/facultades/<int:id_facultad>')
@admin_required
def facultad_delete(id_facultad):
    with connection('administrador') as db:
        _, affected = execute(db, 'DELETE FROM facultad WHERE id_facultad = %s', (id_facultad,))
        if not affected:
            raise APIError('Facultad no encontrada.', 404)
        db.commit()
    return ('', 204)


@bp.get('/turnos')
@api_login_required
def turnos_list():
    with connection(g.db_role) as db:
        rows = fetch_all(db, TURNO + ' ORDER BY hora_inicio')
    return jsonify(to_json_value(rows))


@bp.get('/turnos/<int:id_turno>')
@api_login_required
def turno_detail(id_turno):
    with connection(g.db_role) as db:
        row = fetch_one(db, TURNO + ' WHERE id_turno = %s', (id_turno,))
    return jsonify(to_json_value(found(row, 'Turno no encontrado.')))


@bp.post('/turnos')
@admin_required
def turno_create():
    data = validate_turno(json_body())
    with connection('administrador') as db:
        new_id, _ = execute(db, 'INSERT INTO turno (hora_inicio, hora_fin) VALUES (%s, %s)',
                            (data['hora_inicio'], data['hora_fin']))
        db.commit()
    return jsonify({'id_turno': new_id, **data}), 201


@bp.patch('/turnos/<int:id_turno>')
@admin_required
def turno_update(id_turno):
    data = validate_turno(json_body())
    with connection('administrador') as db:
        found(fetch_one(db, TURNO + ' WHERE id_turno = %s', (id_turno,)), 'Turno no encontrado.')
        execute(db, 'UPDATE turno SET hora_inicio = %s, hora_fin = %s WHERE id_turno = %s',
                (data['hora_inicio'], data['hora_fin'], id_turno))
        db.commit()
    return jsonify({'id_turno': id_turno, **data})


@bp.delete('/turnos/<int:id_turno>')
@admin_required
def turno_delete(id_turno):
    with connection('administrador') as db:
        _, affected = execute(db, 'DELETE FROM turno WHERE id_turno = %s', (id_turno,))
        if not affected:
            raise APIError('Turno no encontrado.', 404)
        db.commit()
    return ('', 204)


@bp.get('/canchas/disponibles')
@api_login_required
def canchas_disponibles():
    """Combinaciones cancha + turno libres en un día (postergados y cancelados liberan la reserva)."""
    dia = required_date(request.args.get('dia'), 'Día').isoformat()
    complejo = query_int('id_complejo', 'Complejo')
    with connection(g.db_role) as db:
        rows = fetch_all(db, '''
            SELECT c.id_complejo, co.nombre AS complejo, c.nombre_cancha, c.superficie, c.techada,
                   t.id_turno, t.hora_inicio, t.hora_fin
              FROM cancha c
              JOIN complejo co ON co.id_complejo = c.id_complejo
             CROSS JOIN turno t
             WHERE (%s IS NULL OR c.id_complejo = %s)
               AND NOT EXISTS (
                   SELECT 1 FROM partido p
                    WHERE p.dia = %s AND p.id_turno = t.id_turno
                      AND p.nombre_cancha = c.nombre_cancha AND p.id_complejo = c.id_complejo
                      AND p.estado NOT IN ('cancelado', 'postergado'))
             ORDER BY t.hora_inicio, co.nombre, c.nombre_cancha
        ''', (complejo, complejo, dia))
    return jsonify(to_json_value(rows))
