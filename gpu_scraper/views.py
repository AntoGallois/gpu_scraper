import operator
import json
from pickle import GET
from django.shortcuts import render
from django.shortcuts import HttpResponse

from .models import *

import datetime

today = datetime.date.today()
one_week = datetime.timedelta(weeks=1)

#Add 1 week if wednesday or more
if today.isoweekday()>=3:
    today = today + one_week

last_weekday = today - datetime.timedelta(today.isoweekday())



# Create your views here.
def index(request):
    template_name = 'gpu_scraper/graph.html'
    range_values = [7,-1]
    GETlist = request.GET

    page_filter = GETlist.get('filter')
    chipset_choice = GETlist.getlist('chipset')
    manufact_choice = GETlist.getlist('manufacturer')
    data = display_all_by_chipset(page_filter, chipset_choice, manufact_choice)

    context = {
        'chipsets': list(GPUChipset.objects.all().values()),
        'manufacturers': list(GPUManufacturer.objects.all().values()),
        'data': json.dumps(data),
        'GETlist': dict(GETlist),
    }
    return render(request, template_name, context)

def display_all_by_chipset(filter, chipset_choice, manufact_choice):
    choice_opts= {
        'chipset': {
            'main_filter': 'gpu__model__category__chipset',
            'list': list(GPUChipset.objects.all().values()),
            },
        'manufacturer': {
            'main_filter': 'gpu__model__brand__manufacturer',
            'list': list(GPUManufacturer.objects.all().values()),
            },
        'mp_name': {
            'main_filter': 'gpu__marketplace__mp_name',
            'list': list(MarketPlace.objects.all().values()),
            },
        'additional_opts':{}
    }
    if chipset_choice:
        choice_opts['additional_opts']['gpu__model__category__chipset__in'] = chipset_choice
    if manufact_choice:
        choice_opts['additional_opts']['gpu__model__brand__manufacturer__in'] = manufact_choice

    choice_list = choice_opts[filter or 'chipset']['list']

    dataset = []
    for choice in choice_list:
        main_filter = {choice_opts[filter or 'chipset']['main_filter']: choice[filter or 'chipset']}
        chip_prices = []
        for week_n in range(7,-1,-1):
            gpu_list = list(PriceList.objects.filter(**main_filter, **choice_opts['additional_opts'], price_date__gt=last_weekday-(one_week*(week_n+1)), price_date__lte=last_weekday-(week_n*one_week)))
            chip_prices.append(sum(gpu.price for gpu in gpu_list) / len(gpu_list) if gpu_list else None)

        if check_if_not_all_none(chip_prices):
            dataset.append({
                'label':choice[filter or 'chipset'],
                'backgroundColor': 'grey' if 'Radeon' in choice[filter or 'chipset'] else 'black',
                'borderColor': 'red' if 'Radeon' in choice[filter or 'chipset'] else 'green',
                'data':chip_prices,
                'borderWidth':3,
            })

    return {'labels': create_graph_labels(), 'datasets': dataset,}

def check_if_not_all_none(list_of_elem):
    """ Check if all elements in list are None """
    result = False
    return next((True for elem in list_of_elem if elem is not None), result)

def create_graph_labels():
    last_saturday = last_weekday - datetime.timedelta(days=1)
    labels = [(last_saturday - x*one_week).strftime("%d/%m") for x in  range(7,-1,-1)]
    if today.isoweekday()<7:
        labels[-1] = (last_saturday-datetime.timedelta(days=3)).strftime("%d/%m")
    return labels
    