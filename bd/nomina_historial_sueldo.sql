DROP TABLE IF EXISTS `nomina_historial_sueldo`;
CREATE TABLE `nomina_historial_sueldo` (
  `id_nomina` INT NOT NULL,
  `fecha_sueldo` DATE NOT NULL,
  `id_cargo` INT NOT NULL,
  PRIMARY KEY (`id_nomina`, `fecha_sueldo`, `id_cargo`),
  FOREIGN KEY (`id_nomina`) REFERENCES `nomina`(`id_nomina`) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (`id_cargo`) REFERENCES `cargo`(`id_cargo`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
