DROP TABLE IF EXISTS `institucion_capacitacion`;
CREATE TABLE `institucion_capacitacion` (
  `id_institucion` INT NOT NULL,
  `id_capacitacion` INT NOT NULL,
  PRIMARY KEY (`id_institucion`, `id_capacitacion`),
  FOREIGN KEY (`id_institucion`) REFERENCES `institucion` (`id_institucion`) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (`id_capacitacion`) REFERENCES `capacitacion` (`id_capacitacion`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
