from django.db import models


class User(models.Model):
    first_name = models.CharField(max_length=20, null=False)
    last_name = models.CharField(max_length=20, null=False)
    username = models.CharField(max_length=30, null=False)
    password = models.CharField(max_length=50, null=False)
    is_admin = models.BooleanField(default=False)
    chat_id = models.CharField(max_length=20, null=False)