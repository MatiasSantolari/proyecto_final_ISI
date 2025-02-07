DROP TABLE IF EXISTS `beneficio_empleado_nomina`;
CREATE TABLE `beneficio_empleado_nomina` (
  `id_empleado` INT NOT NULL,
  `id_beneficio` INT NOT NULL,
  `id_nomina` INT NOT NULL,
  PRIMARY KEY (`id_empleado`, `id_beneficio`, `id_nomina`),
  FOREIGN KEY (`id_empleado`) REFERENCES `empleado`(`id_empleado`) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (`id_beneficio`) REFERENCES `beneficio`(`id_beneficio`) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (`id_nomina`) REFERENCES `nomina`(`id_nomina`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
