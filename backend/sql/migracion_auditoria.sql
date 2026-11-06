-- Actualizacion incremental e idempotente, para ejecutar como DBA.
-- Conserva tablas y datos; detener las escrituras de la aplicacion durante el cambio.
-- El DDL de MySQL hace COMMIT implicito: realizar un respaldo antes de migrar.
USE torneo_ucu;

-- Mantener una sola sentencia ALTER para no dejar el plantel sin integridad referencial.
SET @fk_plantel = (
    SELECT CONSTRAINT_NAME FROM information_schema.REFERENTIAL_CONSTRAINTS
     WHERE CONSTRAINT_SCHEMA=DATABASE() AND TABLE_NAME='equipo_jugador_torneo'
       AND REFERENCED_TABLE_NAME='equipo' AND DELETE_RULE<>'CASCADE' LIMIT 1
);
SET @ddl_plantel = IF(@fk_plantel IS NULL,
    'SELECT ''Plantel: cascada ya configurada'' AS migracion',
    CONCAT('ALTER TABLE equipo_jugador_torneo DROP FOREIGN KEY `', REPLACE(@fk_plantel,'`','``'),
           '`, ADD CONSTRAINT fk_plantel_equipo_cascada FOREIGN KEY (id_equipo,id_torneo) ',
           'REFERENCES equipo(id_equipo,id_torneo) ON DELETE CASCADE'));
PREPARE migrar_plantel FROM @ddl_plantel;
EXECUTE migrar_plantel;
DEALLOCATE PREPARE migrar_plantel;

DELIMITER $$
DROP PROCEDURE IF EXISTS validar_datos_jugador$$
CREATE PROCEDURE validar_datos_jugador(
    IN p_ci INT, IN p_nombre VARCHAR(100), IN p_apellido VARCHAR(100),
    IN p_email VARCHAR(150), IN p_nacimiento DATE
)
BEGIN
    IF p_ci < 100000 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La cedula debe tener al menos 6 digitos';
    END IF;
    IF NOT REGEXP_LIKE(p_nombre, '[^[:space:]]') OR NOT REGEXP_LIKE(p_apellido, '[^[:space:]]') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Nombre y apellido son obligatorios';
    END IF;
    IF NOT REGEXP_LIKE(p_email, '^[^[:space:]@]+@[^[:space:]@]+[.][^[:space:]@]+$') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El correo del jugador no es valido';
    END IF;
    IF p_nacimiento >= CURDATE() THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La fecha de nacimiento debe ser anterior a hoy';
    END IF;
END$$

DROP PROCEDURE IF EXISTS validar_edicion_partido$$
CREATE PROCEDURE validar_edicion_partido(IN p_partido INT)
BEGIN
    DECLARE v_estado VARCHAR(20) DEFAULT NULL;
    DECLARE v_fin DATETIME DEFAULT NULL;

    -- Todas las escrituras de planillas, goles y tarjetas se serializan por edicion.
    -- La lectura con bloqueo usa el estado actual incluso con un snapshot RR previo.
    SELECT p.estado, TIMESTAMP(p.dia, t.hora_fin)
      INTO v_estado, v_fin
      FROM partido p
      JOIN turno t ON t.id_turno = p.id_turno
      JOIN torneo ed ON ed.id_torneo = p.id_torneo
     WHERE p.id_partido = p_partido FOR UPDATE OF ed;

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

DROP PROCEDURE IF EXISTS validar_participante_planilla$$
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
    DECLARE v_automaticas INT DEFAULT 0;

    CALL validar_edicion_partido(p_partido);
    SELECT id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante
      INTO v_torneo, v_fecha, v_local, v_visitante
      FROM partido WHERE id_partido = p_partido FOR SHARE;
    IF p_equipo NOT IN (v_local, v_visitante) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El equipo de la planilla no participa en ese partido';
    END IF;
    SELECT COUNT(*) INTO v_inscrito FROM equipo_jugador_torneo
     WHERE id_equipo = p_equipo AND id_torneo = v_torneo AND ci_jugador = p_ci FOR SHARE;
    IF v_inscrito <> 1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El jugador no integra el plantel de ese equipo';
    END IF;
    -- Las vistas con UNION/ventanas pueden reutilizar un snapshot antiguo.
    -- Leer las tablas base con FOR SHARE mantiene la misma regla de v_sanciones.
    SELECT COUNT(*) INTO v_suspendido FROM sancion_jugador
     WHERE ci_jugador = p_ci AND id_torneo = v_torneo
       AND v_fecha >= numero_fecha_inicio
       AND v_fecha < numero_fecha_inicio + cantidad_fechas FOR SHARE;
    SELECT COUNT(*) INTO v_automaticas FROM (
        SELECT eventos.numero_fecha, eventos.color,
               ROW_NUMBER() OVER (PARTITION BY eventos.color
                   ORDER BY eventos.numero_fecha, eventos.dia, eventos.minuto, eventos.id_tarjeta) AS orden_color
          FROM (
              SELECT t.id_tarjeta, t.color, t.minuto, p.numero_fecha, p.dia
                FROM tarjeta t JOIN partido p ON p.id_partido=t.id_partido
               WHERE t.ci_jugador=p_ci AND p.id_torneo=v_torneo AND p.estado='jugado' FOR SHARE
          ) eventos
    ) x
    WHERE x.numero_fecha + 1 = v_fecha
      AND (x.color='roja' OR (x.color='amarilla' AND MOD(x.orden_color,3)=0));
    SET v_suspendido = v_suspendido + v_automaticas;
    IF v_suspendido > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El jugador esta suspendido para esta fecha';
    END IF;
END$$

DROP PROCEDURE IF EXISTS validar_sancion$$
CREATE PROCEDURE validar_sancion(
    IN p_ci INT, IN p_torneo INT, IN p_inicio INT, IN p_cantidad INT
)
BEGIN
    DECLARE v_conflictos INT DEFAULT 0;
    DECLARE v_miembro INT DEFAULT 0;
    DECLARE v_estado VARCHAR(20);
    SELECT estado INTO v_estado FROM torneo WHERE id_torneo=p_torneo FOR UPDATE;
    SELECT COUNT(*) INTO v_miembro FROM equipo_jugador_torneo
     WHERE ci_jugador = p_ci AND id_torneo = p_torneo FOR SHARE;
    IF v_miembro = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se puede sancionar a un jugador ajeno a esa edicion';
    END IF;
    SELECT COUNT(*) INTO v_conflictos FROM planilla_partido pp
      JOIN partido p ON p.id_partido = pp.id_partido
     WHERE pp.ci_jugador = p_ci AND p.id_torneo = p_torneo
       AND p.numero_fecha >= p_inicio
       AND p.numero_fecha < p_inicio + p_cantidad FOR SHARE;
    IF v_conflictos > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La sancion se superpone con planillas existentes';
    END IF;
END$$

DROP PROCEDURE IF EXISTS validar_coherencia_sanciones_automaticas$$
CREATE PROCEDURE validar_coherencia_sanciones_automaticas(IN p_ci INT, IN p_torneo INT)
BEGIN
    DECLARE v_incompatibles INT DEFAULT 0;
    -- La entrada de la ventana y las planillas deben ser lecturas actuales.
    SELECT COUNT(*) INTO v_incompatibles
      FROM (
        SELECT eventos.numero_fecha, eventos.color,
               ROW_NUMBER() OVER (PARTITION BY eventos.color
                   ORDER BY eventos.numero_fecha, eventos.dia, eventos.minuto, eventos.id_tarjeta) AS orden_color
          FROM (
              SELECT t.id_tarjeta, t.color, t.minuto, p.numero_fecha, p.dia
                FROM tarjeta t JOIN partido p ON p.id_partido=t.id_partido
               WHERE t.ci_jugador=p_ci AND p.id_torneo=p_torneo AND p.estado='jugado' FOR SHARE
          ) eventos
      ) sa
      JOIN partido p ON p.id_torneo=p_torneo AND p.numero_fecha=sa.numero_fecha+1
      JOIN planilla_partido pp ON pp.id_partido=p.id_partido AND pp.ci_jugador=p_ci
     WHERE sa.color='roja' OR (sa.color='amarilla' AND MOD(sa.orden_color,3)=0) FOR SHARE;
    IF v_incompatibles > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'La tarjeta generaria una suspension incompatible con una planilla existente';
    END IF;
END$$

DROP TRIGGER IF EXISTS bi_jugador$$
CREATE TRIGGER bi_jugador BEFORE INSERT ON jugador FOR EACH ROW
BEGIN
    CALL validar_datos_jugador(NEW.ci, NEW.nombre, NEW.apellido, NEW.email, NEW.fecha_nacimiento);
END$$

DROP TRIGGER IF EXISTS bu_jugador$$
CREATE TRIGGER bu_jugador BEFORE UPDATE ON jugador FOR EACH ROW
BEGIN
    DECLARE v_inscrito INT DEFAULT 0;
    CALL validar_datos_jugador(NEW.ci, NEW.nombre, NEW.apellido, NEW.email, NEW.fecha_nacimiento);
    IF NEW.id_facultad <> OLD.id_facultad OR NEW.tipo <> OLD.tipo THEN
        SELECT COUNT(*) INTO v_inscrito FROM equipo_jugador_torneo
         WHERE ci_jugador = OLD.ci;
        IF v_inscrito > 0 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Para cambiar facultad o tipo, primero debe salir de todos los planteles';
        END IF;
    END IF;
END$$

DROP TRIGGER IF EXISTS bd_equipo$$
CREATE TRIGGER bd_equipo BEFORE DELETE ON equipo FOR EACH ROW
BEGIN
    DECLARE v_estado VARCHAR(20) DEFAULT NULL;
    DECLARE v_sanciones INT DEFAULT 0;
    SELECT estado INTO v_estado FROM torneo WHERE id_torneo = OLD.id_torneo FOR UPDATE;
    IF v_estado IS NULL OR v_estado <> 'inscripción' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo se eliminan equipos durante la inscripcion';
    END IF;
    SELECT COUNT(*) INTO v_sanciones
      FROM sancion_jugador s
      JOIN equipo_jugador_torneo ejt
        ON ejt.ci_jugador = s.ci_jugador AND ejt.id_torneo = s.id_torneo
     WHERE ejt.id_equipo = OLD.id_equipo AND ejt.id_torneo = OLD.id_torneo;
    IF v_sanciones > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El equipo tiene jugadores con sanciones en esta edicion';
    END IF;
    -- Las FK de partido y planilla impiden eliminar equipos con historial.
END$$

DROP TRIGGER IF EXISTS bu_turno$$
CREATE TRIGGER bu_turno BEFORE UPDATE ON turno FOR EACH ROW
BEGIN
    DECLARE v_jugados INT DEFAULT 0;
    IF NEW.hora_inicio <> OLD.hora_inicio OR NEW.hora_fin <> OLD.hora_fin THEN
        SELECT COUNT(*) INTO v_jugados FROM partido
         WHERE id_turno = OLD.id_turno AND estado = 'jugado';
        IF v_jugados > 0 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se puede cambiar un turno utilizado por partidos jugados';
        END IF;
    END IF;
END$$

DROP TRIGGER IF EXISTS bd_sancion$$
CREATE TRIGGER bd_sancion BEFORE DELETE ON sancion_jugador FOR EACH ROW
BEGIN
    DECLARE v_estado VARCHAR(20);
    SELECT estado INTO v_estado FROM torneo WHERE id_torneo=OLD.id_torneo FOR UPDATE;
    IF OLD.origen = 'automatica' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'No se permite eliminar sanciones automaticas';
    END IF;
END$$

DROP TRIGGER IF EXISTS ai_tarjeta$$
CREATE TRIGGER ai_tarjeta AFTER INSERT ON tarjeta FOR EACH ROW
BEGIN
    DECLARE v_torneo INT DEFAULT NULL;
    SELECT id_torneo INTO v_torneo FROM partido WHERE id_partido = NEW.id_partido FOR SHARE;
    CALL validar_coherencia_sanciones_automaticas(NEW.ci_jugador, v_torneo);
END$$

DROP TRIGGER IF EXISTS au_tarjeta$$
CREATE TRIGGER au_tarjeta AFTER UPDATE ON tarjeta FOR EACH ROW
BEGIN
    DECLARE v_torneo_anterior INT DEFAULT NULL;
    DECLARE v_torneo_nuevo INT DEFAULT NULL;
    SELECT id_torneo INTO v_torneo_anterior FROM partido WHERE id_partido = OLD.id_partido FOR SHARE;
    SELECT id_torneo INTO v_torneo_nuevo FROM partido WHERE id_partido = NEW.id_partido FOR SHARE;
    CALL validar_coherencia_sanciones_automaticas(OLD.ci_jugador, v_torneo_anterior);
    IF OLD.ci_jugador <> NEW.ci_jugador OR v_torneo_anterior <> v_torneo_nuevo THEN
        CALL validar_coherencia_sanciones_automaticas(NEW.ci_jugador, v_torneo_nuevo);
    END IF;
END$$

DROP TRIGGER IF EXISTS ad_tarjeta$$
CREATE TRIGGER ad_tarjeta AFTER DELETE ON tarjeta FOR EACH ROW
BEGIN
    DECLARE v_torneo INT DEFAULT NULL;
    SELECT id_torneo INTO v_torneo FROM partido WHERE id_partido = OLD.id_partido FOR SHARE;
    CALL validar_coherencia_sanciones_automaticas(OLD.ci_jugador, v_torneo);
END$$

DROP TRIGGER IF EXISTS bd_plantel$$
CREATE TRIGGER bd_plantel BEFORE DELETE ON equipo_jugador_torneo FOR EACH ROW
BEGIN
    DECLARE v_estado VARCHAR(20) DEFAULT NULL;
    DECLARE v_es_capitan INT DEFAULT 0;
    DECLARE v_partidos INT DEFAULT 0;
    DECLARE v_cantidad INT DEFAULT 0;
    DECLARE v_sanciones INT DEFAULT 0;
    SELECT estado INTO v_estado FROM torneo WHERE id_torneo = OLD.id_torneo FOR UPDATE;
    IF v_estado <> 'inscripción' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El plantel solo se modifica en inscripcion';
    END IF;
    SELECT COUNT(*) INTO v_sanciones FROM sancion_jugador
     WHERE ci_jugador=OLD.ci_jugador AND id_torneo=OLD.id_torneo FOR SHARE;
    IF v_sanciones > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El jugador tiene sanciones en esta edicion; revise sus sanciones antes de quitarlo del plantel';
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

DELIMITER ;
