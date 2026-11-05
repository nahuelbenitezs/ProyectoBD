"""ABM de partidos (fixture), cambios de estado y resultado calculado."""
from flask import Blueprint, g, jsonify

from core import APIError, admin_required, api_login_required, found, json_body, query_choice, query_int
from database import connection, execute, fetch_all, fetch_one, to_json_value
from logic import ESTADOS_PARTIDO, choice, validate_partido

bp = Blueprint('partidos', __name__)

# El resultado no se guarda: se lee de v_resultado_partido (calculado desde los goles).
PARTIDO = '''SELECT p.id_partido, p.id_torneo, p.numero_fecha,
                    p.id_equipo_local, el.nombre AS equipo_local,
                    p.id_equipo_visitante, ev.nombre AS equipo_visitante,
                    p.dia, p.id_turno, t.hora_inicio, t.hora_fin,
                    p.nombre_cancha, p.id_complejo, co.nombre AS complejo, p.estado,
                    r.goles_local, r.goles_visitante
               FROM partido p
               JOIN equipo el ON el.id_equipo = p.id_equipo_local
               JOIN equipo ev ON ev.id_equipo = p.id_equipo_visitante
               JOIN turno t ON t.id_turno = p.id_turno
               JOIN complejo co ON co.id_complejo = p.id_complejo
               LEFT JOIN v_resultado_partido r ON r.id_partido = p.id_partido'''
CAMPOS = ('id_torneo', 'numero_fecha', 'id_equipo_local', 'id_equipo_visitante',
          'dia', 'id_turno', 'nombre_cancha', 'id_complejo', 'estado')


def load_partido(db, id_partido):
    return found(fetch_one(db, PARTIDO + ' WHERE p.id_partido = %s', (id_partido,)), 'Partido no encontrado.')


@bp.get('/partidos')
@api_login_required
def partidos_list():
    torneo = query_int('id_torneo', 'Edición')
    fecha = query_int('numero_fecha', 'Número de fecha')
    equipo = query_int('id_equipo', 'Equipo')
    estado = query_choice('estado', ESTADOS_PARTIDO, 'Estado')
    with connection(g.db_role) as db:
        rows = fetch_all(db, PARTIDO + '''
             WHERE (%s IS NULL OR p.id_torneo = %s)
               AND (%s IS NULL OR p.numero_fecha = %s)
               AND (%s IS NULL OR %s IN (p.id_equipo_local, p.id_equipo_visitante))
               AND (%s IS NULL OR p.estado = %s)
             ORDER BY p.id_torneo, p.numero_fecha, p.dia, t.hora_inicio, p.id_partido''',
            (torneo, torneo, fecha, fecha, equipo, equipo, estado, estado))
    return jsonify(to_json_value(rows))


@bp.get('/partidos/<int:id_partido>')
@api_login_required
def partido_detail(id_partido):
    with connection(g.db_role) as db:
        row = load_partido(db, id_partido)
    return jsonify(to_json_value(row))


@bp.get('/partidos/<int:id_partido>/resultado')
@api_login_required
def partido_resultado(id_partido):
    with connection(g.db_role) as db:
        partido = load_partido(db, id_partido)
        if partido['estado'] != 'jugado':
            raise APIError('El partido todavía no se jugó: no tiene resultado.', 409)
        goles = fetch_all(db, '''
            SELECT g.id_gol, g.ci_jugador, j.nombre, j.apellido, pp.id_equipo, g.minuto, g.autogol
              FROM gol g
              JOIN planilla_partido pp ON pp.id_partido = g.id_partido AND pp.ci_jugador = g.ci_jugador
              JOIN jugador j ON j.ci = g.ci_jugador
             WHERE g.id_partido = %s ORDER BY g.minuto, g.id_gol''', (id_partido,))
    return jsonify(to_json_value({
        'id_partido': id_partido,
        'equipo_local': partido['equipo_local'], 'goles_local': partido['goles_local'],
        'equipo_visitante': partido['equipo_visitante'], 'goles_visitante': partido['goles_visitante'],
        'goles': goles,
    }))


@bp.post('/partidos')
@admin_required
def partido_create():
    data = validate_partido(json_body())
    with connection('administrador') as db:
        # bi_partido -> validar_programacion: edición, planteles, rivales, fecha y cancha libres.
        new_id, _ = execute(db, f'''INSERT INTO partido ({', '.join(CAMPOS)})
                                    VALUES ({', '.join(['%s'] * len(CAMPOS))})''',
                            tuple(data[c] for c in CAMPOS))
        db.commit()
        row = load_partido(db, new_id)
    return jsonify(to_json_value(row)), 201


@bp.patch('/partidos/<int:id_partido>')
@admin_required
def partido_update(id_partido):
    payload = json_body()
    with connection('administrador') as db:
        current = load_partido(db, id_partido)
        if current['estado'] == 'jugado':
            raise APIError('Un partido jugado no puede modificarse; corregí la planilla, goles o tarjetas.', 409)
        data = validate_partido({**to_json_value(current), **payload})
        execute(db, f'''UPDATE partido SET {', '.join(c + ' = %s' for c in CAMPOS)}
                         WHERE id_partido = %s''', (*(data[c] for c in CAMPOS), id_partido))
        db.commit()
        row = load_partido(db, id_partido)
    return jsonify(to_json_value(row))


@bp.patch('/partidos/<int:id_partido>/estado')
@admin_required
def partido_estado(id_partido):
    """Postergar, cancelar, reprogramar o marcar jugado (solo después del turno)."""
    estado = choice(json_body().get('estado'), ESTADOS_PARTIDO,
                    'El estado debe ser programado, jugado, postergado o cancelado.')
    with connection('administrador') as db:
        current = load_partido(db, id_partido)
        if current['estado'] == 'jugado':
            raise APIError('Un partido jugado no puede cambiar de estado.', 409)
        execute(db, 'UPDATE partido SET estado = %s WHERE id_partido = %s', (estado, id_partido))
        db.commit()
        row = load_partido(db, id_partido)
    return jsonify(to_json_value(row))


@bp.delete('/partidos/<int:id_partido>')
@admin_required
def partido_delete(id_partido):
    with connection('administrador') as db:
        current = load_partido(db, id_partido)
        if current['estado'] == 'jugado':
            raise APIError('No se puede eliminar un partido jugado.', 409)
        execute(db, 'DELETE FROM partido WHERE id_partido = %s', (id_partido,))
        db.commit()
    return ('', 204)
