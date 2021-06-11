from datetime import datetime
from django.shortcuts import render, redirect
from django.conf import settings
from django import forms
from django.db.models import Sum
from django.db import connection
from django.template import loader


from abc import *

from .models import *


class report_template(metaclass = ABCMeta):

    def __init__(self):
        if not hasattr(self,'extra'):
            self.extra = []
        if not hasattr(self,'report_name'):
            self.report_name = 'report'

        for h in self.header:
            if 'label' not in h:
                h['label'] = h['field']

    def make_table(self, data):

        def do_format(a):
            if type(a) == datetime.datetime:
                a = datetime.datetime.strftime(a, '%d.%m.%Y %H:%M')
            return a

        t_data = []  # формируем двумерный массив в порядке следования заголовка таблици
        for row in data:  # txt - текст ячейки таблици, rs - ROWSPAN
            f = []
            tmp = {}
            for c in self.header:
                r = row[c['field']]

                if type(r) != list:
                    f.append({'txt': do_format(r), 'rs': 'x'})
                else:
                    f.append({'txt': do_format(r[0]) if len(r) > 0 else '', 'rs': 0})
                    tmp[c['field']] = [do_format(i) for i in r[1:]]

            t_data.append(f)
            k = list(tmp.keys())
            if len(k) > 0:
                rs = len(tmp[k[0]])  # ROWSPAN
                for i in f:
                    i['rs'] = rs + 1 if i['rs'] == 'x' else 0
                for i in range(0, rs):
                    t_data.append([{'txt': tmp[s][i], 'rs': 0} for s in k])

        return t_data

    def make_report(self, p):
        tbl = self.make_table(self.process_report(p))
        self.extra.append({'val':len(connection.queries), 'label':'Выполнено запросов к базе'})
        return loader.render_to_string('report_template.html', {'data': tbl,
                                                                'extra':self.extra,
                                                                'header': self.header,
                                                                })

    @abstractmethod
    def process_report(self,p):
        return

class input_form(forms.Form):
    start_data = forms.DateField(required = False, label='С:', input_formats=['%d.%m.%Y','%d-%m-%Y'])
    end_data   = forms.DateField(required = False, label='ПО:',input_formats=['%d.%m.%Y','%d-%m-%Y'] )


class report1(report_template):
    rForm = input_form
    report_name = 'Отчет №1'
    header = [{'field': 'created_date', 'label':'Дата и время'},
              {'field': 'number',       'label':'Номер заказа'},
              {'field': 'total',        'label':'Сумма'},
              {'field': 'products',     'label':'Товары'}]

    def process_report(self,p):

        flt = {}
        if p['start_data'] != None:
            flt['created_date__gt'] = p['start_data']
        if p['end_data'] != None:
            flt['created_date__lt'] = p['end_data']

        rq = Order.objects.filter(**flt).annotate(total=Sum('orderitem__product_price')).prefetch_related('orderitem_set').all()
        res = []
        for i in rq:
            row = forms.model_to_dict(i, exclude=['id'])
            row['total'] = i.total
            row['products'] = ['%s x %s шт.' % (j.product_name, j.amount) for j in i.orderitem_set.all()]
            res.append(row)
        return res

class report2(report_template):
    rForm = input_form
    report_name = 'Отчет №2'
    header = [{'field': 'product_name', 'label':'Имя товара'},
              {'field': 'number',       'label':'Номер заказа'},
              {'field': 'product_price','label':'Цена'},
              {'field': 'created_date', 'label':'Дата'}]

    def process_report(self,p):
        tmp = OrderItem.objects.values('product_name').annotate(total=Sum('amount')).order_by('-total')[:1][0]
        self.extra.append({'val':tmp['product_name'], 'label':'Топ продаж за все время, продано %s единиц' % tmp['total']})

        flt = {}
        if p['start_data'] != None:
            flt['order__created_date__gt'] = p['start_data']
        if p['end_data'] != None:
            flt['order__created_date__lt'] = p['end_data']
        rq1 = OrderItem.objects.filter(**flt).values('product_name').annotate(total = Sum('amount')).order_by('-total')[:20]

        flt['product_name__in'] = [i['product_name'] for i in rq1]

        rq2 = OrderItem.objects.filter(**flt).values('product_name', 'order__number', 'product_price', 'order__created_date')

        res = []
        for i in rq1:
            row = {}
            row['product_name'] = i['product_name']
            row['number'] = []
            row['product_price'] = []
            row['created_date'] = []
            for j in rq2:
                if j['product_name'] != i['product_name']:
                    continue
                row['number'].append(j['order__number'])
                row['product_price'].append(j['product_price'])
                row['created_date'].append(j['order__created_date'])
            res.append(row)
        return res

def index(request):
    return redirect('/reports/0/')


def reports(request, rep_id):
    rep = [report1(), report2()]
    report_list = [{'ref':'/reports/%s' % i[0], 'label':i[1].report_name} for i in enumerate(rep)]
    view_data = ''
    current_report = rep[rep_id]
    if request.method == 'POST':
        form = current_report.rForm(request.POST)
        if form.is_valid():
            f_data = {}
            for i in form.fields:
                f_data[i] = form.cleaned_data[i]
            view_data = current_report.make_report(f_data)
    else:
        form = current_report.rForm()
    return render(request, 'reports_form.html', {'lang':settings.LANGUAGE_CODE,
                                                 'report_list':report_list,
                                                 'report_name':current_report.report_name,
                                                 'form':form,
                                                 'report': view_data})

