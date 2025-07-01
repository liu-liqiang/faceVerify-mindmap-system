from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """扩展的用户模型"""
    email = models.EmailField(unique=True)
    avatar = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.username
