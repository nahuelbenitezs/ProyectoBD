"""Carga inicial del frontend y los 12 reportes (vistas SQL)."""
from flask import Blueprint, g, jsonify, request

from core import APIError, api_login_required
from database import connection, fetch_all, to_json_value
from logic import positive_int
from reports import REPORTS, get_report

bp = Blueprint('reportes', __name__)

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


@bp.get('/bootstrap')
@api_login_required
def bootstrap():
    # Leer con los permisos SQL del rol real, no siempre como administrador.
    with connection(g.db_role) as db:
        data = {key: fetch_all(db, sql) for key, sql in BOOTSTRAP_QUERIES.items()}
    return jsonify(to_json_value(data))


@bp.get('/reportes')
@api_login_required
def reports_index():
    return jsonify(sorted(REPORTS))


@bp.get('/reportes/<slug>')
@api_login_required
def reports(slug):
    if slug not in REPORTS:
        raise APIError('Reporte no encontrado.', 404)
    torneo = positive_int(request.args.get('id_torneo'), 'Edición')
    with connection(g.db_role) as db:
        rows = get_report(db, slug, torneo)
    return jsonify(to_json_value(rows))
