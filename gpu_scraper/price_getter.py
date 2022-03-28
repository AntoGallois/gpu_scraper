from itertools import product
from bs4 import BeautifulSoup
import requests
import urllib3
import csv

def getMaterielPrices(marketplace_id:int, web_link:str) -> float:
    """
    MarketPlaces ID:
        1:Materiel.net
        2:Amazon
        ...
    """
    http = urllib3.PoolManager()
    html = http.request('GET', web_link)
    soup = BeautifulSoup(html.data, 'html.parser')

    #fetch price from Materiel.net website
    product_price = soup.find(id='c-product__id').find('span',{'class':'o-product__price'})
    
    #transform price from string to float
    return float(product_price.text.replace('€', '.'))

def getAmazon(marketplace_id:int, web_link:str) -> float:
    """
    MarketPlaces ID:
        1:Materiel.net
        2:Amazon
        ...
    """
    counter = 0
    t = 0
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.115 Safari/537.36"}

    html = requests.get(web_link, headers=headers)
    soup = BeautifulSoup(html.content, 'html.parser')
    print(soup.prettify)
    #fetch price from Materiel.net website   
    product_price = soup.find(id='corePrice_feature_div')
    if product_price is not None:
        #transform price from string to float
        t = product_price.get_text().strip().split('€')[0].replace(u"\u202f","").replace(",",".")

    return float(t)

def getRakuten(web_link:str) -> float:
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.115 Safari/537.36"}
    html = requests.get(web_link, headers=headers)
    soup = BeautifulSoup(html.content, 'html.parser')
    price_cont = soup.find('div',{'class':'v2_fpp_price'})
    if price_cont is None:
        price_cont = soup.find('p',{'class':'price'})
    #fetch price from Amazon.fr website   
    price = price_cont.get_text().split('€')[0].strip().replace(u"\xa0","").replace(",",".")
    #transform price from string to float
    return float(price)

def getMaterielPrices(web_link:str):
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.115 Safari/537.36"}
    html = requests.get(web_link, headers=headers)
    soup = BeautifulSoup(html.content, 'html.parser')
    links = soup.find_all('li',{'class':'c-products-list__item'})
    list = [
        [
            link.find('h2',{'class':'c-product__title'}).get_text().split(' ')[0],
            link.find('h2',{'class':'c-product__title'}).get_text(),
            'https://www.materiel.net'+link.find('a')['href'],
        ]
        for link in links
    ]

    with open('test.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerows(list)


def main():
    getAmazon(1,'https://www.amazon.fr/ASRock-Radeon-RX-6600-CLD/dp/B09J8VCFWN/ref=sr_1_1?__mk_fr_FR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&crid=1BIKBRJH8VH20&keywords=asrock+rx+6600&qid=1646505453&sprefix=asrock+rx6600%2Caps%2C86&sr=8-1')
    
if __name__=='__main__':
    main()