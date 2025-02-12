from django.db import models
from users.models import User
from django.utils import timezone

class Subscription(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Active", "Active"),
        ("Cancelled", "Cancelled"),
        ("Expired", "Expired"),
        ("Cancelled & Refunded","Cancelled & Refunded")
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="subscriptions")
    subscription_id = models.CharField(max_length=100, blank=True, null=True)
    session_id = models.CharField(max_length=255, blank=True, null=True)
    plan_id = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    start_date = models.DateTimeField()
    expiry_date = models.DateTimeField()
    refund_id = models.CharField(max_length=100, blank=True, null=True) 
    payment_token=models.CharField(max_length=50, blank=True, null=True)

 

    def __str__(self):
        return f"{self.user.username} - ({self.status})"
    
    class Meta:
        verbose_name="Subscription"
        verbose_name_plural="Subscriptions"
