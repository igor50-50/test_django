from django.core.management.base import BaseCommand
from datetime import datetime
from django.utils.timezone import make_aware
from ...models import *
from django.db.models import Max
import random

val_or_default= lambda x,y : x if x != None else y
start_date = datetime.datetime.strptime('01.01.2018 09:00', '%d.%m.%Y %H:%M')

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('count', nargs=1, type=int) # задаем принимать аргумент "count"

    def handle(self, *args, **kwargs):
        max_number = val_or_default(Order.objects.aggregate(Max('number'))['number__max'], 0) + 1
        for i in range(max_number, max_number + kwargs['count'][0]):
            param = {'number'       :i,
                     'created_date' :make_aware(start_date + datetime.timedelta(hours=i)),}
            Order_obj = Order.objects.create(**param)
            Order_obj.save()

            for j in range(0, random.randint(1, 5)):    #заполнение таблтци "OrderItem"
                param = {'order'        : Order_obj,
                         'product_name' : 'Товар-%s' % random.randint(1, 100),
                         'product_price':  random.randint(100, 9999), # Заказщик не пожелал наполнять с плавающей точкой
                         'amount'       :  random.randint(1, 10),}
                OrderItem_obj = OrderItem.objects.create(**param)
                OrderItem_obj.save()

        self.stdout.write("Готово!")