"""Doble de mysql.connector para probar la API sin servidor MySQL.

Registra cada sentencia con sus parámetros, los COMMIT/ROLLBACK y la cuenta
técnica usada en cada conexión. Las respuestas se programan por fragmento de SQL.
"""
import hashlib

from mysql.connector import errors

ADMIN_TOKEN = 'a' * 43
PLANILLERO_TOKEN = 'p' * 43


class Result:
    """Respuesta de un INSERT/UPDATE/DELETE."""
    def __init__(self, rowcount=1, lastrowid=1):
        self.rowcount, self.lastrowid = rowcount, lastrowid


def mysql_error(errno, msg, sqlstate=None):
    return errors.DatabaseError(msg=msg, errno=errno, sqlstate=sqlstate)


def signal(msg):
    """Error tal como llega desde un SIGNAL SQLSTATE '45000' de un trigger."""
    return mysql_error(1644, msg, '45000')


class FakeDB:
    def __init__(self):
        self.rules = []
        self.queries = []
        self.commits = 0
        self.rollbacks = 0
        self.users = []
        self.sessions = {
            hashlib.sha256(ADMIN_TOKEN.encode()).hexdigest(): {'correo': 'admin@demo', 'rol': 'administrador'},
            hashlib.sha256(PLANILLERO_TOKEN.encode()).hexdigest(): {'correo': 'plan@demo', 'rol': 'planillero'},
        }

    def on(self, fragment, response):
        """Programa la respuesta para el SQL que contenga `fragment` (la última regla gana)."""
        self.rules.append((fragment, response))
        return self

    def connect(self, **kwargs):
        self.users.append(kwargs['user'])
        return FakeConnection(self, kwargs['user'])

    def respond(self, sql, params):
        if 'FROM sesion_api s JOIN login' in sql:
            return self.sessions.get(params[0])
        for fragment, response in reversed(self.rules):
            if fragment in sql:
                if callable(response):
                    response = response(sql, params)
                if isinstance(response, Exception):
                    raise response
                return response
        return None

    def executed(self, fragment):
        """Sentencias (sql, params, usuario) que contienen el fragmento, sin contar la autenticación."""
        return [q for q in self.queries if fragment in q[0] and 'sesion_api s JOIN login' not in q[0]]


class FakeConnection:
    def __init__(self, fake, user):
        self.fake, self.user = fake, user

    def cursor(self, dictionary=False):
        return FakeCursor(self)

    def commit(self):
        self.fake.commits += 1

    def rollback(self):
        self.fake.rollbacks += 1

    def close(self):
        pass


class FakeCursor:
    def __init__(self, conn):
        self.conn = conn
        self.rows, self.rowcount, self.lastrowid = [], 0, None

    def execute(self, sql, params=()):
        sql = ' '.join(sql.split())
        self.conn.fake.queries.append((sql, tuple(params), self.conn.user))
        result = self.conn.fake.respond(sql, tuple(params))
        if isinstance(result, Result):
            self.rows, self.rowcount, self.lastrowid = [], result.rowcount, result.lastrowid
        elif result is None and not sql.lstrip().upper().startswith('SELECT'):
            self.rows, self.rowcount, self.lastrowid = [], 1, 1
        else:
            self.rows = [] if result is None else [dict(r) for r in (result if isinstance(result, list) else [result])]
            self.rowcount = len(self.rows)

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def close(self):
        pass
