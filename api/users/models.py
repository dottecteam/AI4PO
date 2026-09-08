from django.db import models

# Create your models here.
class User(models.Model):
    nome = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    # Continuar