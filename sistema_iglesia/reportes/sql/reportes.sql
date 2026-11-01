-- =====================================================================
--  Reportes de la Semana 8 — consultas SQL equivalentes al ORM
--
--  Las vistas usan el ORM de Django (reportes/consultas.py) para que el
--  mismo código funcione en MySQL 8 y en SQLite (pruebas). Aquí queda el
--  SQL puro de cada reporte, listo para ejecutarse en cursor_demo/iglesia_db.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Asistencia por evento
--    ORM: AsistenciaPorEvento -> asistencia_por_evento()
-- ---------------------------------------------------------------------
SELECT e.nombre,
       e.fecha,
       COALESCE(e.tipo, '—')                    AS tipo,
       SUM(a.id IS NOT NULL AND a.estado = 'presente')    AS presentes,
       SUM(a.id IS NOT NULL AND a.estado = 'ausente')     AS ausentes,
       SUM(a.id IS NOT NULL AND a.estado = 'justificado') AS justificados,
       SUM(a.id IS NOT NULL AND a.estado = 'retraso')     AS retrasos,
       COUNT(a.id)                              AS total,
       ROUND(100 * SUM(a.estado = 'presente') / NULLIF(COUNT(a.id), 0), 1)
                                                AS porcentaje_asistencia
FROM eventos e
LEFT JOIN asistencias a ON a.evento_id = e.id
GROUP BY e.id, e.nombre, e.fecha, e.tipo
ORDER BY e.fecha DESC, e.nombre;

-- ---------------------------------------------------------------------
-- 2. Crecimiento mensual de la asistencia
--    ORM: crecimiento_asistencia() con TruncMonth
-- ---------------------------------------------------------------------
SELECT DATE_FORMAT(e.fecha, '%Y-%m')            AS mes,
       COUNT(DISTINCT e.id)                     AS eventos,
       COUNT(a.id)                              AS asistencias,
       SUM(a.estado = 'presente')               AS presentes,
       ROUND(100 * SUM(a.estado = 'presente') / NULLIF(COUNT(a.id), 0), 1)
                                                AS porcentaje_asistencia,
       ROUND(SUM(a.estado = 'presente') / COUNT(DISTINCT e.id), 1)
                                                AS presentes_por_evento
FROM eventos e
JOIN asistencias a ON a.evento_id = e.id
GROUP BY mes
ORDER BY mes;

-- ---------------------------------------------------------------------
-- 3. Eventos más concurridos
-- ---------------------------------------------------------------------
SELECT e.nombre,
       e.fecha,
       COALESCE(e.tipo, '—')                    AS tipo,
       SUM(a.estado = 'presente')               AS presentes,
       COUNT(a.id)                              AS total,
       ROUND(100 * SUM(a.estado = 'presente') / NULLIF(COUNT(a.id), 0), 1)
                                                AS porcentaje_asistencia
FROM eventos e
JOIN asistencias a ON a.evento_id = e.id
GROUP BY e.id, e.nombre, e.fecha, e.tipo
ORDER BY presentes DESC, total DESC, e.fecha
LIMIT 10;

-- ---------------------------------------------------------------------
-- 4. Estado del inventario por categoría
--    Disponibles = unidades - préstamos activos - unidades de baja
-- ---------------------------------------------------------------------
SELECT c.categoria,
       c.equipos,
       c.unidades,
       COALESCE(p.prestadas, 0)                 AS en_prestamo,
       GREATEST(c.unidades - COALESCE(p.prestadas, 0) - c.baja, 0)
                                                AS disponibles,
       c.mantenimiento,
       c.baja
FROM (
    SELECT categoria,
           COUNT(*)                             AS equipos,
           SUM(cantidad)                        AS unidades,
           SUM(CASE WHEN estado = 'mantenimiento' THEN cantidad ELSE 0 END)
                                                AS mantenimiento,
           SUM(CASE WHEN estado = 'baja' THEN cantidad ELSE 0 END)
                                                AS baja
    FROM equipos
    GROUP BY categoria
) c
LEFT JOIN (
    SELECT eq.categoria,
           SUM(p.cantidad)                      AS prestadas
    FROM prestamos p
    JOIN equipos eq ON eq.id = p.equipo_id
    WHERE p.estado = 'prestado'
    GROUP BY eq.categoria
) p ON p.categoria = c.categoria
ORDER BY c.categoria;

-- ---------------------------------------------------------------------
-- 5. Préstamos activos y atrasos
-- ---------------------------------------------------------------------
SELECT eq.nombre                              AS equipo,
       CONCAT(m.nombres, ' ', m.apellidos)     AS miembro,
       p.cantidad,
       p.fecha_prestamo,
       p.fecha_devolucion_prevista,
       DATEDIFF(CURDATE(), p.fecha_devolucion_prevista) AS dias_atraso
FROM prestamos p
JOIN equipos eq  ON eq.id = p.equipo_id
JOIN miembros m  ON m.id = p.miembro_id
WHERE p.estado = 'prestado'
ORDER BY p.fecha_devolucion_prevista;

-- ---------------------------------------------------------------------
-- 6. Datos demográficos
-- ---------------------------------------------------------------------
-- 6.1 Por estado
SELECT estado, COUNT(*) AS miembros
FROM miembros
GROUP BY estado
ORDER BY miembros DESC;

-- 6.2 Por sexo
SELECT COALESCE(sexo, 'Sin dato') AS sexo, COUNT(*) AS miembros
FROM miembros
GROUP BY sexo
ORDER BY miembros DESC;

-- 6.3 Por rango de edad
SELECT CASE
           WHEN fecha_nacimiento IS NULL      THEN 'Sin fecha'
           WHEN TIMESTAMPDIFF(YEAR, fecha_nacimiento, CURDATE()) < 18  THEN 'Menores de 18'
           WHEN TIMESTAMPDIFF(YEAR, fecha_nacimiento, CURDATE()) <= 25 THEN '18 a 25 años'
           WHEN TIMESTAMPDIFF(YEAR, fecha_nacimiento, CURDATE()) <= 35 THEN '26 a 35 años'
           WHEN TIMESTAMPDIFF(YEAR, fecha_nacimiento, CURDATE()) <= 45 THEN '36 a 45 años'
           WHEN TIMESTAMPDIFF(YEAR, fecha_nacimiento, CURDATE()) <= 60 THEN '46 a 60 años'
           ELSE 'Mayores de 60'
       END AS rango,
       COUNT(*) AS miembros
FROM miembros
GROUP BY rango
ORDER BY miembros DESC;

-- 6.4 Familias con más miembros
SELECT COALESCE(f.nombre_familia, 'Sin familia') AS familia, COUNT(m.id) AS miembros
FROM miembros m
LEFT JOIN familias f ON f.id = m.familia_id
GROUP BY familia
ORDER BY miembros DESC
LIMIT 10;

-- 6.5 Participación por ministerio
SELECT mi.nombre,
       COUNT(DISTINCT mm.miembro_id)                        AS miembros,
       COUNT(DISTINCT CASE WHEN m.estado = 'activo' THEN m.id END) AS activos
FROM ministerios mi
LEFT JOIN miembros_ministerios mm ON mm.ministerio_id = mi.id
LEFT JOIN miembros m              ON m.id = mm.miembro_id
GROUP BY mi.id, mi.nombre
ORDER BY miembros DESC, mi.nombre;
