DROP TABLE IF EXISTS `cargo_departamento`;
CREATE TABLE `cargo_departamento` (
  `id_cargo` INT NOT NULL,
  `id_departamento` INT NOT NULL,
  PRIMARY KEY (`id_cargo`, `id_departamento`),
  FOREIGN KEY (`id_cargo`) REFERENCES `cargo`(`id_cargo`) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (`id_departamento`) REFERENCES `departamento`(`id_departamento`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
