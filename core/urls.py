from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('login/', views.login_view, name='login'),
    path('cadastro/', views.cadastro_view, name='cadastro'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('adicionar/', views.adicionar_view, name='adicionar'),
    path('editar/<int:id>/', views.editar_view, name='editar'),
    path('excluir/<int:id>/', views.excluir_view, name='excluir'),
    path('sair/', views.sair_view, name='sair'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('exportar/', views.exportar_csv_view, name='exportar'),
    path('limites/', views.limites_view, name='limites'),
    path('metas/', views.metas_view, name='metas'),
]