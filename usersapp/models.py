from operator import ge
from django.db import models

# Create your models here.

class userka(models.Model):
    gender_choices = [
        ('nin', 'Male'),
        ('naag', 'Female'),
    ]
    name = models.CharField(max_length=100,blank=False,null=False)
    profile_picture = models.ImageField(upload_to='static/user_profile', blank=True, null=True)
    email = models.EmailField(unique=True,blank=False,null=False)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    username = models.CharField(max_length=128,blank=False,null=False)
    password = models.CharField(max_length=128,blank=False,null=False)
    address = models.TextField(blank=True, null=True)
    gender = models.CharField(max_length=4, choices=gender_choices, blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name}'
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']


