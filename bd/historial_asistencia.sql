DROP TABLE IF EXISTS `historial_asistencia`;
CREATE TABLE `historial_asistencia` (
    `id_empleado` INT NOT NULL,
    `fecha_asistencia` DATE NOT NULL,
    `hora_entrada` TIME NOT NULL,
    `hora_salida` TIME DEFAULT NULL,
    PRIMARY KEY (`id_empleado`, `fecha_asistencia`, `hora_entrada`),
    FOREIGN KEY (`id_empleado`) REFERENCES `empleado`(`id_empleado`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;