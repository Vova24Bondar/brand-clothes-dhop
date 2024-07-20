from functools import wraps
from django.http import JsonResponse
from django.conf import settings
import requests
import json

BOT_TOKEN = '7047933724:AAHofJokHNaWRtde2LoqokvTi8bfPBbFSWw'
TG_BASE_URL = 'https://api.telegram.org/bot'


def admin_only(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        data = json.loads(request.body)
        chat_id = data.get('message', {}).get('chat', {}).get('id')
        user_id = str(data.get('message', {}).get('from', {}).get('id'))

        if int(user_id) in settings.TELEGRAM_ADMINS_ID:
            return view_func(request, *args, **kwargs)
        else:
            response_data = {
                'chat_id': chat_id,
                'text': 'Access denied. You are not an administrator.'
            }
            requests.post(f'{TG_BASE_URL}{BOT_TOKEN}/sendMessage', json=response_data)
            return JsonResponse({'error': 'Access denied'}, status=403)

    return _wrapped_view