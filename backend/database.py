"""Conexión a MySQL mediante SQL directo y cursores parametrizados; sin ORM."""
import os
from contextlib import contextmanager
from datetime import date, datetime, time, timedelta
from decimal import Decimal

import mysql.connector


def _settings(role):
    if role not in ('administrador', 'planillero'):
        raise ValueError('Rol de base de datos no permitido')
    prefix = 'MYSQL_ADMIN' if role == 'administrador' else 'MYSQL_PLANILLERO'
    user = os.getenv(prefix + '_USER', '').strip()
    password = os.getenv(prefix + '_PASSWORD', '')
    if not user or not password:
        raise RuntimeError(f'Faltan {prefix}_USER y {prefix}_PASSWORD en backend/.env')
    return dict(
        host=os.getenv('MYSQL_HOST', '127.0.0.1'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        database=os.getenv('MYSQL_DATABASE', 'torneo_ucu'),
        user=user, password=password,
        connection_timeout=5,
        charset='utf8mb4',
        autocommit=False,
    )


@contextmanager
def connection(role='administrador'):
    db = mysql.connector.connect(**_settings(role))
    try:
        yield db
    finally:
        db.close()


def fetch_all(db, sql, params=()):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        cursor.close()


def fetch_one(db, sql, params=()):
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        return cursor.fetchone()
    finally:
        cursor.close()


def execute(db, sql, params=()):
    cursor = db.cursor()
    try:
        cursor.execute(sql, params)
        return cursor.lastrowid, cursor.rowcount
    finally:
        cursor.close()


def to_json_value(value):
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    # MySQL TIME suele llegar desde mysql.connector como timedelta.
    if isinstance(value, timedelta):
        seconds = int(value.total_seconds())
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return f'{hours:02}:{minutes:02}:{seconds:02}'
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, list):
        return [to_json_value(v) for v in value]
    if isinstance(value, dict):
        return {k: to_json_value(v) for k, v in value.items()}
    return value
