from django.db import models
from productapp.models import Product
from usersapp.models import userka


class Order(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('canceled', 'Canceled'),
    ]

    user = models.ForeignKey(userka, on_delete=models.CASCADE, related_name='orders')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    order_date = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    PAYMENT_CHOICES = [
        ('cash', 'Cash on Delivery'),
        ('card', 'Credit/Debit Card'),
        ('wallet', 'Mobile Wallet (E-Dahab/Zaad)'),
    ]

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='cash')

    def __str__(self):
        return f'Order #{self.id} - {self.user.username}'

    def save(self, *args, **kwargs):
        if not self.email:
            self.email = self.user.email if self.user.email else 'bananka@mail.com'
        if not self.address:
            self.address = self.user.address if self.user.address else 'No Address '
        if not self.phone_number:
            self.phone_number = self.user.phone_number if self.user.phone_number else '0000000000'
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-order_date']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_at_order = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.quantity} x {self.product.name} (Order #{self.order.id})'

    def get_total_price(self):
        if self.quantity and self.price_at_order:
            return self.quantity * self.price_at_order
        return 0

    def save(self, *args, **kwargs):
        if not self.price_at_order:
            self.price_at_order = self.product.price
        super().save(*args, **kwargs)
