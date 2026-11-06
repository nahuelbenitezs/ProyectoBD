"""Integración MySQL: exclusión entre sanciones y planillas con transacciones concurrentes."""
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import timedelta
import os
from pathlib import Path
import sys
from threading import Event
import unittest
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
RUN = os.getenv('RUN_INTEGRATION') == '1'
if RUN:
    from mysql.connector import Error as MySQLError
    from database import connection, execute, fetch_one


@unittest.skipUnless(RUN, 'Requiere RUN_INTEGRATION=1 y MySQL con el esquema del proyecto.')
class ConcurrenciaSancionesTest(unittest.TestCase):
    """Cada operación usa una conexión independiente y un snapshot RR anterior al conflicto."""

    @classmethod
    def setUpClass(cls):
        with connection('administrador') as db:
            row = fetch_one(db, 'SELECT CURDATE() AS hoy, MAX(anio)+1 AS anio FROM torneo')
            hoy, anio = row['hoy'], row['anio']
            nombre = 'Concurrencia ' + uuid4().hex[:8]
            cls.torneo, _ = execute(db, '''INSERT INTO torneo
                (nombre,anio,semestre,fecha_inicio,fecha_fin) VALUES (%s,%s,1,%s,%s)''',
                (nombre, anio, hoy-timedelta(days=30), hoy+timedelta(days=30)))
            complejo, _ = execute(db, '''INSERT INTO complejo (nombre,direccion,departamento)
                VALUES (%s,'Direccion de prueba','Montevideo')''', (nombre,))
            execute(db, '''INSERT INTO cancha (nombre_cancha,id_complejo,superficie,techada)
                VALUES ('Cancha concurrencia',%s,'parquet',1)''', (complejo,))
            equipos = []
            for facultad in (1, 2, 3):
                capitan = 50000001 + facultad*100
                equipo, _ = execute(db, '''INSERT INTO equipo
                    (nombre,id_torneo,id_facultad,ci_capitan) VALUES (%s,%s,%s,%s)''',
                    (f'Equipo {facultad}', cls.torneo, facultad, capitan))
                equipos.append(equipo)
                for numero in range(1, 6):
                    execute(db, '''INSERT INTO equipo_jugador_torneo
                        (id_equipo,ci_jugador,id_torneo,numero_camiseta) VALUES (%s,%s,%s,%s)''',
                        (equipo, capitan+numero-1, cls.torneo, numero))
            execute(db, "UPDATE torneo SET estado='en curso' WHERE id_torneo=%s", (cls.torneo,))
            cls.equipo = equipos[0]
            cls.jugador = 50000101
            partidos = []
            for fecha, rival in enumerate(equipos[1:], start=1):
                partido, _ = execute(db, '''INSERT INTO partido
                    (id_torneo,numero_fecha,id_equipo_local,id_equipo_visitante,dia,id_turno,
                     nombre_cancha,id_complejo,estado)
                    VALUES (%s,%s,%s,%s,%s,%s,'Cancha concurrencia',%s,'jugado')''',
                    (cls.torneo, fecha, cls.equipo, rival, hoy-timedelta(days=1), fecha, complejo))
                partidos.append(partido)
            cls.primero, cls.siguiente = partidos
            execute(db, '''INSERT INTO planilla_partido (id_partido,ci_jugador,id_equipo)
                VALUES (%s,%s,%s)''', (cls.primero, cls.jugador, cls.equipo))
            db.commit()

    def tearDown(self):
        # Solo se limpian las filas de la edición creada por esta clase.
        with connection('administrador') as db:
            execute(db, 'DELETE FROM planilla_partido WHERE id_partido=%s AND ci_jugador=%s',
                    (self.siguiente, self.jugador))
            execute(db, 'DELETE FROM tarjeta WHERE id_partido=%s AND ci_jugador=%s',
                    (self.primero, self.jugador))
            execute(db, 'DELETE FROM sancion_jugador WHERE id_torneo=%s AND ci_jugador=%s',
                    (self.torneo, self.jugador))
            db.commit()

    def statement(self, operacion):
        if operacion == 'planilla':
            return ('INSERT INTO planilla_partido (id_partido,ci_jugador,id_equipo) VALUES (%s,%s,%s)',
                    (self.siguiente, self.jugador, self.equipo))
        if operacion == 'roja':
            return ("INSERT INTO tarjeta (id_partido,ci_jugador,minuto,color) VALUES (%s,%s,55,'roja')",
                    (self.primero, self.jugador))
        return ('''INSERT INTO sancion_jugador
                   (ci_jugador,id_torneo,motivo,numero_fecha_inicio,cantidad_fechas)
                   VALUES (%s,%s,'disciplinaria',2,1)''', (self.jugador, self.torneo))

    def comprobar_exclusion(self, primera, segunda, mensaje):
        snapshot_listo, continuar, intento = Event(), Event(), Event()

        def ejecutar_segunda():
            rol = 'administrador' if segunda == 'disciplinaria' else 'planillero'
            with connection(rol) as db:
                execute(db, 'SET SESSION innodb_lock_wait_timeout=5')
                db.start_transaction(isolation_level='REPEATABLE READ')
                fetch_one(db, 'SELECT COUNT(*) AS n FROM v_sanciones WHERE id_torneo=%s', (self.torneo,))
                fetch_one(db, 'SELECT COUNT(*) AS n FROM planilla_partido WHERE id_partido=%s',
                          (self.siguiente,))
                snapshot_listo.set()
                if not continuar.wait(5):
                    raise AssertionError('No se inició la primera transacción.')
                intento.set()
                try:
                    execute(db, *self.statement(segunda))
                    db.commit()
                    return None
                except MySQLError as error:
                    db.rollback()
                    return error

        rol = 'administrador' if primera == 'disciplinaria' else 'planillero'
        with connection(rol) as db, ThreadPoolExecutor(max_workers=1) as pool:
            futuro = pool.submit(ejecutar_segunda)
            try:
                self.assertTrue(snapshot_listo.wait(5), 'La segunda conexión no creó su snapshot.')
                execute(db, *self.statement(primera))
                continuar.set()
                self.assertTrue(intento.wait(5), 'No se intentó la operación concurrente.')
                # La segunda operación debe esperar al COMMIT de la primera.
                with self.assertRaises(TimeoutError):
                    futuro.result(timeout=0.3)
                db.commit()
                error = futuro.result(timeout=7)
                self.assertIsNotNone(error, 'Se confirmaron las dos operaciones incompatibles.')
                self.assertEqual(error.errno, 1644, str(error))
                self.assertIn(mensaje, error.msg)
            finally:
                continuar.set()
                db.rollback()
        with connection('administrador') as db:
            row = fetch_one(db, '''SELECT COUNT(*) AS n FROM planilla_partido pp
                JOIN partido p ON p.id_partido=pp.id_partido
                JOIN v_sanciones s ON s.id_torneo=p.id_torneo AND s.ci_jugador=pp.ci_jugador
                WHERE p.id_torneo=%s AND p.numero_fecha>=s.numero_fecha_inicio
                  AND p.numero_fecha<s.numero_fecha_inicio+s.cantidad_fechas''', (self.torneo,))
            self.assertEqual(row['n'], 0)

    def test_roja_antes_de_planilla(self):
        self.comprobar_exclusion('roja', 'planilla', 'suspendido')

    def test_planilla_antes_de_roja(self):
        self.comprobar_exclusion('planilla', 'roja', 'incompatible')

    def test_disciplinaria_antes_de_planilla(self):
        self.comprobar_exclusion('disciplinaria', 'planilla', 'suspendido')

    def test_planilla_antes_de_disciplinaria(self):
        self.comprobar_exclusion('planilla', 'disciplinaria', 'superpone')

    def test_retiro_de_integrante_con_sancion_manual(self):
        # Una edición en inscripción permite comprobar la protección específica
        # de sanciones, sin que el rechazo dependa del estado del torneo.
        with connection('administrador') as db:
            row = fetch_one(db, 'SELECT CURDATE() AS hoy, MAX(anio)+1 AS anio FROM torneo')
            torneo, _ = execute(db, '''INSERT INTO torneo
                (nombre,anio,semestre,fecha_inicio,fecha_fin) VALUES ('Retiro con sancion',%s,1,%s,%s)''',
                (row['anio'], row['hoy'], row['hoy']+timedelta(days=30)))
            equipo, _ = execute(db, '''INSERT INTO equipo (nombre,id_torneo,id_facultad,ci_capitan)
                VALUES ('Plantel con sancion',%s,2,50000201)''', (torneo,))
            for camiseta, jugador in enumerate((50000201, 50000202), start=1):
                execute(db, '''INSERT INTO equipo_jugador_torneo
                    (id_equipo,ci_jugador,id_torneo,numero_camiseta) VALUES (%s,%s,%s,%s)''',
                    (equipo, jugador, torneo, camiseta))
            execute(db, '''INSERT INTO sancion_jugador
                (ci_jugador,id_torneo,motivo,numero_fecha_inicio,cantidad_fechas)
                VALUES (50000202,%s,'disciplinaria',1,1)''', (torneo,))
            with self.assertRaises(MySQLError) as ctx:
                execute(db, 'DELETE FROM equipo_jugador_torneo WHERE id_equipo=%s AND ci_jugador=50000202',
                        (equipo,))
            self.assertEqual(ctx.exception.errno, 1644)
            self.assertIn('sanciones', ctx.exception.msg)
            self.assertEqual(fetch_one(db, 'SELECT COUNT(*) AS n FROM equipo_jugador_torneo WHERE id_equipo=%s',
                                       (equipo,))['n'], 2)
            db.rollback()


if __name__ == '__main__':
    unittest.main()
