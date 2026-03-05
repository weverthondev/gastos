from django.contrib import admin
from .models import Transacao, LimiteCategoria, MetaFinanceira

admin.site.register(Transacao)
admin.site.register(LimiteCategoria)
admin.site.register(MetaFinanceira)