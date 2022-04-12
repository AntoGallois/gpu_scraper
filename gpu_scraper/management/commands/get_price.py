from itertools import product
from urllib import request
from django.core.management.base import BaseCommand, CommandError
from gpu_scraper.models import *
from bs4 import BeautifulSoup
import urllib3
import datetime
import re
import requests


import csv

class Command(BaseCommand):
    def handle(self, *args, **options):
        # getMaterielPrices()
            for gpu_item in GPUList.objects.all().exclude(marketplace__mp_name='Amazon.fr'):
                try:
                    gpu_price = getGPUPrices(gpu_item.marketplace_id, gpu_item.buy_link)
                    new_gpu_price = PriceList(
                        gpu = gpu_item,
                        price = gpu_price,
                    )
                    if gpu_price != 0:
                        new_gpu_price.save()
                        self.stdout.write(self.style.SUCCESS(f'{gpu_item.model} at {gpu_item.marketplace} successfully added!'))
                    else:
                        self.stderr.write(self.style.ERROR(f'{gpu_item.model}: NO PRICE or Blocked with {gpu_item.marketplace}'))
                except urllib3.exceptions.MaxRetryError:
                    self.stderr.write(self.style.ERROR(f'{gpu_item.model}: WRONG LINK'))

            for gpu_price_list in getAmazonPrice():
                try:
                    if gpu_price_list.price != 0:
                        gpu_price_list.save()
                        self.stdout.write(self.style.SUCCESS(f'{gpu_price_list.gpu.model} at {gpu_price_list.gpu.marketplace} successfully added!'))
                    else:
                        self.stderr.write(self.style.ERROR(f'{gpu_price_list.gpu.model}: NO PRICE or Blocked with {gpu_price_list.gpu.marketplace}'))
                except urllib3.exceptions.MaxRetryError:
                    self.stderr.write(self.style.ERROR(f'{gpu_price_list.gpu.model}: WRONG LINK'))


def getMaterielPrice(web_link:str):
    http = urllib3.PoolManager()
    html = http.request('GET', web_link)
    soup = BeautifulSoup(html.data, 'html.parser')
    try:
        price = soup.find(id='c-product__id').find('span',{'class':'o-product__price'}).text.replace('€', '.').replace(u"\xa0","")
        return float(price)
    except Exception:
        return 0

def getAmazonPrice():
    type_pages = [
        ['RTX 3080',1, 'https://www.amazon.fr/s?k=rtx+3080&i=computers&bbn=430340031&rh=n%3A340858031%2Cn%3A427941031%2Cn%3A17414956031%2Cn%3A430340031%2Cp_36%3A10000-&dc&page='],
        ['RTX 3080 Ti',1, 'https://www.amazon.fr/s?k=rtx+3080+Ti&i=computers&bbn=430340031&rh=n%3A430340031%2Cp_36%3A428411031&dc&page='],
        ['RTX 3090',1, 'https://www.amazon.fr/s?k=rtx+3090&i=computers&bbn=430340031&rh=n%3A430340031%2Cp_36%3A428411031&dc&page='],
        ['Radeon RX 6600',1, 'https://www.amazon.fr/s?k=rx+6600&i=computers&bbn=430340031&rh=n%3A430340031%2Cp_36%3A10000-&dc&page='],
        ['Radeon RX 6600 XT',1, 'https://www.amazon.fr/s?k=rx+6600+xt&rh=p_36%3A10000-&page='],
        ['Radeon RX 6700',1, 'https://www.amazon.fr/s?k=rx6700&rh=p_36%3A10000-'],
        ['Radeon RX 6700 XT',1, 'https://www.amazon.fr/s?k=rx6700+xt&rh=p_36%3A10000-&page='],
        ['Radeon RX 6800',1, 'https://www.amazon.fr/s?k=rx+6800&rh=p_36%3A10000-&page='],
        ['Radeon RX 6800 XT',1, 'https://www.amazon.fr/s?k=rx6800+xt&rh=p_36%3A10000-&page='],
        ['Radeon RX 6900 XT',1, 'https://www.amazon.fr/s?k=rx6900+xt&rh=p_36%3A10000-&page='],
    ]
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.115 Safari/537.36"}
    gpu_from_amazon = []

    for gpu_pages in type_pages:
        price_list = []
        for i in range(1,gpu_pages[1]+1):
            web_link = gpu_pages[2]+str(i)
            html = requests.get(web_link, headers=headers)
            soup = BeautifulSoup(html.content, 'html.parser')
            divs = soup.find('div', class_='s-main-slot')
            if not divs:
                break
            divs = divs.select('div[data-asin]')
            price_list.extend(
                [
                    div['data-asin'],
                    div.select_one('.a-price ')
                    .get_text('|', strip=True)
                    .split('|')[0]
                    .split('€')[0]
                    .replace(u"\u202f","")
                    .replace(u"\xa0","")
                    .replace(",","."),
                ]
                for div in divs
                if div['data-asin']
                and div.select_one('.a-price ')
            )

    gpu_from_amazon.extend(
        PriceList(
            gpu=gpu_db,
            price=gpu[1],
        )
        for gpu in price_list
        if (
            gpu_db := GPUList.objects.filter(
                asin=gpu[0], model__category__chipset=gpu_pages[0]
            )
        )
    )
    return gpu_from_amazon

def getRakutenPrice(web_link:str):
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.115 Safari/537.36"}
    html = requests.get(web_link, headers=headers)
    soup = BeautifulSoup(html.content, 'html.parser')
    price = 0
    
    # Get price if single vendor
    price_cont = soup.find('div',{'class':'v2_fpp_price'})
    if price_cont is None:
        # Get price if multiple vendors
        price_cont = soup.find('p',{'class':'price'})

    # handle possible problem
    if price_cont is not None:
        price = price_cont.get_text().split('€')[0].strip().replace(u"\xa0","").replace(",",".")

    #transform price from string to float
    return float(price)

def getGPUPrices(marketplace_id:int, web_link:str) -> float:
    """
    MarketPlaces ID:
        1:Materiel.net
        2:Amazon
        ...
    """
    marketplaces = {
        1:getMaterielPrice,
        2:getAmazonPrice,
        3:getRakutenPrice,
    }

    #transform price from string to float
    return marketplaces[marketplace_id](web_link)

def getMaterielPrices():
    with open('test.csv',newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for item in spamreader:
        # Save GPU type to database
            item[0]='ASUS' if item[0]=='Asus' else item[0]
            new_gpu_price = GPUType(
                    product_name = item[1],
                    category = GPUChipset.objects.get(chipset='RTX 3080'),
                    brand = GPUManufacturer.objects.get(manufacturer=item[0]),
                    memory_size = 10
                )
            new_gpu_price.save()

        # Save GPU link to the list of gpus
            new_gpu = GPUList(
                model = GPUType.objects.get(product_name=item[1]),
                marketplace = MarketPlace.objects.get(mp_name='Materiel.net'),
                buy_link=item[2],
            )
            new_gpu.save()