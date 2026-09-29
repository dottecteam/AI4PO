from django.db import models
from projects.models import Projeto
from django.contrib.postgres.fields import ArrayField

# Entidade "Epico" do diagrama
class Epico(models.Model):
    # Relação 'possui' (1, 1): cada épico pertence a um Projeto
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='epicos')
    titulo = models.CharField(max_length=255)
    descricao = models.TextField()
    objetivo = models.TextField()
    escopo_macro = ArrayField(models.CharField(max_length=500), blank=True, default=list)
    resultado = models.TextField()
    criterios_de_aceitacao = ArrayField(models.CharField(max_length=500), blank=True, default=list)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo


# Entidade "Feature" do diagrama
class Feature(models.Model):
    # Relação 'possui' (1, 1): cada feature pertence a um Épico
    epico = models.ForeignKey(Epico, on_delete=models.CASCADE, related_name='features')
    titulo = models.CharField(max_length=255)
    descricao = models.TextField()
    objetivo = models.TextField()
    criterios_de_aceitacao = ArrayField(models.CharField(max_length=500), blank=True, default=list)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo


# Entidade "PBI" do diagrama
class PBI(models.Model):
    # Relação 'possui' (1, 1): cada item de backlog (PBI) pertence a uma Feature
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name='pbis')
    titulo = models.CharField(max_length=255)

    # userStory: COMO UM / EU QUERO / PARA QUE
    userstory_como = models.CharField(max_length=255)
    userstory_quero = models.TextField()
    userstory_paraque = models.TextField()

    criterio_de_aceitacao = models.TextField()
    regras_observacoes = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo
class Cenario(models.Model):
    # Relação 'possui' (1, 1): cada item de Cenário pertence a um PBI
    pbi = models.ForeignKey(PBI, on_delete=models.CASCADE, related_name='cenarios')
    dado = models.TextField()
    quando = models.TextField()
    entao = models.TextField()

    def __str__(self):
        return f"Cenário {self.ordem} de {self.pbi.titulo}"