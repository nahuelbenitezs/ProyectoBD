"""Reportes basados en las vistas SQL del obligatorio, no recalculados en Python."""
from database import fetch_all

# Solo nombres fijos: ningún nombre de tabla viene del usuario.
REPORTS = {
    'posiciones': ('v_reporte_01_posiciones', 'puntos DESC, diferencia_goles DESC, goles_favor DESC, equipo'),
    'goleadores': ('v_reporte_02_goleadores', 'posicion'),
    'fair-play': ('v_reporte_03_fair_play', 'puntos_fair_play ASC, amarillas, rojas, equipo'),
    'promedio-goles': ('v_reporte_04_promedio_goles', 'alcance, numero_fecha'),
    'uso-espacios': ('v_reporte_05_uso_espacios', 'tipo_recurso, partidos_jugados DESC, recurso'),
    'jugadores-facultad': ('v_reporte_06_jugadores_facultad_tipo', 'facultad, tipo'),
    'sin-participacion': ('v_reporte_07_nunca_participaron', 'equipo, apellido, nombre'),
    'sanciones': ('v_reporte_08_sanciones_equipo', 'equipo, motivo'),
    'estados': ('v_reporte_09_estados_partidos', 'id_torneo'),
    'local-visitante': ('v_reporte_10_local_visitante', 'equipo'),
    'disciplina': ('v_reporte_11_disciplina_jugadores', 'indice_disciplina DESC, fechas_suspension DESC, apellido'),
    'goles-tramos': ('v_reporte_12_goles_por_tramo', 'tramo'),
}


def adapt_rows(slug, rows):
    if slug in ('goleadores', 'sin-participacion', 'disciplina'):
        return [{**r, 'nombre_completo': f"{r['nombre']} {r['apellido']}"} for r in rows]
    if slug == 'promedio-goles':
        return [{**r, 'fecha': f"Fecha {r['numero_fecha']}" if r['alcance'] == 'fecha'
                 else 'Toda la edición'} for r in rows]
    if slug == 'estados':
        # La vista SQL tiene una columna por estado; la tabla UI requiere 4 filas.
        if not rows:
            return []
        r = rows[0]
        return [
            {'estado': estado, 'cantidad': r[plural], 'porcentaje': r['porcentaje_' + plural]}
            for estado, plural in (
                ('jugado', 'jugados'), ('postergado', 'postergados'),
                ('cancelado', 'cancelados'), ('programado', 'programados')
            )
        ]
    return rows


def get_report(db, slug, torneo):
    view, order = REPORTS[slug]
    if slug == 'jugadores-facultad':
        # Esta vista de la letra mide el padrón global, NO una edición particular.
        rows = fetch_all(db, f'SELECT * FROM {view} ORDER BY {order}')
    else:
        rows = fetch_all(db, f'SELECT * FROM {view} WHERE id_torneo = %s ORDER BY {order}', (torneo,))
    return adapt_rows(slug, rows)
