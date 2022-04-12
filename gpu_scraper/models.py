from enum import unique
from django.db import models

class GPUManufacturer(models.Model):
    manufacturer = models.CharField(max_length=200, default='')
    def __str__(self) -> str:
        return self.manufacturer
    class Meta:
        ordering=['manufacturer']

class GPUChipset(models.Model):
    chipset = models.CharField(max_length=200, default='')
    def __str__(self) -> str:
        return self.chipset
    class Meta:
        ordering=['chipset']

class GPUType(models.Model):
    product_name = models.CharField(max_length=200, default='', unique=True)
    category = models.ForeignKey(GPUChipset, on_delete=models.CASCADE)
    brand = models.ForeignKey(GPUManufacturer, on_delete=models.CASCADE)
    memory_size = models.IntegerField(default=0)
    def __str__(self) -> str:
        return self.product_name
    class Meta:
        ordering=['product_name']

class MarketPlace(models.Model):
    mp_name = models.CharField(max_length=200, default='')
    def __str__(self) -> str:
        return self.mp_name

class GPUList(models.Model):
    model = models.ForeignKey(GPUType, on_delete=models.CASCADE)
    marketplace = models.ForeignKey(MarketPlace, on_delete=models.CASCADE)
    buy_link = models.CharField(max_length=300, default='')
    asin = models.CharField(max_length=50, default='')
    def __str__(self) -> str:
        return f'{self.model} - {self.marketplace}'
    class Meta:
        ordering=['model', 'marketplace']
        unique_together = [('model', 'marketplace')]

class PriceList(models.Model):
    gpu = models.ForeignKey(GPUList, on_delete=models.CASCADE)
    price_date = models.DateField(auto_now=True)
    price = models.FloatField(default=-1)
    def __str__(self) -> str:
        return f'{self.gpu} - {self.price_date} - {self.price}'
    class Meta:
        ordering=['-price_date', 'gpu']

