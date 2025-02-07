DROP TABLE IF EXISTS `objetivos`;
CREATE TABLE `objetivos` (
  `id_objetivo` INT NOT NULL AUTO_INCREMENT,
  `descripcion` VARCHAR(255) NOT NULL,
  `fecha_inicio` DATE NOT NULL,
  `fecha_fin` DATE NOT NULL,
  `estado` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`id_objetivo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
