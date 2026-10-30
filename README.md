# ⚽ Sistema de Gestión del Torneo Interfacultades de Fútbol 5

**Trabajo Obligatorio — Base de Datos 1**  
**Universidad Católica del Uruguay (UCU) · Segundo semestre de 2026**

## 📌 Descripción

Proyecto académico que consiste en diseñar e implementar un sistema de información para gestionar el **Torneo Interfacultades de Fútbol 5** de la UCU.

El sistema busca centralizar la inscripción de equipos y jugadores, la organización del fixture, el registro de resultados y sanciones, y la generación de reportes. De esta manera, se pretende evitar inconsistencias en la tabla de posiciones, superposiciones de partidos en una misma cancha y participación de jugadores suspendidos.


## 🎯 Objetivos

- Gestionar las ediciones semestrales del torneo y sus participantes.
- Organizar partidos, fechas, canchas y turnos sin superposiciones.
- Registrar planillas de juego, goles y tarjetas.
- Aplicar y controlar suspensiones.
- Generar estadísticas y reportes para la organización.
- Garantizar integridad, trazabilidad y controles de acceso.

## 🛠️ Tecnologías y restricciones

| Componente | Tecnología o requisito |
| --- | --- |
| Backend | **Python** |
| Base de datos | **MySQL** (modelo relacional) |
| Frontend | Framework de libre elección, si aplica |
| Acceso a datos | **Sin ORM** |
| Seguridad | Permisos diferenciados a nivel de base de datos |
| Validaciones | Frontend, backend y base de datos |
| Control de versiones | Git / GitHub (repositorio público valorado) |
| Contenedores | Docker y Docker Compose (opcionales, valorados) |

## 🧩 Funcionalidades requeridas

### Administración

- ABM de jugadores.
- ABM de equipos y sus planteles.
- ABM de complejos deportivos y canchas.
- ABM de partidos, respetando las reglas de programación.
- ABM de sanciones a jugadores.
- Gestión de ediciones del torneo y sus estados.

### Registro de partidos

- Carga de la planilla de jugadores participantes.
- Registro de goles (jugador y minuto) y tarjetas amarillas o rojas.
- Cálculo del resultado a partir de los goles registrados.
- Control de jugadores habilitados y plazos para corregir resultados.

### Roles

- **Administrador:** gestiona toda la información del torneo.
- **Planillero:** registra únicamente planillas, goles y tarjetas de partidos.

## 📋 Reglas de negocio

### Torneos y equipos

- Cada torneo corresponde a un semestre y puede estar en estado **inscripción**, **en curso** o **finalizado**.
- El formato es de **liga a una sola rueda**: cada pareja de equipos se enfrenta una vez por edición.
- Cada equipo representa a una facultad y designa como capitán a uno de sus jugadores.
- Cada plantel debe contar con **5 a 10 jugadores**, todos pertenecientes a la facultad representada.
- Se admiten como máximo **2 docentes o funcionarios** por plantel.
- Un jugador no puede integrar más de un equipo en la misma edición.
- Los planteles solo se modifican durante la etapa de inscripción.

### Fixture y canchas

- Los encuentros se agrupan por números de fecha.
- Se programan turnos de una hora entre las **18:00 y las 23:00**.
- Los equipos de un partido deben pertenecer a la misma edición y tener al menos cinco integrantes.
- Un equipo no puede jugar contra sí mismo, repetir un rival (salvo si el encuentro previo fue cancelado) ni disputar más de un partido en la misma fecha.
- Una cancha no puede tener dos partidos el mismo día y turno.

### Resultados y sanciones

- En las planillas solo pueden figurar integrantes de los equipos participantes que no estén suspendidos.
- Solo los jugadores incluidos en la planilla pueden registrar goles o tarjetas.
- Un partido solo puede marcarse como jugado una vez pasado su día y turno.
- Los partidos jugados no pueden eliminarse; los resultados solo pueden corregirse durante las **48 horas** posteriores.
- Puntuación: **victoria = 3 puntos**, **empate = 1**, **derrota = 0**.
- Desempates: **puntos → diferencia de goles → goles a favor**.
- Una **tarjeta roja** o la acumulación de **3 amarillas en una edición** genera automáticamente **una fecha de suspensión**, a cumplir en la siguiente fecha.
- La organización puede aplicar suspensiones disciplinarias de varias fechas.
- Un jugador sancionado no puede participar en las planillas de las fechas alcanzadas por la suspensión.

## 📊 Reportes requeridos

1. **Tabla de posiciones:** partidos jugados, ganados, empatados y perdidos; goles a favor, en contra, diferencia y puntos.
2. **Tabla de goleadores:** los diez jugadores con más goles.
3. **Fair play por equipo:** 1 punto por amarilla y 3 por roja; gana el menor puntaje.
4. **Promedio de goles:** por fecha y por edición.
5. **Utilización de instalaciones:** canchas y turnos más usados.
6. **Jugadores por facultad y tipo:** grado, posgrado, docente y funcionario.
7. **Jugadores sin participación:** inscritos en un plantel que nunca aparecieron en una planilla.
8. **Sanciones:** cantidad por equipo y por motivo.
9. **Estado de partidos:** porcentaje jugados frente a postergados/cancelados.
10. **Tres consultas adicionales:** a definir por el equipo de desarrollo.

## 🗄️ Modelo de datos requerido

La consigna establece como mínimo las siguientes tablas:

| Tabla | Finalidad |
| --- | --- |
| `login` | Credenciales y roles de acceso |
| `facultad` | Facultades participantes |
| `jugador` | Datos personales, facultad y tipo de jugador |
| `torneo` | Ediciones y estados del torneo |
| `equipo` | Equipos, facultad y capitán |
| `equipo_jugador_torneo` | Integrantes y números de camiseta por edición |
| `complejo` | Complejos deportivos |
| `cancha` | Canchas, superficies y condición de techado |
| `turno` | Horarios de comienzo y finalización |
| `partido` | Fixture, equipos, fecha, ubicación y estado |
| `planilla_partido` | Participantes de cada partido |
| `gol` | Goles, minutos y autogoles |
| `tarjeta` | Tarjetas, color y minuto |
| `sancion_jugador` | Motivo, inicio y duración de sanciones |

Se pueden incorporar tablas o atributos adicionales si su necesidad se fundamenta en el diseño.

## 🚀 Ejecución local

La consigna requiere un instructivo completo para ejecutar la aplicación localmente. **Los comandos exactos se documentarán al definir la estructura y las dependencias reales del proyecto.**

Requisitos mínimos previstos:

- Python (versión a confirmar).
- Servidor MySQL (versión a confirmar).
- Dependencias del backend (a documentar).
- Frontend y herramientas adicionales, si corresponde.

Pasos que deberá cubrir la instalación final:

1. Clonar el repositorio.
2. Configurar las credenciales y permisos de MySQL.
3. Ejecutar el script de creación de base de datos y datos maestros.
4. Cargar los datos de prueba.
5. Instalar dependencias y levantar la aplicación.
6. Verificar las funcionalidades y ejecutar los reportes.

> **Pendiente:** agregar comandos verificables de instalación y ejecución cuando estén definidos.

## 🧪 Datos de prueba

La base de datos incluye los siguientes registros para comprobar el funcionamiento del sistema y generar los reportes solicitados.

| Tabla | Registros |
|---|---:|
| Facultades | 6 |
| Equipos | 6 |
| Jugadores | 42 |
| Torneos | 1 |
| Complejos deportivos | 2 |
| Canchas | 3 |
| Turnos | 5 |
| Partidos jugados | 9 |
| Participaciones en planillas | 90 |
| Goles | 29 |
| Tarjetas | 6 |
| Sanciones | 3 |
| Usuarios | 2 |

Los datos corresponden a **6 equipos y 3 fechas disputadas**, e incluyen información sobre planteles, partidos, goles, tarjetas, sanciones y usuarios con diferentes roles.

El archivo `datos_prueba_torneo.sql` contiene las instrucciones SQL necesarias para cargar los registros en la base de datos MySQL.

Los casos de prueba permiten comprobar restricciones de planteles, horarios, sanciones, resultados y control de acceso.

## 📦 Entregables

- [ ] Script SQL completo para crear la base de datos y los datos maestros.
- [ ] Datos de prueba suficientes para los reportes.
- [ ] Aplicación funcional que compile y cumpla los requisitos.
- [ ] Instructivo para ejecución local.
- [ ] Informe con fundamentación de decisiones de implementación.
- [ ] Mejoras implementadas o consideradas en el modelo de datos.
- [ ] Bitácora del trabajo realizado.
- [ ] Bibliografía.

## 📅 Fechas de la asignatura

| Hito | Fecha |
| --- | --- |
| Publicación de consigna | 09/10/2026 |
| Avance | 30/10/2026 |
| Entrega final | 06/11/2026 |
| Defensas | 13/11/2026 |

## 👥 Integrantes

Brian Rocha | 
Nahuel Benitez | 
Jorge Inzaurralde

## 📚 Fuente

Documento de consigna: **«Obligatorio BD - Segundo Semestre 2026»**, Base de Datos 1, Universidad Católica del Uruguay.

---

*Proyecto académico — Universidad Católica del Uruguay, 2026.*
