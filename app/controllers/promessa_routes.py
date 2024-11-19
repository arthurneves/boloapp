from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from . import main_bp
from sqlalchemy.exc import SQLAlchemyError
from app import db
from app.models.promessa import Promessa
from app.forms.promessa_forms import PromessaForm
import logging


@main_bp.route('/promessas')
@login_required
def listar_promessas():
    try:
        # Listar promessas do usuário atual, ordenadas por data de criação
        promessas = Promessa.query.filter_by(
            id_usuario=current_user.id_usuario
        ).order_by(
            Promessa.data_criacao.desc()
        ).all()
        
        return render_template('promessas/listar.html', promessas=promessas)
    except SQLAlchemyError as e:
        logging.error(f"Erro ao listar promessas: {e}")
        flash('Erro ao carregar promessas. Tente novamente.', 'danger')
        return redirect(url_for('main.home'))

@main_bp.route('/promessas/nova', methods=['GET', 'POST'])
@login_required
def nova_promessa():
    form = PromessaForm()
    
    if form.validate_on_submit():
        try:
            # Criar nova promessa
            nova_promessa = Promessa(
                id_usuario=current_user.id_usuario,
                titulo_promessa=form.titulo_promessa.data,
                descricao_promessa=form.descricao_promessa.data,
                is_ativo=form.is_ativo.data
            )
            db.session.add(nova_promessa)
            db.session.commit()
            flash('Promessa criada com sucesso!', 'success')
            return redirect(url_for('promessa.listar_promessas'))
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Erro ao criar promessa: {e}")
            flash('Erro ao criar promessa. Tente novamente.', 'danger')
    
    return render_template('promessas/nova.html', form=form)

@main_bp.route('/promessas/editar/<int:id_promessa>', methods=['GET', 'POST'])
@login_required
def editar_promessa(id_promessa):
    try:
        # Buscar promessa do usuário atual
        promessa = Promessa.query.filter_by(
            id_promessa=id_promessa, 
            id_usuario=current_user.id_usuario
        ).first_or_404()
        
        form = PromessaForm(obj=promessa)
        
        if form.validate_on_submit():
            try:
                # Atualizar promessa
                form.populate_obj(promessa)
                db.session.commit()
                flash('Promessa atualizada com sucesso!', 'success')
                return redirect(url_for('promessa.listar_promessas'))
            except SQLAlchemyError as e:
                db.session.rollback()
                logging.error(f"Erro ao editar promessa: {e}")
                flash('Erro ao atualizar promessa. Tente novamente.', 'danger')
        
        return render_template('promessas/editar.html', form=form, promessa=promessa)
    
    except SQLAlchemyError as e:
        logging.error(f"Erro ao acessar promessa: {e}")
        flash('Promessa não encontrada ou você não tem permissão.', 'danger')
        return redirect(url_for('promessa.listar_promessas'))

@main_bp.route('/promessas/desativar/<int:id_promessa>', methods=['POST'])
@login_required
def desativar_promessa(id_promessa):
    try:
        # Buscar promessa do usuário atual
        promessa = Promessa.query.filter_by(
            id_promessa=id_promessa, 
            id_usuario=current_user.id_usuario
        ).first_or_404()
        
        # Desativar promessa
        promessa.is_ativo = False
        
        try:
            db.session.commit()
            flash('Promessa desativada com sucesso!', 'success')
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Erro ao desativar promessa: {e}")
            flash('Erro ao desativar promessa. Tente novamente.', 'danger')
        
        return redirect(url_for('promessa.listar_promessas'))
    
    except SQLAlchemyError as e:
        logging.error(f"Erro ao acessar promessa para desativação: {e}")
        flash('Promessa não encontrada ou você não tem permissão.', 'danger')
        return redirect(url_for('promessa.listar_promessas'))
