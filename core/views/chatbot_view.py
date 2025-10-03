from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from ..chatbot import chatbot


@csrf_exempt # Esto es porque la respuesta la recibo de js y no django
def get_response_chatbot(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get("message")
        bot_response = chatbot.get_response(user_message)
        return JsonResponse({"response": str(bot_response)})