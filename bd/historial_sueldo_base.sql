DROP TABLE IF EXISTS `historial_sueldo_base`;
CREATE TABLE `historial_sueldo_base` (
  `fecha_sueldo` DATE NOT NULL,
  `id_cargo` INT NOT NULL,
  `sueldo_base` DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (`fecha_sueldo`, `id_cargo`),
  FOREIGN KEY (`id_cargo`) REFERENCES `cargo`(`id_cargo`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
