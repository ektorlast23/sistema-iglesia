# Registro de sesión — Proyecto Horas Sociales (Sistema Iglesia)
Última actualización: 19-sep-2026 (viernes, cierre Semana 2) | Stack: Python Django + MySQL

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
