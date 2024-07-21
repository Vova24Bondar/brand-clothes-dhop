from django.db import models


class Purchase(models.Model):
    user_id = models.ForeignKey(
        'user.User',
        on_delete=models.SET_NULL,
        related_name='user_id',
        null=True
    )
    product_id = models.ForeignKey(
        'product.Product',
        on_delete=models.SET_NULL,
        related_name='product_id',
        null=True
    )
    quantity = models.IntegerField(null=False)
    purchase_date = models.DateTimeField(auto_now_add=True)
    is_done = models.BooleanField(default=False)