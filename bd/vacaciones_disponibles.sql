DROP TABLE IF EXISTS `vacaciones_disponibles`;
CREATE TABLE `vacaciones_disponibles` (
    `id_empleado` INT NOT NULL,
    `fecha` DATE NOT NULL,
    `cantidad_dias_disponibles` INT NOT NULL,
    PRIMARY KEY (`id_empleado`, `fecha`),
    FOREIGN KEY (`id_empleado`) REFERENCES `empleado`(`id_empleado`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
