# Generated by Django 5.0.7 on 2024-07-21 11:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0006_purchase_delete_productuser'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Purchase',
        ),
    ]
