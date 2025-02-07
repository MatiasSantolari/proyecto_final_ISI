DROP TABLE IF EXISTS `empleado_cargo`;
CREATE TABLE `empleado_cargo` (
  `fecha_asignacion` DATE NOT NULL,
  `fecha_desasignado` DATE,
  `id_empleado` INT NOT NULL,
  `id_cargo` INT NOT NULL,
  PRIMARY KEY (`id_empleado`, `id_cargo`, `fecha_asignacion`),
  FOREIGN KEY (`id_empleado`) REFERENCES `empleado`(`id_empleado`) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (`id_cargo`) REFERENCES `cargo`(`id_cargo`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
