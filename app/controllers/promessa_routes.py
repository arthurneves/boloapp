from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from . import main_bp
from app.models.promessa import Promessa
from app.models.usuario import Usuario
from app.forms.promessa_forms import PromessaForm
from app import db

@main_bp.route('/promessas', methods=['GET'])
@login_required
def listar_promessas():
    promessas = Promessa.query.all()
    return render_template('promessas/listar.html', promessas=promessas)

@main_bp.route('/promessas/nova', methods=['GET', 'POST'])
@login_required
def criar_promessa():
    form = PromessaForm()
    
    if form.validate_on_submit():

        usuario = Usuario.query.get(form.id_usuario.data)

        nova_promessa = Promessa(
            titulo_promessa = form.titulo_promessa.data,
            descricao_promessa = form.descricao_promessa.data,
            is_ativo = True,
            id_usuario = usuario.id_usuario
        )
        
        db.session.add(nova_promessa)
        db.session.commit()
        
        flash('Promessa criada com sucesso!', 'success')
        return redirect(url_for('main.listar_promessas'))
    
    return render_template('promessas/nova.html', form=form)

@main_bp.route('/promessas/editar/<int:id_promessa>', methods=['GET', 'POST'])
@login_required
def editar_promessa(id_promessa):
    promessa = Promessa.query.get_or_404(id_promessa)
    
    form = PromessaForm(promessa_id=id_promessa)
    
    if form.validate_on_submit():

        usuario = Usuario.query.get(form.id_usuario.data)

        promessa.titulo_promessa = form.titulo_promessa.data
        promessa.descricao_promessa = form.descricao_promessa.data
        promessa.is_ativo = True
        promessa.id_usuario = usuario.id_usuario
        
        db.session.commit()
        
        flash('Promessa atualizada com sucesso!', 'success')
        return redirect(url_for('main.listar_promessas'))
    
    # Preenche o formulário com os dados existentes
    form.titulo_promessa.data = promessa.titulo_promessa
    form.descricao_promessa.data = promessa.descricao_promessa
    form.id_usuario.data = promessa.id_usuario if promessa.usuario else 0
    
    return render_template('promessas/editar.html', form=form, promessa=promessa)

@main_bp.route('/promessas/desativar/<int:id_promessa>', methods=['GET'])
@login_required
def desativar_promessa(id_promessa):
    promessa = Promessa.query.get_or_404(id_promessa)
    
    # Desativa a promessa
    promessa.is_ativo = False
    db.session.commit()
    
    flash('Promessa desativada com sucesso!', 'success')
    return redirect(url_for('main.listar_promessas'))

@main_bp.route('/promessas/reativar/<int:id_promessa>', methods=['GET'])
@login_required
def reativar_promessa(id_promessa):
    promessa = Promessa.query.get_or_404(id_promessa)

    promessa.is_ativo = True
    db.session.commit()
    
    flash('Promessa reativada com sucesso!', 'success')
    return redirect(url_for('main.listar_promessas'))
