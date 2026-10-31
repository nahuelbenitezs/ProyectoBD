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


# Backend — Torneo Interfacultades de Fútbol 5

## Objetivo

Implementar una API REST en **Python** que permita gestionar el Torneo Interfacultades de Fútbol 5, utilizando **MySQL** como base de datos y **consultas SQL directas, sin ORM**, de acuerdo con la consigna del obligatorio de Base de Datos 1.

## Tecnologías y criterios

- **Backend:** Python con Flask o FastAPI.
- **Base de datos:** MySQL.
- **Conexión SQL:** `mysql-connector-python` o `PyMySQL`.
- **Acceso a datos:** sentencias SQL parametrizadas (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) y, cuando corresponda, llamadas a procedimientos almacenados.
- **Restricción:** no utilizar ORM (SQLAlchemy ORM, Django ORM, Peewee, etc.).
- **Seguridad:** autenticación, autorización por rol y permisos de base de datos diferenciados.

## Checklist de implementación

### 1. Configuración inicial

- [ ] Crear el proyecto Python y configurar las dependencias.
- [ ] Configurar Flask o FastAPI y las rutas de la API REST.
- [ ] Implementar la conexión a MySQL sin ORM.
- [ ] Utilizar consultas parametrizadas para evitar inyección SQL.
- [ ] Configurar credenciales y secretos mediante variables de entorno; incluir `.env.example` sin contraseñas reales.
- [ ] Centralizar el manejo de errores y las respuestas HTTP.
- [ ] Configurar CORS si el frontend se encuentra en otro origen.
- [ ] Organizar rutas, servicios, validaciones y acceso a datos.

### 2. Autenticación y autorización

- [ ] Implementar inicio de sesión mediante correo electrónico y contraseña.
- [ ] Validar las credenciales con la tabla `login` y un mecanismo seguro de verificación de contraseñas.
- [ ] Implementar sesiones o tokens de autenticación y cierre de sesión.
- [ ] Diferenciar los roles `administrador` y `planillero`.
- [ ] Restringir endpoints según el rol autenticado.
- [ ] Comprobar que las cuentas y permisos de MySQL se utilizan correctamente desde el backend.
- [ ] No exponer contraseñas, tokens ni datos internos de conexión en las respuestas.

| Operación | Administrador | Planillero |
| --- | :---: | :---: |
| Administrar jugadores, equipos y planteles | ✅ | ❌ |
| Administrar torneos, complejos y canchas | ✅ | ❌ |
| Programar y modificar partidos | ✅ | ❌ |
| Registrar planillas de juego | ✅ | ✅ |
| Registrar goles y tarjetas | ✅ | ✅ |
| Administrar sanciones disciplinarias | ✅ | ❌ |
| Consultar información y reportes autorizados | ✅ | ✅ |

### 3. Gestión de jugadores (ABM)

- [ ] Listar jugadores y consultar el detalle por cédula.
- [ ] Registrar jugadores.
- [ ] Modificar sus datos.
- [ ] Eliminar jugadores cuando las referencias de la BD lo permitan.
- [ ] Filtrar jugadores por facultad y tipo.
- [ ] Validar cédula, nombre, apellido, correo, fecha de nacimiento, facultad y tipo.
- [ ] Controlar la unicidad de cédula y correo electrónico.

### 4. Gestión de equipos y planteles (ABM)

- [ ] Crear, listar, consultar, modificar y eliminar equipos cuando corresponda.
- [ ] Asignar torneo, facultad y capitán.
- [ ] Consultar planteles e inscribir o quitar jugadores.
- [ ] Asignar o modificar números de camiseta.
- [ ] Impedir jugadores duplicados en una misma edición.
- [ ] Validar que cada jugador pertenezca a la facultad representada.
- [ ] Respetar el máximo de 10 jugadores por plantel.
- [ ] Respetar el máximo conjunto de 2 docentes o funcionarios.
- [ ] Exigir al menos 5 integrantes antes de habilitar al equipo para competir.
- [ ] Comprobar que el capitán pertenezca al plantel.
- [ ] Impedir camisetas repetidas dentro del mismo equipo y edición.
- [ ] Permitir cambios de plantel únicamente durante la etapa de inscripción.

> Durante la inscripción, un equipo puede incorporar progresivamente sus integrantes. El mínimo de cinco se controla antes de disputar partidos.

### 5. Gestión de torneos

- [ ] Listar y consultar ediciones del torneo.
- [ ] Crear y modificar ediciones con año, semestre y fechas de inicio y fin.
- [ ] Gestionar estados: `inscripción`, `en curso` y `finalizado`.
- [ ] Validar las transiciones de estado y los planteles antes de comenzar una edición.
- [ ] Consultar equipos y fechas correspondientes a cada torneo.

### 6. Gestión de complejos deportivos, canchas y turnos

- [ ] Implementar ABM de complejos deportivos.
- [ ] Implementar ABM de canchas asociadas a sus complejos.
- [ ] Validar superficie (`sintético` o `parquet`) y condición de techada.
- [ ] Consultar turnos y disponibilidad de canchas.
- [ ] Respetar turnos de una hora entre las 18:00 y las 23:00.
- [ ] Impedir bajas que vulneren las relaciones referenciales.

### 7. Gestión de partidos y fixture (ABM)

- [ ] Listar partidos por torneo, fecha, estado o equipo.
- [ ] Programar partidos indicando local, visitante, fecha, cancha y turno.
- [ ] Modificar partidos cuando esté permitido.
- [ ] Postergar o cancelar partidos.
- [ ] Marcar partidos como jugados únicamente cuando corresponda.
- [ ] Impedir eliminar un partido ya disputado.
- [ ] Consultar el resultado calculado a partir de los goles.
- [ ] Validar que los equipos pertenezcan al mismo torneo y tengan al menos cinco jugadores.
- [ ] Impedir enfrentamientos de un equipo contra sí mismo.
- [ ] Impedir repetir rivales en la misma edición, salvo las excepciones por cancelación.
- [ ] Impedir más de un partido por equipo en una misma fecha del torneo.
- [ ] Impedir superposiciones de cancha, día y turno.
- [ ] Respetar la liga a una sola rueda.

### 8. Registro de planillas de partido

- [ ] Consultar los planteles de los dos equipos del partido.
- [ ] Registrar los participantes en `planilla_partido`.
- [ ] Consultar y corregir la planilla cuando corresponda.
- [ ] Impedir incluir jugadores ajenos a los equipos participantes.
- [ ] Impedir incluir jugadores suspendidos para esa fecha.
- [ ] Ejecutar operaciones de varias filas mediante transacciones y `ROLLBACK` ante fallos.

### 9. Registro de goles y tarjetas

**Goles**

- [ ] Registrar jugador, partido, minuto y condición de autogol.
- [ ] Listar, corregir y eliminar goles dentro del plazo permitido.
- [ ] Impedir registrar goles de jugadores que no figuren en la planilla.
- [ ] Consultar el resultado calculado en `v_resultado_partido`, incluidos autogoles y empates 0-0.

**Tarjetas**

- [ ] Registrar jugador, partido, minuto y color de la tarjeta.
- [ ] Consultar, corregir y eliminar tarjetas dentro del plazo permitido.
- [ ] Impedir tarjetas de jugadores no incluidos en la planilla.
- [ ] Respetar el límite de 48 horas para las correcciones posteriores al partido.

### 10. Sanciones

- [ ] Listar sanciones por jugador, equipo, motivo y torneo.
- [ ] Crear, modificar y eliminar sanciones **disciplinarias** cuando esté permitido.
- [ ] Consultar las sanciones automáticas derivadas de tarjetas.
- [ ] Contemplar una fecha de suspensión por roja o por acumulación de tres amarillas.
- [ ] Comprobar si un jugador está suspendido para una fecha antes de registrar su participación.
- [ ] Consultar la vista `v_sanciones` cuando se necesiten sanciones manuales y automáticas juntas.
- [ ] Evitar duplicar en Python la generación de sanciones que resuelve MySQL.

### 11. Reportes estadísticos

- [ ] Exponer los 9 reportes obligatorios mediante endpoints de consulta.
- [ ] Exponer los 3 reportes adicionales propuestos.
- [ ] Consultar las vistas SQL existentes, sin recalcular innecesariamente los reportes en Python.
- [ ] Permitir filtros por edición del torneo cuando correspondan.
- [ ] Devolver respuestas JSON aptas para el frontend.

| N.º | Reporte | Ruta sugerida (GET) |
| --- | --- | --- |
| 1 | Tabla de posiciones | `/reportes/posiciones` |
| 2 | Top 10 goleadores | `/reportes/goleadores` |
| 3 | Fair play por equipo | `/reportes/fair-play` |
| 4 | Promedio de goles por fecha y edición | `/reportes/promedio-goles` |
| 5 | Canchas y turnos más utilizados | `/reportes/uso-espacios` |
| 6 | Jugadores por facultad y tipo | `/reportes/jugadores-facultad` |
| 7 | Jugadores inscriptos que nunca participaron | `/reportes/sin-participacion` |
| 8 | Sanciones por equipo y motivo | `/reportes/sanciones` |
| 9 | Porcentaje de partidos por estado | `/reportes/estados` |
| 10 | Rendimiento local y visitante | `/reportes/local-visitante` |
| 11 | Disciplina individual | `/reportes/disciplina` |
| 12 | Goles por tramo del partido | `/reportes/goles-tramos` |

> Las rutas son sugerencias de diseño de la API, no nombres impuestos por la consigna.

### 12. Validaciones, errores y pruebas

- [ ] Validar datos en el backend antes de enviarlos a MySQL.
- [ ] Manejar errores por duplicados, referencias inexistentes y restricciones SQL.
- [ ] Traducir los mensajes de triggers y procedimientos a respuestas comprensibles.
- [ ] Utilizar códigos HTTP adecuados (`400`, `401`, `403`, `404`, `409`, `500`, según corresponda).
- [ ] Asegurar transacciones atómicas en operaciones que modifican varias tablas.
- [ ] Crear pruebas para autenticación, permisos, ABM y reportes.
- [ ] Verificar rechazo de un undécimo integrante y de un tercer docente/funcionario.
- [ ] Verificar rechazo de jugadores de otra facultad, duplicados y suspendidos.
- [ ] Verificar rechazo de partidos superpuestos o enfrentamientos repetidos.
- [ ] Verificar un partido con goles, un autogol y un empate 0-0.
- [ ] Verificar generación y cumplimiento de sanciones automáticas.
- [ ] Verificar bloqueo de correcciones después de 48 horas.
- [ ] Verificar el resultado de los 12 reportes.
- [ ] Comprobar efectivamente los permisos de administrador y planillero en MySQL.

## Estructura sugerida de carpetas

```text
backend/
├── app.py
├── config.py
├── database.py
├── requirements.txt
├── .env.example
├── routes/
│   ├── auth.py
│   ├── jugadores.py
│   ├── equipos.py
│   ├── torneos.py
│   ├── complejos.py
│   ├── canchas.py
│   ├── partidos.py
│   ├── planillas.py
│   ├── goles.py
│   ├── tarjetas.py
│   ├── sanciones.py
│   └── reportes.py
├── services/
│   ├── auth_service.py
│   ├── plantel_service.py
│   ├── partido_service.py
│   └── sancion_service.py
├── validators/
│   └── validaciones.py
├── middleware/
│   └── permisos.py
└── tests/
    ├── test_auth.py
    ├── test_jugadores.py
    ├── test_equipos.py
    ├── test_partidos.py
    ├── test_sanciones.py
    └── test_reportes.py
```

## Orden de desarrollo recomendado

1. **Conexión, autenticación y permisos.** Configurar infraestructura y control de acceso.
2. **Jugadores, equipos y planteles.** Construir las entidades y validar inscripciones.
3. **Torneos, complejos, canchas y turnos.** Completar los datos necesarios para organizar las fechas.
4. **Partidos y fixture.** Programación, estados y restricciones de encuentros.
5. **Planillas, goles, tarjetas y sanciones.** Registrar los resultados y aplicar la disciplina.
6. **Reportes, pruebas e integración.** Consultar vistas, verificar reglas y conectar con el frontend.

## Consideraciones de entrega

- [ ] Documentar cómo configurar las variables de entorno e instalar dependencias.
- [ ] Documentar cómo iniciar el backend localmente.
- [ ] Explicar las decisiones de implementación y la ausencia de ORM.
- [ ] Registrar las pruebas realizadas y sus resultados.
- [ ] Integrar la API con el frontend elegido.
- [ ] Preparar el instructivo completo y la bitácora exigidos por la consigna.

---

## 📓 Bitácora de desarrollo — Torneo Interfacultades de Fútbol 5

**Proyecto:** Obligatorio de Base de Datos 1 — Segundo semestre de 2026  
**Período registrado:** 26/10/2026 al 31/10/2026  
**Alcance:** diseño y mejora de la base de datos MySQL, datos de prueba, reportes SQL, seguridad y planificación del backend.

### Resumen de avances

| Área | Trabajo realizado | Estado |
| --- | --- | --- |
| Modelo relacional | Revisión y mejora de las 14 tablas exigidas | Implementado en SQL |
| Identificadores | Incorporación de `AUTO_INCREMENT` en 9 claves primarias numéricas | Implementado en SQL |
| Integridad y reglas de negocio | Claves foráneas, `UNIQUE`, `CHECK`, `ENUM`, procedimientos y triggers | Implementado; pendiente de pruebas integrales |
| Sanciones | Cálculo de suspensiones por tarjetas y protección frente a cambios manuales | Implementado; pendiente de pruebas integrales |
| Reportes | 9 reportes solicitados y 3 reportes adicionales | Implementado mediante vistas |
| Seguridad | Cuentas y permisos diferenciados de MySQL | Configurado en SQL; pendiente de comprobar accesos |
| Datos de prueba | Ampliación de partidos, estados, autogol y empate 0-0 | Incorporados al script |
| Verificación | Script para comprobar resultados y restricciones | Preparado; pendiente de ejecutar en MySQL |
| Backend | Checklist de módulos para API Python sin ORM | Planificado; no implementado |

### Registro cronológico de trabajo

#### Etapa 1. Revisión del enunciado y del SQL inicial

- Se analizó la consigna del Torneo Interfacultades de Fútbol 5 y se comparó con el script de creación y datos de prueba.
- Se revisaron las entidades principales: usuarios, facultades, jugadores, torneos, equipos, planteles, complejos, canchas, turnos, partidos, planillas, goles, tarjetas y sanciones.
- Se identificaron reglas de negocio que requerían restricciones adicionales, triggers o procedimientos almacenados.
- Se distinguieron las funcionalidades que pueden controlarse desde MySQL de las que corresponde implementar en el backend.

#### Etapa 2. Claves primarias y estructura

- Se incorporó `AUTO_INCREMENT` en `facultad`, `torneo`, `complejo`, `turno`, `equipo`, `partido`, `gol`, `tarjeta` y `sancion_jugador`.
- Se adaptaron las inserciones para no asignar manualmente esos identificadores.
- Se conservaron la cédula (`jugador.ci`), el correo (`login.correo`) y las claves primarias compuestas cuando corresponden a identificadores naturales o relaciones.
- Se revisaron las referencias entre los registros de prueba para preservar su consistencia.

#### Etapa 3. Restricciones y reglas de negocio a nivel MySQL

- Se reforzaron los valores permitidos y la integridad mediante `ENUM`, `CHECK`, `UNIQUE` y claves foráneas.
- Se incorporaron controles para que los jugadores pertenezcan a la facultad del equipo y para que el capitán forme parte de su plantel.
- Se incorporaron controles sobre el tamaño del plantel (máximo de 10 integrantes) y el máximo conjunto de 2 docentes/funcionarios; el mínimo de 5 se exige para competir.
- Se incorporaron validaciones para restringir modificaciones de planteles fuera de la etapa de inscripción.
- Se agregaron controles de programación: equipos del mismo torneo, rivales diferentes, enfrentamientos no repetidos, una participación por fecha y ausencia de superposiciones de cancha y turno.
- Se reforzaron las condiciones para registrar participantes en planillas, goles y tarjetas.
- Se contempló la protección de partidos jugados y el límite de 48 horas para correcciones permitidas.
- Se desarrollaron procedimientos almacenados y triggers para complementar las restricciones declarativas.

#### Etapa 4. Reportes SQL

Se incorporaron **12 reportes** mediante vistas: **9 de la consigna y 3 propuestos**, de dificultad media.

**Reportes obligatorios:**

1. Tabla de posiciones por edición: jugados, ganados, empatados, perdidos, goles a favor/en contra, diferencia y puntos.
2. Diez máximos goleadores.
3. Fair play por equipo.
4. Promedio de goles por fecha y edición.
5. Canchas y turnos más utilizados.
6. Jugadores por facultad y tipo.
7. Jugadores inscriptos que nunca participaron de una planilla.
8. Cantidad de sanciones por equipo y motivo.
9. Porcentaje de partidos jugados, postergados y cancelados (con programados informados por separado).

**Reportes adicionales propuestos:**

10. Rendimiento de cada equipo como local y visitante.
11. Disciplina individual: tarjetas y sanciones de cada jugador.
12. Goles distribuidos por tramos del partido.

También se actualizó la vista `v_resultado_partido` para calcular los marcadores desde los goles, contemplar autogoles y utilizar `COALESCE` en los totales.

#### Etapa 5. Sanciones automáticas

- Se revisó el riesgo de permitir la modificación o eliminación manual de sanciones generadas a partir de tarjetas.
- Se implementó `v_sanciones_automaticas` para derivar las suspensiones a partir de tarjetas rojas y de cada tercera amarilla acumulada en la edición.
- Se incorporó `v_sanciones`, que reúne sanciones automáticas y disciplinarias.
- Se reservó la tabla `sancion_jugador` para sanciones disciplinarias registradas manualmente.
- Se añadieron controles para rechazar registros físicos de sanciones automáticas y conservar la coherencia de las planillas con las suspensiones.

#### Etapa 6. Seguridad y permisos de MySQL

- Se incorporaron instrucciones de creación de dos cuentas técnicas: `torneo_app_administrador` y `torneo_app_planillero`.
- Se definieron permisos diferenciados con `GRANT`: gestión de datos para el administrador; lectura y operaciones de planillas, goles y tarjetas para el planillero.
- Se evitó otorgar al planillero privilegios para modificar jugadores, equipos, partidos o sanciones disciplinarias.
- Se optó por contraseñas aleatorias generadas por MySQL, sin guardarlas en el script.
- Se mantuvo diferenciada la autenticación de usuarios de la aplicación (`login`) respecto de las cuentas técnicas de conexión a MySQL.

#### Etapa 7. Ampliación y ajuste de datos de prueba

- Se conservaron los 6 equipos y los 42 jugadores de la edición de prueba.
- Se actualizaron los correos de los jugadores al formato `inicialdelnombre+apellido@example.edu.uy`, por ejemplo `spereira@example.edu.uy`.
- Se incorporaron partidos adicionales en estados **programado**, **postergado** y **cancelado** para ampliar los casos de prueba.
- Se agregó un autogol para verificar su incidencia en resultados y reportes.
- Se incorporó un partido **Halcones vs. Leones, fecha 4 (26/10/2026), terminado 0-0**, con diez participantes en la planilla y **sin registros de goles**.
- Se ajustó la numeración de las fechas de los partidos posteriores para mantener la secuencia del fixture.

**Datos de prueba previstos en el archivo SQL más reciente:**

| Dato | Cantidad |
| --- | ---: |
| Facultades | 6 |
| Equipos | 6 |
| Jugadores | 42 |
| Partidos totales | 13 |
| Partidos jugados | 10 |
| Partidos programados | 1 |
| Partidos postergados | 1 |
| Partidos cancelados | 1 |
| Goles | 30 |
| Autogoles incluidos | 1 |
| Partidos 0-0 agregados | 1 |
| Reportes SQL | 12 |

#### Etapa 8. Preparación de verificaciones

- Se preparó un script de comprobación de los datos y de los 12 reportes.
- Se agregaron verificaciones del partido 0-0: marcador en cero, planilla con cinco participantes por equipo y ausencia de registros en `gol`.
- Se incluyeron comprobaciones del impacto del empate en la tabla de posiciones, del autogol, de las sanciones y de los estados de partidos.
- Se prepararon pruebas negativas para verificar que determinadas operaciones inválidas sean rechazadas por la base de datos.
- **Pendiente:** ejecutar el SQL y el script de comprobación en un servidor MySQL y corregir cualquier incompatibilidad o fallo que se detecte.

#### Etapa 9. Planificación del backend

- Se definió el alcance del backend en **Python, sin ORM**, mediante acceso directo a MySQL con SQL parametrizado.
- Se diseñó una checklist para autenticación, roles, ABM de jugadores y equipos, planteles, torneos, complejos, canchas, partidos, planillas, goles, tarjetas, sanciones y reportes.
- Se documentaron validaciones, permisos, manejo de errores, transacciones y pruebas necesarias para la API.
- Se generó un documento Markdown independiente con el plan de implementación: `README_BACKEND.md`.
- **Pendiente:** desarrollar e integrar efectivamente los módulos del backend.

### Archivos de trabajo generados

| Archivo | Propósito |
| --- | --- |
| `datos_torneo_autoincrement.sql` | Primera actualización de claves automáticas y datos de prueba. |
| `datos_torneo_mejorado.sql` | Restricciones y controles de negocio ampliados. |
| `datos_torneo_reportes_sanciones_pruebas.sql` | Reportes, sanciones calculadas y casos de prueba adicionales. |
| `datos_torneo_reportes_seguridad_correos.sql` | Permisos MySQL y correos de jugadores con nuevo formato. |
| `datos_torneo_con_empate_0_0.sql` | **Versión SQL más reciente**, con el partido 0-0 incorporado. |
| `verificacion_torneo_con_empate_0_0.sql` | Script de verificación correspondiente a la versión más reciente. |
| `README_BACKEND.md` | Checklist de implementación del backend Python sin ORM. |

### Estado al cierre de este registro

**Implementado en los archivos SQL:** estructura de 14 tablas, 26 triggers, 7 procedimientos almacenados y 15 vistas (12 reportes y 3 auxiliares), con datos de prueba y permisos diferenciados.

**Aún pendiente de validar o desarrollar:**

- [ ] Ejecutar la creación completa en MySQL con una base vacía.
- [ ] Ejecutar `verificacion_torneo_con_empate_0_0.sql` y revisar los resultados.
- [ ] Probar las restricciones con operaciones válidas e inválidas y comprobar los privilegios reales de ambos usuarios.
- [ ] Implementar la API REST en Python, **sin ORM**, y conectarla a las tablas, vistas y procedimientos de MySQL.
- [ ] Integrar el frontend, realizar pruebas funcionales y preparar el instructivo y el informe final.


---

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
