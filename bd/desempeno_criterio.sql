DROP TABLE IF EXISTS `desempeno_criterio`;
CREATE TABLE `desempeno_criterio` (
  `id_criterio` INT NOT NULL,
  `id_empleado` INT NOT NULL,
  `fecha_evaluacion` DATE NOT NULL,
  PRIMARY KEY (`id_criterio`, `id_empleado`, `fecha_evaluacion`),
  KEY `FK_desempeno_criterio_criterio_idx` (`id_criterio`),
  KEY `FK_desempeno_criterio_empleado_fecha_idx` (`id_empleado`, `fecha_evaluacion`),
  CONSTRAINT `FK_desempeno_criterio_criterio` FOREIGN KEY (`id_criterio`) REFERENCES `criterio_evaluacion` (`id_criterio`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `FK_desempeno_criterio_empleado_fecha` FOREIGN KEY (`id_empleado`, `fecha_evaluacion`) REFERENCES `evaluacion` (`id_empleado`, `fecha_evaluacion`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
