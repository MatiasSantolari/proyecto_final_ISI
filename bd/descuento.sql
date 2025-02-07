DROP TABLE IF EXISTS `descuento`;
CREATE TABLE `descuento` (
  `id_descuento` INT NOT NULL AUTO_INCREMENT,
  `tipo` VARCHAR(100) NOT NULL,
  `monto` DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (`id_descuento`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
