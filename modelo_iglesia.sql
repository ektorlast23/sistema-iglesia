-- ============================================================
-- Sistema Web Open-Source de Gestión cristiana, Inventario y Asistencia
-- Semana 2: Modelo de Datos EER (MySQL Workbench)
-- BD: iglesia_db | Stack: Python Django + MySQL
-- Tablas: familias, ministerios, miembros, miembros_ministerios, eventos, asistencias
-- Reglas: familia 1-N miembros | miembro N-M ministerios | evento 1-N asistencias
-- ============================================================

CREATE DATABASE IF NOT EXISTS iglesia_db
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE iglesia_db;

-- ---------- 1. FAMILIAS ----------
CREATE TABLE IF NOT EXISTS familias (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre_familia VARCHAR(100) NOT NULL,
  direccion VARCHAR(255) NULL,
  telefono VARCHAR(20) NULL,
  fecha_registro DATE NULL,
  CONSTRAINT uq_familias_nombre UNIQUE (nombre_familia)
) ENGINE=InnoDB;

-- ---------- 2. MINISTERIOS ----------
CREATE TABLE IF NOT EXISTS ministerios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  descripcion TEXT NULL,
  activo TINYINT(1) NOT NULL DEFAULT 1,
  CONSTRAINT uq_ministerios_nombre UNIQUE (nombre)
) ENGINE=InnoDB;

-- ---------- 3. MIEMBROS ----------
CREATE TABLE IF NOT EXISTS miembros (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombres VARCHAR(100) NOT NULL,
  apellidos VARCHAR(100) NOT NULL,
  fecha_nacimiento DATE NULL,
  sexo ENUM('M','F') NULL,
  telefono VARCHAR(20) NULL,
  email VARCHAR(100) NULL,
  direccion VARCHAR(255) NULL,
  familia_id INT NULL,
  fecha_ingreso DATE NULL,
  estado ENUM('activo','inactivo','visitante') NOT NULL DEFAULT 'activo',
  CONSTRAINT fk_miembros_familia
    FOREIGN KEY (familia_id) REFERENCES familias (id)
    ON DELETE SET NULL ON UPDATE CASCADE,
  INDEX idx_miembros_familia (familia_id),
  INDEX idx_miembros_estado (estado)
) ENGINE=InnoDB;

-- ---------- 3b. MIEMBROS_MINISTERIOS (N-M: un miembro en varios ministerios) ----------
CREATE TABLE IF NOT EXISTS miembros_ministerios (
  miembro_id INT NOT NULL,
  ministerio_id INT NOT NULL,
  fecha_asignacion DATE NULL,
  rol VARCHAR(50) NULL,
  PRIMARY KEY (miembro_id, ministerio_id),
  CONSTRAINT fk_mm_miembro
    FOREIGN KEY (miembro_id) REFERENCES miembros (id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_mm_ministerio
    FOREIGN KEY (ministerio_id) REFERENCES ministerios (id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  INDEX idx_mm_ministerio (ministerio_id)
) ENGINE=InnoDB;

-- ---------- 4. EVENTOS ----------
CREATE TABLE IF NOT EXISTS eventos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(150) NOT NULL,
  descripcion TEXT NULL,
  fecha DATE NOT NULL,
  hora_inicio TIME NULL,
  hora_fin TIME NULL,
  lugar VARCHAR(150) NULL,
  tipo VARCHAR(50) NULL COMMENT 'culto, grupo pequeno, ensayo, etc.',
  responsable_id INT NULL,
  CONSTRAINT fk_eventos_responsable
    FOREIGN KEY (responsable_id) REFERENCES miembros (id)
    ON DELETE SET NULL ON UPDATE CASCADE,
  INDEX idx_eventos_fecha (fecha),
  INDEX idx_eventos_responsable (responsable_id)
) ENGINE=InnoDB;

-- ---------- 5. ASISTENCIAS ----------
CREATE TABLE IF NOT EXISTS asistencias (
  id INT AUTO_INCREMENT PRIMARY KEY,
  miembro_id INT NOT NULL,
  evento_id INT NOT NULL,
  fecha DATE NOT NULL,
  presente TINYINT(1) NOT NULL DEFAULT 1,
  observaciones VARCHAR(255) NULL,
  CONSTRAINT fk_asistencias_miembro
    FOREIGN KEY (miembro_id) REFERENCES miembros (id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_asistencias_evento
    FOREIGN KEY (evento_id) REFERENCES eventos (id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT uq_asistencia_miembro_evento UNIQUE (miembro_id, evento_id),
  INDEX idx_asistencias_evento (evento_id),
  INDEX idx_asistencias_fecha (fecha)
) ENGINE=InnoDB;
