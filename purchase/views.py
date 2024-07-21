from django.shortcuts import render
from django.views import View
import json
import requests
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
from user.models import User
from product.models import Product
from purchase.models import Purchase


class PurchaseCreateView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        message = data.get('message', {})
        chat = message.get('chat', {})
        user_data = message.get('from', {})
        chat_id = chat.get('id')
        text = message.get('text')
        username = user_data.get('username')

        step = cache.get(f'{chat_id}_step', 1)

        if step == 1:
            response_data = {
                'chat_id': chat_id,
                'text': 'Будь ласка, введіть ID товару який ви хочете придбати(не натискайте на іншу команду поки не завершите виконання цієї)'
            }
            cache.set(f'{chat_id}_step', 2)
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
            return JsonResponse({'message': 'ID requested successfully'}, status=200)

        elif step == 2:
            cache.set(f'{chat_id}_product_id', text)
            response_data = {
                'chat_id': chat_id,
                'text': 'Будь ласка, введіть кількість товару яку ви хочете придбати(не натискайте на іншу команду поки не завершите виконання цієї)'
            }
            cache.set(f'{chat_id}_step', 3)
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
            return JsonResponse({'message': 'Quantity requested successfully'}, status=200)

        elif step == 3:
            cache.set(f'{chat_id}_quantity', text)
            try:
                user = User.objects.get(username=username)
                product_id = cache.get(f'{chat_id}_product_id')
                quantity = int(cache.get(f'{chat_id}_quantity'))

                product = Product.objects.get(id=product_id)

                if quantity > product.number_of_goods:
                    raise ValueError("Insufficient quantity of goods available")

                product.number_of_goods -= quantity
                product.save()

                purchase = Purchase.objects.create(
                    user_id=user,
                    product_id=product,
                    quantity=quantity,
                    is_done=True
                )

                photo_data = {
                    'chat_id': chat_id,
                    'photo': product.image,
                    'caption': (f"Покупець: {user.username}\n"
                                f"ID товару: {product_id}\n"
                                f"Кількість: {purchase.quantity}\n"
                                f"Ціна: {product.price} UAH\n"
                                f"Статус: {purchase.is_done}")
                }
                requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendPhoto', data=photo_data)
                cache.delete_many([f'{chat_id}_step', f'{chat_id}_product_id', f'{chat_id}_quantity'])
                return JsonResponse({'message': 'Purchase created successfully'}, status=200)

            except User.DoesNotExist:
                response_data = {
                    'chat_id': chat_id,
                    'text': 'Користувача не знайдено. Будь ласка, спробуйте пізніше.'
                }
                requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                cache.delete_many([f'{chat_id}_step', f'{chat_id}_product_id', f'{chat_id}_quantity'])
                return JsonResponse({'error': 'User not found'}, status=400)

            except Product.DoesNotExist:
                response_data = {
                    'chat_id': chat_id,
                    'text': 'Товар не знайдено. Будь ласка, спробуйте пізніше.'
                }
                requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                cache.delete_many([f'{chat_id}_step', f'{chat_id}_product_id', f'{chat_id}_quantity'])
                return JsonResponse({'error': 'Product not found'}, status=400)

            except ValueError as e:
                response_data = {
                    'chat_id': chat_id,
                    'text': f'Помилка: {str(e)}. Будь ласка, спробуйте ще раз.'
                }
                requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                cache.delete_many([f'{chat_id}_step', f'{chat_id}_product_id', f'{chat_id}_quantity'])
                return JsonResponse({'error': 'Invalid quantity'}, status=400)

            except Exception as e:
                response_data = {
                    'chat_id': chat_id,
                    'text': f'Помилка. Будь ласка, спробуйте пізніше. ({str(e)})'
                }
                requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                cache.delete_many([f'{chat_id}_step', f'{chat_id}_product_id', f'{chat_id}_quantity'])
                return JsonResponse({'error': str(e)}, status=400)

        else:
            response_data = {
                'chat_id': chat_id,
                'text': 'Невідома команда. Будь ласка, спробуйте ще раз.'
            }
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
            cache.delete_many([f'{chat_id}_step', f'{chat_id}_product_id', f'{chat_id}_quantity'])
            return JsonResponse({'error': 'Unknown command'}, status=400)


class PurchaseListView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        chat_id = data.get('message').get('chat').get('id')

        try:
            user = User.objects.get(chat_id=chat_id)
            user_id = user.id
        except User.DoesNotExist:
            response_data = {
                'chat_id': chat_id,
                'text': 'Користувача не знайдено.'
            }
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
            return JsonResponse({'error': 'User not found'}, status=400)

        purchases = Purchase.objects.filter(user_id=user_id)

        if not purchases.exists():
            response_data = {
                'chat_id': chat_id,
                'text': 'Наразі, у вас немає покупок.'
            }
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
            return JsonResponse({'message': 'No purchases available'}, status=200)

        for purchase in purchases:
            product = purchase.product_id
            photo_data = {
                'chat_id': chat_id,
                'photo': product.image,
                'caption': (f"Айді покупця: {purchase.user_id}\n"
                         f"Айді товару: {purchase.product_id}\n"
                         f"Кількість купленого товару: {purchase.quantity}\n"
                         f"Дата покупки: {purchase.purchase_date}\n"
                         f"Ціна: {product.price} UAH")
            }
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendPhoto', data=photo_data)

        return JsonResponse({'message': 'Purchases sent successfully'}, status=200)