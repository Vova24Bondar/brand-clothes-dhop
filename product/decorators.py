from functools import wraps
from django.http import JsonResponse
import requests
import json
from django.conf import settings

TELEGRAM_ADMINS_ID = settings.TELEGRAM_ADMINS_ID

def admin_only(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        data = json.loads(request.body)
        chat_id = data.get('message', {}).get('chat', {}).get('id')
        user_id = str(data.get('message', {}).get('from', {}).get('id'))
        try:
            if user_id in TELEGRAM_ADMINS_ID:
                return view_func(request, *args, **kwargs)
            else:
                response_data = {
                    'chat_id': chat_id,
                    'text': 'Access denied. You are not an administrator.'
                }
                requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}//sendMessage', json=response_data)
                return JsonResponse({'error': 'Access denied'}, status=403)
        except (json.JSONDecodeError, KeyError) as e:
            response_data = {
                'chat_id': chat_id,
                'text': 'Error processing the request. Please try again later.'
            }
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}//sendMessage', json=response_data)
            return JsonResponse({'error': 'Bad request'}, status=400)
        except Exception as e:
            response_data = {
                'chat_id': chat_id,
                'text': 'An unexpected error occurred.'
            }
            requests.post(f'{TG_BASE_URL}{BOT_TOKEN}/sendMessage', json=response_data)
            return JsonResponse({'error': str(e)}, status=500)

    return _wrapped_view