from django.db import models
from projects.models import Projeto

# Entidade "Epico" do diagrama
class Epico(models.Model):
    # Relação 'possui' (1, 1): cada épico pertence a um Projeto
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='epicos')
    titulo = models.CharField(max_length=255)
    descricao = models.TextField()
    objetivo = models.TextField()
    escopo_macro = models.TextField()
    resultado = models.TextField()
    criterios_de_aceitacao = models.TextField()

    def __str__(self):
        return self.titulo


# Entidade "Feature" do diagrama
class Feature(models.Model):
    # Relação 'possui' (1, 1): cada feature pertence a um Épico
    epico = models.ForeignKey(Epico, on_delete=models.CASCADE, related_name='features')
    titulo = models.CharField(max_length=255)
    descricao = models.TextField()
    objetivo = models.TextField()
    criterios_de_aceitacao = models.TextField()

    def __str__(self):
        return self.titulo


# Entidade "PBI" do diagrama
class PBI(models.Model):
    # Relação 'possui' (1, 1): cada item de backlog (PBI) pertence a uma Feature
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name='pbis')
    titulo = models.CharField(max_length=255)
    user_story = models.TextField()
    criterio_de_aceitacao = models.TextField()
    regras_observacoes = models.TextField()

    def __str__(self):
        return self.titulo