DROP TABLE IF EXISTS `nomina`;
CREATE TABLE `nomina` (
  `id_nomina` INT NOT NULL AUTO_INCREMENT,
  `id_empleado` INT NOT NULL,
  `fecha_generacion` DATE NOT NULL,
  `monto_bruto` DECIMAL(10,2) NOT NULL,
  `monto_neto` DECIMAL(10,2) NOT NULL,
  `cant_dias_trabajados` INT NOT NULL,
  `total_descuentos` DECIMAL(10,2) NOT NULL,
  `estado` VARCHAR(50) NOT NULL,
  `periodo` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`id_nomina`),
  FOREIGN KEY (`id_empleado`) REFERENCES `empleado` (`id_empleado`) ON DELETE CASCADE ON UPDATE CASCADE
);
