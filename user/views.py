from django.http import HttpResponse, JsonResponse
import json
import requests
from user.models import User
from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
import os
from product.views import ProductCreateView, ProductDeleteView, ProductListView
from django.views import View
from django.conf import settings


class TelegramBotWebhook(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            message = data.get('message', {})
            chat_id = message.get('chat', {}).get('id')
            text = message.get('text')

            if text and text.startswith('/product_create'):
                return self.handle_product_create(request, chat_id, data)
            elif text and text.startswith('/product_delete'):
                return self.handle_product_delete(request, chat_id, data)
            elif text and text.startswith('/product_list'):
                return self.handle_product_list(request, chat_id, data)
            elif text and text.startswith('/commands'):
                return self.handle_commands_list(request, chat_id, data)
            elif text and text.startswith('/start'):
                return self.handle_start_bot(request, chat_id, data)
            else:
                cache.set(f'{chat_id}_restart', 2)
                step = cache.get(f'{chat_id}_step')
                if step:
                    command = cache.get(f'{chat_id}_command', '')
                    if 'create' in command:
                        return self.handle_product_create(request, chat_id, data)
                    elif 'delete' in command:
                        return self.handle_product_delete(request, chat_id, data)
                    elif 'list' in command:
                        return self.handle_product_list(request, chat_id, data)
                    else:
                        self.send_message(chat_id, 'Invalid input. Please try again.')
                        return JsonResponse({'message': 'Invalid input'}, status=400)
                else:
                    self.handle_unknown_command(request, chat_id)
                    return JsonResponse({'message': 'Unknown command'}, status=400)
        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({'message': 'Internal Server Error'}, status=500)

    def handle_product_create(self, request, chat_id, data):
        cache.set(f'{chat_id}_command', 'product_create')
        product_create_view = ProductCreateView()
        request._body = json.dumps(data)
        return product_create_view.post(request)

    def handle_product_delete(self, request, chat_id, data):
        cache.set(f'{chat_id}_command', 'product_delete')
        product_delete_view = ProductDeleteView()
        request._body = json.dumps(data)
        return product_delete_view.post(request)

    def handle_product_list(self, request, chat_id, data):
        cache.set(f'{chat_id}_command', 'product_list')
        product_list_view = ProductListView()
        request._body = json.dumps(data)
        return product_list_view.post(request)

    def handle_commands_list(self, request, chat_id, data):
        data = json.loads(request.body)
        chat_id = data.get('message').get('chat').get('id')
        response_data = {
            'chat_id': chat_id,
            'text': f'List of commands:\n/start\n/commands\n/product_list\n/product_create\n/product_delete'
        }
        requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
        return JsonResponse({'message': 'ok'}, status=200)

    def handle_start_bot(self, request, chat_id, data):
        user_data = data.get('message', {}).get('from', {})
        username = user_data.get('username')
        user = User.objects.filter(username=username).first()

        if user:
            response_text = ('Вітаю.\nВи потрапили до телеграм бота Brand Clothes.\n'
                             'Тут ви можете придбати найкращий брендовий одяг.\n'
                             'Також ви можете подивитися функціонал бота за командою /commands')
        else:
            User.objects.create(
                username=username,
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                password=make_password(username)
            )
            response_text = ('Вітаю.\nВи потрапили до телеграм бота Brand Clothes.\n'
                             'Тут ви можете придбати найкращий брендовий одяг.\n'
                             'Також ви можете подивитися функціонал бота за командою /commands')

        self.send_message(chat_id, response_text)
        return JsonResponse({'message': 'ok'}, status=200)

    def handle_unknown_command(self, request, chat_id):
        self.send_message(chat_id, 'Unknown command. Please try again.')
        cache.delete(f'{chat_id}_restart')
        cache.delete(f'{chat_id}_step')
        cache.delete(f'{chat_id}_command')

    def send_message(self, chat_id, text):
        response_data = {
            'chat_id': chat_id,
            'text': text
        }
        try:
            response = requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error sending message: {e}")


def hello_world(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            chat_id = data.get('message').get('chat').get('id')
            response_data = {
                'chat_id': chat_id,
                'text': 'Hello, World!'
            }
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
            return JsonResponse({'message': 'ok'}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return HttpResponse("Hello world")
