#!/bin/bash
# Inicializa la base del contenedor con los scripts del repositorio, sin modificarlos.
# - Las cuentas técnicas se crean para '%' (el backend se conecta desde otro contenedor/host).
# - Las claves aleatorias de CREATE USER se reemplazan por las del archivo .env.
set -eo pipefail

run_sql() {
  mysql --protocol=socket -uroot -p"${MYSQL_ROOT_PASSWORD}" --default-character-set=utf8mb4 "$@"
}

adapt() {
  # Quita CR (checkout en Windows) y cambia el host de las cuentas a '%'.
  sed -e 's/\r$//' -e "s/'@'localhost'/'@'%'/g" "$1"
}

echo '[init] torneo_ucu_creacion.sql'
adapt /sql/torneo_ucu_creacion.sql | run_sql > /dev/null

echo '[init] sesiones.sql'
adapt /sql/sesiones.sql | run_sql

echo '[init] claves de las cuentas técnicas'
run_sql <<SQL
ALTER USER 'torneo_app_administrador'@'%' IDENTIFIED BY '${MYSQL_ADMIN_PASSWORD}';
ALTER USER 'torneo_app_planillero'@'%' IDENTIFIED BY '${MYSQL_PLANILLERO_PASSWORD}';
SQL
