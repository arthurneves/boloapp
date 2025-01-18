from flask import render_template, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models.transacao_pontos import TransacaoPontos
from app.models.usuario import Usuario
from app.models.log import Log
from app.forms.transacao_pontos_forms import TransacaoPontosForm
from . import main_bp

@main_bp.route('/transacoes-pontos', methods=['GET'])
@login_required
def listar_transacoes_pontos():
    transacoes = TransacaoPontos.query.order_by(TransacaoPontos.id_transacao.desc()).all()
    return render_template('transacoes_pontos/listar.html', transacoes=transacoes)

@main_bp.route('/transacoes-pontos/nova', methods=['GET', 'POST'])
@login_required
def criar_transacao_pontos():
    form = TransacaoPontosForm()
    if form.validate_on_submit():
        nova_transacao = TransacaoPontos(
            id_usuario=form.id_usuario.data,
            id_categoria=form.id_categoria.data,
            pontos_transacao=form.pontos_transacao.data,
            descricao_transacao=form.descricao_transacao.data
        )
        
        db.session.add(nova_transacao)
        db.session.commit()

        Log.criar_log(nova_transacao.id_transacao, 'transacao_pontos', 'criar', nova_transacao.id_usuario)
        
        flash('Transação de pontos criada com sucesso!', 'success')
        return redirect(url_for('main.listar_transacoes_pontos'))
    
    return render_template('transacoes_pontos/nova.html', form=form)

@main_bp.route('/transacoes-pontos/editar/<int:id_transacao>', methods=['GET', 'POST'])
@login_required
def editar_transacao_pontos(id_transacao):
    transacao = TransacaoPontos.query.get_or_404(id_transacao)
    form = TransacaoPontosForm()
    
    if form.validate_on_submit():

        transacao.aux_evento = 'edicao'

        if form.pontos_transacao.data < transacao.pontos_transacao:
            transacao.aux_saldo = form.pontos_transacao.data - transacao.pontos_transacao
        else:
            transacao.aux_saldo = transacao.pontos_transacao - form.pontos_transacao.data
 
        transacao.pontos_transacao = form.pontos_transacao.data

        transacao.id_usuario = form.id_usuario.data
        transacao.id_categoria = form.id_categoria.data
        transacao.descricao_transacao = form.descricao_transacao.data
        transacao.is_ativo = True  
     
        db.session.commit()

        Log.criar_log(id_transacao, 'transacao_pontos', 'editar', transacao.id_usuario)
        
        flash('Transação de pontos atualizada com sucesso!', 'success')
        return redirect(url_for('main.listar_transacoes_pontos'))
    
    # Preenche o formulário com os dados atuais da transação
    form.id_usuario.data = transacao.id_usuario
    form.id_categoria.data = transacao.id_categoria
    form.pontos_transacao.data = transacao.pontos_transacao
    form.descricao_transacao.data = transacao.descricao_transacao
    
    return render_template('transacoes_pontos/editar.html', form=form, transacao=transacao)

@main_bp.route('/transacoes-pontos/desativar/<int:id_transacao>', methods=['GET'])
@login_required
def desativar_transacao_pontos(id_transacao):
    transacao = TransacaoPontos.query.get_or_404(id_transacao)

    transacao.aux_evento = 'desativacao'
    
    transacao.is_ativo = False
    db.session.commit()

    Log.criar_log(id_transacao, 'transacao_pontos', 'desativar', transacao.id_usuario)
    
    flash('Transação de pontos desativada com sucesso!', 'success')
    return redirect(url_for('main.listar_transacoes_pontos'))

@main_bp.route('/transacoes-pontos/reativar/<int:id_transacao>', methods=['GET'])
@login_required
def reativar_transacao_pontos(id_transacao):
    transacao = TransacaoPontos.query.get_or_404(id_transacao)

    transacao.aux_evento = 'reativacao'
    
    transacao.is_ativo = True
    db.session.commit()

    Log.criar_log(id_transacao, 'transacao_pontos', 'reativar', transacao.id_usuario)
    
    flash('Transação de pontos reativada com sucesso!', 'success')
    return redirect(url_for('main.listar_transacoes_pontos'))
