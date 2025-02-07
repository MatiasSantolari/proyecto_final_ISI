DROP TABLE IF EXISTS `solicitud`;
CREATE TABLE `solicitud` (
    `id_solicitud` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `id_persona` INT NOT NULL,
    `id_cargo` INT NOT NULL,
    `descripcion` VARCHAR(255),
    `fecha_postulacion` DATE NOT NULL,
    `estado_postulacion` ENUM('pendiente', 'aprobado', 'rechazado') NOT NULL,
    FOREIGN KEY (`id_persona`) REFERENCES `persona`(`id_persona`) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (`id_cargo`) REFERENCES `cargo`(`id_cargo`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
