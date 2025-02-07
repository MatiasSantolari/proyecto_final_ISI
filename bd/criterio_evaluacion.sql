DROP TABLE IF EXISTS `criterio_evaluacion`;
CREATE TABLE `criterio_evaluacion` (
  `id_criterio` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(100) NOT NULL,
  `descripcion` VARCHAR(255) DEFAULT NULL,
  `ponderacion` DECIMAL(5,2) NOT NULL,
  `id_tipo_criterio` INT NOT NULL,
  PRIMARY KEY (`id_criterio`),
  KEY `FK_criterio_tipo_criterio_idx` (`id_tipo_criterio`),
  CONSTRAINT `FK_criterio_tipo_criterio` FOREIGN KEY (`id_tipo_criterio`) REFERENCES `tipo_criterio` (`id_tipo_criterio`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
