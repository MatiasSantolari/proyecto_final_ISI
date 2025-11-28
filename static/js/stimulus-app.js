import { Application } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js";
import PersonasController from "./controllers/personas_controller.js";

// Arranca Stimulus y registra los controladores usados en el proyecto.
window.Stimulus = Application.start();
Stimulus.register("personas", PersonasController);
