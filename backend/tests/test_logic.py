"""Pruebas unitarias sin servidor MySQL."""
from datetime import date
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from logic import (ValidationError, positive_int, validate_cancha, validate_equipo,  # noqa: E402
                   validate_gol, validate_partido, validate_planilla, validate_player,
                   validate_sancion, validate_tarjeta, validate_torneo,
                   validate_torneo_transition, validate_turno, verify_role)
from reports import REPORTS, adapt_rows, get_report  # noqa: E402
import reports  # noqa: E402


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.player = {
            'ci': 50000999, 'nombre': 'Valeria', 'apellido': 'Pérez',
            'email': 'VA@UCU.EDU.UY', 'fecha_nacimiento': '2000-06-20',
            'id_facultad': 1, 'tipo': 'grado',
        }

    def test_player_valid(self):
        value = validate_player(self.player)
        self.assertEqual(value['email'], 'va@ucu.edu.uy')
        self.assertEqual(value['ci'], 50000999)

    def test_invalid_ci(self):
        with self.assertRaises(ValidationError):
            validate_player({**self.player, 'ci': 'ABC123'})

    def test_future_birth(self):
        with self.assertRaises(ValidationError):
            validate_player({**self.player, 'fecha_nacimiento': date.today().isoformat()})

    def test_missing_name(self):
        with self.assertRaises(ValidationError):
            validate_player({**self.player, 'nombre': ''})

    def test_invalid_type(self):
        with self.assertRaises(ValidationError):
            validate_player({**self.player, 'tipo': 'director'})

    def test_player_rejects_structured_type(self):
        for invalid in ([], {}, None, True, 1):
            with self.subTest(tipo=invalid), self.assertRaises(ValidationError):
                validate_player({**self.player, 'tipo': invalid})

    def test_ci_cannot_change(self):
        with self.assertRaises(ValidationError):
            validate_player({**self.player, 'ci': 50000101}, expected_ci=50000999)

    def test_positive_int_rejects_bool(self):
        with self.assertRaises(ValidationError):
            positive_int(True, 'ID')

    def test_admin_permissions(self):
        self.assertTrue(verify_role('administrador', 'administracion'))
        self.assertFalse(verify_role('planillero', 'administracion'))
        self.assertTrue(verify_role('planillero', 'lectura'))
        self.assertFalse(verify_role('usuario_inventado', 'lectura'))


class EntityValidationTests(unittest.TestCase):
    def test_turno_must_be_one_hour_between_18_and_23(self):
        self.assertEqual(validate_turno({'hora_inicio': '18:00'}),
                         {'hora_inicio': '18:00:00', 'hora_fin': '19:00:00'})
        for bad in ({'hora_inicio': '17:00'}, {'hora_inicio': '23:00'}, {'hora_inicio': '18:30'},
                    {'hora_inicio': '18:00', 'hora_fin': '20:00'}, {'hora_inicio': '6pm'}):
            with self.assertRaises(ValidationError):
                validate_turno(bad)

    def test_torneo_dates_and_state(self):
        base = {'nombre': 'Interfacultades', 'anio': 2027, 'semestre': 1,
                'fecha_inicio': '2027-03-01', 'fecha_fin': '2027-06-30'}
        self.assertEqual(validate_torneo(base)['estado'], 'inscripción')
        for bad in ({'semestre': 3}, {'fecha_fin': '2027-02-01'}, {'estado': 'suspendido'}, {'anio': '20x7'}):
            with self.assertRaises(ValidationError):
                validate_torneo({**base, **bad})

    def test_torneo_cannot_go_back(self):
        validate_torneo_transition('inscripción', 'en curso')
        validate_torneo_transition('en curso', 'finalizado')
        with self.assertRaises(ValidationError):
            validate_torneo_transition('en curso', 'inscripción')
        with self.assertRaises(ValidationError):
            validate_torneo_transition('finalizado', 'en curso')

    def test_equipo_defaults_captain_shirt(self):
        data = validate_equipo({'nombre': 'Halcones', 'id_torneo': 1, 'id_facultad': 1, 'ci_capitan': 50000101})
        self.assertEqual(data['numero_camiseta_capitan'], 1)
        with self.assertRaises(ValidationError):
            validate_equipo({'nombre': 'X', 'id_torneo': 1, 'id_facultad': 1, 'ci_capitan': 1,
                             'numero_camiseta_capitan': 100})

    def test_cancha_surface_and_roof(self):
        self.assertTrue(validate_cancha({'nombre_cancha': 'A', 'superficie': 'parquet', 'techada': 'true'})['techada'])
        with self.assertRaises(ValidationError):
            validate_cancha({'nombre_cancha': 'A', 'superficie': 'césped', 'techada': True})
        with self.assertRaises(ValidationError):
            validate_cancha({'nombre_cancha': 'A', 'superficie': 'parquet', 'techada': 'quizás'})

    def test_partido_rejects_same_team(self):
        partido = {'id_torneo': 1, 'numero_fecha': 1, 'id_equipo_local': 1, 'id_equipo_visitante': 2,
                   'dia': '2026-10-05', 'id_turno': 1, 'nombre_cancha': 'Cancha A', 'id_complejo': 1}
        self.assertEqual(validate_partido(partido)['estado'], 'programado')
        with self.assertRaises(ValidationError):
            validate_partido({**partido, 'id_equipo_visitante': 1})
        with self.assertRaises(ValidationError):
            validate_partido({**partido, 'estado': 'suspendido'})

    def test_planilla_rejects_duplicates(self):
        rows = validate_planilla({'participantes': [{'ci_jugador': 1234567, 'id_equipo': 1}]})
        self.assertEqual(rows, [{'ci_jugador': 1234567, 'id_equipo': 1}])
        with self.assertRaises(ValidationError):
            validate_planilla({'participantes': [{'ci_jugador': 1234567, 'id_equipo': 1},
                                                 {'ci_jugador': 1234567, 'id_equipo': 2}]})
        with self.assertRaises(ValidationError):
            validate_planilla({'participantes': 'todos'})

    def test_goal_and_card_minutes(self):
        self.assertFalse(validate_gol({'ci_jugador': 1234567, 'minuto': 0})['autogol'])
        self.assertTrue(validate_gol({'ci_jugador': 1234567, 'minuto': 60, 'autogol': True})['autogol'])
        for bad in (61, -1, '10.5', True):
            with self.assertRaises(ValidationError):
                validate_gol({'ci_jugador': 1234567, 'minuto': bad})
        with self.assertRaises(ValidationError):
            validate_tarjeta({'ci_jugador': 1234567, 'minuto': 10, 'color': 'azul'})

    def test_catalog_fields_reject_structured_values(self):
        partido = {'id_torneo': 1, 'numero_fecha': 1, 'id_equipo_local': 1,
                   'id_equipo_visitante': 2, 'dia': '2026-10-05', 'id_turno': 1,
                   'nombre_cancha': 'Cancha A', 'id_complejo': 1}
        for invalid in ([], {}, None, True, 1):
            for validate, payload in (
                (validate_tarjeta, {'ci_jugador': 1234567, 'minuto': 10, 'color': invalid}),
                (validate_cancha, {'nombre_cancha': 'A', 'superficie': invalid, 'techada': True}),
                (validate_partido, {**partido, 'estado': invalid}),
            ):
                with self.subTest(validator=validate.__name__, value=invalid), self.assertRaises(ValidationError):
                    validate(payload)

    def test_only_disciplinary_sanctions_are_manual(self):
        data = validate_sancion({'ci_jugador': 1234567, 'id_torneo': 1,
                                 'numero_fecha_inicio': 2, 'cantidad_fechas': 3})
        self.assertEqual(data['cantidad_fechas'], 3)
        with self.assertRaises(ValidationError):
            validate_sancion({**data, 'motivo': 'roja'})
        with self.assertRaises(ValidationError):
            validate_sancion({**data, 'cantidad_fechas': 0})


class ReportTests(unittest.TestCase):
    def test_all_twelve_reports_available(self):
        self.assertEqual(len(REPORTS), 12)
        self.assertIn('goles-tramos', REPORTS)

    def test_top_scorer_has_display_name(self):
        result = adapt_rows('goleadores', [{'nombre': 'Sofía', 'apellido': 'Pereira', 'goles': 2}])
        self.assertEqual(result[0]['nombre_completo'], 'Sofía Pereira')

    def test_round_average_has_readable_label(self):
        rows = adapt_rows('promedio-goles', [
            {'numero_fecha': 3, 'alcance': 'fecha'},
            {'numero_fecha': None, 'alcance': 'edicion'},
        ])
        self.assertEqual([r['fecha'] for r in rows], ['Fecha 3', 'Toda la edición'])

    def test_match_status_is_four_rows(self):
        data = {'jugados': 10, 'postergados': 1, 'cancelados': 1, 'programados': 1,
                'porcentaje_jugados': 76.92, 'porcentaje_postergados': 7.69,
                'porcentaje_cancelados': 7.69, 'porcentaje_programados': 7.69}
        result = adapt_rows('estados', [data])
        self.assertEqual(len(result), 4)
        self.assertEqual(sum(row['cantidad'] for row in result), 13)

    def test_query_uses_parameter_not_interpolation(self):
        with patch.object(reports, 'fetch_all', Mock(return_value=[])) as fetch:
            get_report(None, 'posiciones', 14)
        sql, params = fetch.call_args.args[1:]
        self.assertIn('WHERE id_torneo = %s', sql)
        self.assertEqual(params, (14,))

    def test_faculty_counts_are_global_by_original_sql(self):
        with patch.object(reports, 'fetch_all', Mock(return_value=[])) as fetch:
            get_report(None, 'jugadores-facultad', 14)
        sql = fetch.call_args.args[1]
        self.assertNotIn('WHERE id_torneo', sql)


if __name__ == '__main__':
    unittest.main()
