DROP TABLE IF EXISTS `tipo_contrato`;
CREATE TABLE `tipo_contrato` (
  `id_contrato` INT NOT NULL AUTO_INCREMENT,
  `descripcion` VARCHAR(255) NOT NULL,
  `costo` DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (`id_contrato`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
