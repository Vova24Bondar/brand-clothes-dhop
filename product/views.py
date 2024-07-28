from django.http import JsonResponse
import json
import requests
from product.models import Product
from django.core.cache import cache
from django.views import View
from django.utils.decorators import method_decorator
from product.decorators import admin_only
from django.conf import settings
from product.decorators import apply_class_decorator

@apply_class_decorator(admin_only)
class ProductCreateView(View):
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
                'text': f'Будь ласка, відправте одну фотграфію вашого товару.(не натискайте на іншу команду поки не завершите виконання цієї)'
            }
            cache.set(f'{chat_id}_step', 2)
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
            return JsonResponse({'message': 'Image requested successfully'})

        elif step == 2:
            if 'photo' in data.get('message') and len(photo) <= 4:
                try:
                    file_id = data['message']['photo'][-1]['file_id']
                    cache.set(f'{chat_id}_image', file_id)
                    response_data = {
                        'chat_id': chat_id,
                        'text': f'Будь ласка, введіть назву товару(не натискайте на іншу команду поки не завершите виконання цієї)'
                    }
                    cache.set(f'{chat_id}_step', 3)
                    requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                    return JsonResponse({'message': 'Name requested successfully'})
                except Exception as e:
                    response_data = {
                        'chat_id': chat_id,
                        'text': f'Будь ласка, відправте ОДНУ фотографію товару(не натискайте на іншу команду поки не завершите виконання цієї)'
                    }
                    requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                    cache.set(f'{chat_id}_step', 1)
                    cache.delete_many([f'{chat_id}_image'])
                    return JsonResponse({'error': str(e)})
            else:
                response_data = {
                    'chat_id': chat_id,
                    'text': f'Невірний ввід. Будь ласка, відправте фотографію для свого товару.(не натискайте на іншу команду поки не завершите виконання цієї)'
                }
                requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                cache.set(f'{chat_id}_step', 1)
                cache.delete_many([f'{chat_id}_image'])
                return JsonResponse({'error': 'Image not provided'})

        elif step == 3:
            cache.set(f'{chat_id}_name', text)
            response_data = {
                'chat_id': chat_id,
                'text': f'Будь ласка, введіть опис товару.(не натискайте на іншу команду поки не завершите виконання цієї)'
            }
            cache.set(f'{chat_id}_step', 4)
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
            return JsonResponse({'message': 'Description requested successfully'})

        elif step == 4:
            cache.set(f'{chat_id}_description', text)
            response_data = {
                'chat_id': chat_id,
                'text': f'Будь ласка, введіть кількість товару у наявності.(не натискайте на іншу команду поки не завершите виконання цієї)'
            }
            cache.set(f'{chat_id}_step', 5)
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
            return JsonResponse({'message': 'number_of_goods requested successfully'})

        elif step == 5:
            cache.set(f'{chat_id}_number_of_goods', text)
            response_data = {
                'chat_id': chat_id,
                'text': f'Будь ласка, введіть ціну для свого продукта.(не натискайте на іншу команду поки не завершите виконання цієї)'
            }
            cache.set(f'{chat_id}_step', 6)
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
            return JsonResponse({'message': 'Price requested successfully'})

        elif step == 6:
            try:
                price = int(text)
                cache.set(f'{chat_id}_price', price)
                image = cache.get(f'{chat_id}_image')
                name = cache.get(f'{chat_id}_name')
                description = cache.get(f'{chat_id}_description')
                int_price = cache.get(f'{chat_id}_price')
                number_of_goods = cache.get(f'{chat_id}_number_of_goods')
            except ValueError:
                response_data = {
                    'chat_id': chat_id,
                    'text': f'Невірний ввід. Будь ласка, в наступний раз введіть валідну циформу ціну(не натискайте на іншу команду поки не завершите виконання цієї)'
                }
                requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                cache.delete_many(
                    [f'{chat_id}_image', f'{chat_id}_name', f'{chat_id}_description', f'{chat_id}_price',
                     f'{chat_id}_step', f'{chat_id}_number_of_goods'])
                return JsonResponse({'error': 'Invalid price'})

            try:
                product = Product.objects.create(
                    image=image,
                    name=name,
                    description=description,
                    price=int_price,
                    number_of_goods=number_of_goods
                )
                photo_data = {
                    'chat_id': chat_id,
                    'photo': image,
                    'caption': f"Id: {product.id}\nName: {name}\nDescription: {description}\nNumber of goods: {number_of_goods}\nPrice: {price}UAH"
                }
                requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendPhoto', data=photo_data)
                cache.delete_many(
                    [f'{chat_id}_image', f'{chat_id}_name', f'{chat_id}_description', f'{chat_id}_price',
                     f'{chat_id}_step', f'{chat_id}_number_of_goods'])
                return JsonResponse({'message': 'Product created successfully'}, status=201)

            except Exception as e:
                response_data = {
                    'chat_id': chat_id,
                    'text': 'Будь ласка, надішліть лише одну фотографію'
                }
                requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                cache.delete_many(
                    [f'{chat_id}_image', f'{chat_id}_name', f'{chat_id}_description', f'{chat_id}_price',
                     f'{chat_id}_step', f'{chat_id}_number_of_goods'])
                return JsonResponse({'error': str(e)})


@apply_class_decorator(admin_only)
class ProductUpdateView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        chat_id = data.get('message', {}).get('chat', {}).get('id')
        text = data.get('message', {}).get('text', '')
        user_data = data.get('message', {}).get('from', {})
        username = user_data.get('username')

        step = cache.get(f'{chat_id}_step', 1)

        if step == 1:
            response_data = {
                'chat_id': chat_id,
                'text': f"Буль ласка, введіть ID товару який ви хочете змінити(не натискайте на іншу команду поки не завершите виконання цієї)"
            }
            cache.set(f'{chat_id}_step', 2)
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
            return JsonResponse({'message': 'request created successfully'}, status=200)

        elif step == 2:
            cache.set(f'{chat_id}_product_id', text)
            response_data = {
                'chat_id': chat_id,
                'text': ("Буль ласка, введіть поле яке ви хочете змінити.\n"
                         "'image'(фотографія товару)\n"
                         "'name'(назва товару)\n"
                         "'description'(опис товару)\n"
                         "'price'(ціна товару)\n"
                         "'number_of_goods'(кількість товару в наявності)\n"
                         "Відправляйте так як вказано в прикладах, але без лапок")
            }
            cache.set(f'{chat_id}_step', 3)
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
            return JsonResponse({'message': 'request created successfully'})

        elif step == 3:
            cache.set(f'{chat_id}_update_field', text)
            response_data = {
                'chat_id': chat_id,
                'text': f"Буль ласка, відправте нове значення для поля {text}(не натискайте на іншу команду поки не завершите виконання цієї)"
            }
            cache.set(f'{chat_id}_step', 4)
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
            return JsonResponse({'message': 'request created successfully'})

        elif step == 4:
            product_id = cache.get(f'{chat_id}_product_id')
            update_field = cache.get(f'{chat_id}_update_field')

            if update_field == 'image':
                if 'photo' in data.get('message', {}):
                    try:
                        file_id = data['message']['photo'][-1]['file_id']
                        update_value = file_id
                    except Exception as e:
                        response_data = {
                            'chat_id': chat_id,
                            'text': 'Сталася помилка під час обробки фотографії. Спробуйте ще раз.'
                        }
                        requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                        cache.set(f'{chat_id}_step', 3)
                        return JsonResponse({'error': str(e)})
                else:
                    response_data = {
                        'chat_id': chat_id,
                        'text': 'Будь ласка, в наступний раз відправте ФОТОГРАФІЮ для поля image.'
                    }
                    requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                    cache.delete_many([f'{chat_id}_step', f'{chat_id}_product_id', f'{chat_id}_update_field'])
                    return JsonResponse({'error': 'No photo provided'})
            else:
                update_value = text

            try:
                Product.objects.filter(pk=product_id).update(**{update_field: update_value})

                response_data = {
                    'chat_id': chat_id,
                    'text': f"Поле {update_field} успішно оновлене"
                }
                requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                cache.delete_many([f'{chat_id}_step', f'{chat_id}_product_id', f'{chat_id}_update_field'])
                return JsonResponse({'message': 'Product updated successfully'})

            except ValueError:
                response_data = {
                    'chat_id': chat_id,
                    'text': "Сталася помилка під час оновлення продукту. Спробуйте ще раз."
                }
                requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                return JsonResponse({'error': 'Invalid input value'})

            except Exception as e:
                response_data = {
                    'chat_id': chat_id,
                    'text': "Сталася помилка під час оновлення продукту. Спробуйте ще раз."
                }
                requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                return JsonResponse({'error': str(e)})

        else:
            response_data = {
                'chat_id': chat_id,
                'text': 'Невідома команді. Будь ласка, спробуйте ще раз.'
            }
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
            return JsonResponse({'error': 'Unknown command'})


@apply_class_decorator(admin_only)
class ProductDeleteView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        chat_id = data.get('message', {}).get('chat', {}).get('id')
        text = data.get('message', {}).get('text', '')
        step = cache.get(f'{chat_id}_step', 1)

        if step == 1:
            response_data = {
                'chat_id': chat_id,
                'text': f'Будь ласка, введіть ID товару який ви хочете оновити.(не натискайте на іншу команду поки не завершите виконання цієї)'
            }
            cache.set(f'{chat_id}_step', 2)
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
            return JsonResponse({'message': 'ID requested successfully'})

        elif step == 2:
            cache.set(f'{chat_id}_id', text)
            try:
                product_id = int(cache.get(f'{chat_id}_id'))
                product = Product.objects.filter(pk=product_id)

                if product.exists():
                    product.delete()
                    response_data = {
                        'chat_id': chat_id,
                        'text': 'Товар успішно видалений'
                    }
                    requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                else:
                    response_data = {
                        'chat_id': chat_id,
                        'text': 'Товар з таким ID відсутній'
                    }
                    requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)

                cache.delete_many([f'{chat_id}_id', f'{chat_id}_step'])
                return JsonResponse({'message': 'Product operation completed'}, status=200)
            except ValueError:
                response_data = {
                    'chat_id': chat_id,
                    'text': 'Невірний формат ID. Будь ласка, введіть вірний числовий формат ID'
                }
                requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                cache.delete_many([f'{chat_id}_id', f'{chat_id}_step'])
                return JsonResponse({'error': 'Invalid ID format'})
            except Exception as e:
                response_data = {
                    'chat_id': chat_id,
                    'text': 'There was a problem with the models.'
                }
                requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
                cache.delete_many([f'{chat_id}_id', f'{chat_id}_step'])
                return JsonResponse({'error': str(e)})

        response_data = {
            'chat_id': chat_id,
            'text': 'Невідома команда, або процес вже завершений'
        }
        requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
        cache.delete_many([f'{chat_id}_id', f'{chat_id}_step'])
        return JsonResponse({'message': 'Unknown command or process completed'})


class ProductListView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        chat_id = data.get('message').get('chat').get('id')

        products = Product.objects.filter(is_active=True)

        if not products.exists():
            response_data = {
                'chat_id': chat_id,
                'text': 'Наразі, немає товарів у наявності.'
            }
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendMessage', json=response_data)
            return JsonResponse({'message': 'No products available'})

        for product in products:
            photo_data = {
                'chat_id': chat_id,
                'photo': product.image,
                'caption': f"ID: {product.id}\nName: {product.name}\nDescription: {product.description}\nNumber of goods: {product.number_of_goods}\nPrice: {product.price}UAH",
                'reply_markup': json.dumps({
                    'inline_keyboard': [[{
                        'text': 'Купити товар',
                        'callback_data': f'buy_{product.id}'
                    }]]
                })
            }
            requests.post(f'{settings.TG_BASE_URL}{settings.BOT_TOKEN}/sendPhoto', data=photo_data)

        return JsonResponse({'message': 'Products sent successfully'})