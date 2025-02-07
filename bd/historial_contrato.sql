DROP TABLE IF EXISTS `historial_contrato`;
CREATE TABLE `historial_contrato` (
  `id_empleado` INT NOT NULL,
  `fecha_inicio` DATE NOT NULL,
  `fecha_fin` DATE NOT NULL,
  `condiciones` VARCHAR(255) NOT NULL,
  `id_contrato` INT NOT NULL,
  PRIMARY KEY (`id_empleado`, `fecha_inicio`),
  FOREIGN KEY (`id_empleado`) REFERENCES `empleado` (`id_empleado`) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (`id_contrato`) REFERENCES `tipo_contrato` (`id_contrato`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
