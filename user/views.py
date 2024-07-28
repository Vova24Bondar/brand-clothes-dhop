from django.http import HttpResponse, JsonResponse
import json
import requests
from user.models import User
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
import os
from product.views import ProductCreateView, ProductDeleteView, ProductListView, ProductUpdateView
from purchase.views import PurchaseCreateView, PurchaseListView
from django.views import View
from django.conf import settings



class TelegramBotWebhook(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            message = data.get('message', {})
            callback_query = data.get('callback_query', {})
            chat_id = message.get('chat', {}).get('id') if message else callback_query.get('message', {}).get('chat', {}).get('id')
            text = message.get('text') if message else callback_query.get('data')

            if callback_query:
                return self.handle_callback_query(request, chat_id, callback_query)

            if text and text.startswith('/product_create'):
                return self.handle_product_create(request, chat_id, data)
            elif text and text.startswith('/product_update'):
                return self.handle_product_update(request, chat_id, data)
            elif text and text.startswith('/product_delete'):
                return self.handle_product_delete(request, chat_id, data)
            elif text and text.startswith('/product_list'):
                return self.handle_product_list(request, chat_id, data)
            elif text and text.startswith('/commands'):
                return self.handle_commands_list(request, chat_id, data)
            elif text and text.startswith('/start'):
                return self.handle_start_bot(request, chat_id, data)
            elif text and text.startswith('/purchase_create'):
                return self.handle_purchase_create(request, chat_id, data)
            elif text and text.startswith('/purchase_list'):
                return self.handle_purchase_list(request, chat_id, data)
            else:
                cache.set(f'{chat_id}_restart', 2)
                step = cache.get(f'{chat_id}_step')
                if step:
                    command = cache.get(f'{chat_id}_command', '')
                    if 'product_create' in command:
                        return self.handle_product_create(request, chat_id, data)
                    elif 'product_update' in command:
                        return self.handle_product_update(request, chat_id, data)
                    elif 'product_delete' in command:
                        return self.handle_product_delete(request, chat_id, data)
                    elif 'product_list' in command:
                        return self.handle_product_list(request, chat_id, data)
                    elif 'purchase_create' in command:
                        return self.handle_purchase_create(request, chat_id, data)
                    elif 'purchase_list' in command:
                        return self.handle_purchase_list(request, chat_id, data)
                    else:
                        self.send_message(chat_id, 'Invalid input. Please try again.')
                        return JsonResponse({'message': 'Invalid input'})
                else:
                    self.handle_unknown_command(request, chat_id)
                    return JsonResponse({'message': 'Unknown command'})
        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({'message': 'Internal Server Error'})

    def handle_callback_query(self, request, chat_id, callback_query):
        data = callback_query.get('data')
        if not data or not data.startswith('buy_'):
            self.send_message(chat_id, 'Invalid callback data.')
            return JsonResponse({'message': 'Invalid callback data'}, status=400)

        product_id = data.split('_')[1]
        purchase_create_view = PurchaseCreateView()

        new_request_data = {
            'message': {
                'chat': {
                    'id': chat_id
                },
                'from': {
                    'username': callback_query.get('from', {}).get('username', '')
                },
                'text': product_id
            }
        }
        request._body = json.dumps(new_request_data)
        return purchase_create_view.post(request)

    def handle_product_create(self, request, chat_id, data):
        cache.set(f'{chat_id}_command', 'product_create')
        product_create_view = ProductCreateView()
        request._body = json.dumps(data)
        return product_create_view.post(request)

    def handle_product_update(self, request, chat_id, data):
        cache.set(f'{chat_id}_command', 'product_update')
        product_update_view = ProductUpdateView()
        request._body = json.dumps(data)
        return product_update_view.post(request)

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

    def handle_purchase_create(self, request, chat_id, data):
        cache.set(f'{chat_id}_command', 'purchase_create')
        purchase_create_view = PurchaseCreateView()
        request._body = json.dumps(data)
        return purchase_create_view.post(request)

    def handle_purchase_list(self, request, chat_id, data):
        cache.set(f'{chat_id}_command', 'purchase_list')
        purchase_list_view = PurchaseListView()
        request._body = json.dumps(data)
        return purchase_list_view.post(request)

    def handle_commands_list(self, request, chat_id, data):
        data = json.loads(request.body)
        chat_id = data.get('message').get('chat').get('id')
        response_data = {
            'chat_id': chat_id,
            'text': f'List of commands:\n/start\n/commands\n/product_create\n/product_update\n/product_delete\n/product_list\n/purchase_create\n/purchase_list'
        }
        requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
        return JsonResponse({'message': 'ok'}, status=200)

    def handle_start_bot(self, request, chat_id, data):
        user_data = data.get('message', {}).get('from', {})
        username = user_data.get('username')
        data = json.loads(request.body)
        chat_id = data.get('message').get('chat').get('id')
        user = User.objects.filter(chat_id=chat_id)

        if user.exists():
            response_text = ('Вітаю.\nВи потрапили до телеграм бота Brand Clothes.\n'
                             'Тут ви можете придбати найкращий брендовий одяг.\n'
                             'Також ви можете подивитися функціонал бота за командою /commands')
        else:
            User.objects.create(
                username=username,
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                password=make_password(username),
                chat_id=chat_id
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
                'text': f'Просимо вибачення за принесені незручності.\nНаразі, бот працює справно і готовий до використання.'
            }
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
            return JsonResponse({'message': 'ok'}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return HttpResponse("Hello world")
