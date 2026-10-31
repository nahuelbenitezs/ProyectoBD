-- Verificacion de la carga de DEMOSTRACION de datos_torneo_con_empate_0_0.sql
-- MySQL 8.0.16+. Ejecutar DESPUES del script principal, antes de modificar datos.
-- Comprueba los 12 reportes, autogoles, estados y sanciones automáticas.
-- Las pruebas negativas deben ser rechazadas por las restricciones de BD.

DELIMITER $$
CREATE PROCEDURE verificar_datos_torneo_demo()
BEGIN
    DECLARE n INT DEFAULT 0;
    DECLARE rechazado BOOLEAN DEFAULT FALSE;

    SELECT COUNT(*) INTO n FROM equipo WHERE id_torneo = 1;
    IF n <> 6 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Fallo: cantidad de equipos'; END IF;

    SELECT COUNT(*) INTO n FROM partido WHERE estado = 'jugado' AND id_torneo = 1;
    IF n <> 10 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Fallo: partidos jugados'; END IF;

    SELECT COUNT(*) INTO n FROM partido WHERE id_torneo = 1;
    IF n <> 13 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Fallo: partidos totales'; END IF;

    -- Validar explicitamente el partido jugado 0-0 de fecha 4.
    -- Debe tener planilla de ambos equipos, pero ninguna fila en gol.
    SELECT COUNT(*) INTO n
      FROM partido p
      JOIN v_resultado_partido r ON r.id_partido = p.id_partido
     WHERE p.id_torneo = 1 AND p.numero_fecha = 4
       AND p.id_equipo_local = 1 AND p.id_equipo_visitante = 3
       AND p.dia = '2026-10-26' AND p.estado = 'jugado'
       AND r.goles_local = 0 AND r.goles_visitante = 0
       AND NOT EXISTS (SELECT 1 FROM gol g WHERE g.id_partido = p.id_partido)
       AND (SELECT COUNT(*) FROM planilla_partido pp
             WHERE pp.id_partido = p.id_partido AND pp.id_equipo = 1) = 5
       AND (SELECT COUNT(*) FROM planilla_partido pp
             WHERE pp.id_partido = p.id_partido AND pp.id_equipo = 3) = 5;
    IF n <> 1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Fallo: partido 0-0 o planilla'; END IF;

    -- El partido 0-0 debe sumar un empate y un punto a cada equipo.
    -- Resto de partidos se comprueba en los reportes generales.
    SELECT COUNT(*) INTO n
      FROM v_resultado_partido r
     WHERE r.id_torneo = 1 AND r.numero_fecha = 4
       AND r.goles_local = r.goles_visitante
       AND r.goles_local = 0;
    IF n <> 1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Fallo: empate de fecha 4'; END IF;

    -- La tabla de posiciones debe sumar un punto a cada equipo por el 0-0.
    SELECT COUNT(*) INTO n FROM v_reporte_01_posiciones
     WHERE id_torneo = 1 AND (
           (id_equipo = 1 AND empatados = 2 AND puntos = 8)
        OR (id_equipo = 3 AND empatados = 2 AND puntos = 2));
    IF n <> 2 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Fallo: puntos del 0-0 en posiciones'; END IF;

    SELECT COUNT(*) INTO n FROM gol WHERE autogol = TRUE;
    IF n <> 1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Fallo: autogol de prueba'; END IF;

    SELECT SUM(goles_local + goles_visitante) INTO n FROM v_resultado_partido WHERE id_torneo = 1;
    IF n <> 30 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Fallo: total de goles'; END IF;

    SELECT COUNT(*) INTO n FROM v_reporte_01_posiciones WHERE id_torneo = 1;
    IF n <> 6 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Fallo: posiciones'; END IF;

    SELECT COUNT(*) INTO n FROM v_reporte_02_goleadores WHERE id_torneo = 1;
    IF n <> 10 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Fallo: top 10 goleadores'; END IF;

    SELECT SUM(puntos_fair_play) INTO n FROM v_reporte_03_fair_play WHERE id_torneo = 1;
    IF n <> 8 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Fallo: fair play'; END IF;

    SELECT total_goles INTO n FROM v_reporte_04_promedio_goles
     WHERE id_torneo = 1 AND alcance = 'edicion';
    IF n <> 30 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Fallo: promedio de goles'; END IF;

    SELECT COUNT(*) INTO n FROM v_reporte_05_uso_espacios WHERE id_torneo = 1;
    IF n <> 4 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Fallo: uso de canchas/turnos'; END IF;

    SELECT SUM(cantidad_jugadores) INTO n FROM v_reporte_06_jugadores_facultad_tipo;
    IF n <> 42 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Fallo: jugadores por facultad'; END IF;

    SELECT COUNT(*) INTO n FROM v_reporte_07_nunca_participaron WHERE id_torneo = 1;
    IF n <> 10 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Fallo: no participantes'; END IF;

    SELECT SUM(cantidad_sanciones) INTO n FROM v_reporte_08_sanciones_equipo WHERE id_torneo = 1;
    IF n <> 3 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Fallo: sanciones por equipo'; END IF;

    SELECT jugados + postergados + cancelados + programados INTO n
      FROM v_reporte_09_estados_partidos WHERE id_torneo = 1;
    IF n <> 13 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Fallo: estados de partidos'; END IF;

    SELECT SUM(partidos_local + partidos_visitante) INTO n
      FROM v_reporte_10_local_visitante WHERE id_torneo = 1;
    IF n <> 20 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Fallo: local vs visitante'; END IF;

    SELECT SUM(sanciones) INTO n FROM v_reporte_11_disciplina_jugadores WHERE id_torneo = 1;
    IF n <> 3 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Fallo: disciplina individual'; END IF;

    SELECT SUM(cantidad_goles) INTO n FROM v_reporte_12_goles_por_tramo WHERE id_torneo = 1;
    IF n <> 30 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Fallo: goles por tramo'; END IF;

    SELECT COUNT(*) INTO n FROM v_sanciones_automaticas
     WHERE ci_jugador = 50000103 AND motivo = 'roja' AND numero_fecha_inicio = 2;
    IF n <> 1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Fallo: sancion por roja'; END IF;

    SELECT COUNT(*) INTO n FROM v_sanciones_automaticas
     WHERE ci_jugador = 50000203 AND motivo = 'acumulación de amarillas'
       AND numero_fecha_inicio = 4;
    IF n <> 1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Fallo: sancion por 3 amarillas'; END IF;

    -- Intentar insertar una sancion automatica en la tabla fisica: debe fallar.
    SET rechazado = FALSE;
    BEGIN
        DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET rechazado = TRUE;
        INSERT INTO sancion_jugador
             (ci_jugador, id_torneo, motivo, numero_fecha_inicio, cantidad_fechas, origen)
        VALUES (50000103, 1, 'roja', 5, 1, 'automatica');
    END;
    IF NOT rechazado THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Fallo: se pudo insertar una sancion automatica';
    END IF;

    -- Intentar editar una sancion automatica derivada: la vista no es actualizable.
    SET rechazado = FALSE;
    BEGIN
        DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET rechazado = TRUE;
        UPDATE v_sanciones_automaticas
           SET cantidad_fechas = 5
         WHERE ci_jugador = 50000103;
    END;
    IF NOT rechazado THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Fallo: sancion automatica editable';
    END IF;

    SELECT 'OK: 12 reportes, empate 0-0, planillas, estados, sanciones y protecciones' AS resultado;
END$$
DELIMITER ;

CALL verificar_datos_torneo_demo();
DROP PROCEDURE verificar_datos_torneo_demo;
