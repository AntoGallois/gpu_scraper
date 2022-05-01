#! ~/Documents/Django/djenv/bin/python

from itertools import product
from json import loads
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
        with open("test.log",  "a") as f:
            f.write(f"Started price fetching at {datetime.datetime.now().time()} on {datetime.date.today()}\n")
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
            
        amazon_gpu_list = getAmazonPrice()
        for gpulist_by_asin in amazon_gpu_list:
            try:
                if amazon_gpu_list[gpulist_by_asin] != 0:
                    new_gpu_price = PriceList(
                        gpu = gpulist_by_asin,
                        price = amazon_gpu_list[gpulist_by_asin],
                    )
                    new_gpu_price.save()
                    self.stdout.write(self.style.SUCCESS(f'{gpulist_by_asin.model} at {gpulist_by_asin.marketplace} successfully added!'))
                else:
                    self.stderr.write(self.style.ERROR(f'{gpulist_by_asin.model}: NO PRICE or Blocked with {gpulist_by_asin.marketplace}'))
            except urllib3.exceptions.MaxRetryError:
                self.stderr.write(self.style.ERROR(f'{gpulist_by_asin.model}: WRONG LINK'))
        with open("test.log",  "a") as f:
            f.write(f"  => Finished price fetching at {datetime.datetime.now().time()}\n")


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
    gpu_chipsets = [chipset[0] for chipset in list(GPUChipset.objects.values_list('chipset'))]
    gpu_list = {}
    url = "https://amazon-price1.p.rapidapi.com/search"

    headers = {
        "X-RapidAPI-Host": "amazon-price1.p.rapidapi.com",
        "X-RapidAPI-Key": "c788efc4ebmsh55254886f711d27p18b517jsn015b9c75f70f"
    }
    for chipset in gpu_chipsets:
        querystring = {"keywords":chipset,"marketplace":"FR"}

        response = requests.request("GET", url, headers=headers, params=querystring)
        gpu_dict = loads(response.text)
        gpu_list.update({
            GPUList.objects.filter(asin=gpu['ASIN'])[0]: float(gpu['price']
                .replace(u"\u202f", "")
                .replace(u"\xa0€", "")
                .replace(",", ".")) 
            for gpu in gpu_dict
            if GPUList.objects.filter(asin=gpu['ASIN'])
        })
    return gpu_list

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