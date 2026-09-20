from django.db import models
from django.conf import settings
from users.models import Funcionario

# Entidade "Projeto" do diagrama
class Projeto(models.Model):
    # Relação 'organiza' (1, 1): cada projeto pertence a um único PO responsável
    usuario_po = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='projetos'
    )
    nome = models.CharField(max_length=255)
    descricao = models.TextField()
    
    # Relação 'participa' (1, n): vários funcionários alocados no mesmo projeto
    funcionarios = models.ManyToManyField(Funcionario, related_name='projetos', blank=True)

    class Status(models.TextChoices):
        RASCUNHO = "Rascunho", "Rascunho"
        INATIVO = "Inativo", "Inativo"
        ATIVO = "Ativo", "Ativo"

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RASCUNHO)

    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


# Entidade "Documento" do diagrama
class Documento(models.Model):
    # Relação 'possui' (1, 1): cada documento pertence obrigatoriamente a um Projeto
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='documentos')
    nome = models.CharField(max_length=255)
    tipo = models.CharField(max_length=50)  # ex: pdf, txt, docx
    data = models.DateTimeField(auto_now_add=True)  # grava automaticamente a data de upload

    def __str__(self):
        return self.nome
    