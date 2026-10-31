-- Ejecutar DESPUÉS de torneo_ucu_creacion.sql, como administrador de MySQL.
-- Tabla adicional para permitir cierre de sesión real y expiración de tokens.
USE torneo_ucu;
CREATE TABLE IF NOT EXISTS sesion_api (
  token_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
  correo VARCHAR(150) NOT NULL,
  expira_en DATETIME NOT NULL,
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_sesion_login FOREIGN KEY (correo) REFERENCES login(correo) ON DELETE CASCADE,
  INDEX idx_sesion_expira (expira_en)
) ENGINE=InnoDB;

-- Permisos para la cuenta usada para autenticar y revocar tokens.
GRANT SELECT, INSERT, DELETE ON torneo_ucu.sesion_api
  TO 'torneo_app_administrador'@'localhost';
-- El planillero técnico NO tiene acceso a login ni a sesion_api.
