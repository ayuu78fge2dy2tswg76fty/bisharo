from django.db import models

# Create your models here.\

from catogories.models import Category

class Product(models.Model):
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='static/product_image', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quatentity = models.PositiveIntegerField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)
    available = models.BooleanField(default=True)
    

    def __str__(self):
        return f'{self.name} - {self.category.name}'

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
