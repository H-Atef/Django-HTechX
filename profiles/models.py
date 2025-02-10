from django.db import models
from django.conf import settings

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    address= models.CharField(max_length=100, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    paypal_payment_email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    class Meta:
        verbose_name="Profile"
        verbose_name_plural="Profiles"