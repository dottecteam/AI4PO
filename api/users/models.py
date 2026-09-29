from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UsuarioPOManager(BaseUserManager):
    # Django exige um manager customizado quando o User não usa "username".
    def create_user(self, email, nome, password=None):
        if not email:
            raise ValueError("O e-mail é obrigatório.")

        user = self.model(
            email=self.normalize_email(email),
            nome=nome
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, nome, password=None):
        user = self.create_user(email, nome, password)

        user.is_staff = True
        user.is_superuser = True

        user.save(using=self._db)

        return user


class UsuarioPO(AbstractBaseUser, PermissionsMixin):
    id_po = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UsuarioPOManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nome"]

    def __str__(self):
        return self.email


class Competencia(models.Model):
    nome = models.CharField(max_length=150)

    def __str__(self):
        return self.nome


class Funcionario(models.Model):
    nome = models.CharField(max_length=255)
    email = models.EmailField(unique=True)

    competencias = models.ManyToManyField(
        Competencia,
        related_name="funcionarios"
    )

    def __str__(self):
        return self.nome