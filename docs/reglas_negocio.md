# Reglas de negocio e integridad — Semana 2 (miercoles)

BD: cursor_demo (dev) / iglesia_db (prod) | 6 tablas | 5 FKs + 1 UQ compuesta

## Tabla de claves foraneas
- **fk_miembros_familia**: miembros.familia_id -> familias.id | 1-N | ON DELETE/UPDATE SET NULL / CASCADE | Al borrar familia se conserva el miembro sin familia
- **fk_mm_miembro**: miembros_ministerios.miembro_id -> miembros.id | N-M puente | ON DELETE/UPDATE CASCADE / CASCADE | Al borrar miembro se borran sus asignaciones
- **fk_mm_ministerio**: miembros_ministerios.ministerio_id -> ministerios.id | N-M puente | ON DELETE/UPDATE CASCADE / CASCADE | Al borrar ministerio se borran sus asignaciones
- **fk_eventos_responsable**: eventos.responsable_id -> miembros.id | 1-N | ON DELETE/UPDATE SET NULL / CASCADE | Al borrar miembro el evento queda sin responsable
- **fk_asistencias_miembro**: asistencias.miembro_id -> miembros.id | 1-N | ON DELETE/UPDATE CASCADE / CASCADE | Al borrar miembro se borran sus asistencias
- **fk_asistencias_evento**: asistencias.evento_id -> eventos.id | 1-N | ON DELETE/UPDATE CASCADE / CASCADE | Al borrar evento se borran sus asistencias

## Cardinalidades
- familias 1-N miembros
- miembros N-M ministerios (puente miembros_ministerios)
- miembros 1-N eventos (responsable, SET NULL)
- miembros 1-N asistencias (CASCADE)
- eventos 1-N asistencias (CASCADE)

## Evidencias de prueba
- R1 Hernandez=2 miembros OK | R2 Hector=2 ministerios OK | R3 Culto=2 asistencias OK | R4 JOIN valido OK
- Negativo FK miembro 999 ERROR 1452 bloqueado | Negativo duplicado (1,1) ERROR 1062 bloqueado

## Reglas de aplicacion
- UQ(miembro_id,evento_id): un registro por miembro y evento
- UQ nombres de familia y ministerio
- presente DEFAULT 1, estado DEFAULT activo