
#python manage.py makemigrations
#python manage.py migrate

from django.db import models
import datetime
from django.db.models import Max
from django.db.models.expressions import RawSQL

class Order(models.Model):
    number          = models.IntegerField()
    created_date    = models.DateTimeField()

class OrderItem(models.Model):
    order           = models.ForeignKey(Order, on_delete=models.CASCADE)
    product_name    = models.CharField(max_length=255)
    product_price   = models.DecimalField(max_digits=8, decimal_places=2)
    amount          = models.IntegerField()




