from django.contrib import admin
from .models import Product
from ordersapp.admin import OrderItemInline

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'quatentity', 'created_at', 'available')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    inlines = [OrderItemInline]

admin.site.register(Product, ProductAdmin)