from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('price_at_order', 'get_total_price')
    
    def get_total_price(self, obj):
        return obj.get_total_price()
    get_total_price.short_description = 'Total'

class OrdersAppAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'email', 'total_price', 'status', 'order_date')
    list_filter = ('status', 'order_date')
    search_fields = ('user__username', 'user__email', 'id')
    ordering = ('-order_date',)
    inlines = [OrderItemInline]

admin.site.register(Order, OrdersAppAdmin)
admin.site.register(OrderItem) # Optional: allowing separate management if needed
