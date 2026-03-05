from django.db import models
from django.contrib.auth.models import User

class Transacao(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
    ]

    CATEGORIA_CHOICES = [
        ('alimentacao', 'Alimentação'),
        ('transporte', 'Transporte'),
        ('lazer', 'Lazer'),
        ('saude', 'Saúde'),
        ('educacao', 'Educação'),
        ('outros', 'Outros'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    data = models.DateField()
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.titulo} - R$ {self.valor}'


class LimiteCategoria(models.Model):
    CATEGORIA_CHOICES = [
        ('alimentacao', 'Alimentação'),
        ('transporte', 'Transporte'),
        ('lazer', 'Lazer'),
        ('saude', 'Saúde'),
        ('educacao', 'Educação'),
        ('outros', 'Outros'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    limite = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ['usuario', 'categoria']

    def __str__(self):
        return f'{self.categoria} - R$ {self.limite}'


class MetaFinanceira(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    valor_alvo = models.DecimalField(max_digits=10, decimal_places=2)
    valor_atual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    prazo = models.DateField()
    concluida = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.titulo} - R$ {self.valor_alvo}'

    def percentual(self):
        if self.valor_alvo > 0:
            return min(int((float(self.valor_atual) / float(self.valor_alvo)) * 100), 100)
        return 0