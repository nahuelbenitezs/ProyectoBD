-- Torneo Interfacultades de Futbol 5 - MySQL 8.0.18 o superior
-- Esquema, datos de prueba, integridad y 12 reportes (9 + 3 propuestos).
-- Incluye un partido 0-0 (fecha 4) con planilla y sin goles registrados.
-- Ejecutar en una base de datos VACIA desde MySQL Workbench o cliente mysql.
-- El script crea y selecciona el esquema torneo_ucu antes de crear las tablas.
-- Requiere cuenta de instalacion con CREATE USER y permiso para GRANT.
-- Las cuentas se crean con contrasenas aleatorias (NO se guardan en este archivo).
-- IMPORTANTE: guardar las claves mostradas por MySQL al crear las cuentas.
-- CREATE TABLE y CREATE TRIGGER implican COMMIT en MySQL; DDL no es transaccional.

CREATE DATABASE torneo_ucu CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE torneo_ucu;

CREATE TABLE login (
    correo VARCHAR(150) PRIMARY KEY,
    contrasena VARCHAR(255) NOT NULL,
    rol ENUM('administrador', 'planillero') NOT NULL
) ENGINE=InnoDB;

CREATE TABLE facultad (
    id_facultad INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE torneo (
    id_torneo INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    anio INT NOT NULL,
    semestre TINYINT NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    estado ENUM('inscripción', 'en curso', 'finalizado') NOT NULL DEFAULT 'inscripción',
    CONSTRAINT uq_torneo_edicion UNIQUE (anio, semestre),
    CONSTRAINT chk_torneo_semestre CHECK (semestre IN (1, 2)),
    CONSTRAINT chk_torneo_fechas CHECK (fecha_fin >= fecha_inicio)
) ENGINE=InnoDB;

CREATE TABLE complejo (
    id_complejo INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    direccion VARCHAR(150) NOT NULL,
    departamento VARCHAR(100) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE cancha (
    nombre_cancha VARCHAR(100) NOT NULL,
    id_complejo INT NOT NULL,
    superficie ENUM('sintético', 'parquet') NOT NULL,
    techada BOOLEAN NOT NULL,
    PRIMARY KEY (nombre_cancha, id_complejo),
    CONSTRAINT fk_cancha_complejo FOREIGN KEY (id_complejo) REFERENCES complejo(id_complejo),
    CONSTRAINT chk_cancha_techada CHECK (techada IN (0, 1))
) ENGINE=InnoDB;

CREATE TABLE turno (
    id_turno INT AUTO_INCREMENT PRIMARY KEY,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    CONSTRAINT uq_turno_horas UNIQUE (hora_inicio, hora_fin),
    CONSTRAINT chk_turno_horario CHECK (
        hora_inicio >= '18:00:00' AND hora_fin <= '23:00:00'
        AND MINUTE(hora_inicio) = 0 AND SECOND(hora_inicio) = 0
        AND TIMEDIFF(hora_fin, hora_inicio) = '01:00:00'
    )
) ENGINE=InnoDB;

CREATE TABLE jugador (
    ci INT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    fecha_nacimiento DATE NOT NULL,
    id_facultad INT NOT NULL,
    tipo ENUM('grado', 'posgrado', 'docente', 'funcionario') NOT NULL,
    CONSTRAINT fk_jugador_facultad FOREIGN KEY (id_facultad) REFERENCES facultad(id_facultad),
    CONSTRAINT chk_jugador_ci CHECK (ci > 0)
) ENGINE=InnoDB;

CREATE TABLE equipo (
    id_equipo INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    id_torneo INT NOT NULL,
    id_facultad INT NOT NULL,
    ci_capitan INT NOT NULL,
    CONSTRAINT fk_equipo_torneo FOREIGN KEY (id_torneo) REFERENCES torneo(id_torneo),
    CONSTRAINT fk_equipo_facultad FOREIGN KEY (id_facultad) REFERENCES facultad(id_facultad),
    CONSTRAINT fk_equipo_capitan FOREIGN KEY (ci_capitan) REFERENCES jugador(ci),
    CONSTRAINT uq_equipo_torneo UNIQUE (id_equipo, id_torneo),
    CONSTRAINT uq_equipo_nombre_edicion UNIQUE (id_torneo, nombre)
) ENGINE=InnoDB;

CREATE TABLE equipo_jugador_torneo (
    id_equipo INT NOT NULL,
    ci_jugador INT NOT NULL,
    id_torneo INT NOT NULL,
    numero_camiseta INT NOT NULL,
    PRIMARY KEY (id_equipo, ci_jugador, id_torneo),
    CONSTRAINT fk_plantel_equipo FOREIGN KEY (id_equipo, id_torneo)
        REFERENCES equipo(id_equipo, id_torneo),
    CONSTRAINT fk_plantel_jugador FOREIGN KEY (ci_jugador) REFERENCES jugador(ci),
    CONSTRAINT uq_plantel_camiseta UNIQUE (id_equipo, id_torneo, numero_camiseta),
    CONSTRAINT uq_plantel_jugador_edicion UNIQUE (ci_jugador, id_torneo),
    CONSTRAINT chk_plantel_camiseta CHECK (numero_camiseta BETWEEN 1 AND 99)
) ENGINE=InnoDB;

CREATE TABLE partido (
    id_partido INT AUTO_INCREMENT PRIMARY KEY,
    id_torneo INT NOT NULL,
    numero_fecha INT NOT NULL,
    id_equipo_local INT NOT NULL,
    id_equipo_visitante INT NOT NULL,
    dia DATE NOT NULL,
    id_turno INT NOT NULL,
    nombre_cancha VARCHAR(100) NOT NULL,
    id_complejo INT NOT NULL,
    estado ENUM('programado', 'jugado', 'postergado', 'cancelado') NOT NULL DEFAULT 'programado',
    -- Claves generadas para confrontaciones no ordenadas y reservas activas.
    rival_menor INT GENERATED ALWAYS AS (LEAST(id_equipo_local, id_equipo_visitante)) STORED,
    rival_mayor INT GENERATED ALWAYS AS (GREATEST(id_equipo_local, id_equipo_visitante)) STORED,
    rival_vigente TINYINT GENERATED ALWAYS AS (
        CASE WHEN estado = 'cancelado' THEN NULL ELSE 1 END
    ) STORED,
    reserva_vigente TINYINT GENERATED ALWAYS AS (
        CASE WHEN estado IN ('cancelado', 'postergado') THEN NULL ELSE 1 END
    ) STORED,
    CONSTRAINT fk_partido_torneo FOREIGN KEY (id_torneo) REFERENCES torneo(id_torneo),
    CONSTRAINT fk_partido_local FOREIGN KEY (id_equipo_local, id_torneo)
        REFERENCES equipo(id_equipo, id_torneo),
    CONSTRAINT fk_partido_visitante FOREIGN KEY (id_equipo_visitante, id_torneo)
        REFERENCES equipo(id_equipo, id_torneo),
    CONSTRAINT fk_partido_turno FOREIGN KEY (id_turno) REFERENCES turno(id_turno),
    CONSTRAINT fk_partido_cancha FOREIGN KEY (nombre_cancha, id_complejo)
        REFERENCES cancha(nombre_cancha, id_complejo),
    CONSTRAINT uq_partido_reserva UNIQUE
        (dia, id_turno, nombre_cancha, id_complejo, reserva_vigente),
    CONSTRAINT uq_partido_rivales UNIQUE
        (id_torneo, rival_menor, rival_mayor, rival_vigente),
    CONSTRAINT chk_partido_rivales CHECK (id_equipo_local <> id_equipo_visitante),
    CONSTRAINT chk_partido_fecha CHECK (numero_fecha > 0),
    INDEX idx_partido_fecha (id_torneo, numero_fecha, estado),
    INDEX idx_partido_local (id_equipo_local, id_torneo),
    INDEX idx_partido_visitante (id_equipo_visitante, id_torneo)
) ENGINE=InnoDB;

CREATE TABLE planilla_partido (
    id_partido INT NOT NULL,
    ci_jugador INT NOT NULL,
    id_equipo INT NOT NULL,
    PRIMARY KEY (id_partido, ci_jugador),
    CONSTRAINT fk_planilla_partido FOREIGN KEY (id_partido) REFERENCES partido(id_partido),
    CONSTRAINT fk_planilla_jugador FOREIGN KEY (ci_jugador) REFERENCES jugador(ci),
    CONSTRAINT fk_planilla_equipo FOREIGN KEY (id_equipo) REFERENCES equipo(id_equipo),
    INDEX idx_planilla_equipo (id_equipo, id_partido)
) ENGINE=InnoDB;

CREATE TABLE gol (
    id_gol INT AUTO_INCREMENT PRIMARY KEY,
    id_partido INT NOT NULL,
    ci_jugador INT NOT NULL,
    minuto INT NOT NULL,
    autogol BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_gol_planilla FOREIGN KEY (id_partido, ci_jugador)
        REFERENCES planilla_partido(id_partido, ci_jugador),
    CONSTRAINT chk_gol_minuto CHECK (minuto BETWEEN 0 AND 60),
    CONSTRAINT chk_gol_autogol CHECK (autogol IN (0, 1))
) ENGINE=InnoDB;

CREATE TABLE tarjeta (
    id_tarjeta INT AUTO_INCREMENT PRIMARY KEY,
    id_partido INT NOT NULL,
    ci_jugador INT NOT NULL,
    minuto INT NOT NULL,
    color ENUM('amarilla', 'roja') NOT NULL,
    CONSTRAINT fk_tarjeta_planilla FOREIGN KEY (id_partido, ci_jugador)
        REFERENCES planilla_partido(id_partido, ci_jugador),
    CONSTRAINT chk_tarjeta_minuto CHECK (minuto BETWEEN 0 AND 60)
) ENGINE=InnoDB;

CREATE TABLE sancion_jugador (
    id_sancion INT AUTO_INCREMENT PRIMARY KEY,
    ci_jugador INT NOT NULL,
    id_torneo INT NOT NULL,
    motivo ENUM('roja', 'acumulación de amarillas', 'disciplinaria') NOT NULL,
    numero_fecha_inicio INT NOT NULL,
    cantidad_fechas INT NOT NULL,
    origen ENUM('manual', 'automatica') NOT NULL DEFAULT 'manual',
    CONSTRAINT fk_sancion_jugador FOREIGN KEY (ci_jugador) REFERENCES jugador(ci),
    CONSTRAINT fk_sancion_torneo FOREIGN KEY (id_torneo) REFERENCES torneo(id_torneo),
    CONSTRAINT chk_sancion_fecha CHECK (numero_fecha_inicio > 0),
    CONSTRAINT chk_sancion_duracion CHECK (cantidad_fechas > 0),
    -- Las automaticas se derivan de las tarjetas: nunca se almacenan manualmente.
    CONSTRAINT chk_sancion_solo_manual CHECK (origen = 'manual' AND motivo = 'disciplinaria'),
    CONSTRAINT uq_sancion_evento UNIQUE
        (ci_jugador, id_torneo, motivo, numero_fecha_inicio, origen),
    INDEX idx_sancion_vigencia (ci_jugador, id_torneo, numero_fecha_inicio)
) ENGINE=InnoDB;

START TRANSACTION;

-- LOGIN
INSERT INTO login (correo, contrasena, rol) VALUES
  ('admin@demo.ucu.edu.uy', SHA2('AdminDemo2026!', 256), 'administrador'),
  ('planillero@demo.ucu.edu.uy', SHA2('PlanillaDemo2026!', 256), 'planillero');

-- FACULTAD
INSERT INTO facultad (nombre) VALUES
  ('Ingenieria'),
  ('Ciencias Empresariales'),
  ('Derecho'),
  ('Ciencias de la Salud'),
  ('Humanidades'),
  ('Psicologia');

-- TORNEO
INSERT INTO torneo (nombre, anio, semestre, fecha_inicio, fecha_fin, estado) VALUES
  ('Interfacultades Futbol 5 - 2026 S2', 2026, 2, '2026-10-01', '2026-11-30', 'en curso');

-- COMPLEJO
INSERT INTO complejo (nombre, direccion, departamento) VALUES
  ('Complejo Norte', 'Av. Demo 1200', 'Montevideo'),
  ('Complejo Sur', 'Calle Ejemplo 550', 'Montevideo');

-- CANCHA
INSERT INTO cancha (nombre_cancha, id_complejo, superficie, techada) VALUES
  ('Cancha A', 1, 'sintético', FALSE),
  ('Cancha B', 1, 'sintético', TRUE),
  ('Cancha 1', 2, 'parquet', TRUE);

-- TURNO
INSERT INTO turno (hora_inicio, hora_fin) VALUES
  ('18:00:00', '19:00:00'),
  ('19:00:00', '20:00:00'),
  ('20:00:00', '21:00:00'),
  ('21:00:00', '22:00:00'),
  ('22:00:00', '23:00:00');

-- JUGADOR
INSERT INTO jugador (ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo) VALUES
  (50000101, 'Sofia', 'Pereira', 'spereira@example.edu.uy', '1991-02-11', 1, 'grado'),
  (50000102, 'Martin', 'Rodriguez', 'mrodriguez@example.edu.uy', '1992-02-12', 1, 'grado'),
  (50000103, 'Camila', 'Fernandez', 'cfernandez@example.edu.uy', '1993-02-13', 1, 'grado'),
  (50000104, 'Luciano', 'Silva', 'lsilva@example.edu.uy', '1994-02-14', 1, 'grado'),
  (50000105, 'Valentina', 'Gonzalez', 'vgonzalez@example.edu.uy', '1995-02-15', 1, 'posgrado'),
  (50000106, 'Nicolas', 'Lopez', 'nlopez@example.edu.uy', '1996-02-16', 1, 'docente'),
  (50000107, 'Florencia', 'Martinez', 'fmartinez@example.edu.uy', '1997-02-17', 1, 'grado'),
  (50000201, 'Sofia', 'Rodriguez', 'srodriguez@example.edu.uy', '1991-03-11', 2, 'grado'),
  (50000202, 'Martin', 'Fernandez', 'mfernandez@example.edu.uy', '1992-03-12', 2, 'grado'),
  (50000203, 'Camila', 'Silva', 'csilva@example.edu.uy', '1993-03-13', 2, 'grado'),
  (50000204, 'Luciano', 'Gonzalez', 'lgonzalez@example.edu.uy', '1994-03-14', 2, 'grado'),
  (50000205, 'Valentina', 'Lopez', 'vlopez@example.edu.uy', '1995-03-15', 2, 'posgrado'),
  (50000206, 'Nicolas', 'Martinez', 'nmartinez@example.edu.uy', '1996-03-16', 2, 'docente'),
  (50000207, 'Florencia', 'Pereira', 'fpereira@example.edu.uy', '1997-03-17', 2, 'funcionario'),
  (50000301, 'Sofia', 'Fernandez', 'sfernandez@example.edu.uy', '1991-04-11', 3, 'grado'),
  (50000302, 'Martin', 'Silva', 'msilva@example.edu.uy', '1992-04-12', 3, 'grado'),
  (50000303, 'Camila', 'Gonzalez', 'cgonzalez@example.edu.uy', '1993-04-13', 3, 'grado'),
  (50000304, 'Luciano', 'Lopez', 'llopez@example.edu.uy', '1994-04-14', 3, 'grado'),
  (50000305, 'Valentina', 'Martinez', 'vmartinez@example.edu.uy', '1995-04-15', 3, 'posgrado'),
  (50000306, 'Nicolas', 'Pereira', 'npereira@example.edu.uy', '1996-04-16', 3, 'docente'),
  (50000307, 'Florencia', 'Rodriguez', 'frodriguez@example.edu.uy', '1997-04-17', 3, 'grado'),
  (50000401, 'Sofia', 'Silva', 'ssilva@example.edu.uy', '1991-05-11', 4, 'grado'),
  (50000402, 'Martin', 'Gonzalez', 'mgonzalez@example.edu.uy', '1992-05-12', 4, 'grado'),
  (50000403, 'Camila', 'Lopez', 'clopez@example.edu.uy', '1993-05-13', 4, 'grado'),
  (50000404, 'Luciano', 'Martinez', 'lmartinez@example.edu.uy', '1994-05-14', 4, 'grado'),
  (50000405, 'Valentina', 'Pereira', 'vpereira@example.edu.uy', '1995-05-15', 4, 'posgrado'),
  (50000406, 'Nicolas', 'Rodriguez', 'nrodriguez@example.edu.uy', '1996-05-16', 4, 'docente'),
  (50000407, 'Florencia', 'Fernandez', 'ffernandez@example.edu.uy', '1997-05-17', 4, 'funcionario'),
  (50000501, 'Sofia', 'Gonzalez', 'sgonzalez@example.edu.uy', '1991-06-11', 5, 'grado'),
  (50000502, 'Martin', 'Lopez', 'mlopez@example.edu.uy', '1992-06-12', 5, 'grado'),
  (50000503, 'Camila', 'Martinez', 'cmartinez@example.edu.uy', '1993-06-13', 5, 'grado'),
  (50000504, 'Luciano', 'Pereira', 'lpereira@example.edu.uy', '1994-06-14', 5, 'grado'),
  (50000505, 'Valentina', 'Rodriguez', 'vrodriguez@example.edu.uy', '1995-06-15', 5, 'posgrado'),
  (50000506, 'Nicolas', 'Fernandez', 'nfernandez@example.edu.uy', '1996-06-16', 5, 'docente'),
  (50000507, 'Florencia', 'Silva', 'fsilva@example.edu.uy', '1997-06-17', 5, 'grado'),
  (50000601, 'Sofia', 'Lopez', 'slopez@example.edu.uy', '1991-07-11', 6, 'grado'),
  (50000602, 'Martin', 'Martinez', 'mmartinez@example.edu.uy', '1992-07-12', 6, 'grado'),
  (50000603, 'Camila', 'Pereira', 'cpereira@example.edu.uy', '1993-07-13', 6, 'grado'),
  (50000604, 'Luciano', 'Rodriguez', 'lrodriguez@example.edu.uy', '1994-07-14', 6, 'grado'),
  (50000605, 'Valentina', 'Fernandez', 'vfernandez@example.edu.uy', '1995-07-15', 6, 'posgrado'),
  (50000606, 'Nicolas', 'Silva', 'nsilva@example.edu.uy', '1996-07-16', 6, 'docente'),
  (50000607, 'Florencia', 'Gonzalez', 'fgonzalez@example.edu.uy', '1997-07-17', 6, 'grado');

-- EQUIPO
INSERT INTO equipo (nombre, id_torneo, id_facultad, ci_capitan) VALUES
  ('Halcones', 1, 1, 50000101),
  ('Tigres', 1, 2, 50000201),
  ('Leones', 1, 3, 50000301),
  ('Pumas', 1, 4, 50000401),
  ('Lobos', 1, 5, 50000501),
  ('Aguilas', 1, 6, 50000601);

-- EQUIPO_JUGADOR_TORNEO
INSERT INTO equipo_jugador_torneo (id_equipo, ci_jugador, id_torneo, numero_camiseta) VALUES
  (1, 50000101, 1, 1),
  (1, 50000102, 1, 2),
  (1, 50000103, 1, 3),
  (1, 50000104, 1, 4),
  (1, 50000105, 1, 5),
  (1, 50000106, 1, 6),
  (1, 50000107, 1, 7),
  (2, 50000201, 1, 1),
  (2, 50000202, 1, 2),
  (2, 50000203, 1, 3),
  (2, 50000204, 1, 4),
  (2, 50000205, 1, 5),
  (2, 50000206, 1, 6),
  (2, 50000207, 1, 7),
  (3, 50000301, 1, 1),
  (3, 50000302, 1, 2),
  (3, 50000303, 1, 3),
  (3, 50000304, 1, 4),
  (3, 50000305, 1, 5),
  (3, 50000306, 1, 6),
  (3, 50000307, 1, 7),
  (4, 50000401, 1, 1),
  (4, 50000402, 1, 2),
  (4, 50000403, 1, 3),
  (4, 50000404, 1, 4),
  (4, 50000405, 1, 5),
  (4, 50000406, 1, 6),
  (4, 50000407, 1, 7),
  (5, 50000501, 1, 1),
  (5, 50000502, 1, 2),
  (5, 50000503, 1, 3),
  (5, 50000504, 1, 4),
  (5, 50000505, 1, 5),
  (5, 50000506, 1, 6),
  (5, 50000507, 1, 7),
  (6, 50000601, 1, 1),
  (6, 50000602, 1, 2),
  (6, 50000603, 1, 3),
  (6, 50000604, 1, 4),
  (6, 50000605, 1, 5),
  (6, 50000606, 1, 6),
  (6, 50000607, 1, 7);

-- PARTIDO
INSERT INTO partido (id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante, dia, id_turno, nombre_cancha, id_complejo, estado) VALUES
  (1, 1, 1, 6, '2026-10-05', 1, 'Cancha A', 1, 'jugado'),
  (1, 1, 2, 5, '2026-10-05', 1, 'Cancha B', 1, 'jugado'),
  (1, 1, 3, 4, '2026-10-05', 1, 'Cancha 1', 2, 'jugado'),
  (1, 2, 1, 5, '2026-10-12', 1, 'Cancha A', 1, 'jugado'),
  (1, 2, 6, 4, '2026-10-12', 1, 'Cancha B', 1, 'jugado'),
  (1, 2, 2, 3, '2026-10-12', 1, 'Cancha 1', 2, 'jugado'),
  (1, 3, 1, 4, '2026-10-19', 1, 'Cancha A', 1, 'jugado'),
  (1, 3, 5, 3, '2026-10-19', 1, 'Cancha B', 1, 'jugado'),
  (1, 3, 6, 2, '2026-10-19', 1, 'Cancha 1', 2, 'jugado');

-- PLANILLA_PARTIDO
INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES
  (1, 50000101, 1),
  (1, 50000102, 1),
  (1, 50000103, 1),
  (1, 50000104, 1),
  (1, 50000105, 1),
  (1, 50000601, 6),
  (1, 50000602, 6),
  (1, 50000603, 6),
  (1, 50000604, 6),
  (1, 50000605, 6),
  (2, 50000201, 2),
  (2, 50000202, 2),
  (2, 50000203, 2),
  (2, 50000204, 2),
  (2, 50000205, 2),
  (2, 50000501, 5),
  (2, 50000502, 5),
  (2, 50000503, 5),
  (2, 50000504, 5),
  (2, 50000505, 5),
  (3, 50000301, 3),
  (3, 50000302, 3),
  (3, 50000303, 3),
  (3, 50000304, 3),
  (3, 50000305, 3),
  (3, 50000401, 4),
  (3, 50000402, 4),
  (3, 50000403, 4),
  (3, 50000404, 4),
  (3, 50000405, 4),
  (4, 50000101, 1),
  (4, 50000102, 1),
  (4, 50000104, 1),
  (4, 50000105, 1),
  (4, 50000106, 1),
  (4, 50000501, 5),
  (4, 50000502, 5),
  (4, 50000503, 5),
  (4, 50000504, 5),
  (4, 50000505, 5),
  (5, 50000601, 6),
  (5, 50000602, 6),
  (5, 50000603, 6),
  (5, 50000604, 6),
  (5, 50000605, 6),
  (5, 50000401, 4),
  (5, 50000402, 4),
  (5, 50000403, 4),
  (5, 50000404, 4),
  (5, 50000405, 4),
  (6, 50000201, 2),
  (6, 50000202, 2),
  (6, 50000203, 2),
  (6, 50000204, 2),
  (6, 50000205, 2),
  (6, 50000301, 3),
  (6, 50000302, 3),
  (6, 50000303, 3),
  (6, 50000304, 3),
  (6, 50000305, 3),
  (7, 50000101, 1),
  (7, 50000102, 1),
  (7, 50000103, 1),
  (7, 50000104, 1),
  (7, 50000105, 1),
  (7, 50000401, 4),
  (7, 50000402, 4),
  (7, 50000403, 4),
  (7, 50000404, 4),
  (7, 50000405, 4),
  (8, 50000501, 5),
  (8, 50000502, 5),
  (8, 50000503, 5),
  (8, 50000504, 5),
  (8, 50000505, 5),
  (8, 50000301, 3),
  (8, 50000302, 3),
  (8, 50000303, 3),
  (8, 50000305, 3),
  (8, 50000306, 3),
  (9, 50000601, 6),
  (9, 50000602, 6),
  (9, 50000603, 6),
  (9, 50000604, 6),
  (9, 50000605, 6),
  (9, 50000201, 2),
  (9, 50000202, 2),
  (9, 50000203, 2),
  (9, 50000204, 2),
  (9, 50000205, 2);

-- GOL
INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES
  (1, 50000101, 10, FALSE),
  (1, 50000102, 22, FALSE),
  (1, 50000601, 18, FALSE),
  (2, 50000201, 10, FALSE),
  (2, 50000501, 18, FALSE),
  (3, 50000401, 18, FALSE),
  (3, 50000402, 30, FALSE),
  (3, 50000403, 42, FALSE),
  (4, 50000101, 10, FALSE),
  (4, 50000102, 22, FALSE),
  (4, 50000104, 34, FALSE),
  (5, 50000601, 10, FALSE),
  (5, 50000401, 18, FALSE),
  (5, 50000402, 30, FALSE),
  (6, 50000201, 10, FALSE),
  (6, 50000202, 22, FALSE),
  (6, 50000301, 18, FALSE),
  (6, 50000302, 30, FALSE),
  (7, 50000401, 18, FALSE),
  (8, 50000501, 10, FALSE),
  (8, 50000502, 22, FALSE),
  (8, 50000503, 34, FALSE),
  (8, 50000504, 46, FALSE),
  (8, 50000301, 18, FALSE),
  (8, 50000302, 30, FALSE),
  (9, 50000601, 10, FALSE),
  (9, 50000201, 18, FALSE),
  (9, 50000202, 30, FALSE),
  (9, 50000203, 42, FALSE);

-- TARJETA
INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES
  (1, 50000103, 52, 'roja'),
  (2, 50000203, 35, 'amarilla'),
  (5, 50000402, 54, 'amarilla'),
  (6, 50000203, 35, 'amarilla'),
  (9, 50000203, 35, 'amarilla'),
  (9, 50000605, 40, 'amarilla');

-- SANCION_JUGADOR: únicamente sanciones disciplinarias manuales.
-- Las sanciones por tarjetas se obtienen en v_sanciones_automaticas.
INSERT INTO sancion_jugador (ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas, origen) VALUES
  (50000304, 1, 'disciplinaria', 3, 1, 'manual');

-- CASOS ADICIONALES DE PRUEBA: fecha 5, los tres estados no jugados.
-- Partidos sin planilla ni goles; la cancha de postergados/cancelados queda libre.
INSERT INTO partido
  (id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante,
   dia, id_turno, nombre_cancha, id_complejo, estado)
VALUES
  (1, 5, 1, 2, '2026-11-02', 2, 'Cancha A', 1, 'cancelado'),
  (1, 5, 3, 6, '2026-11-02', 2, 'Cancha B', 1, 'postergado'),
  (1, 5, 4, 5, '2026-11-02', 2, 'Cancha 1', 2, 'programado');

-- CASO DE PRUEBA: PARTIDO JUGADO 0-0, FECHA 4 (2026-10-26).
-- Halcones (equipo 1) vs Leones (equipo 3): no disputaron otro partido
-- entre si en esta edicion. El partido no coincide con ninguna reserva.
INSERT INTO partido
  (id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante,
   dia, id_turno, nombre_cancha, id_complejo, estado)
VALUES (1, 4, 1, 3, '2026-10-26', 1, 'Cancha A', 1, 'jugado');

-- Se registra una planilla valida (5 participantes por equipo).
-- Deliberadamente NO se insertan filas en gol para este partido.
SET @id_partido_empate_0_0 = LAST_INSERT_ID();
INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES
  (@id_partido_empate_0_0, 50000101, 1),
  (@id_partido_empate_0_0, 50000102, 1),
  (@id_partido_empate_0_0, 50000103, 1),
  (@id_partido_empate_0_0, 50000104, 1),
  (@id_partido_empate_0_0, 50000105, 1),
  (@id_partido_empate_0_0, 50000301, 3),
  (@id_partido_empate_0_0, 50000302, 3),
  (@id_partido_empate_0_0, 50000303, 3),
  (@id_partido_empate_0_0, 50000304, 3),
  (@id_partido_empate_0_0, 50000305, 3);

-- AUTOGOL EN UN PARTIDO YA DISPUTADO (favorece al equipo local).
INSERT INTO gol (id_partido, ci_jugador, minuto, autogol)
VALUES (7, 50000402, 38, TRUE);

COMMIT;

-- Sanciones de tarjetas calculadas en tiempo real, SIN filas automaticas editables.
-- Tercera, sexta, novena... amarilla y cada roja generan una fecha de suspension.
-- ID negativos = identificador virtual de la tarjeta que origino la sancion.
CREATE SQL SECURITY DEFINER VIEW v_sanciones_automaticas AS
SELECT -x.id_tarjeta AS id_sancion, x.ci_jugador, x.id_torneo,
       CASE WHEN x.color = 'roja' THEN 'roja'
            ELSE 'acumulación de amarillas' END AS motivo,
       x.numero_fecha + 1 AS numero_fecha_inicio,
       1 AS cantidad_fechas, 'automatica' AS origen
  FROM (
    SELECT t.id_tarjeta, t.ci_jugador, t.color, p.id_torneo, p.numero_fecha,
           ROW_NUMBER() OVER (
               PARTITION BY p.id_torneo, t.ci_jugador, t.color
               ORDER BY p.numero_fecha, p.dia, t.minuto, t.id_tarjeta
           ) AS orden_color
      FROM tarjeta t
      JOIN partido p ON p.id_partido = t.id_partido
     WHERE p.estado = 'jugado'
  ) x
 WHERE x.color = 'roja'
    OR (x.color = 'amarilla' AND MOD(x.orden_color, 3) = 0);

-- Punto unico de lectura para sanciones manuales y automaticas.
CREATE SQL SECURITY DEFINER VIEW v_sanciones AS
SELECT id_sancion, ci_jugador, id_torneo, motivo,
       numero_fecha_inicio, cantidad_fechas, origen
  FROM sancion_jugador
UNION ALL
SELECT id_sancion, ci_jugador, id_torneo, motivo,
       numero_fecha_inicio, cantidad_fechas, origen
  FROM v_sanciones_automaticas;

-- Se instalan las validaciones DESPUES de los datos historicos:
-- no se reprocesan tarjetas antiguas ni se bloquea su carga fuera de 48 horas.
-- Las sanciones automaticas historicas se derivan de las tarjetas en una vista.
-- Requiere MySQL 8.0.16+ y DELIMITER al ejecutar el script completo.

DELIMITER $$

CREATE PROCEDURE validar_edicion_partido(IN p_partido INT)
BEGIN
    DECLARE v_estado VARCHAR(20) DEFAULT NULL;
    DECLARE v_fin DATETIME DEFAULT NULL;

    SELECT p.estado, TIMESTAMP(p.dia, t.hora_fin)
      INTO v_estado, v_fin
      FROM partido p
      JOIN turno t ON t.id_turno = p.id_turno
     WHERE p.id_partido = p_partido;

    IF v_estado IS NULL OR v_estado <> 'jugado' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo se pueden registrar o corregir datos de partidos jugados';
    END IF;
    IF NOW() < v_fin THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El partido todavia no termino';
    END IF;
    IF NOW() > DATE_ADD(v_fin, INTERVAL 48 HOUR) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Vencio el plazo de 48 horas para corregir la planilla';
    END IF;
END$$

CREATE PROCEDURE validar_capitan_facultad(IN p_ci INT, IN p_facultad INT)
BEGIN
    DECLARE v_total INT DEFAULT 0;
    SELECT COUNT(*) INTO v_total FROM jugador
     WHERE ci = p_ci AND id_facultad = p_facultad;
    IF v_total <> 1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El capitan debe pertenecer a la facultad del equipo';
    END IF;
END$$

CREATE PROCEDURE validar_alta_plantel(IN p_equipo INT, IN p_torneo INT, IN p_ci INT)
BEGIN
    DECLARE v_facultad_equipo INT DEFAULT NULL;
    DECLARE v_facultad_jugador INT DEFAULT NULL;
    DECLARE v_tipo VARCHAR(20) DEFAULT NULL;
    DECLARE v_estado VARCHAR(20) DEFAULT NULL;
    DECLARE v_cantidad INT DEFAULT 0;
    DECLARE v_personal INT DEFAULT 0;

    -- Serializa los cambios del plantel dentro de una misma edicion.
    SELECT estado INTO v_estado FROM torneo WHERE id_torneo = p_torneo FOR UPDATE;
    IF v_estado IS NULL OR v_estado <> 'inscripción' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El plantel solo se modifica en inscripcion';
    END IF;
    SELECT id_facultad INTO v_facultad_equipo
      FROM equipo WHERE id_equipo = p_equipo AND id_torneo = p_torneo;
    SELECT id_facultad, tipo INTO v_facultad_jugador, v_tipo
      FROM jugador WHERE ci = p_ci;
    IF v_facultad_equipo IS NULL OR v_facultad_jugador IS NULL OR
       v_facultad_equipo <> v_facultad_jugador THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Jugador y equipo deben pertenecer a la misma facultad';
    END IF;
    SELECT COUNT(*), COALESCE(SUM(j.tipo IN ('docente','funcionario')),0)
      INTO v_cantidad, v_personal
      FROM equipo_jugador_torneo ejt
      JOIN jugador j ON j.ci = ejt.ci_jugador
     WHERE ejt.id_equipo = p_equipo AND ejt.id_torneo = p_torneo;
    IF v_cantidad >= 10 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El plantel no puede tener mas de 10 jugadores';
    END IF;
    IF v_tipo IN ('docente','funcionario') AND v_personal >= 2 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El plantel admite como maximo dos docentes o funcionarios';
    END IF;
END$$

CREATE PROCEDURE validar_programacion(
    IN p_torneo INT, IN p_fecha INT, IN p_local INT, IN p_visitante INT,
    IN p_dia DATE, IN p_turno INT, IN p_estado VARCHAR(20), IN p_excluir INT
)
BEGIN
    DECLARE v_estado VARCHAR(20) DEFAULT NULL;
    DECLARE v_inicio DATE DEFAULT NULL;
    DECLARE v_fin DATE DEFAULT NULL;
    DECLARE v_hora_fin TIME DEFAULT NULL;
    DECLARE v_conteo INT DEFAULT 0;
    DECLARE v_equipo INT DEFAULT NULL;
    DECLARE v_capitan INT DEFAULT NULL;

    -- Bloqueo para reducir condiciones de carrera al programar partidos de una edicion.
    SELECT estado, fecha_inicio, fecha_fin
      INTO v_estado, v_inicio, v_fin
      FROM torneo WHERE id_torneo = p_torneo FOR UPDATE;
    IF v_estado IS NULL OR v_estado = 'finalizado' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se pueden programar partidos en esa edicion';
    END IF;
    IF p_dia NOT BETWEEN v_inicio AND v_fin THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La fecha del partido esta fuera del torneo';
    END IF;
    IF p_estado = 'jugado' THEN
        SELECT hora_fin INTO v_hora_fin FROM turno WHERE id_turno = p_turno;
        IF v_hora_fin IS NULL OR NOW() <= TIMESTAMP(p_dia, v_hora_fin) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un partido solo puede marcarse jugado despues del turno';
        END IF;
    END IF;
    IF p_estado <> 'cancelado' THEN
        -- El mismo equipo no debe participar en dos partidos de la misma fecha.
        SELECT COUNT(*) INTO v_conteo
          FROM partido p
         WHERE p.id_torneo = p_torneo AND p.numero_fecha = p_fecha
           AND p.estado <> 'cancelado'
           AND p.id_partido <> COALESCE(p_excluir, 0)
           AND (p.id_equipo_local IN (p_local,p_visitante)
                OR p.id_equipo_visitante IN (p_local,p_visitante));
        IF v_conteo > 0 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un equipo no puede jugar dos veces en la misma fecha';
        END IF;
        -- Comprobar los dos planteles y que sus capitanes esten inscriptos.
        SELECT COUNT(*) INTO v_conteo
          FROM equipo_jugador_torneo
         WHERE id_equipo = p_local AND id_torneo = p_torneo;
        IF v_conteo < 5 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El equipo local tiene menos de 5 jugadores';
        END IF;
        SELECT COUNT(*) INTO v_conteo
          FROM equipo_jugador_torneo
         WHERE id_equipo = p_visitante AND id_torneo = p_torneo;
        IF v_conteo < 5 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El equipo visitante tiene menos de 5 jugadores';
        END IF;
        SELECT COUNT(*) INTO v_conteo FROM equipo e
          JOIN equipo_jugador_torneo ejt
            ON ejt.id_equipo = e.id_equipo AND ejt.id_torneo = e.id_torneo
           AND ejt.ci_jugador = e.ci_capitan
         WHERE e.id_equipo IN (p_local,p_visitante) AND e.id_torneo = p_torneo;
        IF v_conteo <> 2 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ambos capitanes deben integrar sus respectivos planteles';
        END IF;
    END IF;
END$$

CREATE PROCEDURE validar_participante_planilla(
    IN p_partido INT, IN p_ci INT, IN p_equipo INT
)
BEGIN
    DECLARE v_torneo INT DEFAULT NULL;
    DECLARE v_fecha INT DEFAULT NULL;
    DECLARE v_local INT DEFAULT NULL;
    DECLARE v_visitante INT DEFAULT NULL;
    DECLARE v_inscrito INT DEFAULT 0;
    DECLARE v_suspendido INT DEFAULT 0;

    CALL validar_edicion_partido(p_partido);
    SELECT id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante
      INTO v_torneo, v_fecha, v_local, v_visitante
      FROM partido WHERE id_partido = p_partido;
    IF p_equipo NOT IN (v_local, v_visitante) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El equipo de la planilla no participa en ese partido';
    END IF;
    SELECT COUNT(*) INTO v_inscrito FROM equipo_jugador_torneo
     WHERE id_equipo = p_equipo AND id_torneo = v_torneo AND ci_jugador = p_ci;
    IF v_inscrito <> 1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El jugador no integra el plantel de ese equipo';
    END IF;
    SELECT COUNT(*) INTO v_suspendido FROM v_sanciones
     WHERE ci_jugador = p_ci AND id_torneo = v_torneo
       AND v_fecha >= numero_fecha_inicio
       AND v_fecha < numero_fecha_inicio + cantidad_fechas;
    IF v_suspendido > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El jugador esta suspendido para esta fecha';
    END IF;
END$$

CREATE PROCEDURE validar_sancion(
    IN p_ci INT, IN p_torneo INT, IN p_inicio INT, IN p_cantidad INT
)
BEGIN
    DECLARE v_conflictos INT DEFAULT 0;
    DECLARE v_miembro INT DEFAULT 0;
    SELECT COUNT(*) INTO v_miembro FROM equipo_jugador_torneo
     WHERE ci_jugador = p_ci AND id_torneo = p_torneo;
    IF v_miembro = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se puede sancionar a un jugador ajeno a esa edicion';
    END IF;
    SELECT COUNT(*) INTO v_conflictos FROM planilla_partido pp
      JOIN partido p ON p.id_partido = pp.id_partido
     WHERE pp.ci_jugador = p_ci AND p.id_torneo = p_torneo
       AND p.numero_fecha >= p_inicio
       AND p.numero_fecha < p_inicio + p_cantidad;
    IF v_conflictos > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La sancion se superpone con planillas existentes';
    END IF;
END$$

-- Rechaza correcciones de tarjetas que invalidarian planillas ya registradas.
-- No toca sanciones: estas se generan automaticamente en la vista.
CREATE PROCEDURE validar_coherencia_sanciones_automaticas(IN p_ci INT, IN p_torneo INT)
BEGIN
    DECLARE v_incompatibles INT DEFAULT 0;
    SELECT COUNT(*) INTO v_incompatibles
      FROM v_sanciones_automaticas sa
      JOIN partido p ON p.id_torneo = sa.id_torneo
      JOIN planilla_partido pp ON pp.id_partido = p.id_partido
                             AND pp.ci_jugador = sa.ci_jugador
     WHERE sa.ci_jugador = p_ci AND sa.id_torneo = p_torneo
       AND p.numero_fecha >= sa.numero_fecha_inicio
       AND p.numero_fecha < sa.numero_fecha_inicio + sa.cantidad_fechas;
    IF v_incompatibles > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'La tarjeta generaria una suspension incompatible con una planilla existente';
    END IF;
END$$

-- TORNEO: las ediciones nuevas comienzan en inscripcion.
CREATE TRIGGER bi_torneo BEFORE INSERT ON torneo FOR EACH ROW
BEGIN
    IF NEW.estado <> 'inscripción' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Una edicion nueva debe comenzar en inscripcion';
    END IF;
END$$

-- No iniciar la edicion con planteles incompletos ni capitanes ausentes.
CREATE TRIGGER bu_torneo BEFORE UPDATE ON torneo FOR EACH ROW
BEGIN
    DECLARE v_incompletos INT DEFAULT 0;
    IF OLD.estado = 'finalizado' AND NEW.estado <> OLD.estado THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se puede reabrir un torneo finalizado';
    END IF;
    IF OLD.estado = 'en curso' AND NEW.estado = 'inscripción' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se puede reabrir la inscripcion';
    END IF;
    IF NEW.estado <> 'inscripción' AND OLD.estado = 'inscripción' THEN
        SELECT COUNT(*) INTO v_incompletos FROM equipo e
         WHERE e.id_torneo = NEW.id_torneo
           AND (
               (SELECT COUNT(*) FROM equipo_jugador_torneo ejt
                 WHERE ejt.id_equipo = e.id_equipo AND ejt.id_torneo = e.id_torneo) NOT BETWEEN 5 AND 10
               OR NOT EXISTS (
                  SELECT 1 FROM equipo_jugador_torneo ejt
                   WHERE ejt.id_equipo = e.id_equipo AND ejt.id_torneo = e.id_torneo
                     AND ejt.ci_jugador = e.ci_capitan
               )
           );
        IF v_incompletos > 0 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se puede iniciar el torneo con planteles incompletos';
        END IF;
    END IF;
END$$

CREATE TRIGGER bi_equipo BEFORE INSERT ON equipo FOR EACH ROW
BEGIN
    DECLARE v_estado VARCHAR(20) DEFAULT NULL;
    SELECT estado INTO v_estado FROM torneo WHERE id_torneo = NEW.id_torneo FOR UPDATE;
    IF v_estado IS NULL OR v_estado <> 'inscripción' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo se crean equipos durante la inscripcion';
    END IF;
    CALL validar_capitan_facultad(NEW.ci_capitan, NEW.id_facultad);
END$$

CREATE TRIGGER bu_equipo BEFORE UPDATE ON equipo FOR EACH ROW
BEGIN
    DECLARE v_en_plantel INT DEFAULT 0;
    CALL validar_capitan_facultad(NEW.ci_capitan, NEW.id_facultad);
    IF NEW.id_torneo <> OLD.id_torneo OR NEW.id_facultad <> OLD.id_facultad THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se puede cambiar la edicion o facultad de un equipo';
    END IF;
    IF NEW.ci_capitan <> OLD.ci_capitan THEN
        SELECT COUNT(*) INTO v_en_plantel FROM equipo_jugador_torneo
         WHERE id_equipo = NEW.id_equipo AND id_torneo = NEW.id_torneo
           AND ci_jugador = NEW.ci_capitan;
        IF v_en_plantel <> 1 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El nuevo capitan debe integrar el plantel';
        END IF;
    END IF;
END$$

CREATE TRIGGER bu_jugador BEFORE UPDATE ON jugador FOR EACH ROW
BEGIN
    DECLARE v_inscrito INT DEFAULT 0;
    IF NEW.id_facultad <> OLD.id_facultad OR NEW.tipo <> OLD.tipo THEN
        SELECT COUNT(*) INTO v_inscrito FROM equipo_jugador_torneo
         WHERE ci_jugador = OLD.ci;
        IF v_inscrito > 0 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Para cambiar facultad o tipo, primero debe salir de todos los planteles';
        END IF;
    END IF;
END$$

CREATE TRIGGER bi_plantel BEFORE INSERT ON equipo_jugador_torneo FOR EACH ROW
BEGIN
    CALL validar_alta_plantel(NEW.id_equipo, NEW.id_torneo, NEW.ci_jugador);
END$$

CREATE TRIGGER bu_plantel BEFORE UPDATE ON equipo_jugador_torneo FOR EACH ROW
BEGIN
    DECLARE v_estado VARCHAR(20) DEFAULT NULL;
    IF NEW.id_equipo <> OLD.id_equipo OR NEW.id_torneo <> OLD.id_torneo
       OR NEW.ci_jugador <> OLD.ci_jugador THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Para cambiar jugador o equipo, quitar y agregar la inscripcion';
    END IF;
    SELECT estado INTO v_estado FROM torneo WHERE id_torneo = OLD.id_torneo FOR UPDATE;
    IF v_estado <> 'inscripción' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El plantel solo se modifica en inscripcion';
    END IF;
END$$

CREATE TRIGGER bd_plantel BEFORE DELETE ON equipo_jugador_torneo FOR EACH ROW
BEGIN
    DECLARE v_estado VARCHAR(20) DEFAULT NULL;
    DECLARE v_es_capitan INT DEFAULT 0;
    DECLARE v_partidos INT DEFAULT 0;
    DECLARE v_cantidad INT DEFAULT 0;
    SELECT estado INTO v_estado FROM torneo WHERE id_torneo = OLD.id_torneo FOR UPDATE;
    IF v_estado <> 'inscripción' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El plantel solo se modifica en inscripcion';
    END IF;
    SELECT COUNT(*) INTO v_es_capitan FROM equipo
     WHERE id_equipo = OLD.id_equipo AND ci_capitan = OLD.ci_jugador;
    IF v_es_capitan > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Asigne otro capitan antes de quitar al actual';
    END IF;
    SELECT COUNT(*) INTO v_partidos FROM partido
     WHERE id_torneo = OLD.id_torneo AND estado <> 'cancelado'
       AND (id_equipo_local = OLD.id_equipo OR id_equipo_visitante = OLD.id_equipo);
    IF v_partidos > 0 THEN
        SELECT COUNT(*) INTO v_cantidad FROM equipo_jugador_torneo
         WHERE id_torneo = OLD.id_torneo AND id_equipo = OLD.id_equipo;
        IF v_cantidad <= 5 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un equipo con partidos programados debe conservar al menos 5 jugadores';
        END IF;
    END IF;
END$$

CREATE TRIGGER bi_partido BEFORE INSERT ON partido FOR EACH ROW
BEGIN
    CALL validar_programacion(NEW.id_torneo, NEW.numero_fecha,
       NEW.id_equipo_local, NEW.id_equipo_visitante, NEW.dia,
       NEW.id_turno, NEW.estado, NULL);
END$$

CREATE TRIGGER bu_partido BEFORE UPDATE ON partido FOR EACH ROW
BEGIN
    IF OLD.estado = 'jugado' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Un partido jugado no puede cambiar su programacion';
    END IF;
    CALL validar_programacion(NEW.id_torneo, NEW.numero_fecha,
       NEW.id_equipo_local, NEW.id_equipo_visitante, NEW.dia,
       NEW.id_turno, NEW.estado, OLD.id_partido);
END$$

CREATE TRIGGER bd_partido BEFORE DELETE ON partido FOR EACH ROW
BEGIN
    IF OLD.estado = 'jugado' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se puede eliminar un partido jugado';
    END IF;
END$$

CREATE TRIGGER bi_planilla BEFORE INSERT ON planilla_partido FOR EACH ROW
BEGIN
    CALL validar_participante_planilla(NEW.id_partido, NEW.ci_jugador, NEW.id_equipo);
END$$

CREATE TRIGGER bu_planilla BEFORE UPDATE ON planilla_partido FOR EACH ROW
BEGIN
    CALL validar_edicion_partido(OLD.id_partido);
    CALL validar_participante_planilla(NEW.id_partido, NEW.ci_jugador, NEW.id_equipo);
END$$

CREATE TRIGGER bd_planilla BEFORE DELETE ON planilla_partido FOR EACH ROW
BEGIN
    CALL validar_edicion_partido(OLD.id_partido);
END$$

CREATE TRIGGER bi_gol BEFORE INSERT ON gol FOR EACH ROW
BEGIN
    CALL validar_edicion_partido(NEW.id_partido);
END$$

CREATE TRIGGER bu_gol BEFORE UPDATE ON gol FOR EACH ROW
BEGIN
    CALL validar_edicion_partido(OLD.id_partido);
    CALL validar_edicion_partido(NEW.id_partido);
END$$

CREATE TRIGGER bd_gol BEFORE DELETE ON gol FOR EACH ROW
BEGIN
    CALL validar_edicion_partido(OLD.id_partido);
END$$

CREATE TRIGGER bi_tarjeta BEFORE INSERT ON tarjeta FOR EACH ROW
BEGIN
    CALL validar_edicion_partido(NEW.id_partido);
END$$

CREATE TRIGGER bu_tarjeta BEFORE UPDATE ON tarjeta FOR EACH ROW
BEGIN
    CALL validar_edicion_partido(OLD.id_partido);
    CALL validar_edicion_partido(NEW.id_partido);
END$$

CREATE TRIGGER bd_tarjeta BEFORE DELETE ON tarjeta FOR EACH ROW
BEGIN
    CALL validar_edicion_partido(OLD.id_partido);
END$$

-- No se permite insertar, editar o eliminar sanciones automaticas fisicas.
-- Las vistas v_sanciones_automaticas y v_sanciones son de solo lectura
-- (derivaciones, UNION y ventanas: no actualizables en MySQL).
CREATE TRIGGER bi_sancion BEFORE INSERT ON sancion_jugador FOR EACH ROW
BEGIN
    IF NEW.origen <> 'manual' OR NEW.motivo <> 'disciplinaria' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Las sanciones por tarjetas son automaticas y no se insertan manualmente';
    END IF;
    CALL validar_sancion(NEW.ci_jugador, NEW.id_torneo,
                         NEW.numero_fecha_inicio, NEW.cantidad_fechas);
END$$

CREATE TRIGGER bu_sancion BEFORE UPDATE ON sancion_jugador FOR EACH ROW
BEGIN
    IF OLD.origen = 'automatica' OR NEW.origen <> 'manual'
       OR NEW.motivo <> 'disciplinaria' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'No se permite modificar sanciones automaticas';
    END IF;
    CALL validar_sancion(NEW.ci_jugador, NEW.id_torneo,
                         NEW.numero_fecha_inicio, NEW.cantidad_fechas);
END$$

CREATE TRIGGER bd_sancion BEFORE DELETE ON sancion_jugador FOR EACH ROW
BEGIN
    IF OLD.origen = 'automatica' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'No se permite eliminar sanciones automaticas';
    END IF;
END$$

-- El cálculo de sanciones se actualiza solo: sin INSERT/UPDATE/DELETE físicos.
CREATE TRIGGER ai_tarjeta AFTER INSERT ON tarjeta FOR EACH ROW
BEGIN
    DECLARE v_torneo INT DEFAULT NULL;
    SELECT id_torneo INTO v_torneo FROM partido WHERE id_partido = NEW.id_partido;
    CALL validar_coherencia_sanciones_automaticas(NEW.ci_jugador, v_torneo);
END$$

CREATE TRIGGER au_tarjeta AFTER UPDATE ON tarjeta FOR EACH ROW
BEGIN
    DECLARE v_torneo_anterior INT DEFAULT NULL;
    DECLARE v_torneo_nuevo INT DEFAULT NULL;
    SELECT id_torneo INTO v_torneo_anterior FROM partido WHERE id_partido = OLD.id_partido;
    SELECT id_torneo INTO v_torneo_nuevo FROM partido WHERE id_partido = NEW.id_partido;
    CALL validar_coherencia_sanciones_automaticas(OLD.ci_jugador, v_torneo_anterior);
    IF OLD.ci_jugador <> NEW.ci_jugador OR v_torneo_anterior <> v_torneo_nuevo THEN
        CALL validar_coherencia_sanciones_automaticas(NEW.ci_jugador, v_torneo_nuevo);
    END IF;
END$$

CREATE TRIGGER ad_tarjeta AFTER DELETE ON tarjeta FOR EACH ROW
BEGIN
    DECLARE v_torneo INT DEFAULT NULL;
    SELECT id_torneo INTO v_torneo FROM partido WHERE id_partido = OLD.id_partido;
    CALL validar_coherencia_sanciones_automaticas(OLD.ci_jugador, v_torneo);
END$$

DELIMITER ;

-- Vista de resultado calculada desde goles, contemplando autogoles.
CREATE SQL SECURITY DEFINER VIEW v_resultado_partido AS
SELECT p.id_partido, p.id_torneo, p.numero_fecha,
       p.id_equipo_local, p.id_equipo_visitante,
       COALESCE(SUM(CASE WHEN (g.autogol = 0 AND pp.id_equipo = p.id_equipo_local)
                     OR (g.autogol = 1 AND pp.id_equipo = p.id_equipo_visitante)
                THEN 1 ELSE 0 END), 0) AS goles_local,
       COALESCE(SUM(CASE WHEN (g.autogol = 0 AND pp.id_equipo = p.id_equipo_visitante)
                     OR (g.autogol = 1 AND pp.id_equipo = p.id_equipo_local)
                THEN 1 ELSE 0 END), 0) AS goles_visitante
  FROM partido p
  LEFT JOIN gol g ON g.id_partido = p.id_partido
  LEFT JOIN planilla_partido pp ON pp.id_partido = g.id_partido
                              AND pp.ci_jugador = g.ci_jugador
 WHERE p.estado = 'jugado'
 GROUP BY p.id_partido, p.id_torneo, p.numero_fecha,
          p.id_equipo_local, p.id_equipo_visitante;


-- ===============================================================
-- REPORTES OBLIGATORIOS (1..9) Y PROPUESTOS (10..12)
-- Todos son vistas reutilizables; filtrar por id_torneo al consultarlas.
-- En MySQL 8, las vistas muestran los datos actuales sin recalcular tablas.
-- ===============================================================

-- 01. TABLA DE POSICIONES: PJ, PG, PE, PP, GF, GC, DG, puntos.
-- El desempate se aplica al consultar: puntos DESC, DG DESC, GF DESC.
CREATE SQL SECURITY DEFINER VIEW v_reporte_01_posiciones AS
SELECT e.id_torneo, e.id_equipo, e.nombre AS equipo,
       COUNT(m.id_partido) AS partidos_jugados,
       COALESCE(SUM(m.goles_favor > m.goles_contra), 0) AS ganados,
       COALESCE(SUM(m.goles_favor = m.goles_contra), 0) AS empatados,
       COALESCE(SUM(m.goles_favor < m.goles_contra), 0) AS perdidos,
       COALESCE(SUM(m.goles_favor), 0) AS goles_favor,
       COALESCE(SUM(m.goles_contra), 0) AS goles_contra,
       COALESCE(SUM(m.goles_favor - m.goles_contra), 0) AS diferencia_goles,
       COALESCE(SUM(CASE WHEN m.goles_favor > m.goles_contra THEN 3
                         WHEN m.goles_favor = m.goles_contra THEN 1
                         ELSE 0 END), 0) AS puntos
  FROM equipo e
  LEFT JOIN (
    SELECT id_partido, id_torneo, id_equipo_local AS id_equipo,
           goles_local AS goles_favor, goles_visitante AS goles_contra
      FROM v_resultado_partido
    UNION ALL
    SELECT id_partido, id_torneo, id_equipo_visitante AS id_equipo,
           goles_visitante AS goles_favor, goles_local AS goles_contra
      FROM v_resultado_partido
  ) m ON m.id_equipo = e.id_equipo AND m.id_torneo = e.id_torneo
 GROUP BY e.id_torneo, e.id_equipo, e.nombre;

-- 02. LOS 10 GOLEADORES DE CADA EDICION: autogoles NO cuentan al autor.
CREATE SQL SECURITY DEFINER VIEW v_reporte_02_goleadores AS
SELECT s.id_torneo, s.posicion, s.ci_jugador, s.nombre, s.apellido,
       s.id_equipo, s.equipo, s.goles
  FROM (
    SELECT p.id_torneo, j.ci AS ci_jugador, j.nombre, j.apellido,
           e.id_equipo, e.nombre AS equipo, COUNT(*) AS goles,
           ROW_NUMBER() OVER (
               PARTITION BY p.id_torneo
               ORDER BY COUNT(*) DESC, j.apellido, j.nombre, j.ci
           ) AS posicion
      FROM gol g
      JOIN partido p ON p.id_partido = g.id_partido AND p.estado = 'jugado'
      JOIN planilla_partido pp ON pp.id_partido = g.id_partido
                            AND pp.ci_jugador = g.ci_jugador
      JOIN equipo e ON e.id_equipo = pp.id_equipo
      JOIN jugador j ON j.ci = g.ci_jugador
     WHERE g.autogol = 0
     GROUP BY p.id_torneo, j.ci, j.nombre, j.apellido, e.id_equipo, e.nombre
  ) s
 WHERE s.posicion <= 10;

-- 03. FAIR PLAY: amarilla = 1, roja = 3; menor puntaje es mejor.
CREATE SQL SECURITY DEFINER VIEW v_reporte_03_fair_play AS
SELECT e.id_torneo, e.id_equipo, e.nombre AS equipo,
       COALESCE(SUM(t.color = 'amarilla'), 0) AS amarillas,
       COALESCE(SUM(t.color = 'roja'), 0) AS rojas,
       COALESCE(SUM(CASE t.color WHEN 'amarilla' THEN 1
                                 WHEN 'roja' THEN 3 ELSE 0 END), 0) AS puntos_fair_play
  FROM equipo e
  LEFT JOIN planilla_partido pp ON pp.id_equipo = e.id_equipo
  LEFT JOIN partido p ON p.id_partido = pp.id_partido
                     AND p.id_torneo = e.id_torneo AND p.estado = 'jugado'
  LEFT JOIN tarjeta t ON t.id_partido = p.id_partido
                    AND t.ci_jugador = pp.ci_jugador
 GROUP BY e.id_torneo, e.id_equipo, e.nombre;

-- 04. PROMEDIO DE GOLES POR FECHA Y POR EDICION COMPLETA.
CREATE SQL SECURITY DEFINER VIEW v_reporte_04_promedio_goles AS
SELECT r.id_torneo, 'fecha' AS alcance, r.numero_fecha,
       COUNT(*) AS partidos_jugados,
       SUM(r.goles_local + r.goles_visitante) AS total_goles,
       ROUND(AVG(r.goles_local + r.goles_visitante), 2) AS promedio_goles
  FROM v_resultado_partido r
 GROUP BY r.id_torneo, r.numero_fecha
UNION ALL
SELECT t.id_torneo, 'edicion' AS alcance, NULL AS numero_fecha,
       COUNT(r.id_partido) AS partidos_jugados,
       COALESCE(SUM(r.goles_local + r.goles_visitante), 0) AS total_goles,
       ROUND(AVG(r.goles_local + r.goles_visitante), 2) AS promedio_goles
  FROM torneo t
  LEFT JOIN v_resultado_partido r ON r.id_torneo = t.id_torneo
 GROUP BY t.id_torneo;

-- 05. CANCHAS Y TURNOS MAS UTILIZADOS (partidos realmente jugados).
CREATE SQL SECURITY DEFINER VIEW v_reporte_05_uso_espacios AS
SELECT p.id_torneo, 'cancha' AS tipo_recurso,
       CONCAT(p.nombre_cancha, ' / ', c.nombre) AS recurso,
       COUNT(*) AS partidos_jugados
  FROM partido p
  JOIN complejo c ON c.id_complejo = p.id_complejo
 WHERE p.estado = 'jugado'
 GROUP BY p.id_torneo, p.nombre_cancha, c.id_complejo, c.nombre
UNION ALL
SELECT p.id_torneo, 'turno' AS tipo_recurso,
       CONCAT(TIME_FORMAT(t.hora_inicio, '%H:%i'), '-',
              TIME_FORMAT(t.hora_fin, '%H:%i')) AS recurso,
       COUNT(*) AS partidos_jugados
  FROM partido p
  JOIN turno t ON t.id_turno = p.id_turno
 WHERE p.estado = 'jugado'
 GROUP BY p.id_torneo, t.id_turno, t.hora_inicio, t.hora_fin;

-- 06. CANTIDAD DE JUGADORES POR FACULTAD Y TIPO (incluye ceros).
CREATE SQL SECURITY DEFINER VIEW v_reporte_06_jugadores_facultad_tipo AS
SELECT f.id_facultad, f.nombre AS facultad, tipos.tipo,
       COUNT(j.ci) AS cantidad_jugadores
  FROM facultad f
 CROSS JOIN (
     SELECT 'grado' AS tipo UNION ALL SELECT 'posgrado'
     UNION ALL SELECT 'docente' UNION ALL SELECT 'funcionario'
 ) tipos
 LEFT JOIN jugador j ON j.id_facultad = f.id_facultad AND j.tipo = tipos.tipo
 GROUP BY f.id_facultad, f.nombre, tipos.tipo;

-- 07. INSCRIPTOS QUE NUNCA FIGURARON EN UNA PLANILLA DE LA EDICION.
CREATE SQL SECURITY DEFINER VIEW v_reporte_07_nunca_participaron AS
SELECT e.id_torneo, e.id_equipo, e.nombre AS equipo,
       j.ci AS ci_jugador, j.nombre, j.apellido, j.tipo
  FROM equipo_jugador_torneo ejt
  JOIN equipo e ON e.id_equipo = ejt.id_equipo AND e.id_torneo = ejt.id_torneo
  JOIN jugador j ON j.ci = ejt.ci_jugador
 WHERE NOT EXISTS (
    SELECT 1
      FROM planilla_partido pp
      JOIN partido p ON p.id_partido = pp.id_partido
     WHERE pp.ci_jugador = ejt.ci_jugador
       AND pp.id_equipo = ejt.id_equipo
       AND p.id_torneo = ejt.id_torneo
 );

-- 08. SANCIONES POR EQUIPO Y MOTIVO, automaticas + manuales (incluye ceros).
CREATE SQL SECURITY DEFINER VIEW v_reporte_08_sanciones_equipo AS
SELECT e.id_torneo, e.id_equipo, e.nombre AS equipo, motivos.motivo,
       COUNT(s.id_sancion) AS cantidad_sanciones
  FROM equipo e
 CROSS JOIN (
     SELECT 'roja' AS motivo
     UNION ALL SELECT 'acumulación de amarillas'
     UNION ALL SELECT 'disciplinaria'
 ) motivos
 LEFT JOIN equipo_jugador_torneo ejt
        ON ejt.id_equipo = e.id_equipo AND ejt.id_torneo = e.id_torneo
 LEFT JOIN v_sanciones s
        ON s.ci_jugador = ejt.ci_jugador AND s.id_torneo = e.id_torneo
       AND s.motivo = motivos.motivo
 GROUP BY e.id_torneo, e.id_equipo, e.nombre, motivos.motivo;

-- 09. PORCENTAJE JUGADOS / POSTERGADOS / CANCELADOS.
-- Los programados se incluyen en el denominador y se muestran por separado.
CREATE SQL SECURITY DEFINER VIEW v_reporte_09_estados_partidos AS
SELECT t.id_torneo, COUNT(p.id_partido) AS total_partidos,
       COALESCE(SUM(p.estado = 'jugado'), 0) AS jugados,
       COALESCE(SUM(p.estado = 'postergado'), 0) AS postergados,
       COALESCE(SUM(p.estado = 'cancelado'), 0) AS cancelados,
       COALESCE(SUM(p.estado = 'programado'), 0) AS programados,
       COALESCE(ROUND(100.0 * SUM(p.estado = 'jugado') / NULLIF(COUNT(p.id_partido), 0), 2), 0) AS porcentaje_jugados,
       COALESCE(ROUND(100.0 * SUM(p.estado = 'postergado') / NULLIF(COUNT(p.id_partido), 0), 2), 0) AS porcentaje_postergados,
       COALESCE(ROUND(100.0 * SUM(p.estado = 'cancelado') / NULLIF(COUNT(p.id_partido), 0), 2), 0) AS porcentaje_cancelados,
       COALESCE(ROUND(100.0 * SUM(p.estado = 'programado') / NULLIF(COUNT(p.id_partido), 0), 2), 0) AS porcentaje_programados
  FROM torneo t
  LEFT JOIN partido p ON p.id_torneo = t.id_torneo
 GROUP BY t.id_torneo;

-- 10. PROPUESTO [medio]: RENDIMIENTO COMO LOCAL VS VISITANTE.
-- Muestra los resultados, goles y puntos separados por condicion.
CREATE SQL SECURITY DEFINER VIEW v_reporte_10_local_visitante AS
SELECT e.id_torneo, e.id_equipo, e.nombre AS equipo,
       SUM(CASE WHEN s.condicion = 'local' THEN 1 ELSE 0 END) AS partidos_local,
       SUM(CASE WHEN s.condicion = 'visitante' THEN 1 ELSE 0 END) AS partidos_visitante,
       COALESCE(SUM(CASE WHEN s.condicion = 'local' THEN s.goles_favor ELSE 0 END), 0) AS gf_local,
       COALESCE(SUM(CASE WHEN s.condicion = 'visitante' THEN s.goles_favor ELSE 0 END), 0) AS gf_visitante,
       COALESCE(SUM(CASE WHEN s.condicion = 'local' THEN s.puntos ELSE 0 END), 0) AS puntos_local,
       COALESCE(SUM(CASE WHEN s.condicion = 'visitante' THEN s.puntos ELSE 0 END), 0) AS puntos_visitante
  FROM equipo e
  LEFT JOIN (
    SELECT id_torneo, id_equipo_local AS id_equipo, 'local' AS condicion,
           goles_local AS goles_favor,
           CASE WHEN goles_local > goles_visitante THEN 3
                WHEN goles_local = goles_visitante THEN 1 ELSE 0 END AS puntos
      FROM v_resultado_partido
    UNION ALL
    SELECT id_torneo, id_equipo_visitante AS id_equipo, 'visitante' AS condicion,
           goles_visitante AS goles_favor,
           CASE WHEN goles_visitante > goles_local THEN 3
                WHEN goles_visitante = goles_local THEN 1 ELSE 0 END AS puntos
      FROM v_resultado_partido
  ) s ON s.id_torneo = e.id_torneo AND s.id_equipo = e.id_equipo
 GROUP BY e.id_torneo, e.id_equipo, e.nombre;

-- 11. PROPUESTO [medio]: DISCIPLINA INDIVIDUAL (amarillas/rojas/sanciones).
-- Los conteos de tarjetas y sanciones se agregan por separado para evitar duplicados.
CREATE SQL SECURITY DEFINER VIEW v_reporte_11_disciplina_jugadores AS
SELECT ejt.id_torneo, ejt.id_equipo, e.nombre AS equipo,
       j.ci AS ci_jugador, j.nombre, j.apellido,
       COALESCE(tc.amarillas, 0) AS amarillas,
       COALESCE(tc.rojas, 0) AS rojas,
       COALESCE(tc.amarillas, 0) + 3 * COALESCE(tc.rojas, 0) AS indice_disciplina,
       COALESCE(sa.sanciones, 0) AS sanciones,
       COALESCE(sa.fechas_suspension, 0) AS fechas_suspension
  FROM equipo_jugador_torneo ejt
  JOIN equipo e ON e.id_equipo = ejt.id_equipo AND e.id_torneo = ejt.id_torneo
  JOIN jugador j ON j.ci = ejt.ci_jugador
  LEFT JOIN (
      SELECT p.id_torneo, t.ci_jugador,
             SUM(t.color = 'amarilla') AS amarillas,
             SUM(t.color = 'roja') AS rojas
        FROM tarjeta t
        JOIN partido p ON p.id_partido = t.id_partido AND p.estado = 'jugado'
       GROUP BY p.id_torneo, t.ci_jugador
  ) tc ON tc.id_torneo = ejt.id_torneo AND tc.ci_jugador = ejt.ci_jugador
  LEFT JOIN (
      SELECT id_torneo, ci_jugador, COUNT(*) AS sanciones,
             SUM(cantidad_fechas) AS fechas_suspension
        FROM v_sanciones
       GROUP BY id_torneo, ci_jugador
  ) sa ON sa.id_torneo = ejt.id_torneo AND sa.ci_jugador = ejt.ci_jugador
 WHERE COALESCE(tc.amarillas, 0) + COALESCE(tc.rojas, 0) + COALESCE(sa.sanciones, 0) > 0;

-- 12. PROPUESTO [medio]: GOLES POR TRAMOS DEL PARTIDO (incluye autogoles).
CREATE SQL SECURITY DEFINER VIEW v_reporte_12_goles_por_tramo AS
SELECT t.id_torneo, tramo.tramo,
       COUNT(g.id_gol) AS cantidad_goles,
       COALESCE(ROUND(100.0 * COUNT(g.id_gol)
         / NULLIF(SUM(COUNT(g.id_gol)) OVER (PARTITION BY t.id_torneo), 0), 2), 0) AS porcentaje_goles
  FROM torneo t
 CROSS JOIN (
     SELECT '00-15' AS tramo, 0 AS minuto_desde, 15 AS minuto_hasta
     UNION ALL SELECT '16-30', 16, 30
     UNION ALL SELECT '31-45', 31, 45
     UNION ALL SELECT '46-60', 46, 60
 ) tramo
 LEFT JOIN partido p ON p.id_torneo = t.id_torneo AND p.estado = 'jugado'
 LEFT JOIN gol g ON g.id_partido = p.id_partido
                AND g.minuto BETWEEN tramo.minuto_desde AND tramo.minuto_hasta
 GROUP BY t.id_torneo, tramo.tramo;

-- CONSULTAS DE EJEMPLO: id_torneo = 1, datos historicos del test.
-- Se ordena cada vista en SELECT, no dentro de la definicion de la vista.
-- Verificacion visible: este partido debe aparecer 0-0 y sin goles asociados.
-- La vista tambien lo contara como empate: un punto para cada equipo.
SELECT p.id_partido, p.numero_fecha, p.estado,
       r.goles_local, r.goles_visitante,
       (SELECT COUNT(*) FROM gol g WHERE g.id_partido = p.id_partido) AS goles_registrados,
       CASE WHEN r.goles_local = 0 AND r.goles_visitante = 0
                 AND NOT EXISTS (SELECT 1 FROM gol g WHERE g.id_partido = p.id_partido)
            THEN 'OK: empate 0-0 sin goles' ELSE 'ERROR: revisar el caso 0-0'
       END AS comprobacion
  FROM partido p
  JOIN v_resultado_partido r ON r.id_partido = p.id_partido
 WHERE p.id_torneo = 1 AND p.numero_fecha = 4
   AND p.id_equipo_local = 1 AND p.id_equipo_visitante = 3;

SELECT * FROM v_reporte_01_posiciones WHERE id_torneo = 1
 ORDER BY puntos DESC, diferencia_goles DESC, goles_favor DESC, equipo;
SELECT * FROM v_reporte_02_goleadores WHERE id_torneo = 1 ORDER BY posicion;
SELECT * FROM v_reporte_03_fair_play WHERE id_torneo = 1
 ORDER BY puntos_fair_play, amarillas, rojas, equipo;
SELECT * FROM v_reporte_04_promedio_goles WHERE id_torneo = 1
 ORDER BY alcance, numero_fecha;
SELECT * FROM v_reporte_05_uso_espacios WHERE id_torneo = 1
 ORDER BY tipo_recurso, partidos_jugados DESC, recurso;
SELECT * FROM v_reporte_06_jugadores_facultad_tipo ORDER BY facultad, tipo;
SELECT * FROM v_reporte_07_nunca_participaron WHERE id_torneo = 1
 ORDER BY equipo, apellido, nombre;
SELECT * FROM v_reporte_08_sanciones_equipo WHERE id_torneo = 1
 ORDER BY equipo, motivo;
SELECT * FROM v_reporte_09_estados_partidos WHERE id_torneo = 1;
SELECT * FROM v_reporte_10_local_visitante WHERE id_torneo = 1 ORDER BY equipo;
SELECT * FROM v_reporte_11_disciplina_jugadores WHERE id_torneo = 1
 ORDER BY indice_disciplina DESC, fechas_suspension DESC, apellido, nombre;
SELECT * FROM v_reporte_12_goles_por_tramo WHERE id_torneo = 1 ORDER BY tramo;

-- SEGURIDAD MYSQL: dos cuentas tecnicas para el backend del torneo
-- Ejecutar con un usuario administrador en el ESQUEMA YA SELECCIONADO.
-- Requiere MySQL 8.0.18+ (IDENTIFIED BY RANDOM PASSWORD).
-- Las claves se generan en MySQL y aparecen en el resultado de CREATE USER.
-- Guardar ambas claves de forma segura; no copiarlas al SQL ni al repositorio.
-- Estos CREATE USER son intencionalmente de una sola ejecucion: fallan si ya existen.
-- Cambiar 'localhost' por el host/red autorizado si el backend no esta en el mismo host.
-- Estas cuentas MySQL no son las filas de la tabla login de la aplicacion.

CREATE USER 'torneo_app_administrador'@'localhost' IDENTIFIED BY RANDOM PASSWORD;
CREATE USER 'torneo_app_planillero'@'localhost' IDENTIFIED BY RANDOM PASSWORD;

-- Administrador de la aplicacion: gestion de datos y lectura de reportes,
-- pero SIN permisos de DDL, CREATE USER, GRANT OPTION ni TRIGGER.
-- En GRANT, ON * aplica solo al esquema predeterminado, NO a todo el servidor.
GRANT SELECT, INSERT, UPDATE, DELETE ON * TO 'torneo_app_administrador'@'localhost';

-- Planillero: lectura necesaria para identificar torneos, equipos,
-- jugadores, canchas y partidos; no puede editar esas tablas.
GRANT SELECT ON facultad TO 'torneo_app_planillero'@'localhost';
GRANT SELECT ON torneo TO 'torneo_app_planillero'@'localhost';
GRANT SELECT ON complejo TO 'torneo_app_planillero'@'localhost';
GRANT SELECT ON cancha TO 'torneo_app_planillero'@'localhost';
GRANT SELECT ON turno TO 'torneo_app_planillero'@'localhost';
GRANT SELECT ON jugador TO 'torneo_app_planillero'@'localhost';
GRANT SELECT ON equipo TO 'torneo_app_planillero'@'localhost';
GRANT SELECT ON equipo_jugador_torneo TO 'torneo_app_planillero'@'localhost';
GRANT SELECT ON partido TO 'torneo_app_planillero'@'localhost';

-- Unicas tablas donde el planillero puede registrar y corregir datos.
-- Los triggers del esquema siguen imponiendo restricciones de integridad.
GRANT SELECT, INSERT, UPDATE, DELETE ON planilla_partido TO 'torneo_app_planillero'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON gol TO 'torneo_app_planillero'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON tarjeta TO 'torneo_app_planillero'@'localhost';

-- Lectura de resultados y reportes, sin permiso de modificacion.
-- Las vistas SQL SECURITY DEFINER usan permisos de quien las creo.
GRANT SELECT ON v_sanciones_automaticas TO 'torneo_app_planillero'@'localhost';
GRANT SELECT ON v_sanciones TO 'torneo_app_planillero'@'localhost';
GRANT SELECT ON v_resultado_partido TO 'torneo_app_planillero'@'localhost';
GRANT SELECT ON v_reporte_01_posiciones TO 'torneo_app_planillero'@'localhost';
GRANT SELECT ON v_reporte_02_goleadores TO 'torneo_app_planillero'@'localhost';
GRANT SELECT ON v_reporte_03_fair_play TO 'torneo_app_planillero'@'localhost';
GRANT SELECT ON v_reporte_04_promedio_goles TO 'torneo_app_planillero'@'localhost';
GRANT SELECT ON v_reporte_05_uso_espacios TO 'torneo_app_planillero'@'localhost';
GRANT SELECT ON v_reporte_06_jugadores_facultad_tipo TO 'torneo_app_planillero'@'localhost';
GRANT SELECT ON v_reporte_07_nunca_participaron TO 'torneo_app_planillero'@'localhost';
GRANT SELECT ON v_reporte_08_sanciones_equipo TO 'torneo_app_planillero'@'localhost';
GRANT SELECT ON v_reporte_09_estados_partidos TO 'torneo_app_planillero'@'localhost';
GRANT SELECT ON v_reporte_10_local_visitante TO 'torneo_app_planillero'@'localhost';
GRANT SELECT ON v_reporte_11_disciplina_jugadores TO 'torneo_app_planillero'@'localhost';
GRANT SELECT ON v_reporte_12_goles_por_tramo TO 'torneo_app_planillero'@'localhost';

-- Los procedimientos de validacion son INTERNOS y los disparan los triggers.
-- No se concede EXECUTE sobre ellos al planillero.
-- No se concede al planillero SELECT sobre login ni DML sobre sancion_jugador.

-- Inspeccion de privilegios efectivos (ejecutar como DBA).
SHOW GRANTS FOR 'torneo_app_administrador'@'localhost';
SHOW GRANTS FOR 'torneo_app_planillero'@'localhost';
