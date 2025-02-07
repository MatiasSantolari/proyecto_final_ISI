DROP TABLE IF EXISTS `habilidad_empleado`;
CREATE TABLE `habilidad_empleado` (
  `id_habilidad` INT NOT NULL,
  `id_empleado` INT NOT NULL,
  PRIMARY KEY (`id_habilidad`, `id_empleado`),
  FOREIGN KEY (`id_habilidad`) REFERENCES `habilidad` (`id_habilidad`) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (`id_empleado`) REFERENCES `empleado` (`id_empleado`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
