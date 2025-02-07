DROP TABLE IF EXISTS `persona`;
CREATE TABLE `persona` (
    `id_persona` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `nombre` VARCHAR(100) NOT NULL,
    `apellido` VARCHAR(100) NOT NULL,
    `dni` VARCHAR(20) NOT NULL UNIQUE,
    `email` VARCHAR(100) NOT NULL,
    `telefono` VARCHAR(20),
    `fecha_nacimiento` DATE NOT NULL,
    `direccion` VARCHAR(255),
    `tipo_persona` ENUM('empleado', 'postulante') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
