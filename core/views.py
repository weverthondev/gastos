from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import TransacaoForm
from .models import Transacao
from django.db.models import Sum
from datetime import date
import json
from django.core.paginator import Paginator
import csv
from django.http import HttpResponse
from dateutil.relativedelta import relativedelta
from .models import Transacao, LimiteCategoria
from .models import Transacao, LimiteCategoria, MetaFinanceira

def landing_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario ou senha inválidos.')
    return render(request, 'login.html')

def cadastro_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Usuario já existe.')
        else:
            User.objects.create_user(username=username, password=password)
            messages.success(request, 'Conta criada com sucesso. Faça login.')
            return redirect('login')
    return render(request, 'cadastro.html')

def dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    hoje = date.today()
    mes = request.GET.get('mes', str(hoje.month))
    ano = int(request.GET.get('ano', hoje.year))
    tipo_filtro = request.GET.get('tipo', 'todos')
    categoria_filtro = request.GET.get('categoria', 'todos')

    ordem = request.GET.get('ordem', '-data')
    transacoes = Transacao.objects.filter(
        usuario=request.user
    ).order_by(ordem)

    if mes == 'todos':
        transacoes_mes = transacoes.filter(data__year=ano)
    else:
        mes = int(mes)
        transacoes_mes = transacoes.filter(data__month=mes, data__year=ano)

    total_entradas = round(transacoes_mes.filter(tipo='entrada').aggregate(Sum('valor'))['valor__sum'] or 0, 2)
    total_saidas = round(transacoes_mes.filter(tipo='saida').aggregate(Sum('valor'))['valor__sum'] or 0, 2)
    saldo = round(total_entradas - total_saidas, 2)

    if tipo_filtro != 'todos':
        transacoes_mes = transacoes_mes.filter(tipo=tipo_filtro)

    if categoria_filtro != 'todos':
        transacoes_mes = transacoes_mes.filter(categoria=categoria_filtro)

    meses = [
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'),
        (4, 'Abril'), (5, 'Maio'), (6, 'Junho'),
        (7, 'Julho'), (8, 'Agosto'), (9, 'Setembro'),
        (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
    ]

    gastos_categoria = transacoes_mes.filter(tipo='saida').values('categoria').annotate(total=Sum('valor'))

    evolucao = []
    for i in range(5, -1, -1):
        d = hoje - relativedelta(months=i)
        entradas = Transacao.objects.filter(
            usuario=request.user,
            tipo='entrada',
            data__month=d.month,
            data__year=d.year
        ).aggregate(Sum('valor'))['valor__sum'] or 0
        saidas = Transacao.objects.filter(
            usuario=request.user,
            tipo='saida',
            data__month=d.month,
            data__year=d.year
        ).aggregate(Sum('valor'))['valor__sum'] or 0
        evolucao.append({
            'mes': d.strftime('%b/%Y'),
            'entradas': float(entradas),
            'saidas': float(saidas),
        })

    evolucao_labels = json.dumps([e['mes'] for e in evolucao])
    evolucao_entradas = json.dumps([e['entradas'] for e in evolucao])
    evolucao_saidas = json.dumps([e['saidas'] for e in evolucao])
    
    labels = [item['categoria'] for item in gastos_categoria]
    valores = [float(item['total']) for item in gastos_categoria]

    paginator = Paginator(transacoes_mes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    alertas = []
    progressos = []
    limites = LimiteCategoria.objects.filter(usuario=request.user)
    for limite in limites:
        gasto = transacoes_mes.filter(tipo='saida', categoria=limite.categoria).aggregate(Sum('valor'))['valor__sum'] or 0
        percentual = int((float(gasto) / float(limite.limite)) * 100)
        progressos.append({
            'categoria': limite.get_categoria_display(),
            'gasto': round(float(gasto), 2),
            'limite': float(limite.limite),
            'percentual': min(percentual, 100),
            'cor': 'danger' if percentual >= 100 else 'warning' if percentual >= 80 else 'success',
        })
        if percentual >= 80:
            alertas.append({
                'categoria': limite.get_categoria_display(),
                'gasto': round(float(gasto), 2),
                'limite': float(limite.limite),
                'percentual': percentual,
            })

    return render(request, 'dashboard.html', {
        'transacoes': page_obj,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'saldo': saldo,
        'meses': meses,
        'mes_selecionado': mes,
        'ano_selecionado': ano,
        'tipo_filtro': tipo_filtro,
        'categoria_filtro': categoria_filtro,
        'grafico_labels': json.dumps(labels),
        'grafico_valores': json.dumps(valores),
        'page_obj': page_obj,
        'ordem': ordem,
        'evolucao_labels': evolucao_labels,
        'evolucao_entradas': evolucao_entradas,
        'evolucao_saidas': evolucao_saidas,
        'alertas': alertas,
        'progressos': progressos,
    })

def sair_view(request):
    logout(request)
    return redirect('login')

def adicionar_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        form = TransacaoForm(request.POST)
        if form.is_valid():
            transacao = form.save(commit=False)
            transacao.usuario = request.user
            transacao.save()
            messages.success(request, 'Transação adicionada com sucesso! ✅')
            return redirect('dashboard')
    else:
        form = TransacaoForm()
    return render(request, 'adicionar.html', {'form': form})

def excluir_view(request, id):
    if not request.user.is_authenticated:
        return redirect('login')
    transacao = Transacao.objects.get(id=id, usuario=request.user)
    transacao.delete()
    return redirect('dashboard')

def editar_view(request, id):
    if not request.user.is_authenticated:
        return redirect('login')
    transacao = Transacao.objects.get(id=id, usuario=request.user)
    if request.method == 'POST':
        form = TransacaoForm(request.POST, instance=transacao)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transação editada com sucesso! ✅')
            return redirect('dashboard')
    else:
        form = TransacaoForm(instance=transacao)
    return render(request, 'editar.html', {'form': form})

def perfil_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        nome = request.POST.get('first_name', '')
        sobrenome = request.POST.get('last_name', '')
        senha_atual = request.POST.get('senha_atual', '')
        senha_nova = request.POST.get('senha_nova', '')

        request.user.first_name = nome
        request.user.last_name = sobrenome
        request.user.save()

        if senha_atual and senha_nova:
            user = authenticate(request, username=request.user.username, password=senha_atual)
            if user is not None:
                user.set_password(senha_nova)
                user.save()
                messages.success(request, 'Senha alterada com sucesso! Faça login novamente. ✅')
                return redirect('login')
            else:
                messages.error(request, 'Senha atual incorreta.')

        messages.success(request, 'Perfil atualizado com sucesso! ✅')
        return redirect('perfil')
    return render(request, 'perfil.html')

def exportar_csv_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="gastos.csv"'

    writer = csv.writer(response)
    writer.writerow(['Data', 'Título', 'Categoria', 'Tipo', 'Valor', 'Descrição'])

    transacoes = Transacao.objects.filter(usuario=request.user).order_by('-data')
    for transacao in transacoes:
        writer.writerow([
            transacao.data.strftime('%d/%m/%Y'),
            transacao.titulo,
            transacao.get_categoria_display(),
            transacao.get_tipo_display(),
            transacao.valor,
            transacao.descricao or '',
        ])

    return response

def limites_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    categorias = [
        ('alimentacao', 'Alimentação'),
        ('transporte', 'Transporte'),
        ('lazer', 'Lazer'),
        ('saude', 'Saúde'),
        ('educacao', 'Educação'),
        ('outros', 'Outros'),
    ]

    if request.method == 'POST':
        for cat, _ in categorias:
            valor = request.POST.get(cat, '')
            if valor:
                LimiteCategoria.objects.update_or_create(
                    usuario=request.user,
                    categoria=cat,
                    defaults={'limite': valor}
                )
        messages.success(request, 'Limites salvos com sucesso! ✅')
        return redirect('limites')

    limites = {l.categoria: l.limite for l in LimiteCategoria.objects.filter(usuario=request.user)}

    return render(request, 'limites.html', {
            'categorias': categorias,
            'limites': limites,
        })
    
def metas_view(request):
        if not request.user.is_authenticated:
            return redirect('login')

        if request.method == 'POST':
            acao = request.POST.get('acao')

            if acao == 'criar':
                titulo = request.POST.get('titulo')
                valor_alvo = request.POST.get('valor_alvo')
                prazo = request.POST.get('prazo')
                MetaFinanceira.objects.create(
                    usuario=request.user,
                    titulo=titulo,
                    valor_alvo=valor_alvo,
                    prazo=prazo
                )
                messages.success(request, 'Meta criada com sucesso! ✅')

            elif acao == 'atualizar':
                meta_id = request.POST.get('meta_id')
                valor = request.POST.get('valor_atual')
                meta = MetaFinanceira.objects.get(id=meta_id, usuario=request.user)
                meta.valor_atual = valor
                if float(valor) >= float(meta.valor_alvo):
                    meta.concluida = True
                    messages.success(request, f'Parabéns! Meta "{meta.titulo}" concluída! 🎉')
                else:
                    messages.success(request, 'Meta atualizada com sucesso! ✅')
                meta.save()

            elif acao == 'excluir':
                meta_id = request.POST.get('meta_id')
                MetaFinanceira.objects.get(id=meta_id, usuario=request.user).delete()
                messages.success(request, 'Meta excluída! ✅')

            return redirect('metas')

        metas = MetaFinanceira.objects.filter(usuario=request.user).order_by('concluida', 'prazo')
        return render(request, 'metas.html', {'metas': metas})
    
def erro_404_view(request, exception):
    return render(request, '404.html', status=404)