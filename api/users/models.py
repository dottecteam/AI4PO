from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    # Django exige um manager customizado quando o User não usa "username".
    def create_user(self, email, nome, password=None):
        if not email:
            raise ValueError("O e-mail é obrigatório.")
        user = self.model(email=self.normalize_email(email), nome=nome)
        user.set_password(password)  # aplica o hash, nunca salva texto puro
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nome, password=None):
        # usado pelo "python manage.py createsuperuser"
        user = self.create_user(email, nome, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    # AbstractBaseUser já traz o campo "password" (com hash) e o suporte a authenticate().
    # PermissionsMixin traz is_superuser/permissions, exigido pelo admin do Django.
    id_po = models.AutoField(primary_key=True)  # bate com "IdPO" do diagrama ER
    nome = models.CharField(max_length=100)
    email = models.CharField(max_length=100, unique=True)  # unique = obrigatório p/ login funcionar
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # necessário p/ acessar o /admin

    objects = UserManager()

    USERNAME_FIELD = "email"  # diz ao Django: login é por e-mail, não username
    REQUIRED_FIELDS = ["nome"]

    def __str__(self):
        return self.email