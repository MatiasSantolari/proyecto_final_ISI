DROP TABLE IF EXISTS `descuento_empleado_nomina`;
CREATE TABLE `descuento_empleado_nomina` (
  `id_empleado` INT NOT NULL,
  `id_descuento` INT NOT NULL,
  `id_nomina` INT NOT NULL,
  PRIMARY KEY (`id_empleado`, `id_descuento`, `id_nomina`),
  FOREIGN KEY (`id_empleado`) REFERENCES `empleado`(`id_empleado`) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (`id_descuento`) REFERENCES `descuento`(`id_descuento`) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (`id_nomina`) REFERENCES `nomina`(`id_nomina`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
