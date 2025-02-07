DROP TABLE IF EXISTS `objetivos_empleado`;
CREATE TABLE `objetivos_empleado` (
  `id_objetivo` INT NOT NULL,
  `id_empleado` INT NOT NULL,
  PRIMARY KEY (`id_objetivo`, `id_empleado`),
  FOREIGN KEY (`id_objetivo`) REFERENCES `objetivos` (`id_objetivo`) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (`id_empleado`) REFERENCES `empleado` (`id_empleado`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
