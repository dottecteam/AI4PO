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
    objetivo = models.TextField()
    
    # Relação 'participa' (1, n): vários funcionários alocados no mesmo projeto
    funcionarios = models.ManyToManyField(Funcionario, related_name='projetos', blank=True)

    def __str__(self):
        return self.nome


# Entidade "Documento" do diagrama
class Documento(models.Model):
    # Relação 'possui' (1, 1): cada documento pertence obrigatoriamente a um Projeto
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='documentos')
    nome = models.CharField(max_length=255)
    tipo = models.CharField(max_length=50)  # ex: pdf, txt, docx
    # Registros criados antes da rota podem conter apenas os metadados. A rota
    # continua exigindo o arquivo por meio do DocumentoUploadSerializer.
    arquivo = models.FileField(upload_to='uploads/', max_length=255, blank=True)
    data = models.DateTimeField(auto_now_add=True)  # grava automaticamente a data de upload

    def __str__(self):
        return self.nome
