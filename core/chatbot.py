from chatterbot import ChatBot

# Definición del chatbot
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
