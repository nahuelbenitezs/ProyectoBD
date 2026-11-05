"""ABM de complejos deportivos y de sus canchas."""
from flask import Blueprint, g, jsonify

from core import APIError, admin_required, api_login_required, found, json_body, query_int
from database import connection, execute, fetch_all, fetch_one
from logic import validate_cancha, validate_complejo

bp = Blueprint('complejos', __name__)

COMPLEJO = 'SELECT id_complejo, nombre, direccion, departamento FROM complejo'
CANCHA = '''SELECT c.nombre_cancha, c.id_complejo, co.nombre AS complejo, c.superficie, c.techada
              FROM cancha c JOIN complejo co ON co.id_complejo = c.id_complejo'''


def load_complejo(db, id_complejo):
    return found(fetch_one(db, COMPLEJO + ' WHERE id_complejo = %s', (id_complejo,)), 'Complejo no encontrado.')


def load_cancha(db, id_complejo, nombre):
    return found(fetch_one(db, CANCHA + ' WHERE c.id_complejo = %s AND c.nombre_cancha = %s',
                           (id_complejo, nombre)), 'Cancha no encontrada.')


@bp.get('/complejos')
@api_login_required
def complejos_list():
    with connection(g.db_role) as db:
        rows = fetch_all(db, COMPLEJO + ' ORDER BY nombre')
    return jsonify(rows)


@bp.get('/complejos/<int:id_complejo>')
@api_login_required
def complejo_detail(id_complejo):
    with connection(g.db_role) as db:
        row = load_complejo(db, id_complejo)
        row['canchas'] = fetch_all(db, CANCHA + ' WHERE c.id_complejo = %s ORDER BY c.nombre_cancha',
                                   (id_complejo,))
    return jsonify(row)


@bp.post('/complejos')
@admin_required
def complejo_create():
    data = validate_complejo(json_body())
    with connection('administrador') as db:
        new_id, _ = execute(db, 'INSERT INTO complejo (nombre, direccion, departamento) VALUES (%s, %s, %s)',
                            tuple(data.values()))
        db.commit()
    return jsonify({'id_complejo': new_id, **data}), 201


@bp.patch('/complejos/<int:id_complejo>')
@admin_required
def complejo_update(id_complejo):
    payload = json_body()
    with connection('administrador') as db:
        data = validate_complejo({**load_complejo(db, id_complejo), **payload})
        execute(db, 'UPDATE complejo SET nombre = %s, direccion = %s, departamento = %s WHERE id_complejo = %s',
                (*data.values(), id_complejo))
        db.commit()
    return jsonify({'id_complejo': id_complejo, **data})


@bp.delete('/complejos/<int:id_complejo>')
@admin_required
def complejo_delete(id_complejo):
    with connection('administrador') as db:
        _, affected = execute(db, 'DELETE FROM complejo WHERE id_complejo = %s', (id_complejo,))
        if not affected:
            raise APIError('Complejo no encontrado.', 404)
        db.commit()
    return ('', 204)


@bp.get('/canchas')
@api_login_required
def canchas_list():
    complejo = query_int('id_complejo', 'Complejo')
    with connection(g.db_role) as db:
        rows = fetch_all(db, CANCHA + ' WHERE (%s IS NULL OR c.id_complejo = %s) ORDER BY co.nombre, c.nombre_cancha',
                         (complejo, complejo))
    return jsonify(rows)


@bp.get('/complejos/<int:id_complejo>/canchas')
@api_login_required
def complejo_canchas(id_complejo):
    with connection(g.db_role) as db:
        load_complejo(db, id_complejo)
        rows = fetch_all(db, CANCHA + ' WHERE c.id_complejo = %s ORDER BY c.nombre_cancha', (id_complejo,))
    return jsonify(rows)


@bp.get('/complejos/<int:id_complejo>/canchas/<nombre>')
@api_login_required
def cancha_detail(id_complejo, nombre):
    with connection(g.db_role) as db:
        row = load_cancha(db, id_complejo, nombre)
    return jsonify(row)


@bp.post('/complejos/<int:id_complejo>/canchas')
@admin_required
def cancha_create(id_complejo):
    data = validate_cancha(json_body())
    with connection('administrador') as db:
        load_complejo(db, id_complejo)
        execute(db, 'INSERT INTO cancha (nombre_cancha, id_complejo, superficie, techada) VALUES (%s, %s, %s, %s)',
                (data['nombre_cancha'], id_complejo, data['superficie'], data['techada']))
        db.commit()
        row = load_cancha(db, id_complejo, data['nombre_cancha'])
    return jsonify(row), 201


@bp.patch('/complejos/<int:id_complejo>/canchas/<nombre>')
@admin_required
def cancha_update(id_complejo, nombre):
    payload = json_body()
    payload.pop('original_nombre_cancha', None)
    with connection('administrador') as db:
        data = validate_cancha({**load_cancha(db, id_complejo, nombre), **payload})
        # Renombrar falla con 1451 si la cancha ya tiene partidos (FK sin ON UPDATE CASCADE).
        execute(db, '''UPDATE cancha SET nombre_cancha = %s, superficie = %s, techada = %s
                        WHERE id_complejo = %s AND nombre_cancha = %s''',
                (data['nombre_cancha'], data['superficie'], data['techada'], id_complejo, nombre))
        db.commit()
        row = load_cancha(db, id_complejo, data['nombre_cancha'])
    return jsonify(row)


@bp.delete('/complejos/<int:id_complejo>/canchas/<nombre>')
@admin_required
def cancha_delete(id_complejo, nombre):
    with connection('administrador') as db:
        _, affected = execute(db, 'DELETE FROM cancha WHERE id_complejo = %s AND nombre_cancha = %s',
                              (id_complejo, nombre))
        if not affected:
            raise APIError('Cancha no encontrada.', 404)
        db.commit()
    return ('', 204)
