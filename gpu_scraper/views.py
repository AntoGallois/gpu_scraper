import operator
import json
from pickle import GET
from django.shortcuts import render
from django.shortcuts import HttpResponse

from .models import *

import datetime

# Create your views here.
def index(request):
    template_name = 'gpu_scraper/graph.html'
    range_values = [7,-1]
    today = datetime.date.today()
    GETlist = request.GET

    data = {
        'labels': [
            (today - datetime.timedelta(days=x)).strftime("%d/%m")
            for x in range(range_values[0], range_values[1], -1)
        ],
        'datasets': get_label_list(request.GET.get('filter') or 'chipset', GETlist, today, range_values[0], range_values[1]),
    }

    context = {
        'chipsets': list(GPUChipset.objects.all().values()),
        'manufacturers': list(GPUManufacturer.objects.all().values()),
        'data': json.dumps(data),
        'GETlist': dict(GETlist),
    }
    return render(request, template_name, context)

def data_to_display(items_list, first_day, latest_day, today_date, item, item_to_retrieve):
    gpu_data = []
    for x in range(first_day, latest_day, -1) :
        gpu_by_day = [gpu for gpu in items_list if gpu['price_date']==(today_date - datetime.timedelta(days=x))]
        gpu_by_day = list(map(operator.itemgetter('price'), gpu_by_day))
        gpu_data.append(sum(gpu_by_day)/len(gpu_by_day) if gpu_by_day else None)

    return ({
            'label':item[item_to_retrieve],
            'backgroundColor': 'black',
            'borderColor': 'grey',
            'data':gpu_data,
        })

def get_label_list(item_to_retrieve, GETList, today, min_date, max_date):
    data = []
    if item_to_retrieve == 'chipset':
        # Retrieve avg price of selected chipsets
        # or of all chipsets at load or if none selected
        item_list = (list(GPUChipset.objects.filter(chipset__in=GETList.getlist('chipset')).values()) 
            if GETList.getlist('chipset')
            else list(GPUChipset.objects.all().values()))
    elif item_to_retrieve == 'mp_name':
        item_list = list(MarketPlace.objects.all().values())
    elif item_to_retrieve == 'manufacturer':
        item_list = list(GPUManufacturer.objects.all().values())
    
    for item in item_list:
        if item_to_retrieve == 'chipset':
            gpu_list = PriceList.objects.filter(gpu__model__category__chipset=item['chipset'], price_date__gte=(today - datetime.timedelta(days=min_date)))
        elif item_to_retrieve == 'mp_name':
            gpu_list = PriceList.objects.filter(gpu__marketplace__mp_name=item['mp_name'], price_date__gte=(today - datetime.timedelta(days=min_date)))
        elif item_to_retrieve == 'manufacturer':
            gpu_list = PriceList.objects.filter(gpu__model__brand__manufacturer=item['manufacturer'], price_date__gte=(today - datetime.timedelta(days=min_date)))
        
        if GETList.getlist('manufacturer'):
            gpu_list = gpu_list.filter(gpu__model__brand__manufacturer__in=GETList.getlist('manufacturer'))
        if GETList.getlist('chipset'):
            gpu_list = gpu_list.filter(gpu__model__category__chipset__in=GETList.getlist('chipset'))
        gpu_list = list(gpu_list.values())
        
        data.append(data_to_display(gpu_list, min_date, max_date, today, item, item_to_retrieve))
    return data