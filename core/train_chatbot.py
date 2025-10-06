from chatbot import chatbot  # Importa el bot ya definido
from chatterbot.trainers import ChatterBotCorpusTrainer, ListTrainer

print("Entrenando el chatbot...")

# Entrenamiento con corpus
corpus_trainer = ChatterBotCorpusTrainer(chatbot)
corpus_trainer.train("chatterbot.corpus.spanish")

# Entrenamiento con frases personalizadas
list_trainer = ListTrainer(chatbot)
list_trainer.train([
    "¿Qué beneficios tengo como empleado?",
    "Contás con obra social, vacaciones pagas y capacitaciones.",
    "¿Cómo me postulo a una oferta de empleo?",
    "Es recomendable cargar un CV actualizado, después presionás el botón 'postularme' sobre la oferta que prefieras"
])

print("Entrenamiento finalizado ✅")
