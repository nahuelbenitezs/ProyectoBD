"""Prueba del backend en ejecución, sin librerías adicionales.

Ejemplo (NO guardar credenciales en Git):
  API_TEST_EMAIL=admin@demo.ucu.edu.uy API_TEST_PASSWORD='...' \
    python backend/tests/smoke_live.py
"""
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = os.getenv('API_TEST_BASE_URL', 'http://127.0.0.1:5000/api').rstrip('/')
EMAIL = os.getenv('API_TEST_EMAIL', '')
PASSWORD = os.getenv('API_TEST_PASSWORD', '')


def call(path, *, method='GET', token=None, payload=None):
    body = json.dumps(payload).encode('utf-8') if payload is not None else None
    headers = {'Accept': 'application/json'}
    if payload is not None:
        headers['Content-Type'] = 'application/json'
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = Request(BASE_URL + path, data=body, method=method, headers=headers)
    try:
        with urlopen(req, timeout=10) as resp:
            data = resp.read().decode('utf-8')
            return resp.status, json.loads(data) if data else None
    except HTTPError as err:
        data = err.read().decode('utf-8')
        return err.code, json.loads(data) if data else None


def main():
    if not EMAIL or not PASSWORD:
        print('Configurá API_TEST_EMAIL y API_TEST_PASSWORD antes de ejecutar esta prueba.')
        return 2
    status, health = call('/health')
    assert status == 200 and health['status'] == 'ok', ('health', status, health)
    status, login = call('/auth/login', method='POST', payload={'correo': EMAIL, 'contrasena': PASSWORD})
    assert status == 200, ('login', status, login)
    token = login['token']
    status, db = call('/bootstrap', token=token)
    assert status == 200 and all(key in db for key in ('partido', 'jugador', 'gol', 'torneo', 'equipo')), ('bootstrap', status, db)
    print(f"Bootstrap: {len(db['equipo'])} equipos, {len(db['jugador'])} jugadores, {len(db['partido'])} partidos")
    for slug in ('posiciones', 'goleadores', 'fair-play', 'promedio-goles', 'uso-espacios',
                 'jugadores-facultad', 'sin-participacion', 'sanciones', 'estados',
                 'local-visitante', 'disciplina', 'goles-tramos'):
        status, rows = call(f'/reportes/{slug}?id_torneo=1', token=token)
        assert status == 200 and isinstance(rows, list), (slug, status, rows)
        print(f'OK /reportes/{slug}: {len(rows)} filas')
    if login['user']['rol'] == 'planillero':
        status, _ = call('/jugadores', token=token, method='POST', payload={})
        assert status == 403, ('planillero puede escribir jugadores', status)
        print('OK permisos: planillero no puede crear jugadores')
    status, result = call('/auth/logout', token=token, method='POST')
    assert status == 200 and result['ok'] is True, ('logout', status, result)
    status, _ = call('/bootstrap', token=token)
    assert status == 401, ('token no fue revocado', status)
    print('OK: token revocado. Prueba de API completada.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (AssertionError, URLError, ValueError) as exc:
        print('Falló la prueba:', exc)
        sys.exit(1)
