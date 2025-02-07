DROP TABLE IF EXISTS `vacaciones_solicitud`;
CREATE TABLE `vacaciones_solicitud` (
    `id_solicitud` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `id_empleado` INT NOT NULL,
    `fecha_solicitud` DATE NOT NULL,
    `fecha_inicio_estimada` DATE NOT NULL,
    `fecha_fin_estimada` DATE NOT NULL,
    `cant_dias_solicitados` INT NOT NULL,
    `estado` ENUM('pendiente', 'aprobado', 'rechazado') NOT NULL,
    FOREIGN KEY (`id_empleado`) REFERENCES `empleado`(`id_empleado`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
