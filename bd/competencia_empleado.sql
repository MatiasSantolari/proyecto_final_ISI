DROP TABLE IF EXISTS `competencia_empleado`;
CREATE TABLE `competencia_empleado` (
  `id_competencia` INT NOT NULL,
  `id_empleado` INT NOT NULL,
  PRIMARY KEY (`id_competencia`, `id_empleado`),
  FOREIGN KEY (`id_competencia`) REFERENCES `competencias` (`id_competencia`) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (`id_empleado`) REFERENCES `empleado` (`id_empleado`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
