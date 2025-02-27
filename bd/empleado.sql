DROP TABLE IF EXISTS `empleado`;
CREATE TABLE `empleado` (
  `id_empleado` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `estado` ENUM('inactivo', 'en licencia', 'suspendido', 'en prueba', 'jubilado') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
