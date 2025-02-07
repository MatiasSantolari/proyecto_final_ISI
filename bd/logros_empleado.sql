DROP TABLE IF EXISTS `logros_empleado`;
CREATE TABLE `logros_empleado` (
  `id_logros` INT NOT NULL,
  `id_empleado` INT NOT NULL,
  PRIMARY KEY (`id_logros`, `id_empleado`),
  FOREIGN KEY (`id_logros`) REFERENCES `logros` (`id_logro`) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (`id_empleado`) REFERENCES `empleado` (`id_empleado`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
