from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer, ListTrainer

chatbot = ChatBot(
    "RRHH Bot",
    storage_adapter="chatterbot.storage.SQLStorageAdapter",
    database_uri="sqlite:///chatbot.sqlite3",
    logic_adapters=[
        {
            "import_path": "chatterbot.logic.BestMatch",
            "default_response": "Lo siento, no entendí tu consulta.",
            "maximum_similarity_threshold": 0.85
        }
    ],
    read_only=False,
)

# 1) Entrenamiento con corpus en español
corpus_trainer = ChatterBotCorpusTrainer(chatbot)
corpus_trainer.train("chatterbot.corpus.spanish")

# 2) Entrenamiento con frases personalizadas
list_trainer = ListTrainer(chatbot)
list_trainer.train([
    "¿Qué beneficios tengo como empleado?",
    "Contás con obra social, vacaciones pagas y capacitaciones.",
])
