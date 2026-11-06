# Sistema de Gestión del Torneo Interfacultades de Fútbol 5

**Trabajo Obligatorio - Base de Datos 1**
**Universidad Católica del Uruguay (UCU), segundo semestre de 2026**

Aplicación para administrar las ediciones del torneo, jugadores, equipos y planteles, complejos y canchas, fixture, planillas, goles, tarjetas y sanciones. Incluye autenticación de administrador y planillero, permisos diferenciados en MySQL y los doce reportes del obligatorio.

Repositorio: [nahuelbenitezs/ProyectoBD](https://github.com/nahuelbenitezs/ProyectoBD).

## Integrantes y fechas

Brian Rocha, Nahuel Benitez y Jorge Inzaurralde.

| Hito | Fecha |
| --- | --- |
| Publicación de la consigna | 09/10/2026 |
| Avance | 30/10/2026 |
| Entrega final | 06/11/2026 |
| Defensas | 13/11/2026 |

## Estado actual y tecnologías

El backend está implementado en **Python con Flask y mysql-connector-python**, con consultas SQL parametrizadas y **sin ORM**. El frontend utiliza HTML, CSS y JavaScript con módulos; no requiere compilación ni instalación de paquetes para servir la interfaz. MySQL almacena los datos y aplica restricciones, procedimientos, triggers y vistas. Docker Compose reúne MySQL 8.4, la API y Nginx para el frontend.

Se implementaron los ABM de jugadores, equipos y planteles, complejos y canchas, partidos y sanciones disciplinarias; también la gestión de torneos, facultades y turnos. Ambos roles pueden consultar información y reportes. El planillero solo puede escribir planillas, goles y tarjetas; el administrador gestiona las restantes entidades.

El frontend tiene dos modalidades:

- **Demostración:** usa la semilla incluida y guarda sus cambios en el navegador. Permite explorar la interfaz sin MySQL.
- **API:** autentica contra Python y trabaja con la base MySQL. Para verificar el sistema real hay que seleccionar **Usar backend Python** en la pantalla de ingreso. Una prueba en demostración no acredita una escritura en MySQL.

Las verificaciones del 05/11/2026 y sus resultados ejecutados se detallan en la sección de pruebas.

## Ejecución con Docker Compose

Requisitos: Docker Desktop con contenedores Linux y Compose v2. En Windows debe estar disponible su motor, normalmente mediante WSL 2. Para las pruebas JavaScript también se necesita Node.js. No hace falta instalar Python ni MySQL en el host para levantar los servicios.

Todos los comandos de esta sección se ejecutan desde la raíz del repositorio.

### 1. Configurar las claves

En PowerShell:

```powershell
Copy-Item .env.example .env
```

En Linux/macOS u otra terminal POSIX:

```sh
cp .env.example .env
```

Editar `.env` y completar las tres contraseñas:

```dotenv
MYSQL_ROOT_PASSWORD=ElegirUnaClaveRoot
MYSQL_ADMIN_PASSWORD=ElegirUnaClaveAdmin
MYSQL_PLANILLERO_PASSWORD=ElegirUnaClavePlanillero
MYSQL_PORT=3306
```

El archivo `.env` es privado y está excluido de Git. Las claves técnicas de MySQL son distintas de las contraseñas de los usuarios de la aplicación. Si el puerto 3306 ya está ocupado, cambiar `MYSQL_PORT`, por ejemplo a `3307`. Compose interpreta los valores de `.env`: para caracteres especiales, respetar sus reglas de comillas e interpolación. El inicializador SQL duplica las comillas simples de las claves y usa `NO_BACKSLASH_ESCAPES` para conservar las barras inversas.

### 2. Iniciar y comprobar los servicios

```sh
docker compose up -d --build
docker compose ps
```

Esperar a que `db` figure como `healthy`. El control de salud comprueba que la cuenta técnica administradora pueda consultar `sesion_api`; el backend espera ese estado antes de arrancar.

| Servicio | Dirección |
| --- | --- |
| Interfaz | [http://localhost:8080](http://localhost:8080) |
| Salud de la API | [http://localhost:5000/api/health](http://localhost:5000/api/health) |
| MySQL desde el host | `127.0.0.1:MYSQL_PORT`, esquema `torneo_ucu` |

En PowerShell:

```powershell
Invoke-RestMethod http://localhost:5000/api/health
```

En POSIX:

```sh
curl http://localhost:5000/api/health
```

La respuesta esperada es `{"status":"ok","database":"connected"}`.

Al inicializar un volumen vacío, `docker/mysql/init.sh` ejecuta `torneo_ucu_creacion.sql` y `backend/sql/sesiones.sql`, adapta las cuentas técnicas al host `%` para la red de contenedores y les asigna las claves de `.env`. MySQL usa la zona horaria de Uruguay (`-03:00`) para los partidos y el plazo de corrección. Las sesiones se comparan con UTC.

### 3. Ingresar al sistema real

Abrir la interfaz, seleccionar **Usar backend Python** y utilizar una de estas cuentas de demostración:

| Rol | Correo | Contraseña de la aplicación |
| --- | --- | --- |
| Administrador | `admin@demo.ucu.edu.uy` | `AdminDemo2026!` |
| Planillero | `planillero@demo.ucu.edu.uy` | `PlanillaDemo2026!` |

La interfaz debe indicar **Conectado a la API**. Estas credenciales corresponden únicamente a los datos académicos de prueba.

### 4. Operación habitual

```sh
docker compose logs --tail=100 db backend frontend
docker compose up -d --build backend frontend
docker compose stop
docker compose start
docker compose down
```

`stop` y `down` conservan el volumen de datos. El SQL de inicialización solo se aplica al crear un volumen vacío: reconstruir imágenes no actualiza una base ya existente. Para esa situación se utiliza la migración indicada más adelante. `docker compose down -v` elimina el volumen y sus datos; reservarlo para una base de prueba descartable o después de guardar un respaldo.

## Ejecución con MySQL y Python locales

Requisitos: Python 3.11 o posterior, MySQL 8.4 (la verificación utilizó MySQL 8.4.13) y Node.js para la suite JavaScript. Docker utiliza Python 3.12. La cuenta de instalación de MySQL necesita crear bases, usuarios y asignar permisos; la aplicación usa las cuentas técnicas con permisos reducidos.

### Crear una base vacía

Desde la raíz del repositorio, abrir el cliente `mysql` como DBA:

```sh
mysql --default-character-set=utf8mb4 -u root -p
```

Dentro del cliente MySQL:

```sql
SET GLOBAL time_zone = '-03:00';
SET SESSION time_zone = '-03:00';
SOURCE torneo_ucu_creacion.sql;
SOURCE backend/sql/sesiones.sql;
SOURCE torneo_ucu_verificacion.sql;
```

Guardar las contraseñas aleatorias que MySQL muestra al crear `torneo_app_administrador` y `torneo_app_planillero`. El script principal crea el esquema `torneo_ucu` y está diseñado para una instalación vacía: no volver a ejecutarlo sobre una base con información.

### Configurar e iniciar la API

En PowerShell, desde la raíz:

```powershell
Copy-Item backend/.env.example backend/.env
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe backend/app.py
```

En POSIX:

```sh
cp backend/.env.example backend/.env
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
.venv/bin/python backend/app.py
```

Antes de iniciar, completar `backend/.env` con las dos claves técnicas y revisar `MYSQL_HOST`, `MYSQL_PORT` y `MYSQL_DATABASE`. Para usar un MySQL de Docker desde Python local, indicar `MYSQL_HOST=127.0.0.1`, el puerto publicado y las mismas claves del `.env` de la raíz. El `.env` de la raíz configura Compose; `backend/.env` configura la ejecución local de Python.

En otra terminal, desde la raíz, servir la interfaz:

```sh
python -m http.server 5500 --directory frontend
```

En POSIX puede utilizarse `python3`. Abrir [http://localhost:5500](http://localhost:5500) y seleccionar el modo API. `frontend/js/config.js` define la URL de la API (`http://localhost:5000/api`). Si se cambia el origen del frontend, ajustar también `CORS_ORIGINS` del backend.

## Actualización incremental de una base existente

Las correcciones de esquema ya están incluidas en `torneo_ucu_creacion.sql` para instalaciones nuevas. En una instalación anterior, aplicar [backend/sql/migracion_auditoria.sql](backend/sql/migracion_auditoria.sql), como DBA, con un respaldo y las escrituras de la aplicación detenidas:

```sql
SOURCE backend/sql/migracion_auditoria.sql;
```

La migración modifica la FK del plantel para permitir la baja del equipo durante inscripción, agrega sus protecciones y refuerza las validaciones de jugadores y los cambios de turnos ya utilizados por partidos jugados. También actualiza los procedimientos de planillas y sanciones para controlar operaciones concurrentes. No borra tablas ni recarga la semilla. Es **idempotente**: comprueba la configuración de la FK y reemplaza los procedimientos y triggers correspondientes; se verificaron dos ejecuciones consecutivas conservando los datos. Puede aplicarse también a una instalación nueva, aunque esta ya incorpora los cambios. MySQL realiza commits implícitos para DDL, por lo que la actualización completa no es transaccional.

En Docker se puede copiar el archivo al contenedor con `docker compose cp backend/sql/migracion_auditoria.sql db:/tmp/migracion_auditoria.sql`, abrir `docker compose exec db mysql -uroot -p` y ejecutar `SOURCE /tmp/migracion_auditoria.sql;`.

## Datos de prueba y reportes

La semilla de `torneo_ucu_creacion.sql` contiene:

| Dato | Cantidad |
| --- | ---: |
| Ediciones | 1 |
| Facultades | 6 |
| Equipos | 6 |
| Jugadores | 42 |
| Complejos / canchas / turnos | 2 / 3 / 5 |
| Partidos totales | 13 |
| Partidos jugados | 10 |
| Programados / postergados / cancelados | 1 / 1 / 1 |
| Goles registrados, incluido un autogol | 30 |
| Tarjetas | 6 |
| Sanciones manuales / automáticas derivadas | 1 / 2 |
| Usuarios de aplicación | 2 |

Hay tres fechas completas disputadas y un encuentro adicional de la fecha 4: **Halcones contra Leones, 26/10/2026, 0-0**, con cinco participantes por equipo y sin registros en `gol`. Un empate sin goles se obtiene desde el partido jugado, aunque no tenga eventos de gol.

Los reportes se consultan mediante `GET /api/reportes/{slug}?id_torneo=1`. Los primeros nueve responden a la letra y los últimos tres son propuestas del equipo:

| N.º | Slug | Contenido y criterio |
| --- | --- | --- |
| 1 | `posiciones` | PJ, PG, PE, PP, GF, GC, DG y puntos; orden por puntos, DG y GF descendentes |
| 2 | `goleadores` | Diez máximos goleadores; los autogoles no suman al autor |
| 3 | `fair-play` | Amarilla = 1, roja = 3; menor puntaje primero |
| 4 | `promedio-goles` | Promedio por fecha y por edición, incluidos los 0-0 |
| 5 | `uso-espacios` | Canchas y turnos utilizados por partidos jugados |
| 6 | `jugadores-facultad` | Padrón global por facultad y tipo, incluidos ceros; no depende de la edición |
| 7 | `sin-participacion` | Inscriptos que no aparecen en ninguna planilla de esa edición |
| 8 | `sanciones` | Cantidad por equipo y motivo, manuales y automáticas |
| 9 | `estados` | Cantidad y porcentaje de cada estado; programados incluidos en el denominador |
| 10 | `local-visitante` | Partidos, goles y puntos según condición del equipo |
| 11 | `disciplina` | Tarjetas, índice disciplinario y fechas de suspensión por jugador |
| 12 | `goles-tramos` | Goles en los tramos 00-15, 16-30, 31-45 y 46-60, incluidos autogoles |

Las tres consultas propuestas comparan rendimiento según localía, identifican concentración de sanciones y muestran cuándo se convierten los goles. Se implementan con las mismas vistas y permisos de consulta que los reportes obligatorios.

## Modelo, fundamentos y reglas de implementación

Se conservan las catorce tablas mínimas de la consigna: `login`, `facultad`, `jugador`, `torneo`, `equipo`, `equipo_jugador_torneo`, `complejo`, `cancha`, `turno`, `partido`, `planilla_partido`, `gol`, `tarjeta` y `sancion_jugador`. Se agrega `sesion_api` para sesiones revocables y con vencimiento.

- **Identificadores:** se emplea `AUTO_INCREMENT` para los identificadores numéricos artificiales. Se mantienen la cédula del jugador, el correo de acceso y las claves compuestas que identifican relaciones o canchas dentro de un complejo.
- **Ediciones y planteles:** la relación jugador-equipo incluye la edición y tiene una restricción única por jugador y torneo. Las camisetas son únicas dentro de cada plantel. Se controla la facultad común, máximo de diez integrantes y máximo conjunto de dos docentes/funcionarios. La inscripción se construye progresivamente; el mínimo de cinco se exige para programar partidos y abandonar la etapa de inscripción.
- **Capitanes y bajas:** crear un equipo e inscribir a su capitán es una sola transacción. El capitán debe pertenecer al plantel. La baja de un equipo en inscripción elimina sus inscripciones sin eliminar jugadores; las protecciones de sanciones y las FK conservan la información con referencias históricas.
- **Fixture:** claves foráneas compuestas garantizan equipos de la misma edición. Columnas generadas normalizan la pareja de rivales para impedir la revancha, y una clave única protege la reserva de cancha, día y turno. Los cancelados permiten un nuevo enfrentamiento; los postergados y cancelados liberan la reserva de cancha. Los triggers controlan una participación por equipo y fecha, planteles habilitados y fechas del torneo.
- **Resultados calculados:** `v_resultado_partido` suma los goles según equipo y condición de autogol. No se duplica el marcador en otra columna. Las posiciones y estadísticas se obtienen desde vistas SQL; la API adapta tipos y nombres de presentación sin recalcular la competición.
- **Sanciones derivadas:** `v_sanciones_automaticas` calcula una suspensión para la fecha siguiente por cada roja y por cada tercera amarilla acumulada. `sancion_jugador` guarda únicamente las disciplinarias manuales; `v_sanciones` reúne ambas fuentes. Así, corregir una tarjeta actualiza la sanción derivada sin mantener registros duplicados. Las automáticas son de solo lectura y tienen identificadores negativos en la API.
- **Integridad en varias capas:** el frontend valida formularios y permisos de presentación; Python valida tipos, rangos y formatos; MySQL mantiene FK, unicidad, restricciones y reglas entre filas. Las operaciones de varias escrituras hacen `COMMIT` juntas y `ROLLBACK` si falla una validación.
- **Operaciones concurrentes:** las escrituras de planillas y sanciones se serializan mediante un bloqueo de la edición. Las validaciones leen las tablas base con bloqueos compartidos para observar los datos confirmados actuales, incluso si la transacción ya tenía una instantánea bajo `REPEATABLE READ`. Así se evita confirmar simultáneamente una suspensión y una participación incompatible. Las vistas siguen siendo la fuente de los reportes. Esta decisión prioriza la integridad; distintas escrituras de una misma edición pueden tener que esperar entre sí.
- **SQL directo:** el backend utiliza cursores y parámetros `%s`; los nombres de vistas de reportes provienen de una lista fija. No se incorporó un ORM, de acuerdo con la consigna.
- **Autenticación y permisos:** las cuentas de `login` representan usuarios de la aplicación; las dos cuentas técnicas MySQL representan los privilegios de conexión de cada rol. La cuenta técnica planillera puede leer las entidades y vistas autorizadas y modificar solo planillas, goles y tarjetas. No puede leer `login` ni `sesion_api`, administrar entidades ni escribir sanciones. La API usa la cuenta correspondiente al rol autenticado en cada operación de negocio.
- **Sesiones y contraseñas:** las contraseñas SHA-256 de la semilla se migran a scrypt al ingresar correctamente. El token aleatorio se devuelve al cliente, pero MySQL conserva su SHA-256 y vencimiento; cerrar sesión elimina el registro. La duración predeterminada es de doce horas, configurable con `SESSION_TTL_SECONDS`.

### Interpretaciones y límites

El resultado se calcula exclusivamente para partidos marcados como jugados. Solo el administrador cambia ese estado y únicamente después de finalizar el turno; el planillero carga los eventos posteriormente. Los partidos jugados no se pueden eliminar ni reprogramar. Tampoco se puede modificar el horario de un turno utilizado por ellos.

La implementación aplica las **48 horas desde el final del turno tanto a la carga inicial como a la modificación y eliminación de planillas, goles y tarjetas**. Es una interpretación más estricta que el texto de la letra, que menciona expresamente la corrección del resultado. Se conserva como decisión del proyecto: una carga inicial tardía también se rechaza. Los encuentros históricos de la semilla quedan fuera del plazo; para probar altas de eventos se utilizan partidos recientes creados por la integración.

El fixture se administra mediante ABM con restricciones; no se implementó un generador automático de todas las fechas. La unicidad evita rivales repetidos, pero no obliga a haber cargado todos los encuentros antes de finalizar un torneo. Son mejoras futuras posibles junto con el historial explícito de cambios de resultados y un proceso formal de migraciones versionadas.

Las pruebas de concurrencia utilizan dos conexiones independientes, con una instantánea previa bajo `REPEATABLE READ`, y comprueban la espera y el rechazo de la operación incompatible después de confirmar la primera transacción. Cubren tarjeta roja frente a planilla y sanción disciplinaria frente a planilla, en ambos órdenes. Su alcance corresponde a estos cuatro conflictos y al aislamiento utilizado.

## API y estructura del repositorio

El contrato se encuentra en [backend/docs/openapi.yaml](backend/docs/openapi.yaml), importable en herramientas compatibles con OpenAPI 3.0. Todas las rutas llevan el prefijo `/api`. Salvo `GET /health` y `POST /auth/login`, requieren `Authorization: Bearer <token>`.

| Grupo | Operaciones principales |
| --- | --- |
| Sesión | `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`, `GET /health` |
| Administración | Listado, detalle, alta, modificación y baja de `/jugadores`, `/equipos`, `/torneos`, `/complejos`, `/partidos`, `/sanciones`, `/facultades` y `/turnos`, según restricciones |
| Planteles y canchas | `/equipos/{id}/plantel`, `/complejos/{id}/canchas`, `/canchas/disponibles` |
| Registro de partidos | `/partidos/{id}/planilla`, `/goles`, `/tarjetas`, `/habilitados`, `/eventos` y `/resultado` |
| Consultas | `/bootstrap`, `/reportes` y `/reportes/{slug}` |

Respuestas de error: `400` por datos inválidos; `401` por sesión ausente, inválida o vencida; `403` por permisos; `404` por un recurso inexistente; `409` por reglas de negocio, duplicados o referencias; `503` ante problemas de acceso/configuración de MySQL. Los mensajes de negocio de los triggers se traducen a JSON.

```text
ProyectoBD/
  torneo_ucu_creacion.sql         Esquema y semilla para una instalación nueva
  torneo_ucu_verificacion.sql     Verificación de los datos originales y reportes
  docker-compose.yml             MySQL, API, frontend y servicio de pruebas
  docker/mysql/init.sh            Inicialización de MySQL en Docker
  backend/
    app.py, core.py               Aplicación, errores y autenticación
    database.py, logic.py         SQL directo y validaciones
    reports.py, routes/           Reportes y recursos de la API
    sql/                         Sesiones y migración de la auditoría
    tests/                       Unitarias, API simulada, integración y smoke
    docs/openapi.yaml             Contrato de la API
  frontend/
    index.html, styles.css        Interfaz
    js/                          Lógica, repositorio, reportes y validaciones
    tests/                       Suite JavaScript
  README.md                       Ejecución e informe del trabajo
```

## Pruebas reproducibles

### Verificación SQL de la semilla

Ejecutar **antes de las pruebas de integración y de modificar los datos**, porque el verificador compara las cantidades originales, incluido el padrón global de 42 jugadores.

Con MySQL local, como DBA desde la raíz:

```sh
mysql --default-character-set=utf8mb4 -u root -p torneo_ucu
```

Dentro del cliente:

```sql
SOURCE torneo_ucu_verificacion.sql;
```

Con Docker:

```sh
docker compose cp torneo_ucu_verificacion.sql db:/tmp/torneo_ucu_verificacion.sql
docker compose exec db mysql --default-character-set=utf8mb4 -uroot -p torneo_ucu
```

Dentro del cliente del contenedor:

```sql
SOURCE /tmp/torneo_ucu_verificacion.sql;
```

El resultado esperado es `OK: 12 reportes, empate 0-0, planillas, estados, sanciones y protecciones`. También se prueban rechazos a la inserción manual o modificación de sanciones automáticas.

### Python

La suite utiliza `unittest`, incluido en Python; no requiere instalar pytest. `test_logic.py` y `test_api.py` suman 75 pruebas sin un servidor de base de datos. Estas últimas usan un doble de MySQL y verifican autenticación, respuestas, SQL parametrizado, transacciones y las 31 rutas administrativas rechazadas al planillero. `test_integration.py` agrega 14 pruebas contra MySQL real. `test_concurrency.py` agrega cinco: cuatro conflictos entre dos conexiones y el bloqueo de retiro de un integrante con sanción manual.

En Docker, con `db` levantado:

```sh
docker compose run --rm --build tests
```

El servicio de pruebas pertenece al perfil `test` y se ejecuta a pedido; su configuración activa `RUN_INTEGRATION=1`. La suite completa de la versión actual contiene **94 pruebas**: 75 unitarias/API, 14 de integración y 5 de restricciones SQL y concurrencia.

En PowerShell, usando la configuración de `backend/.env`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -p test_logic.py -v
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -p test_api.py -v
$env:RUN_INTEGRATION = '1'
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
Remove-Item Env:RUN_INTEGRATION
```

En POSIX:

```sh
.venv/bin/python -m unittest discover -s backend/tests -p test_logic.py -v
.venv/bin/python -m unittest discover -s backend/tests -p test_api.py -v
RUN_INTEGRATION=1 .venv/bin/python -m unittest discover -s backend/tests -v
```

La integración crea una edición adicional, jugadores y una cancha. Sus partidos recientes utilizan el reloj de MySQL para quedar dentro de las 48 horas. No borra la base ni revierte sus datos al terminar. Ejecutarla en una base de prueba; repetirla agrega otra edición. Incluye planteles inválidos, fixture, bajas, planillas atómicas, goles, autogoles, 0-0, sanciones, reportes y permisos SQL. Sus métodos siguen un recorrido ordenado y comparten los datos de la edición creada.

### JavaScript

No se necesitan paquetes adicionales. Desde la raíz, en PowerShell:

```powershell
node --test (Get-ChildItem frontend/tests/*.test.mjs).FullName
```

En POSIX:

```sh
node --test frontend/tests/*.test.mjs
```

La versión actual contiene 54 pruebas de repositorio, sesiones, permisos, validaciones, reportes y operaciones en demostración. Esta suite no reemplaza una prueba visual en navegador ni una conexión real de la UI con MySQL.

### API publicada y prueba de interfaz

Con la API en ejecución, el smoke test comprueba salud, autenticación, bootstrap, los doce reportes, cierre de sesión y revocación del token. Para el rol planillero también comprueba el rechazo de un alta de jugador.

PowerShell:

```powershell
$env:API_TEST_EMAIL = 'admin@demo.ucu.edu.uy'
$env:API_TEST_PASSWORD = 'AdminDemo2026!'
.\.venv\Scripts\python.exe backend/tests/smoke_live.py
$env:API_TEST_EMAIL = 'planillero@demo.ucu.edu.uy'
$env:API_TEST_PASSWORD = 'PlanillaDemo2026!'
.\.venv\Scripts\python.exe backend/tests/smoke_live.py
Remove-Item Env:API_TEST_EMAIL, Env:API_TEST_PASSWORD
```

POSIX:

```sh
API_TEST_EMAIL=admin@demo.ucu.edu.uy API_TEST_PASSWORD='AdminDemo2026!' .venv/bin/python backend/tests/smoke_live.py
API_TEST_EMAIL=planillero@demo.ucu.edu.uy API_TEST_PASSWORD='PlanillaDemo2026!' .venv/bin/python backend/tests/smoke_live.py
```

La revisión visual debe realizarse en modo API con ambos roles: ingresar, navegar por las entidades, abrir los doce reportes, realizar operaciones válidas y rechazos esperados, guardar una planilla reciente y comprobar su persistencia al recargar. Las comprobaciones efectivamente realizadas se registran a continuación.

### Resultados de verificación del 05/11/2026

| Verificación ejecutada | Resultado registrado |
| --- | --- |
| JavaScript | 54 pruebas aprobadas |
| Python unitario/API sin servidor MySQL | 75 pruebas aprobadas |
| MySQL 8.4.13, instalación en base limpia | Creación, sesiones y script SQL de verificación aprobados |
| Docker Compose, inicialización limpia y verificador SQL ampliado | Aprobados |
| Suite completa en Docker sobre la base actualizada | 94 de 94 aprobadas, sin omisiones: 75 unitarias/API, 14 de integración y 5 de restricciones SQL y concurrencia |
| Suite completa en Docker sobre otra base recién creada con el esquema final | 94 de 94 aprobadas, sin omisiones; inicialización con claves especiales y verificador SQL también aprobados |
| Suite completa contra MySQL 8.4.13 fuera de Docker | 94 de 94 aprobadas con el mismo desglose |
| Actualización incremental de una base existente | Aprobada; dos ejecuciones consecutivas sin pérdida de datos |
| Docker desde base vacía, claves con comillas simples y barras inversas | Inicialización y conexión con ambas cuentas técnicas aprobadas |
| Smoke HTTP con administrador y planillero | Ambos aprobados: salud, sesión, datos iniciales, los doce reportes y revocación del token al cerrar sesión |
| Interfaz real en modo API, administrador | Ingreso, doce reportes con datos, alta de jugador y edición persistida de cancha abierta aprobados |
| Interfaz real en modo API, planillero | Ingreso directo desde reportes, controles administrativos ausentes, carga de participante, gol y amarilla aprobados |
| Rechazos y permisos visibles en la interfaz | Roja incompatible rechazada, suspendido no seleccionable y partido histórico fuera de 48 horas sin acciones de escritura |
| Consola del navegador en los recorridos realizados | Sin errores ni advertencias |

Los resultados de pruebas simuladas, SQL real, API HTTP y navegador se registran por separado. El total esperado de una suite no implica que se haya ejecutado con éxito.

En el recorrido de planillero se agregó un participante a una planilla reciente, un gol en el minuto 55 que cambió el marcador de 2-1 a 3-1 y una amarilla en el minuto 56. Se comprobó el rechazo de una roja que habría generado una suspensión incompatible con otra planilla existente. También se comprobó que un jugador suspendido estuviera deshabilitado al seleccionar participantes y que un partido histórico no permitiera guardar eventos fuera de plazo. El administrador comprobó los doce reportes y la persistencia de una cancha configurada como no techada después de editarla.

## Mejoras realizadas y bitácora

### 26/10/2026 al 31/10/2026

El registro histórico del equipo comprende la revisión de la letra y del SQL inicial; mejora de las catorce entidades; incorporación de identificadores automáticos, FK, restricciones y reglas de negocio; las doce vistas de reportes; cálculo derivado de sanciones; usuarios técnicos con permisos distintos; ampliación de la semilla y preparación del verificador SQL.

Se incorporaron el autogol, los estados adicionales de partidos y el 0-0 de Halcones contra Leones, con su planilla. Se preparó el alcance del backend Python sin ORM y del frontend.

### Estado presente en el repositorio al iniciar la auditoría del 05/11/2026

Ya estaban implementados la API Flask con sus módulos de ABM, sesiones y reportes; el frontend con demostración y modo API; Docker Compose y las pruebas unitarias, de API e integración. Se consolidó su documentación en el presente informe, con las cantidades actuales de la semilla.

### Auditoría y correcciones del 05/11/2026

- Se volvió a leer la letra completa y se comparó con la implementación, manteniendo las modificaciones incrementales.
- Se ejecutaron las suites originales de JavaScript y Python sin MySQL, y luego las regresiones añadidas.
- Se reprodujeron errores de validación ante valores JSON estructurados en campos de catálogo; se corrigieron para devolver errores de datos en lugar de fallos internos de Python.
- Se amplió la prueba de permisos de planillero a las 31 rutas administrativas.
- Se detectó la imposibilidad de dar de baja un equipo recién creado por la relación con su capitán; se corrigió la eliminación de sus inscripciones durante inscripción, conservando las protecciones de historial y sanciones, y se agregó una regresión de integración.
- Se reforzaron en MySQL la validación de datos de jugadores y la protección de turnos utilizados por partidos jugados. Se incorporó y ajustó una actualización incremental para instalaciones anteriores.
- Se reprodujo y corrigió la confirmación de operaciones concurrentes incompatibles entre sanciones y planillas. Se incorporaron bloqueos por edición, lecturas actuales sobre tablas base y cuatro regresiones con dos conexiones, además de la protección al retirar un integrante con sanción manual.
- Se corrigió el tratamiento de comillas simples y barras inversas en las claves técnicas al inicializar Docker.
- Se corrigió la edición de canchas abiertas cuando MySQL devuelve `techada=0`, evitando mostrar y guardar por error una cancha techada. Se descartaron respuestas atrasadas de reportes al cambiar reporte, edición o sesión, y se corrigió la carga inmediata al ingresar directamente en la sección de reportes. Se agregaron cuatro regresiones JavaScript.
- Se actualizó este README como instructivo e informe único, con fundamentos, mejoras, límites, resultados ejecutados, bitácora y bibliografía.
- Se ejecutaron la construcción e inicialización limpia con Docker Compose, el verificador SQL ampliado y las 94 pruebas Python finales, incluidas las de integración y concurrencia contra MySQL, sin omisiones y con resultado aprobado. La suite completa se aprobó tanto en una base actualizada como en otra recién creada con el esquema final, además de la ejecución contra MySQL 8.4.13 fuera de Docker.
- Se verificó que la actualización incremental pudiera ejecutarse dos veces conservando los datos y que la inicialización Docker admitiera claves técnicas con comillas simples y barras inversas.
- Se completaron los recorridos de interfaz en modo API con administrador y planillero, los doce reportes y los rechazos de permisos, sanciones y plazos documentados en la sección de pruebas. Se ejecutó el smoke HTTP completo con ambos roles y se comprobó la revocación de sus sesiones.

## Bibliografía

- Universidad Católica del Uruguay. **Obligatorio BD - Segundo Semestre 2026**, Base de Datos 1. Consigna incluida en el repositorio: `Obligatorio BD - Segundo Semestre 2026.pdf`.
- Oracle. [MySQL 8.4 Reference Manual: restricciones de claves foráneas](https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html). Relaciones, restricciones referenciales y eliminación en cascada.
- Oracle. [MySQL 8.4 Reference Manual: lecturas con bloqueo](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html). Bloqueos compartidos y exclusivos para validaciones concurrentes.
- Oracle. [MySQL 8.4 Reference Manual: niveles de aislamiento](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html). Instantáneas y comportamiento de `REPEATABLE READ`.
- Oracle. [MySQL 8.4 Reference Manual: literales de cadenas](https://dev.mysql.com/doc/refman/8.4/en/string-literals.html). Comillas y tratamiento de barras inversas en las claves del inicializador.
- Oracle. [MySQL Connector/Python: consultas con cursores y parámetros](https://dev.mysql.com/doc/connector-python/en/connector-python-example-cursor-select.html). Acceso SQL directo desde Python.
- Pallets. [Documentación de Flask](https://flask.palletsprojects.com/en/stable/). Aplicación web, rutas, pruebas y manejo de errores.
- Pallets. [Werkzeug: utilidades de seguridad](https://werkzeug.palletsprojects.com/en/stable/utils/#module-werkzeug.security). Hash y verificación de contraseñas.
- Docker. [Docker Compose Quickstart](https://docs.docker.com/compose/gettingstarted/). Servicios, controles de salud y persistencia de datos.
- Python Software Foundation. [unittest](https://docs.python.org/3/library/unittest.html). Pruebas automatizadas y dobles de dependencias.
- Node.js. [Test runner](https://nodejs.org/api/test.html). Ejecución de pruebas JavaScript.

Documentación oficial consultada para esta actualización el 05/11/2026.
