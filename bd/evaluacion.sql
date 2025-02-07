DROP TABLE IF EXISTS `evaluacion`;
CREATE TABLE `evaluacion` (
  `id_empleado` INT NOT NULL,
  `fecha_evaluacion` DATE NOT NULL,
  `descripcion` VARCHAR(255) DEFAULT NULL,
  `comentarios` VARCHAR(255) DEFAULT NULL,
  `calificacion_final` DECIMAL(5,2) NOT NULL,
  PRIMARY KEY (`id_empleado`, `fecha_evaluacion`),
  FOREIGN KEY (`id_empleado`) REFERENCES `empleado` (`id_empleado`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

