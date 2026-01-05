from django.test import TestCase
from .models import Product
from catogories.models import Category

class ProductDetailTest(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Test Category")
        self.product = Product.objects.create(
            name="Test Product",
            price=10.00,
            quatentity=5,
            available=True,
            category=cat
        )

    def test_product_detail_view(self):
        # Using the original redundant prefix 'products/products/'
        response = self.client.get(f'/products/products/{self.product.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")
