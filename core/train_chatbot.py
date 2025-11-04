from chatbot import chatbot  # Importa el bot ya definido
from chatterbot.trainers import ChatterBotCorpusTrainer, ListTrainer

print("Entrenando el chatbot...")

# Entrenamiento con corpus
corpus_trainer = ChatterBotCorpusTrainer(chatbot)
corpus_trainer.train("chatterbot.corpus.spanish")

# Entrenamiento con frases personalizadas
list_trainer = ListTrainer(chatbot)
list_trainer.train([
    ["Hola","Buenas","Buenos dias","Que tal"],
    "Hola como estas? En que te puedo ayudar?",
    ["Chau","Bye","Hasta luego","Nos vemos"],
    "Chau, hasta la proxima",
    "¿Qué beneficios tengo como empleado?",
    "Contás con obra social, vacaciones pagas y capacitaciones.",
    "¿Cómo me postulo a una oferta de empleo?",
    "Es recomendable cargar un CV actualizado, después presionás el botón 'postularme' sobre la oferta que prefieras",
    "¿Como puedo pedir vacaciones?",
    "Dirigete a la seccion de 'solicitar vacaciones' en el menu lateral, luego registras el periodo deseado y presionas el botón solicitar. En esta misma vista vas a ver el estado de tus solicitudes"
])

print("Entrenamiento finalizado ✅")