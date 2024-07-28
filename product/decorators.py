from functools import wraps
from django.http import JsonResponse
import requests
import json
from django.conf import settings
from user.models import User

TELEGRAM_ADMINS_ID = ['932199554']

def admin_only(view_func):
    @wraps(view_func)
    def _wrapped_view(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            message = data.get('message', {})
            chat = message.get('chat', {})
            chat_id = chat.get('id')
            user_id = str(message.get('from', {}).get('id'))

            print(f"Admin Check: chat_id={chat_id}, user_id={user_id}")

            if user_id in TELEGRAM_ADMINS_ID:
                return view_func(self, request, *args, **kwargs)
            else:
                response_data = {
                    'chat_id': chat_id,
                    'text': 'Access denied. You are not an administrator.'
                }
                requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                return JsonResponse({'error': 'Access denied'})
        except Exception as e:
            print(f"Error in admin_only decorator: {e}")
            return JsonResponse({'error': 'Internal Server Error'})

    return _wrapped_view


def apply_class_decorator(decorator):
    def class_decorator(cls):
        for attr_name, attr_value in cls.__dict__.items():
            if callable(attr_value) and not attr_name.startswith('__'):
                setattr(cls, attr_name, decorator(attr_value))
        return cls
    return class_decorator