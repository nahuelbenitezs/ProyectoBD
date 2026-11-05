"""Pruebas de la API REST con un doble de MySQL (no requieren servidor).

Comprueban rutas, códigos HTTP, permisos por rol, SQL parametrizado,
transacciones (COMMIT/ROLLBACK) y la traducción de errores de los triggers.
"""
import hashlib
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
# Primero el .env real (lo usan las pruebas de integración en la misma corrida); luego valores ficticios.
load_dotenv(ROOT / '.env')
for key, value in (('MYSQL_ADMIN_USER', 'torneo_app_administrador'), ('MYSQL_ADMIN_PASSWORD', 'x'),
                   ('MYSQL_PLANILLERO_USER', 'torneo_app_planillero'), ('MYSQL_PLANILLERO_PASSWORD', 'x')):
    os.environ.setdefault(key, value)

from app import app  # noqa: E402
from fakedb import ADMIN_TOKEN, PLANILLERO_TOKEN, FakeDB, Result, mysql_error, signal  # noqa: E402

ADMIN_DB = os.environ['MYSQL_ADMIN_USER']
PLANILLERO_DB = os.environ['MYSQL_PLANILLERO_USER']
PARTIDO_JUGADO = {'id_partido': 7, 'id_torneo': 1, 'numero_fecha': 3, 'id_equipo_local': 1,
                  'id_equipo_visitante': 4, 'estado': 'jugado'}


class APITestCase(unittest.TestCase):
    def setUp(self):
        self.db = FakeDB()
        patcher = patch('mysql.connector.connect', self.db.connect)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = app.test_client()

    def call(self, method, path, token=ADMIN_TOKEN, **kwargs):
        headers = {'Authorization': 'Bearer ' + token} if token else {}
        return self.client.open('/api' + path, method=method, headers=headers, **kwargs)

    def assertStatus(self, response, status):
        self.assertEqual(response.status_code, status, response.get_data(as_text=True))


class AuthTests(APITestCase):
    def test_login_requires_email_and_password(self):
        self.assertStatus(self.call('POST', '/auth/login', token=None, json={'correo': 'x'}), 400)

    def test_login_rejects_wrong_password(self):
        self.db.on('FROM login WHERE correo', {'correo': 'a@b.uy', 'rol': 'administrador',
                                               'contrasena': hashlib.sha256(b'otra').hexdigest()})
        response = self.call('POST', '/auth/login', token=None, json={'correo': 'a@b.uy', 'contrasena': 'x'})
        self.assertStatus(response, 401)
        self.assertFalse(self.db.executed('INSERT INTO sesion_api'))

    def test_login_migrates_legacy_hash_and_creates_session(self):
        self.db.on('FROM login WHERE correo', {'correo': 'a@b.uy', 'rol': 'planillero',
                                               'contrasena': hashlib.sha256(b'Clave1!').hexdigest()})
        response = self.call('POST', '/auth/login', token=None, json={'correo': 'A@B.uy', 'contrasena': 'Clave1!'})
        self.assertStatus(response, 200)
        body = response.get_json()
        self.assertEqual(body['user'], {'correo': 'a@b.uy', 'rol': 'planillero'})
        self.assertNotIn('contrasena', str(body))
        self.assertTrue(self.db.executed('UPDATE login SET contrasena'))
        token_hash = self.db.executed('INSERT INTO sesion_api')[0][1][0]
        self.assertEqual(token_hash, hashlib.sha256(body['token'].encode()).hexdigest())
        self.assertEqual(self.db.commits, 1)

    def test_routes_require_token(self):
        self.assertStatus(self.call('GET', '/jugadores', token=None), 401)
        self.assertStatus(self.call('GET', '/jugadores', token='z' * 43), 401)

    def test_me_and_logout(self):
        self.assertEqual(self.call('GET', '/auth/me', token=PLANILLERO_TOKEN).get_json()['rol'], 'planillero')
        self.assertStatus(self.call('POST', '/auth/logout'), 200)
        self.assertTrue(self.db.executed('DELETE FROM sesion_api'))

    def test_planillero_cannot_use_admin_routes(self):
        for method, path in (('POST', '/jugadores'), ('POST', '/equipos'), ('POST', '/partidos'),
                             ('PATCH', '/torneos/1'), ('DELETE', '/complejos/1'), ('POST', '/sanciones'),
                             ('POST', '/equipos/1/plantel'), ('PATCH', '/partidos/1/estado')):
            with self.subTest(path=path):
                self.assertStatus(self.call(method, path, token=PLANILLERO_TOKEN, json={}), 403)
        self.assertFalse([q for q in self.db.queries if not q[0].startswith('SELECT')])

    def test_reads_use_the_role_database_account(self):
        self.call('GET', '/partidos', token=PLANILLERO_TOKEN)
        self.assertEqual(self.db.executed('FROM partido p')[0][2], PLANILLERO_DB)

    def test_cors_preflight_allows_put(self):
        response = self.client.options('/api/partidos/1/planilla', headers={
            'Origin': 'http://localhost:5500', 'Access-Control-Request-Method': 'PUT'})
        self.assertIn('PUT', response.headers['Access-Control-Allow-Methods'])


class ErrorTranslationTests(APITestCase):
    def test_trigger_signal_becomes_409_and_rolls_back(self):
        self.db.on('FROM equipo e JOIN facultad', {'id_equipo': 1, 'id_torneo': 1})
        self.db.on('INSERT INTO equipo_jugador_torneo', signal('El plantel no puede tener mas de 10 jugadores'))
        response = self.call('POST', '/equipos/1/plantel', json={'ci_jugador': 1234567, 'numero_camiseta': 11})
        self.assertStatus(response, 409)
        self.assertEqual(response.get_json()['error'], 'El plantel no puede tener mas de 10 jugadores')
        self.assertEqual((self.db.commits, self.db.rollbacks), (0, 1))

    def test_unique_key_has_friendly_message(self):
        self.db.on('INSERT INTO partido', mysql_error(
            1062, "Duplicate entry 'x' for key 'partido.uq_partido_reserva'", '23000'))
        response = self.call('POST', '/partidos', json={
            'id_torneo': 1, 'numero_fecha': 6, 'id_equipo_local': 2, 'id_equipo_visitante': 4,
            'dia': '2026-11-03', 'id_turno': 1, 'nombre_cancha': 'Cancha A', 'id_complejo': 1})
        self.assertStatus(response, 409)
        self.assertEqual(response.get_json()['error'], 'La cancha ya tiene un partido ese día y turno.')

    def test_database_permission_denied_is_403(self):
        self.db.on('FROM partido WHERE id_partido', PARTIDO_JUGADO)
        self.db.on('INSERT INTO gol', mysql_error(1142, "INSERT command denied to user", '42000'))
        response = self.call('POST', '/partidos/7/goles', token=PLANILLERO_TOKEN,
                             json={'ci_jugador': 50000401, 'minuto': 3})
        self.assertStatus(response, 403)

    def test_check_constraint_is_400(self):
        self.db.on('INSERT INTO turno', mysql_error(3819, "Check constraint 'chk_turno_horario' is violated.", 'HY000'))
        response = self.call('POST', '/turnos', json={'hora_inicio': '22:00'})
        self.assertStatus(response, 400)
        self.assertIn('18:00 a 23:00', response.get_json()['error'])

    def test_unknown_route_is_404_json(self):
        self.assertEqual(self.call('GET', '/no-existe').get_json()['error'], 'Ruta no encontrada.')


class JugadoresTests(APITestCase):
    PLAYER = {'ci': 51234567, 'nombre': 'Ana', 'apellido': 'Suárez', 'email': 'ana@ucu.edu.uy',
              'fecha_nacimiento': '2001-05-04', 'id_facultad': 1, 'tipo': 'grado'}

    def test_list_filters_are_parameters(self):
        self.assertStatus(self.call('GET', '/jugadores?id_facultad=2&tipo=docente'), 200)
        self.assertEqual(self.db.executed('FROM jugador')[0][1], (2, 2, 'docente', 'docente'))
        self.assertStatus(self.call('GET', '/jugadores?tipo=director'), 400)

    def test_create_validates_and_inserts(self):
        self.assertStatus(self.call('POST', '/jugadores', json={**self.PLAYER, 'email': 'sin-arroba'}), 400)
        self.assertStatus(self.call('POST', '/jugadores', json=self.PLAYER), 201)
        sql, params, user = self.db.executed('INSERT INTO jugador')[0]
        self.assertEqual(params[0], 51234567)
        self.assertEqual(user, ADMIN_DB)

    def test_patch_merges_current_values(self):
        self.db.on('FROM jugador WHERE ci', {**self.PLAYER})
        response = self.call('PATCH', '/jugadores/51234567', json={'nombre': 'Ana María'})
        self.assertStatus(response, 200)
        self.assertEqual(self.db.executed('UPDATE jugador')[0][1][0], 'Ana María')

    def test_delete_missing_is_404(self):
        self.db.on('DELETE FROM jugador', Result(rowcount=0))
        self.assertStatus(self.call('DELETE', '/jugadores/51234567'), 404)

    def test_suspension_reads_v_sanciones(self):
        self.db.on('FROM v_sanciones', [{'id_sancion': -1, 'motivo': 'roja', 'numero_fecha_inicio': 2,
                                         'cantidad_fechas': 1, 'origen': 'automatica'}])
        body = self.call('GET', '/jugadores/50000103/suspension?id_torneo=1&numero_fecha=2').get_json()
        self.assertTrue(body['suspendido'])
        self.assertStatus(self.call('GET', '/jugadores/50000103/suspension'), 400)


class TorneosTests(APITestCase):
    TORNEO = {'id_torneo': 1, 'nombre': 'Interfacultades', 'anio': 2027, 'semestre': 1,
              'fecha_inicio': '2027-03-01', 'fecha_fin': '2027-06-30', 'estado': 'en curso'}

    def test_new_edition_starts_in_inscripcion(self):
        body = {k: v for k, v in self.TORNEO.items() if k != 'id_torneo'}
        self.assertStatus(self.call('POST', '/torneos', json=body), 400)
        self.db.on('INSERT INTO torneo', Result(lastrowid=2))
        response = self.call('POST', '/torneos', json={**body, 'estado': 'inscripción'})
        self.assertStatus(response, 201)
        self.assertEqual(response.get_json()['id_torneo'], 2)

    def test_state_cannot_go_back(self):
        self.db.on('FROM torneo WHERE id_torneo', dict(self.TORNEO))
        self.assertStatus(self.call('PATCH', '/torneos/1', json={'estado': 'inscripción'}), 400)
        self.assertFalse(self.db.executed('UPDATE torneo'))
        self.assertStatus(self.call('PATCH', '/torneos/1', json={'estado': 'finalizado'}), 200)
        self.assertEqual(self.db.executed('UPDATE torneo')[0][1][-2:], ('finalizado', 1))

    def test_fechas_of_missing_edition_is_404(self):
        self.assertStatus(self.call('GET', '/torneos/99/fechas'), 404)


class EquiposTests(APITestCase):
    EQUIPO = {'id_equipo': 7, 'nombre': 'Cóndores', 'id_torneo': 2, 'id_facultad': 1,
              'facultad': 'Ingeniería', 'ci_capitan': 50000101, 'cantidad_jugadores': 1}

    def test_create_inserts_team_and_captain_in_one_transaction(self):
        self.db.on('INSERT INTO equipo ', Result(lastrowid=7))
        self.db.on('FROM equipo e JOIN facultad', dict(self.EQUIPO))
        response = self.call('POST', '/equipos', json={'nombre': 'Cóndores', 'id_torneo': 2,
                                                       'id_facultad': 1, 'ci_capitan': 50000101})
        self.assertStatus(response, 201)
        self.assertEqual(self.db.executed('INSERT INTO equipo_jugador_torneo')[0][1], (7, 50000101, 2, 1))
        self.assertEqual(self.db.commits, 1)

    def test_create_rolls_back_team_when_captain_is_rejected(self):
        self.db.on('INSERT INTO equipo_jugador_torneo', signal('Jugador y equipo deben pertenecer a la misma facultad'))
        response = self.call('POST', '/equipos', json={'nombre': 'X', 'id_torneo': 2,
                                                       'id_facultad': 1, 'ci_capitan': 50000201})
        self.assertStatus(response, 409)
        self.assertEqual((self.db.commits, self.db.rollbacks), (0, 1))

    def test_cannot_change_faculty(self):
        self.db.on('FROM equipo e JOIN facultad', dict(self.EQUIPO))
        self.assertStatus(self.call('PATCH', '/equipos/7', json={'id_facultad': 2}), 400)
        self.assertStatus(self.call('PATCH', '/equipos/7', json={'ci_capitan': 50000102}), 200)
        self.assertEqual(self.db.executed('UPDATE equipo')[0][1], ('Cóndores', 50000102, 7))

    def test_roster_uses_team_edition(self):
        self.db.on('FROM equipo e JOIN facultad', dict(self.EQUIPO))
        self.assertStatus(self.call('POST', '/equipos/7/plantel', json={'ci_jugador': 50000102, 'numero_camiseta': 9}), 201)
        self.assertEqual(self.db.executed('INSERT INTO equipo_jugador_torneo')[0][1], (7, 50000102, 2, 9))
        self.assertStatus(self.call('POST', '/equipos/7/plantel', json={'ci_jugador': 50000102, 'numero_camiseta': 0}), 400)

    def test_roster_update_and_remove(self):
        self.assertStatus(self.call('PATCH', '/equipos/7/plantel/50000102', json={'numero_camiseta': 10}), 404)
        self.db.on('FROM equipo_jugador_torneo ejt JOIN jugador', {'id_equipo': 7, 'ci_jugador': 50000102})
        self.assertStatus(self.call('PATCH', '/equipos/7/plantel/50000102', json={'numero_camiseta': 10}), 200)
        self.db.on('DELETE FROM equipo_jugador_torneo', Result(rowcount=0))
        self.assertStatus(self.call('DELETE', '/equipos/7/plantel/50000102'), 404)


class ComplejosTests(APITestCase):
    def test_complex_crud(self):
        self.db.on('INSERT INTO complejo', Result(lastrowid=3))
        body = {'nombre': 'Complejo Este', 'direccion': 'Av. Italia 1', 'departamento': 'Montevideo'}
        self.assertEqual(self.call('POST', '/complejos', json=body).get_json()['id_complejo'], 3)
        self.assertStatus(self.call('POST', '/complejos', json={**body, 'direccion': ''}), 400)
        self.db.on('DELETE FROM complejo', mysql_error(1451, 'Cannot delete or update a parent row', '23000'))
        self.assertStatus(self.call('DELETE', '/complejos/1'), 409)

    def test_court_requires_existing_complex(self):
        body = {'nombre_cancha': 'Cancha C', 'superficie': 'parquet', 'techada': True}
        self.assertStatus(self.call('POST', '/complejos/9/canchas', json=body), 404)
        self.db.on('FROM complejo WHERE id_complejo', {'id_complejo': 1})
        self.assertStatus(self.call('POST', '/complejos/1/canchas', json={**body, 'superficie': 'pasto'}), 400)
        self.db.on('FROM cancha c JOIN complejo', {'nombre_cancha': 'Cancha C', 'id_complejo': 1})
        self.assertStatus(self.call('POST', '/complejos/1/canchas', json=body), 201)
        self.assertEqual(self.db.executed('INSERT INTO cancha')[0][1], ('Cancha C', 1, 'parquet', True))

    def test_court_names_with_spaces(self):
        self.db.on('FROM cancha c JOIN complejo', {'nombre_cancha': 'Cancha A', 'id_complejo': 1,
                                                   'superficie': 'sintético', 'techada': 0})
        self.assertStatus(self.call('PATCH', '/complejos/1/canchas/Cancha%20A', json={'techada': True}), 200)
        self.assertEqual(self.db.executed('UPDATE cancha')[0][1], ('Cancha A', 'sintético', True, 1, 'Cancha A'))

    def test_availability_requires_date(self):
        self.assertStatus(self.call('GET', '/canchas/disponibles'), 400)
        self.assertStatus(self.call('GET', '/canchas/disponibles?dia=2026-11-10&id_complejo=1'), 200)
        self.assertEqual(self.db.executed('CROSS JOIN turno')[0][1], (1, 1, '2026-11-10'))


class PartidosTests(APITestCase):
    BODY = {'id_torneo': 1, 'numero_fecha': 6, 'id_equipo_local': 2, 'id_equipo_visitante': 4,
            'dia': '2026-11-09', 'id_turno': 1, 'nombre_cancha': 'Cancha A', 'id_complejo': 1}

    def test_create_inserts_all_fields(self):
        self.db.on('INSERT INTO partido', Result(lastrowid=14))
        self.db.on('FROM partido p', {'id_partido': 14, **self.BODY, 'estado': 'programado'})
        self.assertStatus(self.call('POST', '/partidos', json=self.BODY), 201)
        self.assertEqual(self.db.executed('INSERT INTO partido')[0][1],
                         (1, 6, 2, 4, '2026-11-09', 1, 'Cancha A', 1, 'programado'))
        self.assertStatus(self.call('POST', '/partidos', json={**self.BODY, 'id_equipo_visitante': 2}), 400)

    def test_played_match_cannot_change_or_be_deleted(self):
        self.db.on('FROM partido p', {'id_partido': 7, **self.BODY, 'estado': 'jugado'})
        self.assertStatus(self.call('PATCH', '/partidos/7', json={'id_turno': 2}), 409)
        self.assertStatus(self.call('PATCH', '/partidos/7/estado', json={'estado': 'cancelado'}), 409)
        self.assertStatus(self.call('DELETE', '/partidos/7'), 409)
        self.assertFalse(self.db.executed('UPDATE partido') + self.db.executed('DELETE FROM partido'))

    def test_postpone_match(self):
        self.db.on('FROM partido p', {'id_partido': 12, **self.BODY, 'estado': 'programado'})
        self.assertStatus(self.call('PATCH', '/partidos/12/estado', json={'estado': 'postergado'}), 200)
        self.assertEqual(self.db.executed('UPDATE partido SET estado')[0][1], ('postergado', 12))
        self.assertStatus(self.call('PATCH', '/partidos/12/estado', json={'estado': 'suspendido'}), 400)

    def test_list_filters(self):
        self.call('GET', '/partidos?id_torneo=1&numero_fecha=2&id_equipo=3&estado=jugado')
        self.assertEqual(self.db.executed('FROM partido p')[0][1], (1, 1, 2, 2, 3, 3, 'jugado', 'jugado'))

    def test_result_only_for_played_matches(self):
        self.db.on('FROM partido p', {'id_partido': 12, **self.BODY, 'estado': 'programado'})
        self.assertStatus(self.call('GET', '/partidos/12/resultado'), 409)


class PlanillaTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.db.on('FROM partido WHERE id_partido', dict(PARTIDO_JUGADO))

    def test_replace_sheet_applies_only_the_difference(self):
        self.db.on('SELECT ci_jugador, id_equipo FROM planilla_partido',
                   [{'ci_jugador': 50000101, 'id_equipo': 1}, {'ci_jugador': 50000102, 'id_equipo': 1}])
        response = self.call('PUT', '/partidos/7/planilla', token=PLANILLERO_TOKEN, json={'participantes': [
            {'ci_jugador': 50000102, 'id_equipo': 1}, {'ci_jugador': 50000401, 'id_equipo': 4}]})
        self.assertStatus(response, 200)
        self.assertEqual([q[1] for q in self.db.executed('DELETE FROM planilla_partido')], [(7, 50000101)])
        self.assertEqual([q[1] for q in self.db.executed('INSERT INTO planilla_partido')], [(7, 50000401, 4)])
        self.assertTrue(all(q[2] == PLANILLERO_DB for q in self.db.executed('planilla_partido')))
        self.assertEqual(self.db.commits, 1)

    def test_cannot_remove_player_with_goals(self):
        self.db.on('SELECT ci_jugador, id_equipo FROM planilla_partido', [{'ci_jugador': 50000101, 'id_equipo': 1}])
        self.db.on('SELECT ci_jugador FROM gol', [{'ci_jugador': 50000101}])
        response = self.call('PUT', '/partidos/7/planilla', json={'participantes': []})
        self.assertStatus(response, 409)
        self.assertFalse(self.db.executed('DELETE FROM planilla_partido'))

    def test_suspended_player_is_rejected_by_trigger(self):
        self.db.on('INSERT INTO planilla_partido', signal('El jugador esta suspendido para esta fecha'))
        response = self.call('POST', '/partidos/7/planilla', token=PLANILLERO_TOKEN,
                             json={'ci_jugador': 50000103, 'id_equipo': 1})
        self.assertStatus(response, 409)
        self.assertIn('suspendido', response.get_json()['error'])

    def test_enabled_players_flags(self):
        self.db.on('FROM partido p JOIN equipo_jugador_torneo', [
            {'id_equipo': 1, 'ci_jugador': 50000103, 'suspendido': 1, 'en_planilla': 0}])
        row = self.call('GET', '/partidos/7/habilitados', token=PLANILLERO_TOKEN).get_json()[0]
        self.assertEqual((row['suspendido'], row['en_planilla']), (True, False))


class GolesTarjetasTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.db.on('FROM partido WHERE id_partido', dict(PARTIDO_JUGADO))

    def test_planillero_registers_goal_with_own_account(self):
        self.db.on('INSERT INTO gol', Result(lastrowid=31))
        response = self.call('POST', '/partidos/7/goles', token=PLANILLERO_TOKEN,
                             json={'ci_jugador': 50000402, 'minuto': 38, 'autogol': True})
        self.assertStatus(response, 201)
        self.assertEqual(response.get_json()['id_gol'], 31)
        sql, params, user = self.db.executed('INSERT INTO gol')[0]
        self.assertEqual((params, user), ((7, 50000402, 38, True), PLANILLERO_DB))

    def test_goal_after_48_hours_is_rejected(self):
        self.db.on('INSERT INTO gol', signal('Vencio el plazo de 48 horas para corregir la planilla'))
        response = self.call('POST', '/partidos/7/goles', json={'ci_jugador': 50000402, 'minuto': 1})
        self.assertStatus(response, 409)

    def test_goal_update_is_scoped_to_match(self):
        self.assertStatus(self.call('PATCH', '/partidos/7/goles/99', json={'minuto': 5}), 404)
        self.db.on('FROM gol WHERE id_gol', {'ci_jugador': 50000401, 'minuto': 18, 'autogol': 0})
        self.assertStatus(self.call('PATCH', '/partidos/7/goles/19', json={'minuto': 5}), 200)
        self.assertEqual(self.db.executed('UPDATE gol')[0][1], (50000401, 5, False, 19))

    def test_card_create_and_delete(self):
        self.assertStatus(self.call('POST', '/partidos/7/tarjetas', json={'ci_jugador': 1234567, 'minuto': 3,
                                                                          'color': 'verde'}), 400)
        self.assertStatus(self.call('POST', '/partidos/7/tarjetas', token=PLANILLERO_TOKEN,
                                    json={'ci_jugador': 50000401, 'minuto': 3, 'color': 'roja'}), 201)
        self.db.on('DELETE FROM tarjeta', Result(rowcount=0))
        self.assertStatus(self.call('DELETE', '/partidos/7/tarjetas/1', token=PLANILLERO_TOKEN), 404)

    def test_missing_match_is_404(self):
        self.db.on('FROM partido WHERE id_partido', None)
        self.assertStatus(self.call('POST', '/partidos/99/goles', json={'ci_jugador': 1234567, 'minuto': 1}), 404)


class SancionesTests(APITestCase):
    def test_create_is_always_disciplinary(self):
        self.db.on('INSERT INTO sancion_jugador', Result(lastrowid=2))
        self.db.on('FROM v_sanciones s', {'id_sancion': 2, 'motivo': 'disciplinaria', 'origen': 'manual'})
        body = {'ci_jugador': 50000304, 'id_torneo': 1, 'numero_fecha_inicio': 6, 'cantidad_fechas': 2}
        self.assertStatus(self.call('POST', '/sanciones', json={**body, 'motivo': 'roja'}), 400)
        self.assertStatus(self.call('POST', '/sanciones', json=body), 201)
        sql, params, _ = self.db.executed('INSERT INTO sancion_jugador')[0]
        self.assertIn("'disciplinaria'", sql)
        self.assertEqual(params, (50000304, 1, 6, 2))

    def test_automatic_sanctions_are_read_only(self):
        self.db.on('FROM v_sanciones s', {'id_sancion': -1, 'motivo': 'roja', 'origen': 'automatica'})
        self.assertStatus(self.call('GET', '/sanciones/-1'), 200)
        self.assertStatus(self.call('PATCH', '/sanciones/-1', json={'cantidad_fechas': 3}), 409)
        self.assertStatus(self.call('DELETE', '/sanciones/-1'), 409)
        self.assertFalse(self.db.executed('sancion_jugador'))

    def test_filters(self):
        self.assertStatus(self.call('GET', '/sanciones?id_torneo=1&motivo=roja&id_equipo=2', token=PLANILLERO_TOKEN), 200)
        self.assertEqual(self.db.executed('FROM v_sanciones s')[0][1],
                         (1, 1, None, None, 2, 2, 'roja', 'roja', None, None))
        self.assertStatus(self.call('GET', '/sanciones?motivo=insulto'), 400)


class ReportesTests(APITestCase):
    def test_report_by_edition(self):
        self.assertStatus(self.call('GET', '/reportes/posiciones'), 400)
        self.assertStatus(self.call('GET', '/reportes/inventado?id_torneo=1'), 404)
        self.assertStatus(self.call('GET', '/reportes/posiciones?id_torneo=1', token=PLANILLERO_TOKEN), 200)
        self.assertEqual(self.db.executed('v_reporte_01_posiciones')[0][1:], ((1,), PLANILLERO_DB))

    def test_report_index_lists_twelve(self):
        self.assertEqual(len(self.call('GET', '/reportes').get_json()), 12)


if __name__ == '__main__':
    unittest.main()
