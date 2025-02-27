DROP TABLE IF EXISTS `usuario`;
CREATE TABLE `usuario` (
    `id_usuario` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `id_empleado` INT NOT NULL,
    `nombre_usuario` VARCHAR(50) NOT NULL UNIQUE,
    `correo` VARCHAR(100) NOT NULL,
    `contraseña` VARCHAR(255) NOT NULL,
    `rol` ENUM('admin', 'empleado', 'gerente') NOT NULL,
    `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `fecha_ultimo_acceso` TIMESTAMP NULL,
    `estado` ENUM('activo', 'inactivo') DEFAULT 'activo',
    FOREIGN KEY (`id_empleado`) REFERENCES `empleado`(`id_empleado`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
