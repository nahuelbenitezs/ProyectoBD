"""Pruebas de integración: API + MySQL real con torneo_ucu_creacion.sql cargado.

Se ejecutan solo con RUN_INTEGRATION=1 y las credenciales de backend/.env:
  docker compose up -d db
  RUN_INTEGRATION=1 python -m pytest tests/test_integration.py -v

Cada corrida crea su propia edición (año siguiente al último cargado), jugadores
y cancha, de modo que puede repetirse sin recrear la base. Los partidos se juegan
"ayer" según el reloj de MySQL para quedar dentro del plazo de 48 horas.
"""
from datetime import timedelta
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RUN = os.getenv('RUN_INTEGRATION') == '1'
if RUN:
    from mysql.connector import Error as MySQLError
    from app import app
    from database import connection, fetch_one

ADMIN = ('admin@demo.ucu.edu.uy', 'AdminDemo2026!')
PLANILLERO = ('planillero@demo.ucu.edu.uy', 'PlanillaDemo2026!')
REPORTES = ('posiciones', 'goleadores', 'fair-play', 'promedio-goles', 'uso-espacios', 'jugadores-facultad',
            'sin-participacion', 'sanciones', 'estados', 'local-visitante', 'disciplina', 'goles-tramos')


@unittest.skipUnless(RUN, 'Definí RUN_INTEGRATION=1 y levantá MySQL (docker compose up -d db).')
class TorneoCompletoTest(unittest.TestCase):
    """Escenarios en orden: cada test usa lo creado por los anteriores (estado en S)."""
    S = {}

    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        with connection('administrador') as db:
            row = fetch_one(db, 'SELECT CURDATE() AS hoy, COALESCE(MAX(anio), 2026) + 1 AS anio FROM torneo')
        cls.hoy, cls.anio = row['hoy'], row['anio']
        cls.ayer = cls.hoy - timedelta(days=1)
        base = 70000000 + (cls.anio % 100) * 1000
        cls.ci = staticmethod(lambda n: base + n)

    def api(self, method, path, json=None, token='admin', expected=None):
        token = self.S.get(token, token)
        response = self.client.open('/api' + path, method=method, json=json,
                                    headers={'Authorization': 'Bearer ' + token} if token else {})
        body = response.get_json(silent=True)
        if expected is not None:
            self.assertEqual(response.status_code, expected, f'{method} {path}: {body}')
        return response.status_code, body

    def rejected(self, method, path, json, fragment, status=409, token='admin'):
        _, body = self.api(method, path, json, token, expected=status)
        self.assertIn(fragment.lower(), body['error'].lower())

    def test_01_login_y_roles(self):
        for key, (correo, clave) in (('admin', ADMIN), ('planillero', PLANILLERO)):
            _, body = self.api('POST', '/auth/login', {'correo': correo, 'contrasena': clave}, token=None, expected=200)
            self.S[key] = body['token']
        self.api('POST', '/auth/login', {'correo': ADMIN[0], 'contrasena': 'mala'}, token=None, expected=401)
        self.api('POST', '/jugadores', {}, token='planillero', expected=403)
        self.assertEqual(self.api('GET', '/auth/me', token='planillero')[1]['rol'], 'planillero')

    def test_02_permisos_mysql_del_planillero(self):
        """La cuenta técnica del planillero no puede tocar tablas de administración."""
        with connection('planillero') as db:
            for sql in ("INSERT INTO jugador VALUES (1234567, 'X', 'Y', 'x@y.uy', '2000-01-01', 1, 'grado')",
                        'SELECT * FROM login', "UPDATE partido SET estado = 'cancelado'",
                        'DELETE FROM sancion_jugador'):
                with self.subTest(sql=sql), self.assertRaises(MySQLError) as ctx:
                    cursor = db.cursor()
                    cursor.execute(sql)
                self.assertIn(ctx.exception.errno, (1142, 1143))

    def test_03_datos_semilla_y_reportes(self):
        for slug in REPORTES:
            _, rows = self.api('GET', f'/reportes/{slug}?id_torneo=1', token='planillero', expected=200)
            self.assertTrue(rows, slug)
        _, empate = self.api('GET', '/partidos?id_torneo=1&numero_fecha=4', expected=200)
        self.assertEqual((empate[0]['goles_local'], empate[0]['goles_visitante']), (0, 0))
        # Partido 7: gol de Pumas + autogol de Pumas -> 1 a 1 para Halcones (local).
        _, resultado = self.api('GET', '/partidos/7/resultado', expected=200)
        self.assertEqual((resultado['goles_local'], resultado['goles_visitante']), (1, 1))
        _, goleadores = self.api('GET', '/reportes/goleadores?id_torneo=1', expected=200)
        self.assertLessEqual(len(goleadores), 10)
        self.assertEqual([g['goles'] for g in goleadores], sorted((g['goles'] for g in goleadores), reverse=True))

    def test_04_bloqueo_48_horas(self):
        self.rejected('POST', '/partidos/1/goles', {'ci_jugador': 50000101, 'minuto': 5}, '48 horas',
                      token='planillero')
        self.rejected('DELETE', '/partidos/1/goles/1', None, '48 horas')

    def test_05_catalogos(self):
        _, turnos = self.api('GET', '/turnos', expected=200)
        self.assertEqual(len(turnos), 5)
        self.api('POST', '/turnos', {'hora_inicio': '17:00'}, expected=400)
        _, complejo = self.api('POST', '/complejos', {'nombre': f'Complejo IT {self.anio}',
                                                      'direccion': 'Av. Prueba 1', 'departamento': 'Canelones'},
                               expected=201)
        self.S['complejo'] = complejo['id_complejo']
        self.api('POST', f"/complejos/{self.S['complejo']}/canchas",
                 {'nombre_cancha': 'Cancha IT', 'superficie': 'sintético', 'techada': False}, expected=201)
        self.api('POST', f"/complejos/{self.S['complejo']}/canchas",
                 {'nombre_cancha': 'Cancha IT', 'superficie': 'parquet', 'techada': True}, expected=409)

    def test_06_edicion_y_jugadores(self):
        _, torneo = self.api('POST', '/torneos', {
            'nombre': f'Interfacultades IT {self.anio}', 'anio': self.anio, 'semestre': 1,
            'fecha_inicio': (self.hoy - timedelta(days=30)).isoformat(),
            'fecha_fin': (self.hoy + timedelta(days=30)).isoformat()}, expected=201)
        self.S['torneo'] = torneo['id_torneo']
        nuevos = [(n, 1, 'grado') for n in range(1, 9)] + [(20, 2, 'docente')]
        for n, facultad, tipo in nuevos:
            self.api('POST', '/jugadores', {
                'ci': self.ci(n), 'nombre': 'Prueba', 'apellido': f'IT{n}', 'email': f'it{self.ci(n)}@example.edu.uy',
                'fecha_nacimiento': '2000-01-01', 'id_facultad': facultad, 'tipo': tipo}, expected=201)
        self.api('POST', '/jugadores', {
            'ci': self.ci(99), 'nombre': 'Dup', 'apellido': 'Mail', 'email': f'it{self.ci(1)}@example.edu.uy',
            'fecha_nacimiento': '2000-01-01', 'id_facultad': 1, 'tipo': 'grado'}, expected=409)
        _, jugadores = self.api('GET', '/jugadores?id_facultad=2&tipo=docente', expected=200)
        self.assertIn(self.ci(20), [j['ci'] for j in jugadores])

    def add(self, equipo, ci, camiseta, expected=201):
        return self.api('POST', f'/equipos/{self.S[equipo]}/plantel',
                        {'ci_jugador': ci, 'numero_camiseta': camiseta}, expected=expected)

    def test_07_equipos_y_planteles(self):
        t = self.S['torneo']
        for key, facultad, capitan in (('A', 1, 50000101), ('B', 2, 50000201), ('C', 3, 50000301),
                                       ('D', 1, self.ci(4))):
            _, equipo = self.api('POST', '/equipos', {'nombre': f'IT {key}', 'id_torneo': t,
                                                      'id_facultad': facultad, 'ci_capitan': capitan}, expected=201)
            self.S[key] = equipo['id_equipo']
            self.assertEqual(equipo['cantidad_jugadores'], 1)
        self.rejected('POST', '/equipos', {'nombre': 'IT X', 'id_torneo': t, 'id_facultad': 4,
                                           'ci_capitan': 50000101}, 'facultad')
        # A llega a 10 (incluye 1 docente) y rechaza el undécimo.
        for camiseta, ci in enumerate([50000102, 50000103, 50000104, 50000105, 50000106, 50000107,
                                       self.ci(1), self.ci(2), self.ci(3)], start=2):
            self.add('A', ci, camiseta)
        self.rejected('POST', f"/equipos/{self.S['A']}/plantel", {'ci_jugador': self.ci(5), 'numero_camiseta': 11},
                      'mas de 10')
        self.rejected('POST', f"/equipos/{self.S['A']}/plantel", {'ci_jugador': 50000205, 'numero_camiseta': 12},
                      'misma facultad')
        # B con docente y funcionario rechaza un tercer docente.
        for camiseta, ci in enumerate([50000202, 50000203, 50000204, 50000206, 50000207], start=2):
            self.add('B', ci, camiseta)
        self.rejected('POST', f"/equipos/{self.S['B']}/plantel", {'ci_jugador': self.ci(20), 'numero_camiseta': 9},
                      'dos docentes')
        # Jugador ya inscripto en otro equipo de la edición y camiseta repetida.
        self.rejected('POST', f"/equipos/{self.S['D']}/plantel", {'ci_jugador': 50000102, 'numero_camiseta': 5},
                      'ya integra un equipo')
        self.rejected('POST', f"/equipos/{self.S['D']}/plantel", {'ci_jugador': self.ci(5), 'numero_camiseta': 1},
                      'camiseta')
        for camiseta, ci in enumerate([self.ci(5), self.ci(6), self.ci(7), self.ci(8)], start=2):
            self.add('D', ci, camiseta)
        self.rejected('DELETE', f"/equipos/{self.S['A']}/plantel/50000101", None, 'capitan')
        self.api('PATCH', f"/equipos/{self.S['A']}/plantel/50000107", {'numero_camiseta': 70}, expected=200)
        _, equipo = self.api('GET', f"/equipos/{self.S['A']}", expected=200)
        self.assertEqual(len(equipo['plantel']), 10)

    def test_08_inicio_de_edicion(self):
        t = self.S['torneo']
        self.rejected('PATCH', f'/torneos/{t}', {'estado': 'en curso'}, 'planteles incompletos')
        for camiseta, ci in enumerate([50000302, 50000303, 50000304, 50000305], start=2):
            self.add('C', ci, camiseta)
        _, torneo = self.api('PATCH', f'/torneos/{t}', {'estado': 'en curso'}, expected=200)
        self.assertEqual(torneo['estado'], 'en curso')
        self.api('PATCH', f'/torneos/{t}', {'estado': 'inscripción'}, expected=400)
        self.rejected('POST', f"/equipos/{self.S['C']}/plantel", {'ci_jugador': 50000306, 'numero_camiseta': 6},
                      'inscripcion')

    def partido(self, fecha, local, visitante, dia, turno, **extra):
        return {'id_torneo': self.S['torneo'], 'numero_fecha': fecha, 'id_equipo_local': self.S[local],
                'id_equipo_visitante': self.S[visitante], 'dia': dia.isoformat(), 'id_turno': turno,
                'nombre_cancha': 'Cancha IT', 'id_complejo': self.S['complejo'], **extra}

    def test_09_fixture(self):
        _, m1 = self.api('POST', '/partidos', self.partido(1, 'A', 'B', self.ayer, 1), expected=201)
        self.S['M1'] = m1['id_partido']
        self.api('POST', '/partidos', self.partido(1, 'A', 'A', self.ayer, 2), expected=400)
        self.rejected('POST', '/partidos', self.partido(2, 'B', 'A', self.ayer, 4), 'enfrentamiento')
        self.rejected('POST', '/partidos', self.partido(1, 'A', 'C', self.ayer, 2), 'misma fecha')
        self.rejected('POST', '/partidos', self.partido(1, 'C', 'D', self.ayer, 1), 'cancha ya tiene')
        _, libres = self.api('GET', f"/canchas/disponibles?dia={self.ayer}&id_complejo={self.S['complejo']}",
                             expected=200)
        self.assertNotIn(1, [x['id_turno'] for x in libres])
        self.api('POST', '/partidos', self.partido(1, 'C', 'D', self.ayer, 2), expected=201)
        _, m2 = self.api('POST', '/partidos', self.partido(2, 'A', 'C', self.ayer, 3, estado='jugado'), expected=201)
        self.S['M2'] = m2['id_partido']
        self.api('PATCH', f"/partidos/{self.S['M1']}/estado", {'estado': 'jugado'}, expected=200)
        # Partido futuro: no puede marcarse jugado; se posterga, cancela y elimina.
        _, futuro = self.api('POST', '/partidos', self.partido(2, 'B', 'D', self.hoy + timedelta(days=7), 1),
                             expected=201)
        ruta = f"/partidos/{futuro['id_partido']}"
        self.rejected('PATCH', ruta + '/estado', {'estado': 'jugado'}, 'despues del turno')
        self.api('PATCH', ruta + '/estado', {'estado': 'postergado'}, expected=200)
        self.api('PATCH', ruta, {'dia': (self.hoy + timedelta(days=8)).isoformat(), 'estado': 'programado'},
                 expected=200)
        self.api('PATCH', ruta + '/estado', {'estado': 'cancelado'}, expected=200)
        self.api('DELETE', ruta, expected=204)
        self.api('DELETE', f"/partidos/{self.S['M1']}", expected=409)
        self.api('PATCH', f"/partidos/{self.S['M1']}", {'id_turno': 5}, expected=409)

    def test_10_planilla_goles_y_tarjetas(self):
        m1, m2 = self.S['M1'], self.S['M2']
        a, b, c = self.S['A'], self.S['B'], self.S['C']
        intruso = [{'ci_jugador': 50000301, 'id_equipo': a}]
        self.rejected('PUT', f'/partidos/{m1}/planilla', {'participantes': intruso}, 'no integra el plantel',
                      token='planillero')
        planilla = ([{'ci_jugador': ci, 'id_equipo': a} for ci in (50000101, 50000102, 50000103, 50000104, 50000105)]
                    + [{'ci_jugador': ci, 'id_equipo': b} for ci in (50000201, 50000202, 50000203, 50000204, 50000206)])
        _, rows = self.api('PUT', f'/partidos/{m1}/planilla', {'participantes': planilla + intruso},
                           token='planillero', expected=409)
        self.assertEqual(self.api('GET', f'/partidos/{m1}/planilla')[1], [])  # ROLLBACK completo
        _, rows = self.api('PUT', f'/partidos/{m1}/planilla', {'participantes': planilla},
                           token='planillero', expected=200)
        self.assertEqual(len(rows), 10)

        gol = lambda ci, minuto, autogol=False: self.api(  # noqa: E731
            'POST', f'/partidos/{m1}/goles', {'ci_jugador': ci, 'minuto': minuto, 'autogol': autogol},
            token='planillero', expected=201)[1]
        gol(50000101, 10)
        gol(50000201, 20)
        autogol = gol(50000202, 30, True)
        self.rejected('POST', f'/partidos/{m1}/goles', {'ci_jugador': 50000106, 'minuto': 40}, 'no existe',
                      token='planillero')
        _, resultado = self.api('GET', f'/partidos/{m1}/resultado', expected=200)
        self.assertEqual((resultado['goles_local'], resultado['goles_visitante']), (2, 1))
        self.api('PATCH', f"/partidos/{m1}/goles/{autogol['id_gol']}", {'minuto': 31}, token='planillero',
                 expected=200)
        self.rejected('PUT', f'/partidos/{m1}/planilla', {'participantes': planilla[1:]}, 'goles o tarjetas',
                      token='planillero')

        # Roja en fecha 1 -> suspendido en fecha 2 (sanción automática derivada de la tarjeta).
        self.api('POST', f'/partidos/{m1}/tarjetas', {'ci_jugador': 50000102, 'minuto': 50, 'color': 'roja'},
                 token='planillero', expected=201)
        t = self.S['torneo']
        _, susp = self.api('GET', f'/jugadores/50000102/suspension?id_torneo={t}&numero_fecha=2', expected=200)
        self.assertTrue(susp['suspendido'])
        _, habilitados = self.api('GET', f'/partidos/{m2}/habilitados', token='planillero', expected=200)
        self.assertTrue(next(h for h in habilitados if h['ci_jugador'] == 50000102)['suspendido'])
        self.rejected('POST', f'/partidos/{m2}/planilla', {'ci_jugador': 50000102, 'id_equipo': a}, 'suspendido',
                      token='planillero')
        planilla2 = ([{'ci_jugador': ci, 'id_equipo': a} for ci in (50000101, 50000103, 50000104, 50000105, 50000106)]
                     + [{'ci_jugador': ci, 'id_equipo': c} for ci in (50000301, 50000302, 50000303, 50000304, 50000305)])
        self.api('PUT', f'/partidos/{m2}/planilla', {'participantes': planilla2}, token='planillero', expected=200)

        # Tercera amarilla de 50000103 en fecha 1 suspendería una planilla ya cargada en fecha 2.
        for minuto in (5, 15):
            self.api('POST', f'/partidos/{m1}/tarjetas', {'ci_jugador': 50000103, 'minuto': minuto,
                                                          'color': 'amarilla'}, token='planillero', expected=201)
        self.rejected('POST', f'/partidos/{m1}/tarjetas', {'ci_jugador': 50000103, 'minuto': 25,
                                                           'color': 'amarilla'}, 'incompatible', token='planillero')
        _, automaticas = self.api('GET', f'/sanciones?id_torneo={t}&origen=automatica', expected=200)
        self.assertEqual([(s['ci_jugador'], s['motivo'], s['numero_fecha_inicio']) for s in automaticas],
                         [(50000102, 'roja', 2)])
        self.S['automatica'] = automaticas[0]['id_sancion']

    def test_11_sanciones_disciplinarias(self):
        t, b = self.S['torneo'], self.S['B']
        _, sancion = self.api('POST', '/sanciones', {'ci_jugador': 50000203, 'id_torneo': t,
                                                     'numero_fecha_inicio': 3, 'cantidad_fechas': 2}, expected=201)
        self.assertEqual((sancion['motivo'], sancion['origen'], sancion['equipo']), ('disciplinaria', 'manual', 'IT B'))
        _, por_equipo = self.api('GET', f'/sanciones?id_torneo={t}&id_equipo={b}', token='planillero', expected=200)
        self.assertEqual([s['ci_jugador'] for s in por_equipo], [50000203])
        self.api('PATCH', f"/sanciones/{sancion['id_sancion']}", {'cantidad_fechas': 1}, expected=200)
        self.api('DELETE', f"/sanciones/{sancion['id_sancion']}", expected=204)
        self.rejected('POST', '/sanciones', {'ci_jugador': 50000101, 'id_torneo': t, 'numero_fecha_inicio': 1,
                                             'cantidad_fechas': 1}, 'superpone')
        self.rejected('POST', '/sanciones', {'ci_jugador': self.ci(20), 'id_torneo': t, 'numero_fecha_inicio': 1,
                                             'cantidad_fechas': 1}, 'ajeno')
        self.rejected('PATCH', f"/sanciones/{self.S['automatica']}", {'cantidad_fechas': 3}, 'tarjeta')

    def test_12_reportes_de_la_edicion(self):
        t = self.S['torneo']
        _, tabla = self.api('GET', f'/reportes/posiciones?id_torneo={t}', expected=200)
        primero = tabla[0]
        self.assertEqual((primero['equipo'], primero['puntos'], primero['partidos_jugados']), ('IT A', 4, 2))
        _, goleadores = self.api('GET', f'/reportes/goleadores?id_torneo={t}', expected=200)
        self.assertEqual(sorted(g['ci_jugador'] for g in goleadores), [50000101, 50000201])  # autogol excluido
        _, fair = self.api('GET', f'/reportes/fair-play?id_torneo={t}', expected=200)
        self.assertEqual(next(f for f in fair if f['equipo'] == 'IT A')['puntos_fair_play'], 5)
        _, estados = self.api('GET', f'/reportes/estados?id_torneo={t}', expected=200)
        self.assertEqual({e['estado']: e['cantidad'] for e in estados},
                         {'jugado': 2, 'postergado': 0, 'cancelado': 0, 'programado': 1})
        for slug in REPORTES:
            self.api('GET', f'/reportes/{slug}?id_torneo={t}', token='planillero', expected=200)

    def test_13_logout_revoca_token(self):
        self.api('POST', '/auth/logout', token='planillero', expected=200)
        self.api('GET', '/bootstrap', token='planillero', expected=401)


if __name__ == '__main__':
    unittest.main()
