DROP TABLE IF EXISTS `capacitacion_empleado`;
CREATE TABLE `capacitacion_empleado` (
  `id_capacitacion` INT NOT NULL,
  `id_empleado` INT NOT NULL,
  `fecha_inscripcion` DATE NOT NULL,
  `estado` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`id_capacitacion`, `id_empleado`),
  FOREIGN KEY (`id_capacitacion`) REFERENCES `capacitacion` (`id_capacitacion`) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (`id_empleado`) REFERENCES `empleado` (`id_empleado`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
