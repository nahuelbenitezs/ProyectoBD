-- Datos de prueba | Torneo Interfacultades de Futbol 5
-- Edicion: segundo semestre de 2026

START TRANSACTION;

-- LOGIN
INSERT INTO login (correo, contrasena, rol) VALUES
  ('admin@demo.ucu.edu.uy', SHA2('AdminDemo2026!', 256), 'administrador'),
  ('planillero@demo.ucu.edu.uy', SHA2('PlanillaDemo2026!', 256), 'planillero');

-- FACULTAD
INSERT INTO facultad (id_facultad, nombre) VALUES
  (1, 'Ingenieria'),
  (2, 'Ciencias Empresariales'),
  (3, 'Derecho'),
  (4, 'Ciencias de la Salud'),
  (5, 'Humanidades'),
  (6, 'Psicologia');

-- TORNEO
INSERT INTO torneo (id_torneo, nombre, anio, semestre, fecha_inicio, fecha_fin, estado) VALUES
  (1, 'Interfacultades Futbol 5 - 2026 S2', 2026, 2, '2026-10-01', '2026-11-30', 'en curso');

-- COMPLEJO
INSERT INTO complejo (id_complejo, nombre, direccion, departamento) VALUES
  (1, 'Complejo Norte', 'Av. Demo 1200', 'Montevideo'),
  (2, 'Complejo Sur', 'Calle Ejemplo 550', 'Montevideo');

-- CANCHA
INSERT INTO cancha (nombre_cancha, id_complejo, superficie, techada) VALUES
  ('Cancha A', 1, 'sintético', FALSE),
  ('Cancha B', 1, 'sintético', TRUE),
  ('Cancha 1', 2, 'parquet', TRUE);

-- TURNO
INSERT INTO turno (id_turno, hora_inicio, hora_fin) VALUES
  (1, '18:00:00', '19:00:00'),
  (2, '19:00:00', '20:00:00'),
  (3, '20:00:00', '21:00:00'),
  (4, '21:00:00', '22:00:00'),
  (5, '22:00:00', '23:00:00');

-- JUGADOR
INSERT INTO jugador (ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo) VALUES
  (50000101, 'Sofia', 'Pereira', 'jugador0101@example.edu.uy', '1991-02-11', 1, 'grado'),
  (50000102, 'Martin', 'Rodriguez', 'jugador0102@example.edu.uy', '1992-02-12', 1, 'grado'),
  (50000103, 'Camila', 'Fernandez', 'jugador0103@example.edu.uy', '1993-02-13', 1, 'grado'),
  (50000104, 'Luciano', 'Silva', 'jugador0104@example.edu.uy', '1994-02-14', 1, 'grado'),
  (50000105, 'Valentina', 'Gonzalez', 'jugador0105@example.edu.uy', '1995-02-15', 1, 'posgrado'),
  (50000106, 'Nicolas', 'Lopez', 'jugador0106@example.edu.uy', '1996-02-16', 1, 'docente'),
  (50000107, 'Florencia', 'Martinez', 'jugador0107@example.edu.uy', '1997-02-17', 1, 'grado'),
  (50000201, 'Sofia', 'Rodriguez', 'jugador0201@example.edu.uy', '1991-03-11', 2, 'grado'),
  (50000202, 'Martin', 'Fernandez', 'jugador0202@example.edu.uy', '1992-03-12', 2, 'grado'),
  (50000203, 'Camila', 'Silva', 'jugador0203@example.edu.uy', '1993-03-13', 2, 'grado'),
  (50000204, 'Luciano', 'Gonzalez', 'jugador0204@example.edu.uy', '1994-03-14', 2, 'grado'),
  (50000205, 'Valentina', 'Lopez', 'jugador0205@example.edu.uy', '1995-03-15', 2, 'posgrado'),
  (50000206, 'Nicolas', 'Martinez', 'jugador0206@example.edu.uy', '1996-03-16', 2, 'docente'),
  (50000207, 'Florencia', 'Pereira', 'jugador0207@example.edu.uy', '1997-03-17', 2, 'funcionario'),
  (50000301, 'Sofia', 'Fernandez', 'jugador0301@example.edu.uy', '1991-04-11', 3, 'grado'),
  (50000302, 'Martin', 'Silva', 'jugador0302@example.edu.uy', '1992-04-12', 3, 'grado'),
  (50000303, 'Camila', 'Gonzalez', 'jugador0303@example.edu.uy', '1993-04-13', 3, 'grado'),
  (50000304, 'Luciano', 'Lopez', 'jugador0304@example.edu.uy', '1994-04-14', 3, 'grado'),
  (50000305, 'Valentina', 'Martinez', 'jugador0305@example.edu.uy', '1995-04-15', 3, 'posgrado'),
  (50000306, 'Nicolas', 'Pereira', 'jugador0306@example.edu.uy', '1996-04-16', 3, 'docente'),
  (50000307, 'Florencia', 'Rodriguez', 'jugador0307@example.edu.uy', '1997-04-17', 3, 'grado'),
  (50000401, 'Sofia', 'Silva', 'jugador0401@example.edu.uy', '1991-05-11', 4, 'grado'),
  (50000402, 'Martin', 'Gonzalez', 'jugador0402@example.edu.uy', '1992-05-12', 4, 'grado'),
  (50000403, 'Camila', 'Lopez', 'jugador0403@example.edu.uy', '1993-05-13', 4, 'grado'),
  (50000404, 'Luciano', 'Martinez', 'jugador0404@example.edu.uy', '1994-05-14', 4, 'grado'),
  (50000405, 'Valentina', 'Pereira', 'jugador0405@example.edu.uy', '1995-05-15', 4, 'posgrado'),
  (50000406, 'Nicolas', 'Rodriguez', 'jugador0406@example.edu.uy', '1996-05-16', 4, 'docente'),
  (50000407, 'Florencia', 'Fernandez', 'jugador0407@example.edu.uy', '1997-05-17', 4, 'funcionario'),
  (50000501, 'Sofia', 'Gonzalez', 'jugador0501@example.edu.uy', '1991-06-11', 5, 'grado'),
  (50000502, 'Martin', 'Lopez', 'jugador0502@example.edu.uy', '1992-06-12', 5, 'grado'),
  (50000503, 'Camila', 'Martinez', 'jugador0503@example.edu.uy', '1993-06-13', 5, 'grado'),
  (50000504, 'Luciano', 'Pereira', 'jugador0504@example.edu.uy', '1994-06-14', 5, 'grado'),
  (50000505, 'Valentina', 'Rodriguez', 'jugador0505@example.edu.uy', '1995-06-15', 5, 'posgrado'),
  (50000506, 'Nicolas', 'Fernandez', 'jugador0506@example.edu.uy', '1996-06-16', 5, 'docente'),
  (50000507, 'Florencia', 'Silva', 'jugador0507@example.edu.uy', '1997-06-17', 5, 'grado'),
  (50000601, 'Sofia', 'Lopez', 'jugador0601@example.edu.uy', '1991-07-11', 6, 'grado'),
  (50000602, 'Martin', 'Martinez', 'jugador0602@example.edu.uy', '1992-07-12', 6, 'grado'),
  (50000603, 'Camila', 'Pereira', 'jugador0603@example.edu.uy', '1993-07-13', 6, 'grado'),
  (50000604, 'Luciano', 'Rodriguez', 'jugador0604@example.edu.uy', '1994-07-14', 6, 'grado'),
  (50000605, 'Valentina', 'Fernandez', 'jugador0605@example.edu.uy', '1995-07-15', 6, 'posgrado'),
  (50000606, 'Nicolas', 'Silva', 'jugador0606@example.edu.uy', '1996-07-16', 6, 'docente'),
  (50000607, 'Florencia', 'Gonzalez', 'jugador0607@example.edu.uy', '1997-07-17', 6, 'grado');

-- EQUIPO
INSERT INTO equipo (id_equipo, nombre, id_torneo, id_facultad, ci_capitan) VALUES
  (1, 'Halcones', 1, 1, 50000101),
  (2, 'Tigres', 1, 2, 50000201),
  (3, 'Leones', 1, 3, 50000301),
  (4, 'Pumas', 1, 4, 50000401),
  (5, 'Lobos', 1, 5, 50000501),
  (6, 'Aguilas', 1, 6, 50000601);

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
INSERT INTO partido (id_partido, id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante, dia, id_turno, nombre_cancha, id_complejo, estado) VALUES
  (1, 1, 1, 1, 6, '2026-10-05', 1, 'Cancha A', 1, 'jugado'),
  (2, 1, 1, 2, 5, '2026-10-05', 1, 'Cancha B', 1, 'jugado'),
  (3, 1, 1, 3, 4, '2026-10-05', 1, 'Cancha 1', 2, 'jugado'),
  (4, 1, 2, 1, 5, '2026-10-12', 1, 'Cancha A', 1, 'jugado'),
  (5, 1, 2, 6, 4, '2026-10-12', 1, 'Cancha B', 1, 'jugado'),
  (6, 1, 2, 2, 3, '2026-10-12', 1, 'Cancha 1', 2, 'jugado'),
  (7, 1, 3, 1, 4, '2026-10-19', 1, 'Cancha A', 1, 'jugado'),
  (8, 1, 3, 5, 3, '2026-10-19', 1, 'Cancha B', 1, 'jugado'),
  (9, 1, 3, 6, 2, '2026-10-19', 1, 'Cancha 1', 2, 'jugado');

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
INSERT INTO gol (id_gol, id_partido, ci_jugador, minuto, autogol) VALUES
  (1, 1, 50000101, 10, FALSE),
  (2, 1, 50000102, 22, FALSE),
  (3, 1, 50000601, 18, FALSE),
  (4, 2, 50000201, 10, FALSE),
  (5, 2, 50000501, 18, FALSE),
  (6, 3, 50000401, 18, FALSE),
  (7, 3, 50000402, 30, FALSE),
  (8, 3, 50000403, 42, FALSE),
  (9, 4, 50000101, 10, FALSE),
  (10, 4, 50000102, 22, FALSE),
  (11, 4, 50000104, 34, FALSE),
  (12, 5, 50000601, 10, FALSE),
  (13, 5, 50000401, 18, FALSE),
  (14, 5, 50000402, 30, FALSE),
  (15, 6, 50000201, 10, FALSE),
  (16, 6, 50000202, 22, FALSE),
  (17, 6, 50000301, 18, FALSE),
  (18, 6, 50000302, 30, FALSE),
  (19, 7, 50000401, 18, FALSE),
  (20, 8, 50000501, 10, FALSE),
  (21, 8, 50000502, 22, FALSE),
  (22, 8, 50000503, 34, FALSE),
  (23, 8, 50000504, 46, FALSE),
  (24, 8, 50000301, 18, FALSE),
  (25, 8, 50000302, 30, FALSE),
  (26, 9, 50000601, 10, FALSE),
  (27, 9, 50000201, 18, FALSE),
  (28, 9, 50000202, 30, FALSE),
  (29, 9, 50000203, 42, FALSE);

-- TARJETA
INSERT INTO tarjeta (id_tarjeta, id_partido, ci_jugador, minuto, color) VALUES
  (1, 1, 50000103, 52, 'roja'),
  (2, 2, 50000203, 35, 'amarilla'),
  (3, 5, 50000402, 54, 'amarilla'),
  (4, 6, 50000203, 35, 'amarilla'),
  (5, 9, 50000203, 35, 'amarilla'),
  (6, 9, 50000605, 40, 'amarilla');

-- SANCION_JUGADOR
INSERT INTO sancion_jugador (id_sancion, ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas) VALUES
  (1, 50000103, 1, 'roja', 2, 1),
  (2, 50000203, 1, 'acumulación de amarillas', 4, 1),
  (3, 50000304, 1, 'disciplinaria', 3, 1);

COMMIT;
