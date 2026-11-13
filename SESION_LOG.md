# Registro de sesión — Proyecto Horas Sociales (Sistema Iglesia)
Última actualización: 12-nov-2026 (cierre Semana 10) | Stack: Python Django + MySQL

## 1. Contexto
- Plan: PLAN GENERAL Y DETALLADO DE SERVICIO SOCIAL (15 semanas × 20h = 300h), institución religiosa local.
- Sistema: plataforma web open-source de gestión de miembros, inventario y asistencia.
- Carpeta: `C:\Users\EktoR\Documents\MySQLprject` | BD dev: `cursor_demo` (MySQL 8.0.46, host 127.0.0.1:3306).
- venv: `MySQLprject\venv` (Python 3.14.6, Django 6.1.1, PyMySQL 2.2.8, reportlab 5.0.1, openpyxl 3.1.5, python-docx 1.2.0, pillow 12.3.0).

## 2. Accesos y conexiones
- MySQL usuario `Nuclearblast` → SOLO privilegios sobre `cursor_demo.*` (sin CREATE DATABASE). Clave en `C:\Users\EktoR\.cursor\mcp.json` y `C:\Users\EktoR\.config\opencode\opencode.json` (MCP `mysql`, solo lectura, verificado `connected`).
- Clave `root` DESCONOCIDA (pendiente reset con PowerShell admin si se requiere `iglesia_db`).
- Workbench 8.0 instalado y abierto. `mysql.exe`: `C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe` (NO está en PATH; usar ruta completa).

## 3. Decisiones tomadas (por el estudiante)
- Stack: Django + MySQL (descartado PHP). Driver: PyMySQL. Apps: 4 (miembros, inventario, eventos/asistencia, reportes).
- Reportes Sem 8 previstos desde hoy: reportlab + openpyxl.
- Modelo: 6 tablas (se agregó puente N-M `miembros_ministerios`; se eliminó `miembros.ministerio_id`).
- Casos de uso: Admin todo, Secretaría (miembros+eventos+asistencia), Inventario (equipos+mantenimiento); reportes acotados.
- Formatos: formal con portada; diccionario MD+XLSX/DOCX; paquete `docs/` + ZIP; Semana 3 NO adelantada; `.mwb` omitido (Reverse Engineer manual pendiente).

## 4. Estado BD `cursor_demo` (verificado)
- Tablas: productos(3 filas prueba) + familias, ministerios, miembros, miembros_ministerios, eventos, asistencias.
- 6 FKs con ON DELETE/UPDATE definidos. UQ: nombre_familia, nombre ministerio, (miembro_id,evento_id).
- Pruebas OK: R1 familia=2 miembros, R2 Héctor=2 ministerios, R3 evento=2 asistencias, R4 JOIN válido; negativos 1452 y 1062 bloqueados.
- Datos de prueba cargados: familia Hernández (Héctor, Melissa), ministerios (Alabanza, Jóvenes, Diaconado), evento Culto Dominical 2026-09-21.

## 5. Entregables Semana 2 (en `Semana_02/` + `Paquete_Semana02.zip`, ZIP verificado OK)
- 01/Documento_Arquitectura.pdf | 02/Diagrama_ER.pdf + Diccionario_Datos.docx | 03/Casos_Uso.pdf + Matriz_Permisos.xlsx | 04/Informe_Semana_02.docx
- Fuentes: modelo_iglesia.sql (oficial iglesia_db), modelo_iglesia_cursor_demo.sql, diagrama_EER.png/pdf, mermaid-diagram-corregido.mmd/png, casos-uso-corregido.mmd/png, matriz_permisos.md, informe_verificacion.md, docs/reglas_negocio.md, docs/diccionario_datos.xlsx, build_semana02.py (regenera todo), diagrama_er.py, puppeteer-edge.json.

## 6. Pendientes (declarados en informe)
- P1: crear `iglesia_db` + GRANT (requiere clave root).
- P2: firma de matriz de permisos con la institución (4 preguntas en matriz_permisos.md).
- P3: despliegue final local vs VPS sin definir. P4: `Diagrama_ER.mwb` manual. P5: tablas inventario (Sem 6).

## 7. Rutina acordada
- El estudiante dicta cronograma día por día (Lun–Vie); el agente planea/ejecuta por día con entregable; viernes se empaqueta.
- Semana 3 según plan general: UI/UX wireframes (aún no iniciada).
- Reconstruir paquete: `venv\Scripts\python.exe build_semana02.py`.

## 8. Semana 4 — Estructura base (02-oct-2026, cerrada)
- Git init en `MySQLprject/` + `.gitignore` (venv, .env, pycache). Commit inicial `68ebcb1` (identidad ektorlast23).
- venv actualizado: **Django 5.2.17 LTS** (downgrade desde 6.1.1: Django 6.1 exige MySQL 8.4+, servidor es 8.0.46).
- Proyecto en `sistema_iglesia/` (config + apps: miembros, inventario, eventos, reportes) + `.env.example` (credenciales por entorno, nunca commitear).
- Settings: PyMySQL shim en `config/__init__.py`, DATABASES MySQL por env (dev cursor_demo), idioma es, zona America/El_Salvador, DEFAULT_AUTO_FIELD=AutoField (coincide con INT existentes), ALLOWED_HOSTS por env (incluye testserver).
- Models miembros/eventos con db_table exactas al schema (familias, ministerios, miembros, miembros_ministerios, eventos, asistencias). Admin revertido a stubs: **SIN CRUD esta semana** (orden explícita; CRUD = Sem 5+).
- Home `/` con navegación inicial (cards por módulo con semana asignada) + `/admin/`. Verificado: `GET / → 200` y ORM `Miembro.objects.count() == 2` (solo SELECT).
- Verificado: `manage.py check` limpio + `makemigrations` (0001 miembros/eventos) + `sqlmigrate` coincide con schema. **NO se corrió `migrate`** (escribiría tablas auth + choca con tablas existentes; requiere --fake-initial o iglesia_db fresca en Sem 5).
- Diferencias Django vs schema manual (documentadas, funcionalmente equivalentes): puente con `id` propio (manual usa PK compuesta), TEXT→longtext, TINYINT→bool, ENUM→varchar+choices.
- Semana 3 se hizo fuera de sesión: `SEMANA_03/` + `Paquete_Semana03.zip` (wireframes Login/Dashboard/Miembros/Familias/Ministerios/Eventos/Asistencia/Inventario/Reportes + validación + informe).

## 9. Semana 4 — Cierre con informe (02-oct-2026, cerrada)
- `SEMANA_04/` formato espejo SEMANA_03: 01_ENTORNO (versiones.txt), 02_REPOSITORIO (git_log.txt + git_status.txt),
  03_ESTRUCTURA (arbol_proyecto.txt + home.png + admin.png), 04_EVIDENCIAS_BD (tablas_cursor_demo.txt),
  05_INFORME (Informe_Semana_04.docx con tabla Lun-Vie + 2 capturas). `Paquete_Semana04.zip` verificado OK (8 archivos).
- Evidencias: Python 3.14.6, Django 5.2.17, Git 2.54.0, MySQL 8.0.46; commit 68ebcb1; GET / 200; ORM 2 miembros;
  BD = cursor_demo (gestion_iglesia/iglesia_db pendientes de root, declarado en informe).
- Builder: `build_semana04.py` (regenera informe + ZIP). Servidor dev dejado corriendo en 127.0.0.1:8000 al cierre.

## 10. Semana 5 — CRUD de Miembros (sesión aparte, cerrada)
- CRUD completo de miembros en `miembros/` (views por función: lista/registrar/detalle/editar/eliminar), `MiembroForm` (ModelForm 8 campos + familia), `urls.py` con namespace `miembros`, admin registrado.
- Eliminación = **baja lógica** (`estado='inactivo'`), validaciones: obligatorios, email, teléfono como texto; 404 ante id inexistente.
- Plantillas en `templates/miembros/` (lista, formulario, detalle, confirmar_eliminacion) sobre `base.html` (layout Sem 3) + `home.html`.
- Pruebas: 8/8 aceptación (nota: se ejecutaron sin documentar cómo, dado que `Nuclearblast` no puede crear `test_*`).
- `migrate` ejecutado en `cursor_demo` con `--fake-initial` (miembros+eventos FAKED; tablas Sem 2 intactas). Tablas auth_* + django_migrations ya presentes.
- Commits: `b8df53d` (CRUD miembros) y `7f374c0` (evidencias PDF formales: modelo/pruebas/persistencia). `SEMANA_05/` + `Paquete_Semana05.zip` (txt/png reemplazados por PDF).

## 11. Semana 6 — Módulo de Inventario (16-oct-2026, cerrada)
- App `inventario`: modelos **Equipo** (nombre, categoría, descripción, cantidad, estado, ubicación, fecha_registro) y **Prestamo** (equipo FK, miembro FK PROTECT, cantidad, fechas, estado, observaciones). Migración `inventario.0001_initial`; tablas `equipos` y `prestamos` verificadas con DESCRIBE en MySQL.
- Disponibilidad **calculada** (`cantidad − prestamos activos`), no almacenada → evita descuadres. Categoría con choices: instrumento/sonido/mobiliario/recurso.
- CRUD + búsqueda: `lista` (busca por nombre/categoría/ubicación), `registrar`, `detalle` (con historial), `editar`; flujo `prestamos`/`devoluciones` con validación de existencias y fechas (no prestar más que lo disponible). URLs bajo `inventario/` (namespace `inventario`) conectadas en `config/urls.py`; nav en `base.html`/`home.html`.
- Plantillas en `templates/inventario/` (lista, formulario, detalle, prestamos, devoluciones). Decisión: `templates/` (consistente) en vez de `plantillas/`.
- **Pruebas en SQLite**: `config/settings.py` detecta `test` en `sys.argv` y usa SQLite en memoria (el usuario MySQL no tiene CREATE → no puede crear `test_cursor_demo`). Producción sigue en MySQL. `manage.py test inventario` → **15/15 OK**.
- Verificación en vivo: GET 200 (lista/nuevo/detalle/prestamos/devoluciones); POST nuevo 302; POST préstamo 302 (disponible 4→2); exceso → 200 rechazado; 404 id inexistente; devolución 302 (estado `devuelto`, stock liberado).
- Entregables: `SEMANA_06/` (01_MODELO, 02_CRUD con HTML real, 03_PRESTAMOS, 04_PRUEBAS, 05_INFORME) + `Paquete_Semana06.zip`. Builders: `build_semana06.py`, `capturar_semana06.py`.
- Semana 7 planificada: módulo de Eventos y Asistencia.

## 12. Semana 7 — Gestión de eventos y asistencia (24-oct-2026, cerrada)
- **Modelo**: `Asistencia` ampliado con `estado` (choices `presente`/`ausente`/`justificado`/`retraso`, default `presente`) y `unique_together (miembro, evento)`; `__str__` devuelve "miembro en evento: estado". `Evento` mantiene nombre, descripción, fecha, hora_inicio/fin, lugar, tipo y responsable (FK `miembros`, SET NULL).
- **Migración 0002** (`eventos.0002_remove_asistencia_presente_asistencia_estado`): `AddField estado` → `RunPython` `presente_a_estado` (presente=True→`presente`, False→`ausente`) → `RemoveField presente`, con reversión `estado_a_presente`. Datos históricos de `asistencias` preservados.
- **Formularios** (`eventos/forms.py`): `EventoForm` (8 campos, `hora_fin >= hora_inicio`, responsable solo miembros `activo`), `AsistenciaForm` (miembro activo, evento preseleccionado, fecha por defecto hoy, valida duplicado en `clean()`), `AsistenciaEditarForm` (solo estado + observaciones).
- **Vistas** (`eventos/views.py`): `lista` (búsqueda por nombre/lugar/tipo), `registrar`, `detalle` (tabla + total asistentes), `editar`, `eliminar` (confirmación), `asistencia_registrar`, `lista_asistencias`, `asistencia_editar`, `asistencia_consulta_miembro` (selector + historial, 404 si el miembro no existe).
- **Rutas** (namespace `eventos`, montado en `config/urls.py` como `eventos/`):
  - `GET /eventos/` · `GET|POST /eventos/nuevo/` · `GET /eventos/<pk>/` · `GET|POST /eventos/<pk>/editar/` · `GET|POST /eventos/<pk>/eliminar/`
  - `GET|POST /eventos/<evento_id>/asistencia/nuevo/` · `GET /eventos/<evento_id>/asistencias/` · `GET|POST /eventos/asistencia/<pk>/editar/` · `GET /eventos/asistencias/miembro/?miembro_id=<pk>`
- **Templates** `templates/eventos/` (lista, formulario, detalle, confirmar_eliminacion, asistencia_form, asistencias_lista, asistencia_editar, asistencias_miembro) sobre `base.html`; navegación actualizada en `base.html`/`home.html`.
- **Pruebas**: `eventos/tests.py` con **28 pruebas** (modelos, formularios, vistas) sobre SQLite en memoria → `manage.py test eventos -v 2` = **28/28 OK**. Incluye duplicado de asistencia (200, no crea), 404 de evento/miembro inexistente, total de asistentes y filtro por miembro.
- **Verificación en vivo** (runserver 127.0.0.1:8010, BD `cursor_demo`): 7 páginas GET → 200 con HTML real guardado en `SEMANA_07/02_CRUD/`.
- **Entregables**: `SEMANA_07/` (01_MODELO, 02_CRUD, 03_ASISTENCIA, 04_PRUEBAS, 05_INFORME) + `Paquete_Semana07.zip` (18 archivos) + `build_semana07.py` (regenera informe docx, PDFs de evidencia y ZIP).
- **Semana 8 planificada**: módulo de Reportes (asistencias por evento/miembro, eventos más concurridos, exportación de resultados).

## 13. Semana 8 — Módulo de Reportes y Estadísticas (31-oct-2026, cerrada)
- **Alcance**: cuatro reportes sobre la BD real, con filtros, pantalla y descarga en PDF/Excel. App `reportes` (antes vacía).
- **Consultas** (`reportes/consultas.py`): `asistencia_por_evento`, `crecimiento_asistencia`, `inventario`, `demografia`. Agregados del ORM (`Count` con `filter=`, `Sum`, `TruncMonth`) para que el mismo código corra en MySQL 8 y SQLite; objeto `Reporte`/`Seccion` común a pantalla y exportación. SQL puro documentado en `reportes/sql/reportes.sql` (10 sentencias) y ejecutado en MySQL en `SEMANA_08/01_CONSULTAS/sql_mysql.txt`.
- **Asistencia por evento**: desglose presente/ausente/justificado/retraso, total y %; filtros `desde`, `hasta`, `tipo`. **Crecimiento**: serie mensual (3 meses), variación del último mes y top 10 de eventos. **Inventario**: disponibilidad calculada (unidades − préstamos activos − bajas) y préstamos atrasados. **Demografía**: estado, sexo, rangos de edad, familias y ministerios.
- **Exportación** (`reportes/exportar.py`): PDF con reportlab (portada, resumen, tablas paginadas, gráfico de barras en crecimiento, pie con página) y Excel con openpyxl (hoja Resumen + una hoja por sección, encabezado fijo, autofiltro). Ambas consumen el mismo `Reporte` que la pantalla.
- **Rutas** (namespace `reportes`, montado como `reportes/`): `/reportes/` · `/reportes/<clave>/` · `/reportes/<clave>/(pdf|xlsx)/`. Navegación actualizada en `base.html`/`home.html`; `home.html` ya no dice "Semanas 5-8".
- **Datos de demostración**: comando `manage.py cargar_demo` (idempotente) crea 12 miembros, 4 familias, 4 ministerios y los eventos de agosto–octubre 2026 con 184 asistencias; `--limpiar` los retira (marcados con `@demo.local` y descripción "Evento de demostración (Semana 8)"). La BD quedó con 14 miembros, 24 eventos y 184 asistencias.
- **Pruebas**: `reportes/tests.py` con **36 pruebas** (consultas, vistas, exportación, casos de borde) sobre SQLite en memoria → **36/36 OK**; suite completa **88/88 OK**.
- **Verificación real** (cliente de Django sobre `cursor_demo`): 7 pantallas → 200; 9 descargas → 200; 404 de reporte inexistente y 400 de formato no soportado. Evidencias en `SEMANA_08/` (01_CONSULTAS, 02_REPORTES, 03_EXPORTACION, 04_PRUEBAS, 05_INFORME) + `Paquete_Semana08.zip` (29 archivos) + `build_semana08.py`.
- **Hallazgo corregido**: el PDF de cualquier reporte intentaba dibujar el gráfico de crecimiento y fallaba en las tablas de 3 columnas; se agregó el guard por clave y una prueba que exporta los cuatro reportes en ambos formatos.
- **Semana 9 planificada**: pruebas unitarias y de integración del sistema completo.

## 14. Semana 9 — Pruebas Unitarias y de Integración (07-nov-2026, cerrada)
- **Alcance**: cobertura de pruebas sobre todo el sistema sin repetir las 88 pruebas de las semanas 5-8. Se agregaron **133 pruebas** en el paquete `sistema_iglesia/tests/` (se descubren con `manage.py test`), sobre SQLite en memoria.
- **Escenario base** (`tests/base.py`): 4 miembros (activo/inactivo/visitante), 2 ministerios, 2 eventos con asistencias (incluye un retraso y un ausente), 3 equipos (disponible, mantenimiento, baja) y 1 préstamo activo; helpers para generar POST válidos.
- **Lógica de negocio** (`tests/test_logica_negocio.py`, 40 pruebas): disponibilidad calculada (total − préstamos activos, tope 0, baja = 0), `Prestamo.activo`/`atrasado` (vence hoy no es atraso), SET_NULL de familia, PROTECT de miembro con préstamo, CASCADE de evento→asistencias y equipo→préstamos, `unique_together` (ministerio y asistencia), totales y porcentajes de los cuatro reportes, límites de `RANGOS_EDAD` (cumpleaños de hoy ya suma), `a_fecha`, `Reporte.vacio`, `nombre_archivo` y `CATALOGO`.
- **Integración** (`tests/test_integracion.py`, 15 pruebas): alta de miembro → evento → asistencia → reporte → PDF/Excel; duplicado por HTTP sin escribir; cambio de estado reflejado en el reporte; baja lógica que saca al miembro de los selectores; borrado de evento en cascada; préstamo → reporte → devolución → reporte; ocho descargas con firma `%PDF`/`PK`; filtros de fecha y 404 de reporte inexistente.
- **Validación de formularios** (`tests/test_formularios.py`, 43 pruebas): matriz campo por campo de `MiembroForm`, `EventoForm`, `AsistenciaForm`, `EquipoForm` y `PrestamoForm`; incluye formatos de fecha ISO y `DD/MM/AAAA` con `LANGUAGE_CODE='es'`, widgets `date`/`time`, duplicados, longitudes y reglas cruzadas. Resumen en `SEMANA_09/03_FORMULARIOS/matriz_validaciones.txt`.
- **Control de errores** (`tests/test_errores.py`, 21 pruebas): 404 de ids inexistentes en los cuatro módulos, 404 ante ids no numéricos, 405 en POST a la portada, 400 en formato de exportación no soportado, filtros de fecha inválidos ignorados y envíos inválidos que no crean filas.
- **Rendimiento** (`tests/test_rendimiento.py`, 14 pruebas): número de consultas constante en listados y reportes (detección de N+1), umbrales holgados de tiempo (2 s pantallas, 5 s exportaciones) y existencia de índices de claves foráneas. Medición real con `medir_rendimiento.py` sobre MySQL 8.0.46 (`cursor_demo`, solo GET): 13 pantallas → 200, la más lenta la portada con 13,6 ms; listado de inventario en 2 consultas fijas.
- **Defectos corregidos**: (1) `prestamo_id` no numérico en devoluciones → 500, ahora 404 con `_entero()`; (2) `miembro_id` no numérico en el historial → 500, ahora 404; (3) préstamo con `cantidad=0` pasaba la validación (`if equipo and cantidad:`) → ahora `is not None` y se rechaza; (4) N+1 en el listado de inventario (un SUM por equipo) → `prefetch_related("prestamos")` y `cantidad_prestada` que usa la caché cuando está precargada.
- **Hallazgo visual (demostración en vivo)**: los badges de estado usaban clases sin color de fondo (`disponible`, `mantenimiento`, `baja`, `prestado`, `devuelto`), así que el texto blanco quedaba invisible en inventario y préstamos; se agregaron las reglas CSS en `templates/base.html`.
- **Cobertura** (coverage 7.17.2, sin archivos de pruebas ni migraciones): 948 sentencias, 105 sin ejecutar, **89 %** (96,8 % si se excluye `cargar_demo.py`, que está en 0 % por diseño). Detalle en `SEMANA_09/01_UNITARIAS/cobertura.txt` y `htmlcov/`.
- **Resultado**: `manage.py test` → **221 pruebas OK en ~3 s** (88 previas + 133 nuevas). Cero fallos.
- **Entregables**: `SEMANA_09/` (01_UNITARIAS, 02_INTEGRACION, 03_FORMULARIOS, 04_ERRORES, 05_RENDIMIENTO, 06_INFORME con `Informe_Semana_09.docx`), `Paquete_Semana09.zip`, `build_semana09.py` y `medir_rendimiento.py`.
- **Pendientes para la Semana 10**: decidir si un miembro inactivo puede ser responsable de un préstamo (hoy `PrestamoForm` no filtra), índices propios para `prestamos(estado, fecha)` y revisar las ramas de vistas con cobertura 92-96 %. Siguen abiertos autenticación/permisos por rol y la creación de `iglesia_db` con GRANT.
- **Semana 10 planificada**: corrección de bugs y optimización de consultas (depuración, índices y velocidad de carga).

## 15. Dashboard con datos reales (07-nov-2026, cerrada)
- **Motivo**: al recorrer el menú en la demostración en vivo, todos los módulos se veían trabajados salvo la portada, que seguía siendo la plantilla de la Semana 4 (título, un párrafo y una lista de enlaces) sin heredar `base.html`.
- **Vista**: `config/views.py` reemplaza el `TemplateView` de `config/urls.py` por `home`, restringida a GET con `@require_GET`. Arma el resumen desde la base: miembros activos/total, eventos, asistencias, equipos, unidades disponibles, préstamos activos y atrasados, últimos 5 eventos y 5 préstamos activos ordenados por vencimiento. Usa `prefetch_related("prestamos")` para calcular unidades disponibles sin N+1.
- **Plantilla** (`templates/home.html`): hereda de `base.html` y muestra cinco tarjetas de indicadores (la de préstamos pasa a rojo con los atrasados), aviso con enlace a devoluciones cuando hay vencidos, cuatro accesos rápidos (registrar miembro, crear evento, prestar equipo, ver reportes) y dos paneles con las tablas de últimos eventos y préstamos activos.
- **Estilo** (`templates/base.html`): grillas de 5 tarjetas y 4 accesos en escritorio, 2 columnas por debajo de 900 px y 1 columna por debajo de 600 px; la tarjeta de alerta ocupa todo el ancho en pantallas angostas. Badge nuevo `atrasado` en rojo.
- **Prueba ajustada**: `test_portada_no_toca_la_base` (que exigía cero consultas) se reemplazó por `test_portada_usa_un_numero_fijo_de_consultas`: la portada hace como máximo 12 consultas y el número no cambia al crear 20 miembros más.
- **Resultado**: suite completa **221 pruebas OK**; cobertura **948 sentencias, 89 %** (96,8 % sin `cargar_demo.py`). Medición contra MySQL: portada en **11 consultas y 13,6 ms**. Layout verificado por DOM: viewport 852 px → tarjetas en 2 columnas y alerta a todo el ancho.
- **Evidencias regeneradas**: `SEMANA_09/01_UNITARIAS` (`salida_suite_completa.txt`, `cobertura.txt`, `htmlcov/`, `resumen_pruebas.txt`), `SEMANA_09/05_RENDIMIENTO` (`pruebas_rendimiento.txt`, `medicion_mysql.txt`), `Informe_Semana_09.docx` y `Paquete_Semana09.zip`.

## 16. Semana 10 — Corrección de Bugs y Optimización de Consultas (12-nov-2026, cerrada)
- **Parte A (commit `5be7b1a`, ya integrada)**: endurecimiento de acceso — `LoginObligatorioMiddleware` (login obligatorio salvo login/salud), `PermisosPorRolMiddleware` con roles Administrador/Secretaría/Encargado de inventario/Consulta (`config/permisos.py`), comando `crear_roles`, plantillas login/logout/403 y settings de producción (DEBUG/ALLOWED_HOSTS/SECRET_KEY por entorno). `tests/test_permisos.py` (13 pruebas → 234 totales). Se documenta aquí aunque el commit lo etiquetara como Semana 10.
- **Parte B (alcance oficial del plan)**: depuración + índices + velocidad.
- **Depuración**: `PrestamoForm` ya no ofrece miembros inactivos como responsable de un préstamo NUEVO; en edición conserva el miembro actual (queryset activos OR pk actual) y `clean()` rechaza inactivo en alta. `eventos/views.py` detalle y lista de asistencias evalúan el queryset una vez (`list`+`len`) en vez de `count()`+iteración (2→1 consulta a `asistencias`).
- **Índices**: migración `inventario.0002_prestamo_idx_prestamos_estado_devol_and_more` con `idx_prestamos_estado_devol (estado, fecha_devolucion_prevista)` e `idx_prestamos_estado_prest (estado, fecha_prestamo)`. `EXPLAIN` pasó de `type=ALL, key=NULL, Using filesort` a `type=ref, key=idx_prestamos_estado_devol, Using index`.
- **Consultas**: auditoría sin N+1 adicionales; listados con select_related/prefetch_related; reportes con agregados resueltos en SQL.
- **Rendimiento**: `medir_rendimiento.py` 13 pantallas → 42 consultas antes y después (ninguna de esas 13 era la redundante); mejora verificable en el plan de ejecución y en el detalle (2→1 consulta a asistencias). 7/7 rutas en vivo → 200.
- **Pruebas**: `manage.py test` → **239 pruebas OK** (234 previas + 5 regresiones de esta semana).
- **Entregables**: `SEMANA_10/` (01_DEPURACION, 02_INDICES, 03_CONSULTAS, 04_RENDIMIENTO, 05_PRUEBAS, 06_INFORME con `Informe_Semana_10.docx`) + `Paquete_Semana10.zip` + `build_semana10.py`.
- **Semana 11 planificada**: pruebas de usabilidad con usuarios reales (ajustes de interfaz).
