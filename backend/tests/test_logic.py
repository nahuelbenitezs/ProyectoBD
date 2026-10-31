"""Pruebas unitarias sin servidor MySQL ni dependencias de Flask."""
from datetime import date
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# Inyectar solo para probar las transformaciones del módulo reportes.
if 'database' not in sys.modules:
    fake_database = types.ModuleType('database')
    fake_database.fetch_all = Mock(return_value=[])
    sys.modules['database'] = fake_database

from logic import ValidationError, positive_int, validate_player, verify_role  # noqa: E402
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
        reports.fetch_all = Mock(return_value=[])
        get_report(None, 'posiciones', 14)
        sql, params = reports.fetch_all.call_args.args[1:]
        self.assertIn('WHERE id_torneo = %s', sql)
        self.assertEqual(params, (14,))

    def test_faculty_counts_are_global_by_original_sql(self):
        reports.fetch_all = Mock(return_value=[])
        get_report(None, 'jugadores-facultad', 14)
        sql = reports.fetch_all.call_args.args[1]
        self.assertNotIn('WHERE id_torneo', sql)


if __name__ == '__main__':
    unittest.main()
