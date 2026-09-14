from django.db import models
from django.contrib.auth.models import AbstractUser

# Entidade "Usuario (PO)" do diagrama: o PO que acessa a plataforma
class UsuarioPO(AbstractUser):
    # Herdando de AbstractUser, o Django já cria id, username, email, senha criptografada, etc.
    pass


# Entidade "Competência" do diagrama: habilidades técnicas da equipe
class Competencia(models.Model):
    nome = models.CharField(max_length=150)

    def __str__(self):
        return self.nome


# Entidade "Funcionário" do diagrama: membros do time
class Funcionario(models.Model):
    nome = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    
    # Relação 'possui' (1, n) entre Funcionário e Competência:
    # Um funcionário tem várias competências e uma competência pode pertencer a vários funcionários
    competencias = models.ManyToManyField(Competencia, related_name='funcionarios')

    def __str__(self):
        return self.nome
    