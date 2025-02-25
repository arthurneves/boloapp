from flask import render_template, redirect, url_for, flash

from app.models.log import Log
from . import main_bp
from app.models.regra import Regra
from app.forms.regra_forms import RegraForm
from app import db


@main_bp.route('/regras')
def visualizar_regras():
    regra_ativa = Regra.query.filter_by(is_ativo=True).first()
    return render_template('regras/visualizacao.html', regra=regra_ativa)

@main_bp.route('/regras/editar', methods=['GET', 'POST'])
def editar_regras():
    regra_ativa = Regra.query.filter_by(is_ativo=True).first()
    form = RegraForm()
    if form.validate_on_submit():
        nova_regra = Regra(conteudo_regras=form.conteudo_regras.data)
        db.session.add(nova_regra)
        
        if regra_ativa:
            regra_ativa.is_ativo = False
        nova_regra.is_ativo = True

        db.session.flush()
        
        Log.criar_log(nova_regra.id_regra, 'regras', 'criar')
        db.session.commit()

        flash('Regra atualizada com sucesso!', 'success')
        return redirect(url_for('main.visualizar_regras'))
    
    form.conteudo_regras.data = regra_ativa.conteudo_regras if regra_ativa else ''
    
    return render_template('regras/edicao.html', form=form, regra_ativa=regra_ativa)

@main_bp.route('/regras/versoes')
def lista_versoes_regras():
    regras = Regra.query.order_by(Regra.data_criacao.desc()).all()
    return render_template('regras/lista_versoes.html', regras=regras)

@main_bp.route('/regras/versoes/<int:id>')
def visualizar_versao_regra(id):
    regra = Regra.query.get_or_404(id)
    return render_template('regras/visualizar_versao.html', regra=regra)

@main_bp.route('/regras/ativar/<int:id>')
def ativar_regra(id):
    regra = Regra.query.get_or_404(id)

    regra_ativa = Regra.query.filter_by(is_ativo=True).first()

    if regra_ativa:
        regra_ativa.is_ativo = False

    regra.is_ativo = True

    Log.criar_log(regra.id_regra, 'regras', 'ativar')
    db.session.commit()

    flash('Regra ativada com sucesso!', 'success')
    return redirect(url_for('main.visualizar_regras'))
