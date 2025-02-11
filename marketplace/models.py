from django.db import models

class Product(models.Model):
    product_model = models.CharField(max_length=100,default="-")
    product_brand = models.CharField(max_length=100,default="-")
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    product_deal_price = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    product_stock = models.PositiveIntegerField(default=0)
    product_description = models.TextField(default="-")
    product_specifications = models.CharField(max_length=255,default="-")
    product_deal_link = models.URLField(blank=True, null=True)
    is_available=models.BooleanField(default=True)

    def __str__(self):
        return self.product_model
    
    class Meta:
        verbose_name="Product"
        verbose_name_plural="Products"