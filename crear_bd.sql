CREATE DATABASE IF NOT EXISTS hospital CHARACTER SET utf8mb4;
USE hospital;

DROP TABLE IF EXISTS documentos;
DROP TABLE IF EXISTS empleados;
DROP TABLE IF EXISTS checklist;

-- Qué documentos exige cada perfil
CREATE TABLE checklist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    perfil VARCHAR(20) NOT NULL,
    documento VARCHAR(40) NOT NULL
);

-- Tabla principal (padre)
CREATE TABLE empleados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(60) NOT NULL,
    perfil VARCHAR(20) NOT NULL,
    fecha_ingreso DATE NOT NULL,
    correo VARCHAR(80) NOT NULL
);

-- Tabla relacionada (hija): cada documento pertenece a un empleado
CREATE TABLE documentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empleado_id INT NOT NULL,
    documento VARCHAR(40) NOT NULL,
    estado VARCHAR(10) NOT NULL,
    FOREIGN KEY (empleado_id) REFERENCES empleados(id) ON DELETE CASCADE
);

INSERT INTO checklist (perfil, documento) VALUES
('administrativo', 'DUI'),
('administrativo', 'Título'),
('administrativo', 'Antecedentes Penal'),
('administrativo', 'Solvencia PNP'),
('medico', 'DUI'),
('medico', 'Título'),
('medico', 'Antecedentes Penal'),
('medico', 'Solvencia PNP'),
('medico', 'Colegiatura médica'),
('medico', 'Especialidad'),
('enfermeria', 'DUI'),
('enfermeria', 'Título'),
('enfermeria', 'Antecedentes Penal'),
('enfermeria', 'Solvencia PNP'),
('enfermeria', 'Junta de Vigilancia');

INSERT INTO empleados (nombre, perfil, fecha_ingreso, correo) VALUES
('Ana', 'administrativo', '2022-03-15', 'ana@hospital.com'),
('Carlos', 'medico', '2021-07-01', 'carlos@hospital.com'),
('Maria', 'enfermeria', '2023-01-10', 'maria@hospital.com'),
('Luis', 'administrativo', '2024-05-20', 'luis@hospital.com'),
('Sofia', 'medico', '2020-11-02', 'sofia@hospital.com');

INSERT INTO documentos (empleado_id, documento, estado) VALUES
(1, 'DUI', 'Completo'),
(1, 'Título', 'Completo'),
(1, 'Antecedentes Penal', 'Completo'),
(1, 'Solvencia PNP', 'Completo'),
(2, 'DUI', 'Completo'),
(2, 'Título', 'Completo'),
(2, 'Antecedentes Penal', 'Completo'),
(2, 'Solvencia PNP', 'Pendiente'),
(2, 'Colegiatura médica', 'Completo'),
(2, 'Especialidad', 'Pendiente'),
(3, 'DUI', 'Completo'),
(3, 'Título', 'Completo'),
(3, 'Antecedentes Penal', 'Completo'),
(3, 'Solvencia PNP', 'Completo'),
(3, 'Junta de Vigilancia', 'Completo'),
(4, 'DUI', 'Completo'),
(4, 'Título', 'Pendiente'),
(4, 'Antecedentes Penal', 'Pendiente'),
(4, 'Solvencia PNP', 'Pendiente'),
(5, 'DUI', 'Completo'),
(5, 'Título', 'Completo'),
(5, 'Antecedentes Penal', 'Completo'),
(5, 'Solvencia PNP', 'Completo'),
(5, 'Colegiatura médica', 'Completo'),
(5, 'Especialidad', 'Completo');
