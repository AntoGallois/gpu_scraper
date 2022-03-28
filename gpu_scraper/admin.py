from django.contrib import admin
from django.forms import inlineformset_factory
from .models import *

class GPUListAdmin(admin.ModelAdmin):
    list_display = ('model', 'marketplace') 
    list_filter = ('model__brand__manufacturer', 'model__category__chipset','marketplace')  
 
class GPUTypeAdmin(admin.ModelAdmin):
    list_display = ('product_name','category','brand','memory_size')
    list_filter = ('category', 'brand')
class PriceListAdmin(admin.ModelAdmin):
    # list_display = ('gpu','price_date','price') 
    list_display = ('get_gpuModel','get_gpuMarketplace','price_date','price')
    list_filter = ('price_date','gpu__model__brand__manufacturer','gpu__model__category__chipset','gpu__marketplace')

    @admin.display(description='GPU Model',ordering='gpu__model')
    def get_gpuModel(self, obj):
        return obj.gpu.model
    @admin.display(description='Marketplace', ordering='gpu__marketplace')
    def get_gpuMarketplace(self, obj):
        return obj.gpu.marketplace


admin.site.register(GPUManufacturer)
admin.site.register(GPUChipset)
admin.site.register(GPUType, GPUTypeAdmin)
admin.site.register(MarketPlace)
admin.site.register(GPUList, GPUListAdmin)
admin.site.register(PriceList, PriceListAdmin)