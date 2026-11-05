"""API REST UCU League — Flask + MySQL, sin ORM.

Cada módulo de routes/ expone un ABM con SQL parametrizado directo
(SELECT/INSERT/UPDATE/DELETE). Las reglas de negocio que dependen de varios
registros las imponen los triggers de torneo_ucu_creacion.sql; aquí se
traducen sus mensajes a respuestas HTTP.
"""
import os

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from flask import Flask, jsonify, request  # noqa: E402
from mysql.connector import Error as MySQLError  # noqa: E402

from core import APIError  # noqa: E402
from logic import ValidationError  # noqa: E402
from routes import BLUEPRINTS  # noqa: E402

ALLOWED_ORIGINS = {origin.strip() for origin in os.getenv(
    'CORS_ORIGINS', 'http://localhost:5500,http://127.0.0.1:5500'
).split(',') if origin.strip()}

# Errores de MySQL -> (HTTP, mensaje). 45000 (SIGNAL de triggers) se resuelve aparte.
MYSQL_ERRORS = {
    1062: (409, 'Ya existe un registro con esos datos (valor único repetido).'),
    1451: (409, 'No se puede eliminar o modificar: el registro está vinculado a otros datos.'),
    1452: (409, 'Alguno de los datos referenciados no existe.'),
    1048: (400, 'Falta un dato obligatorio.'),
    1265: (400, 'Algún valor no es válido para el campo.'),
    1292: (400, 'Algún valor de fecha u hora no es válido.'),
    1366: (400, 'Algún valor no es válido para el campo.'),
    3819: (400, 'Los datos no cumplen una restricción de la base de datos.'),
    1142: (403, 'La cuenta de base de datos de tu rol no tiene permiso para esta operación.'),
    1143: (403, 'La cuenta de base de datos de tu rol no tiene permiso para esta operación.'),
    1213: (409, 'Conflicto concurrente con otra operación. Reintentá.'),
    1205: (409, 'Conflicto concurrente con otra operación. Reintentá.'),
}
CHECK_MESSAGES = {
    'chk_partido_rivales': 'Un equipo no puede jugar contra sí mismo.',
    'chk_turno_horario': 'Los turnos duran una hora y van de 18:00 a 23:00.',
    'chk_plantel_camiseta': 'El número de camiseta debe estar entre 1 y 99.',
    'chk_gol_minuto': 'El minuto debe estar entre 0 y 60.',
    'chk_tarjeta_minuto': 'El minuto debe estar entre 0 y 60.',
    'chk_torneo_fechas': 'La fecha de fin no puede ser anterior a la de inicio.',
    'chk_torneo_semestre': 'El semestre debe ser 1 o 2.',
}
UNIQUE_MESSAGES = {
    'uq_partido_reserva': 'La cancha ya tiene un partido ese día y turno.',
    'uq_partido_rivales': 'Esos equipos ya tienen un enfrentamiento en la edición.',
    'uq_plantel_camiseta': 'Ese número de camiseta ya está usado en el plantel.',
    'uq_plantel_jugador_edicion': 'El jugador ya integra un equipo en esta edición.',
    'uq_equipo_nombre_edicion': 'Ya existe un equipo con ese nombre en la edición.',
    'uq_torneo_edicion': 'Ya existe una edición para ese año y semestre.',
    'email': 'El correo ya está registrado.',
    'PRIMARY': 'Ya existe un registro con esa clave.',
}


def create_app():
    app = Flask(__name__)
    app.json.ensure_ascii = False
    app.json.sort_keys = False
    for bp in BLUEPRINTS:
        app.register_blueprint(bp, url_prefix='/api')

    @app.after_request
    def add_headers(response):
        origin = request.headers.get('Origin')
        if origin in ALLOWED_ORIGINS:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Vary'] = 'Origin'
            response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type, Accept'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.errorhandler(APIError)
    def http_error(err):
        return jsonify({'error': str(err)}), err.status

    @app.errorhandler(ValidationError)
    def validation_error(err):
        return jsonify({'error': str(err)}), 400

    @app.errorhandler(MySQLError)
    def sql_error(err):
        if err.sqlstate == '45000':
            # Mensajes de negocio definidos por los triggers de nuestro esquema.
            return jsonify({'error': err.msg}), 409
        if err.errno in MYSQL_ERRORS:
            status, message = MYSQL_ERRORS[err.errno]
            names = CHECK_MESSAGES if err.errno == 3819 else UNIQUE_MESSAGES if err.errno == 1062 else {}
            message = next((m for name, m in names.items() if f"'{name}'" in (err.msg or '')
                            or f".{name}'" in (err.msg or '')), message)
            return jsonify({'error': message}), status
        if err.errno in (1044, 1045, 1146, 2003, 2005, 2013):
            app.logger.exception('Error de configuración/conexión MySQL')
            return jsonify({'error': 'No se pudo acceder a MySQL. Revisá el esquema, la tabla sesion_api y las cuentas técnicas.'}), 503
        app.logger.exception('Error inesperado de MySQL')
        return jsonify({'error': 'Error interno al consultar la base de datos.'}), 500

    @app.errorhandler(404)
    def route_missing(_):
        return jsonify({'error': 'Ruta no encontrada.'}), 404

    @app.errorhandler(405)
    def method_not_allowed(_):
        return jsonify({'error': 'Método HTTP no permitido en esta ruta.'}), 405

    return app


app = create_app()


if __name__ == '__main__':
    # Debug deshabilitado: no publicar contraseñas ni información de MySQL.
    app.run(host=os.getenv('HOST', '127.0.0.1'), port=int(os.getenv('PORT', '5000')), debug=False)
