from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import UserManager

class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # Ensure the role is set to 'Admin' for superusers
        extra_fields.setdefault('role', 'Admin')

        # Call the parent class's create_superuser to handle the creation of the superuser
        return super().create_superuser(username, email, password, **extra_fields)

class User(AbstractUser):
    ROLE_CHOICES = [
        ('Basic User', 'Basic User'),
        ('Seller', 'Seller'),
        ('Admin', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Basic User')
    
    
    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        # Check if the role is 'admin'
        if self.role == 'Admin':
            # Grant superuser permissions to the associated user
            self.is_superuser = True
            self.is_staff = True  # If you want to grant staff access as well
        else:
            # Revoke superuser permissions if the role is not 'Admin'
            self.is_superuser = False
            self.is_staff = False  # Remove staff access for non-admins
            self.is_active=True

        super().save(*args, **kwargs)


    class Meta:
        verbose_name="User"
        verbose_name_plural="Users"
        
    def __str__(self):
        return self.username 