from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
import json
import requests
from product.models import Product
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.views import View
from django.utils.decorators import method_decorator
from product.decorators import admin_only
from django.conf import settings


class ProductCreateView(View):
    @method_decorator(admin_only)
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        chat_id = data.get('message').get('chat').get('id')
        text = data.get('message').get('text')
        message = data.get('message')
        photo = message.get('photo')

        step = cache.get(f'{chat_id}_step', 1)

        if step == 1:
            response_data = {
                'chat_id': chat_id,
                'text': 'Please enter ONE image of your product.'
            }
            cache.set(f'{chat_id}_step', 2)
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
            return JsonResponse({'message': 'Image requested successfully'}, status=200)

        elif step == 2:
            if 'photo' in data.get('message') and len(photo) <= 4:
                try:
                    file_id = data['message']['photo'][-1]['file_id']
                    cache.set(f'{chat_id}_image', file_id)
                    response_data = {
                        'chat_id': chat_id,
                        'text': 'Please enter the name of your product.'
                    }
                    cache.set(f'{chat_id}_step', 3)
                    requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                    return JsonResponse({'message': 'Name requested successfully'}, status=200)
                except Exception as e:
                    response_data = {
                        'chat_id': chat_id,
                        'text': 'Please send ONE image of your product'
                    }
                    requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                    cache.set(f'{chat_id}_step', 1)
                    cache.delete_many([f'{chat_id}_image'])
                    return JsonResponse({'error': str(e)}, status=500)
            else:
                response_data = {
                    'chat_id': chat_id,
                    'text': 'Invalid input. Please send image of your product.'
                }
                requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                cache.set(f'{chat_id}_step', 1)
                cache.delete_many([f'{chat_id}_image'])
                return JsonResponse({'error': 'Image not provided'}, status=400)

        elif step == 3:
            cache.set(f'{chat_id}_name', text)
            response_data = {
                'chat_id': chat_id,
                'text': 'Please enter the description of your product.'
            }
            cache.set(f'{chat_id}_step', 4)
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
            return JsonResponse({'message': 'Description requested successfully'}, status=200)

        elif step == 4:
            cache.set(f'{chat_id}_description', text)
            response_data = {
                'chat_id': chat_id,
                'text': 'Please enter the price of your product.'
            }
            cache.set(f'{chat_id}_step', 5)
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
            return JsonResponse({'message': 'Price requested successfully'}, status=200)

        elif step == 5:
            try:
                price = int(text)
                cache.set(f'{chat_id}_price', price)
                image = cache.get(f'{chat_id}_image')
                name = cache.get(f'{chat_id}_name')
                description = cache.get(f'{chat_id}_description')
                int_price = cache.get(f'{chat_id}_price')
            except ValueError:
                response_data = {
                    'chat_id': chat_id,
                    'text': 'Invalid input. Please enter a valid numeric price when you will make a product.'
                }
                requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                cache.delete_many(
                    [f'{chat_id}_image', f'{chat_id}_name', f'{chat_id}_description', f'{chat_id}_price',
                     f'{chat_id}_step'])
                return JsonResponse({'error': 'Invalid price'}, status=400)

            try:
                product = Product.objects.create(
                    image=image,
                    name=name,
                    description=description,
                    price=int_price
                )
                photo_data = {
                    'chat_id': chat_id,
                    'photo': image,
                    'caption': f"Id: {product.id}\nName: {name}\nDescription: {description}\nPrice: {price}UAH"
                }
                requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendPhoto', data=photo_data)
                cache.delete_many(
                    [f'{chat_id}_image', f'{chat_id}_name', f'{chat_id}_description', f'{chat_id}_price',
                     f'{chat_id}_step'])
                return JsonResponse({'message': 'Product created successfully'}, status=201)

            except Exception as e:
                response_data = {
                    'chat_id': chat_id,
                    'text': 'PLEASE, SEND ONE IMAGE'
                }
                requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                cache.delete_many(
                    [f'{chat_id}_image', f'{chat_id}_name', f'{chat_id}_description', f'{chat_id}_price',
                     f'{chat_id}_step'])
                return JsonResponse({'error': str(e)}, status=500)


class ProductDeleteView(View):
    @method_decorator(admin_only)
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        chat_id = data.get('message', {}).get('chat', {}).get('id')
        text = data.get('message', {}).get('text', '')
        step = cache.get(f'{chat_id}_step', 1)

        if step == 1:
            response_data = {
                'chat_id': chat_id,
                'text': 'Please enter the ID of the product you want to delete.'
            }
            cache.set(f'{chat_id}_step', 2)
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
            return JsonResponse({'message': 'ID requested successfully'}, status=200)

        elif step == 2:
            cache.set(f'{chat_id}_id', text)
            try:
                product_id = int(cache.get(f'{chat_id}_id'))
                product = Product.objects.filter(pk=product_id)

                if product.exists():
                    product.delete()
                    response_data = {
                        'chat_id': chat_id,
                        'text': 'Product successfully deleted.'
                    }
                    requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                else:
                    response_data = {
                        'chat_id': chat_id,
                        'text': 'There is no product with this ID.'
                    }
                    requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)

                cache.delete_many([f'{chat_id}_id', f'{chat_id}_step'])
                return JsonResponse({'message': 'Product operation completed'}, status=200)
            except ValueError:
                response_data = {
                    'chat_id': chat_id,
                    'text': 'Invalid ID format. Please enter a numeric ID.'
                }
                requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                cache.delete_many([f'{chat_id}_id', f'{chat_id}_step'])
                return JsonResponse({'error': 'Invalid ID format'}, status=400)
            except Exception as e:
                response_data = {
                    'chat_id': chat_id,
                    'text': 'There was a problem with the models.'
                }
                requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                cache.delete_many([f'{chat_id}_id', f'{chat_id}_step'])
                return JsonResponse({'error': str(e)}, status=500)

        response_data = {
            'chat_id': chat_id,
            'text': 'Unknown command or process already completed.'
        }
        requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
        cache.delete_many([f'{chat_id}_id', f'{chat_id}_step'])
        return JsonResponse({'message': 'Unknown command or process completed'}, status=400)


class ProductListView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        chat_id = data.get('message').get('chat').get('id')

        products = Product.objects.filter(is_active=True)

        if not products.exists():
            response_data = {
                'chat_id': chat_id,
                'text': 'No products available at the moment.'
            }
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
            return JsonResponse({'message': 'No products available'}, status=200)

        for product in products:
            photo_data = {
                'chat_id': chat_id,
                'photo': product.image,
                'caption': f"Id: {product.id}\nName: {product.name}\nDescription: {product.description}\nPrice: {product.price}UAH"
            }
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendPhoto', data=photo_data)

        return JsonResponse({'message': 'Products sent successfully'}, status=200)