# Verificación Modelo EER — Semana 2 (viernes)
BD: `cursor_demo` (usuario `Nuclearblast`) | Modelo objetivo: `iglesia_db` | Stack: Django + MySQL

## Hallazgo principal
El modelo inicial tenía `miembros.ministerio_id` (N-1: un miembro = un ministerio).
La regla pide **N-M** (un miembro en varios ministerios). Se corrigió con tabla puente.

## Schema final (6 tablas)
- `familias(id PK)` — 1-N — `miembros(familia_id FK SET NULL)`
- `ministerios(id PK)` — N-M — `miembros_ministerios(miembro_id FK CASCADE, ministerio_id FK CASCADE, PK compuesta)`
- `miembros(id PK)` — 1-N — `eventos(responsable_id FK SET NULL)`
- `eventos(id PK)` + `miembros(id PK)` — 1-N — `asistencias(miembro_id FK CASCADE, evento_id FK CASCADE, UQ miembro+evento)`

## Pruebas positivas (datos: familia Hernandez, Hector, Melissa, Alabanza/Jovenes/Diaconado, Culto Dominical)
| Regla | Query | Resultado esperado | Resultado real |
|---|---|---|---|
| R1 familia→varios miembros | COUNT miembros por familia | Hernandez = 2 | ✅ 2 |
| R2 miembro→varios ministerios | ministerios de Hector | 2 (Alabanza, Jovenes) | ✅ 2 |
| R3 evento→varias asistencias | COUNT asistencias evento | 2 | ✅ 2 |
| R4 asistencia→miembro+evento | JOIN asistencias-miembros-eventos | 2 filas válidas | ✅ 2 |

## Pruebas negativas (integridad)
- `INSERT asistencias miembro_id=999` → ERROR 1452 FK `fk_asistencias_miembro` ✅ bloqueado
- `INSERT miembros_ministerios (1,1)` duplicado → ERROR 1062 PK ✅ bloqueado

## Entregables en `MySQLprject/`
- `modelo_iglesia.sql` — modelo editable oficial (para `iglesia_db`, con root)
- `modelo_iglesia_cursor_demo.sql` — ejecutable con `Nuclearblast`
- `diagrama_EER.png` / `diagrama_EER.pdf` — diagrama para informe semanal
- `diagrama_er.py` — script que regenera el diagrama

## Pendiente (requiere root)
- `CREATE DATABASE iglesia_db` + `GRANT` a `Nuclearblast` (hoy se trabajó en `cursor_demo` por falta de clave root).
- En Workbench: `Database > Reverse Engineer` sobre `cursor_demo` → `File > Save Model As modelo_iglesia.mwb`.
