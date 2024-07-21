from django.db import models


class Product(models.Model):
    image = models.CharField(max_length=255)
    name = models.CharField(max_length=2000, null=False)
    description = models.CharField(max_length=2000, null=False)
    price = models.IntegerField(null=False)
    sold_by = models.ForeignKey(
        'user.User',
        on_delete=models.SET_NULL,
        related_name='product_sold_by',
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    is_active = models.BooleanField(default=True)
    number_of_goods = models.IntegerField(null=True)