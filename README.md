Trabajo Obligatorio
Diseñar e implementar un sistema de información para la gestión del Torneo
Interfacultades de Fútbol 5 de la universidad. El sistema debe permitir la organización
del fixture, el registro de resultados y sanciones, y la generación de reportes que
apoyen tanto a la organización del torneo como a la toma de decisiones.
Gestión del Torneo Interfacultades de Fútbol 5
La UCU organiza cada semestre el “Torneo Interfacultades de Fútbol 5”, en el que
compiten equipos integrados por estudiantes, docentes y funcionarios de las distintas
facultades. Actualmente, la inscripción de los equipos, el armado del fixture y el
registro de los resultados se realizan en planillas de cálculo y grupos de mensajería, lo
que provoca errores en la tabla de posiciones, partidos superpuestos en una misma
cancha y jugadores suspendidos que igualmente salen a jugar.
Lo que se pretende con este proyecto es brindarles a los organizadores del torneo un
sistema unificado que permita mantener el control y la trazabilidad de los equipos,
jugadores, partidos, resultados y sanciones de cada edición.
Cada edición del torneo corresponde a un semestre y pasa por tres etapas: inscripción,
en curso y finalizado. El torneo se juega en formato de liga a una sola rueda, es decir,
todos los equipos se enfrentan entre sí una única vez. Los partidos se agrupan en
fechas (fecha 1, fecha 2, etc.) y se disputan en las canchas de distintos complejos
deportivos, en turnos de una hora entre las 18:00 y las 23:00 (de 18:00 a 19:00, de
19:00 a 20:00, y así sucesivamente).
Cada equipo representa a una facultad, tiene un nombre y un capitán, que debe ser
uno de sus jugadores. Los jugadores pueden ser:
● Estudiantes de grado o de posgrado
● Docentes y funcionarios
o Pueden integrar un equipo, pero cada plantel admite como máximo 2
jugadores de este tipo
El plantel de un equipo debe tener entre 5 y 10 jugadores, y todos deben pertenecer a
la facultad que el equipo representa. Un jugador no puede integrar más de un equipo
en una misma edición del torneo, y los planteles solo pueden modificarse mientras el
torneo se encuentra en etapa de inscripción.
Al programar un partido, el sistema debe controlar que:
● Ambos equipos pertenezcan a la misma edición del torneo y tengan al menos 5
jugadores en su plantel
pág. 1
Trabajo obligatorio – Sistema para Gestión del Torneo Interfacultades de Fútbol 5
Base de Datos 1 – Universidad Católica del Uruguay
Segundo Semestre 2026
● Un equipo no se enfrente a sí mismo, ni a un rival con el que ya tenga un
partido en esa edición (salvo que ese partido haya sido cancelado)
● Un equipo no juegue más de un partido en la misma fecha del torneo
● Una cancha no tenga más de un partido asignado en el mismo día y turno
Una vez disputado el partido, el planillero registra en el sistema la planilla de juego, es
decir, los jugadores de cada equipo que participaron del partido, junto con los goles
(jugador y minuto) y las tarjetas amarillas y rojas recibidas. Solo pueden figurar en la
planilla jugadores del plantel de alguno de los dos equipos que no estén suspendidos, y
solo pueden convertir goles o recibir tarjetas los jugadores que figuren en la planilla. El
resultado del partido se calcula a partir de los goles registrados, y un partido solo
puede marcarse como jugado si su día y turno ya pasaron.
Un partido jugado no puede eliminarse, y su resultado solo puede corregirse dentro de
las 48 horas posteriores a su disputa. Por cada partido ganado se otorgan 3 puntos, por
empate 1 y por derrota 0. La tabla de posiciones se ordena por puntos y, en caso de
igualdad, por diferencia de goles y luego por goles a favor.
Los jugadores que reciban una tarjeta roja, o que acumulen 3 tarjetas amarillas en la
edición, serán sancionados automáticamente con una fecha de suspensión, que se
cumple en la fecha siguiente del torneo. Además, la organización puede aplicar
sanciones disciplinarias de varias fechas. Un jugador suspendido no puede figurar en la
planilla de ningún partido correspondiente a las fechas que abarca su sanción.
El sistema contará con dos tipos de usuario: los administradores, que gestionan toda la
información del torneo, y los planilleros, que únicamente pueden registrar las planillas,
goles y tarjetas de los partidos.
La UCU está buscando implementar un primer acercamiento que facilite a los
organizadores:
● Alta, baja y modificación (ABM) de jugadores
● ABM de equipos y sus planteles
● ABM de complejos deportivos y canchas
● ABM de partidos (teniendo en cuenta las reglas y restricciones enunciadas
anteriormente)
● Registro de planillas, goles y tarjetas de cada partido
● ABM de sanciones a jugadores
Con el fin de obtener métricas para el área de deportes de la universidad, se solicita
además un sistema de reportes donde se pueda consultar:
● Tabla de posiciones de una edición del torneo (partidos jugados, ganados,
empatados y perdidos, goles a favor, goles en contra, diferencia de goles y
puntos)
● Tabla de goleadores (los 10 jugadores con más goles)
pág. 2
Trabajo obligatorio – Sistema para Gestión del Torneo Interfacultades de Fútbol 5
Base de Datos 1 – Universidad Católica del Uruguay
Segundo Semestre 2026
● Tabla de fair play por equipo (1 punto por cada tarjeta amarilla y 3 por cada
roja; el mejor equipo es el de menor puntaje)
● Promedio de goles por partido en cada fecha y en toda la edición
● Canchas y turnos más utilizados
● Cantidad de jugadores por facultad y por tipo (grado, posgrado, docente,
funcionario)
● Jugadores inscriptos en un plantel que nunca figuraron en una planilla de juego
● Cantidad de sanciones por equipo y por motivo
● Porcentaje de partidos jugados vs. postergados/cancelados
● Adicionar otras tres consultas sugeridas por ustedes.
Para esto deberá crear una base de datos relacional (SQL) con al menos, las siguientes
estructuras:
● login (correo, contraseña, rol [administrador, planillero])
● facultad (id_facultad, nombre)
● jugador (ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo [grado,
posgrado, docente, funcionario])
● torneo (id_torneo, nombre, anio, semestre, fecha_inicio, fecha_fin, estado
[inscripción, en curso, finalizado])
● equipo (id_equipo, nombre, id_torneo, id_facultad, ci_capitan)
● equipo_jugador_torneo (id_equipo, ci_jugador. id_torneo, numero_camiseta)
● complejo (id_complejo, nombre, dirección, departamento)
● cancha (nombre_cancha, id_complejo, superficie [sintético, parquet], techada
[true, false])
● turno (id_turno, hora_inicio, hora_fin)
● partido (id_partido, id_torneo, numero_fecha, id_equipo_local,
id_equipo_visitante, dia, id_turno, nombre_cancha, id_complejo, estado
[programado, jugado, postergado, cancelado])
● planilla_partido (id_partido, ci_jugador, id_equipo)
● gol (id_gol, id_partido, ci_jugador, minuto, autogol)
● tarjeta (id_tarjeta, id_partido, ci_jugador, minuto, color [amarilla, roja])
● sancion_jugador (id_sancion, ci_jugador, id_torneo, motivo [roja, acumulación
de amarillas, disciplinaria], numero_fecha_inicio, cantidad_fechas)
Los atributos subrayados forman la clave primaria y los atributos en cursiva son claves
foráneas. En caso de que lo consideren necesario, se pueden crear tablas adicionales o
agregar atributos.
pág. 3
Trabajo obligatorio – Sistema para Gestión del Torneo Interfacultades de Fútbol 5
Base de Datos 1 – Universidad Católica del Uruguay
Segundo Semestre 2026
Requisitos del entregable
● Script completo SQL para creación de base de datos y datos maestros
o Debe incluir datos de prueba suficientes para ejecutar todos los
reportes (al menos 6 equipos y 3 fechas disputadas)
● Aplicación funcional:
o Debe compilar
o Debe implementar todos los requerimientos funcionales
● Instructivo completo para correr la aplicación de forma local
● Informe del trabajo realizado:
o Fundamentar decisiones de implementación
o Mejoras implementadas o consideradas en el modelo de datos
o Bitácora del trabajo realizado
o Bibliografía
Consideraciones
● El backend debe ser desarrollado en Python
● La base de datos debe ser MySQL
● El framework de frontend es de libre elección (si aplica)
● No se puede utilizar ningún ORM
● Restricciones de seguridad a nivel de base de datos (por ejemplo, usuarios de
base de datos con permisos diferenciados para administradores y planilleros)
● Validación de campos en todas las capas (front-end, back-end y base de datos)
Se valorarán:
● Utilización de repositorio de GitHub público
● Dockerización de la aplicación y Docker-compose con servicios de app, bases de
datos, etc
Entrega de letra: 09/10/2026
Avance: 30/10/2026
Entrega final: 06/11/2026
Defensas: 13/11/2026
pág. 4
Trabajo obligatorio – Sistema para Gestión del Torneo Interfacultades de Fútbol 5
